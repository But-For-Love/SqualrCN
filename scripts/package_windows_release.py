"""Build and package the localized Squalr Windows GUI release.

The script builds the `squalr` binary in release mode and assembles a ready to
use folder plus a zip archive under `dist/`. Run it from the repository root:

    python scripts/package_windows_release.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "squalr" / "Cargo.toml"
BINARY_PATH = ROOT / "target" / "release" / "squalr.exe"
DIST_ROOT = ROOT / "dist"
DOCS_ROOT = ROOT / "docs" / "zh-CN"

README_TEXT = """========================================================================
 Squalr 中文版 v{version} —— 使用说明
========================================================================

【这是什么】
  Squalr 是一款高性能的进程内存扫描与动态分析（逆向工程）工具。
  本版本已完成界面汉化，并内置中文字体自动回退，开箱即用。

【如何运行】
  1) 右键 squalr.exe →「以管理员身份运行」。
     说明：不加管理员权限时，部分进程无法打开、内存无法读写。
  2) 首次运行会在本目录生成配置文件（见下方"配置文件"）。
  3) 顶部「选择进程...」选择目标程序，然后在「扫描器」窗口开始扫描。

【完整教程】
  请阅读 docs 目录下的：
    - Squalr中文版使用教程.docx  （Word 版，推荐）
    - Squalr中文版使用教程.md    （Markdown 版，可用记事本打开）
  内容包含：快速上手、扫描模式、内存/代码查看器、指针扫描、
  调试跟踪、项目系统、设置说明、快捷键与常见问题。

【重要提示：请放在可写目录】
  程序会在自身所在目录写入以下文件，请勿放在 C:\\Program Files\\ 等
  需要管理员权限才能写入的位置：
    docking_settings.json   窗口布局
    scan_settings.json      扫描与内存查询设置
    project_settings.json   项目根目录设置
  项目文件默认保存在「文档\\Squalr\\」目录下。

【界面显示成方块怎么办】
  正常情况下无需任何操作（程序会自动使用系统中文字体）。
  若仍显示异常，可在本目录下新建 fonts 文件夹，放入任意中文字体
  （如 NotoSansSC-VF.ttf、msyh.ttc、simhei.ttf），然后重启程序。

【快捷键】
  Ctrl+C / Ctrl+X / Ctrl+V   复制 / 剪切 / 粘贴
  Enter                      提交输入；Ctrl+Enter 强制提交
  F2                         重命名选中条目
  Delete                     删除选中条目
  Esc                        关闭弹出窗口
  双击标题栏                  最大化 / 还原

【合法使用声明】
  本工具仅用于合法的逆向工程、学习研究与自有软件调试。
  请勿用于破解他人软件、绕过授权、网游作弊或任何违法行为。
  使用后果由使用者自行承担。

  原始项目：https://github.com/Squalr/Squalr （GPL-3.0）
========================================================================
"""


def read_package_version() -> str:
    """Read the squalr package version from its manifest."""
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', manifest_text, re.MULTILINE)
    if version_match is None:
        raise RuntimeError("Could not resolve the squalr package version.")

    return version_match.group(1)


def build_release_binary() -> None:
    """Build the release binary, streaming cargo output to the console."""
    print("building squalr release binary...")
    build_result = subprocess.run(["cargo", "build", "-p", "squalr", "--release"], cwd=ROOT, check=False)
    if build_result.returncode != 0:
        raise RuntimeError(f"cargo build failed with exit code {build_result.returncode}.")

    if not BINARY_PATH.is_file():
        raise RuntimeError(f"Expected binary was not produced: {BINARY_PATH}")


def assemble_package(version: str) -> Path:
    """Copy the binary, documentation, and license into the package folder."""
    package_directory = DIST_ROOT / f"Squalr-中文版-v{version}"
    if package_directory.exists():
        shutil.rmtree(package_directory)
    (package_directory / "docs" / "images").mkdir(parents=True, exist_ok=True)

    shutil.copy2(BINARY_PATH, package_directory / "squalr.exe")
    shutil.copy2(ROOT / "LICENSE", package_directory / "LICENSE.txt")

    for document_name in ("Squalr中文版使用教程.docx", "Squalr中文版使用教程.md"):
        document_path = DOCS_ROOT / document_name
        if document_path.is_file():
            shutil.copy2(document_path, package_directory / "docs" / document_name)

    screenshot_directory = DOCS_ROOT / "images"
    if screenshot_directory.is_dir():
        for screenshot_path in screenshot_directory.iterdir():
            shutil.copy2(screenshot_path, package_directory / "docs" / "images" / screenshot_path.name)

    readme_path = package_directory / "使用说明.txt"
    readme_path.write_text(README_TEXT.format(version=version), encoding="utf-8-sig")

    return package_directory


def create_zip_archive(package_directory: Path) -> Path:
    """Zip the package folder for easy transfer."""
    archive_base_path = DIST_ROOT / package_directory.name
    archive_path = Path(shutil.make_archive(str(archive_base_path), "zip", root_dir=DIST_ROOT, base_dir=package_directory.name))

    # Recompress with deflate level 9 so the 29 MB binary does not dominate the archive.
    temporary_archive_path = archive_path.with_suffix(".tmp.zip")
    with zipfile.ZipFile(archive_path, "r") as source_archive:
        with zipfile.ZipFile(temporary_archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as target_archive:
            for archive_entry in source_archive.infolist():
                target_archive.writestr(archive_entry, source_archive.read(archive_entry.filename))
    temporary_archive_path.replace(archive_path)

    return archive_path


def main() -> int:
    """Build and package the release."""
    version = read_package_version()
    build_release_binary()
    package_directory = assemble_package(version)
    archive_path = create_zip_archive(package_directory)

    print(f"package: {package_directory}")
    print(f"archive: {archive_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
