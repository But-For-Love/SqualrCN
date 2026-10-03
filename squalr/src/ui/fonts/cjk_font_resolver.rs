use epaint::AlphaFromCoverage;
use epaint::text::{FontData, FontDefinitions, FontFamily, Fonts};
use std::path::{Path, PathBuf};
use std::sync::Arc;

/// A CJK capable font that was located on the host system.
pub struct CjkFont {
    /// Name used to register the font within the egui font definitions.
    pub font_name: String,
    /// Parsed font payload handed to egui.
    pub font_data: FontData,
}

/// Locates a Simplified Chinese capable font for the localized interface.
///
/// Egui only ships latin, cyrillic, and emoji glyphs, so localized text needs a fallback font. The
/// resolver prefers a font shipped next to the executable, then falls back to well known system
/// font locations, and validates the payload before handing it to egui because egui panics when a
/// font payload cannot be parsed.
pub struct CjkFontResolver {}

impl CjkFontResolver {
    /// Font file names that are known to carry Simplified Chinese glyphs.
    const KNOWN_FONT_FILE_NAMES: &'static [&'static str] = &[
        "NotoSansSC-Regular.otf",
        "NotoSansSC-Regular.ttf",
        "NotoSansSC.ttf",
        "NotoSansSC-VF.ttf",
        "NotoSansCJK-Regular.ttc",
        "SourceHanSansSC-Regular.otf",
        "msyh.ttc",
        "msyhl.ttc",
        "Deng.ttf",
        "simhei.ttf",
        "simsun.ttc",
        "PingFang.ttc",
        "Hiragino Sans GB.ttc",
        "wqy-zenhei.ttc",
        "wqy-microhei.ttc",
    ];

    /// Bundled font directories that are searched relative to the executable.
    const BUNDLED_FONT_DIRECTORY_NAMES: &'static [&'static str] = &["fonts", "resources/fonts", "../share/squalr/fonts"];

    /// System font directories for the current platform.
    #[cfg(target_os = "windows")]
    const SYSTEM_FONT_DIRECTORY_PATHS: &'static [&'static str] = &["C:\\Windows\\Fonts", "C:\\WINNT\\Fonts"];

    #[cfg(target_os = "macos")]
    const SYSTEM_FONT_DIRECTORY_PATHS: &'static [&'static str] = &[
        "/System/Library/Fonts",
        "/System/Library/Fonts/Supplemental",
        "/Library/Fonts",
        "/Network/Library/Fonts",
    ];

    #[cfg(target_os = "android")]
    const SYSTEM_FONT_DIRECTORY_PATHS: &'static [&'static str] = &["/system/fonts", "/system/font", "/product/fonts"];

    #[cfg(all(unix, not(target_os = "macos"), not(target_os = "android")))]
    const SYSTEM_FONT_DIRECTORY_PATHS: &'static [&'static str] = &[
        "/usr/share/fonts",
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/opentype",
        "/usr/local/share/fonts",
        "/usr/share/fonts/noto-cjk",
    ];

    /// Name used to register the resolved font within the egui font definitions.
    const REGISTERED_FONT_NAME: &'static str = "localized_text";

    /// Resolves a usable CJK font, or returns none when the host has no suitable font.
    pub fn resolve() -> Option<CjkFont> {
        for candidate_file_path in Self::candidate_file_paths() {
            if let Some(cjk_font) = Self::load_candidate(&candidate_file_path) {
                log::info!("Localized text font resolved from: {:?}", candidate_file_path);

                return Some(cjk_font);
            }
        }

        log::warn!("No CJK capable font was found. Localized text will not render correctly.");

        None
    }

    /// Builds the ordered list of font files that may be probed for CJK glyphs.
    fn candidate_file_paths() -> Vec<PathBuf> {
        let mut candidate_file_paths = Vec::new();

        if let Some(executable_directory) = Self::get_executable_directory() {
            for bundled_font_directory_name in Self::BUNDLED_FONT_DIRECTORY_NAMES {
                let bundled_font_directory = executable_directory.join(bundled_font_directory_name);

                Self::append_candidate_file_paths(&mut candidate_file_paths, &bundled_font_directory);
            }
        }

        for system_font_directory_path in Self::SYSTEM_FONT_DIRECTORY_PATHS {
            Self::append_candidate_file_paths(&mut candidate_file_paths, Path::new(system_font_directory_path));
        }

        candidate_file_paths
    }

    /// Appends every known font file name within a directory to the probe list.
    fn append_candidate_file_paths(
        candidate_file_paths: &mut Vec<PathBuf>,
        font_directory_path: &Path,
    ) {
        for known_font_file_name in Self::KNOWN_FONT_FILE_NAMES {
            candidate_file_paths.push(font_directory_path.join(known_font_file_name));
        }
    }

    /// Returns the directory that contains the running executable.
    fn get_executable_directory() -> Option<PathBuf> {
        let executable_file_path = std::env::current_exe().ok()?;

        executable_file_path.parent().map(Path::to_path_buf)
    }

    /// Reads and validates a candidate font file, returning none when it is unusable.
    fn load_candidate(candidate_file_path: &Path) -> Option<CjkFont> {
        if !candidate_file_path.is_file() {
            return None;
        }

        let font_bytes = match std::fs::read(candidate_file_path) {
            Ok(font_bytes) => font_bytes,
            Err(error) => {
                log::debug!("Failed to read candidate font {:?}: {}", candidate_file_path, error);

                return None;
            }
        };

        if !Self::has_true_type_header(&font_bytes) {
            log::debug!("Candidate font {:?} does not look like a true type font.", candidate_file_path);

            return None;
        }

        if !Self::is_parseable(&font_bytes) {
            log::debug!("Candidate font {:?} could not be parsed and was skipped.", candidate_file_path);

            return None;
        }

        Some(CjkFont {
            font_name: Self::REGISTERED_FONT_NAME.to_string(),
            font_data: FontData::from_owned(font_bytes),
        })
    }

    /// Checks the sfnt magic number used by true type, open type, and font collections.
    fn has_true_type_header(font_bytes: &[u8]) -> bool {
        if font_bytes.len() < 4 {
            return false;
        }

        let sfnt_magic = u32::from_be_bytes([font_bytes[0], font_bytes[1], font_bytes[2], font_bytes[3]]);

        matches!(sfnt_magic, 0x0001_0000 | 0x7472_7565 | 0x4F54_544F | 0x7474_6366 | 0x7479_7031)
    }

    /// Verifies that egui can parse the font payload without panicking.
    fn is_parseable(font_bytes: &[u8]) -> bool {
        let mut validation_definitions = FontDefinitions::empty();
        validation_definitions
            .font_data
            .insert(Self::REGISTERED_FONT_NAME.to_string(), Arc::new(FontData::from_owned(font_bytes.to_vec())));
        validation_definitions
            .families
            .insert(FontFamily::Proportional, vec![Self::REGISTERED_FONT_NAME.to_string()]);
        let validation_result = std::panic::catch_unwind(move || {
            // Building a font set parses every payload exactly like the egui render loop does.
            Fonts::new(1024, AlphaFromCoverage::default(), validation_definitions)
        });

        validation_result.is_ok()
    }
}

#[cfg(test)]
mod tests {
    use super::CjkFontResolver;

    #[test]
    fn rejects_payloads_without_a_true_type_header() {
        assert!(!CjkFontResolver::has_true_type_header(&[]));
        assert!(!CjkFontResolver::has_true_type_header(&[0x00, 0x01, 0x00]));
        assert!(!CjkFontResolver::has_true_type_header(b"not a font"));
    }

    #[test]
    fn accepts_known_sfnt_magic_numbers() {
        assert!(CjkFontResolver::has_true_type_header(&[0x00, 0x01, 0x00, 0x00]));
        assert!(CjkFontResolver::has_true_type_header(b"ttcf"));
        assert!(CjkFontResolver::has_true_type_header(b"OTTO"));
    }

    #[test]
    fn rejects_payloads_that_cannot_be_parsed() {
        let fake_font_payload = [0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00];

        assert!(!CjkFontResolver::is_parseable(&fake_font_payload));
    }
}
