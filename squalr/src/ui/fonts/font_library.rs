use crate::ui::fonts::{cjk_font_resolver::CjkFontResolver, font_set::FontSet};
use eframe::egui::{Context, FontData, FontDefinitions, FontFamily};
use std::sync::Arc;

static FONT_NOTO_SANS: &[u8] = include_bytes!("../../../fonts/NotoSans.ttf");
static FONT_UBUNTU_MONO_BOLD: &[u8] = include_bytes!("../../../fonts/UbuntuMonoBold.ttf");

pub struct FontLibrary {
    pub font_noto_sans: FontSet,
    pub font_ubuntu_mono_bold: FontSet,
}

impl FontLibrary {
    pub fn new(context: &Context) -> Self {
        let mut fonts = FontDefinitions::default();

        Self::register_font(&mut fonts, "noto_sans", FONT_NOTO_SANS);
        Self::register_font(&mut fonts, "ubuntu_mono_bold", FONT_UBUNTU_MONO_BOLD);
        Self::register_localized_text_fallback(&mut fonts);

        context.set_fonts(fonts);

        Self {
            font_noto_sans: FontSet::new(FontFamily::Name("noto_sans".into()), 9.0, 13.0, 14.0, 14.0),
            font_ubuntu_mono_bold: FontSet::new(FontFamily::Name("ubuntu_mono_bold".into()), 11.0, 15.0, 16.0, 16.0),
        }
    }

    fn register_font(
        fonts: &mut FontDefinitions,
        name: &str,
        data: &'static [u8],
    ) {
        fonts
            .font_data
            .insert(name.to_owned(), FontData::from_static(data).into());
        fonts
            .families
            .insert(FontFamily::Name(name.into()), vec![name.to_owned()]);
    }

    /// Registers a CJK capable font as the lowest priority fallback of every family.
    ///
    /// The bundled fonts only cover latin and cyrillic glyphs, so localized interface text needs a
    /// system font to fall back to. Appending keeps the configured look for latin text.
    fn register_localized_text_fallback(fonts: &mut FontDefinitions) {
        let Some(cjk_font) = CjkFontResolver::resolve() else {
            return;
        };
        let fallback_font_name = cjk_font.font_name.clone();

        fonts.font_data.insert(fallback_font_name.clone(), Arc::new(cjk_font.font_data));

        for family_font_names in fonts.families.values_mut() {
            if !family_font_names.contains(&fallback_font_name) {
                family_font_names.push(fallback_font_name.clone());
            }
        }
    }
}
