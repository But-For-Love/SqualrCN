# Agentic Current Task
Our current task, from `README.md`, is:
`pr/todo`

# Notes from Owner
- Assume any unstaged/uncommitted file changes are from a previous iteration, or from the human author giving guidance. Keep them if they look good; do not ask about them by default.
- Assume any connected Android devices are rooted, and assume macOS has SIP disabled.
- Do not declare behavior as fixed. Use "needs human verification" after implementation and validation.

## Current Tasklist
- None open. The Simplified Chinese localization round (interface text, CJK font fallback, Chinese tutorial, Windows packaging) is complete and committed.

## Important Information

### Simplified Chinese localization (completed this round)
- `squalr/src` interface text is localized in place. The glossary and the maintenance tooling live in `scripts/localization/` (see its `README.md`).
- `squalr/src/ui/fonts/cjk_font_resolver.rs` locates a system CJK font and validates it by parsing before handing it to egui, then `FontLibrary` appends it as the lowest priority fallback of every font family. Without this, localized text renders as missing glyph boxes.
- Untranslated by design: engine and plugin log output, data type ids (`i32`, `u64`, `i_x64`), window and action ids, egui id salts, and project file formats.
- `StructViewerContainerMode::from_str` accepts both localized and english labels so data authored before localization still parses.
- Chinese docs: `docs/zh-CN/Squalr中文版使用教程.md` plus the generated `.docx` (regenerate with `python scripts/docs/markdown_to_docx.py`).
- Windows packaging: `python scripts/package_windows_release.py` builds `dist/Squalr-中文版-v<version>/` and a zip. `squalr/build.rs` now embeds the app icon and version metadata (the manifest previously had `build = "build.rs"` commented out and the icon path was stale).
- Verified this round: `cargo build -p squalr --release` is clean, the packaged exe launches standalone from `dist/` with a fully localized interface, and a captured window screenshot confirmed Chinese glyph rendering.

### Known pre-existing issue
- `cargo test -p squalr --lib` fails on `instruction_project_item_preview_disassembles_byte_window_as_block`: the test expects `"inc dword [rax]"` while the x86 plugin disassembles `"inc dword ptr [rax]"`. This failure reproduces on the unmodified upstream source (`git stash` check), so it is unrelated to the localization. The test expectation is likely stale.
