//! Build script that embeds the Windows application icon and version metadata.
//!
//! Resource compilation failures are intentionally non fatal, so toolchains without the Windows
//! resource compiler can still build the GUI binary.

fn main() {
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() != Ok("windows") {
        return;
    }

    println!("cargo:rerun-if-changed=images/app/app_icon.ico");

    let mut windows_resource = winresource::WindowsResource::new();
    windows_resource
        .set_icon("images/app/app_icon.ico")
        .set("FileDescription", "Squalr dynamic analysis and reverse-engineering toolkit")
        .set("ProductName", "Squalr")
        .set("OriginalFilename", "squalr.exe")
        .set("LegalCopyright", "GNU General Public License v3.0")
        .set_version_info(winresource::VersionInfo::FILEVERSION, 0x0004_0000_0000_0000)
        .set_version_info(winresource::VersionInfo::PRODUCTVERSION, 0x0004_0000_0000_0000);

    if let Err(error) = windows_resource.compile() {
        println!("cargo:warning=Failed to embed Windows application resources: {error}");
    }
}
