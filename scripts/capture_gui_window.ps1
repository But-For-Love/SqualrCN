# Captures the full Squalr window into a PNG for documentation and verification.
#
# The script enables per monitor DPI awareness before probing the window, because a
# DPI unaware caller only sees a virtualized window rectangle (for example 1280x840 on a
# 150 percent display where the real window is 1920x1260) and would capture a clipped image.
param(
    [string]$ExecutablePath = "dist\Squalr-中文版-v0.4.0\squalr.exe",
    [string]$OutputPath = "docs\zh-CN\images\主界面.png",
    [int]$StartupDelaySeconds = 10
)

Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class SqualrWindowSnapshot {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }

    [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr dpiContext);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr windowHandle, out RECT rectangle);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr windowHandle);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr windowHandle, IntPtr deviceContext, uint flags);
    [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr windowHandle);

    public static bool EnablePerMonitorDpiAwareness() {
        // DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 is the handle value -4.
        return SetProcessDpiAwarenessContext(new IntPtr(-4));
    }
}
"@

if (-not [SqualrWindowSnapshot]::EnablePerMonitorDpiAwareness()) {
    Write-Host "Warning: could not enable per monitor DPI awareness; the capture may be clipped."
}

$resolvedExecutablePath = (Resolve-Path $ExecutablePath).Path
$resolvedOutputPath = Join-Path (Get-Location) $OutputPath
$process = Start-Process -FilePath $resolvedExecutablePath -WorkingDirectory (Split-Path $resolvedExecutablePath) -PassThru
Write-Host "Started process id $($process.Id)"

$windowHandle = [IntPtr]::Zero
for ($attempt = 0; $attempt -lt 50; $attempt++) {
    Start-Sleep -Milliseconds 400
    $process.Refresh()

    if ($process.HasExited) {
        Write-Host "FATAL: process exited early with code $($process.ExitCode)"
        exit 1
    }

    if ($process.MainWindowHandle -ne 0 -and [SqualrWindowSnapshot]::IsWindowVisible($process.MainWindowHandle)) {
        $windowHandle = $process.MainWindowHandle
        break
    }
}

if ($windowHandle -eq [IntPtr]::Zero) {
    Write-Host "FATAL: no visible main window was found."
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    exit 2
}

# Let the first frames render, including the asynchronous update check.
Start-Sleep -Seconds $StartupDelaySeconds

$windowRectangle = New-Object SqualrWindowSnapshot+RECT
[SqualrWindowSnapshot]::GetWindowRect($windowHandle, [ref]$windowRectangle) | Out-Null
$captureWidth = $windowRectangle.Right - $windowRectangle.Left
$captureHeight = $windowRectangle.Bottom - $windowRectangle.Top
Write-Host "window=${captureWidth}x${captureHeight} dpi=$([SqualrWindowSnapshot]::GetDpiForWindow($windowHandle))"

$bitmap = New-Object System.Drawing.Bitmap $captureWidth, $captureHeight
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$deviceContext = $graphics.GetHdc()
# 0x00000002 asks the compositor for the complete window content.
$printResult = [SqualrWindowSnapshot]::PrintWindow($windowHandle, $deviceContext, 2)
$graphics.ReleaseHdc($deviceContext)
$bitmap.Save($resolvedOutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "PrintWindow=$printResult saved=$resolvedOutputPath"
Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
