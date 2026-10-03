use squalr_engine_api::structures::data_values::anonymous_value_string_format::AnonymousValueStringFormat;

/// Converts anonymous value string formats into localized display labels.
///
/// The engine keeps its own english format names because they are parsed back from user input and
/// from settings files, so localization happens here in the interface layer.
pub struct AnonymousValueStringFormatToStringConverter {}

impl AnonymousValueStringFormatToStringConverter {
    /// Returns the localized label for a display format.
    pub fn convert_anonymous_value_string_format_to_string(anonymous_value_string_format: AnonymousValueStringFormat) -> &'static str {
        match anonymous_value_string_format {
            AnonymousValueStringFormat::Bool => "布尔值",
            AnonymousValueStringFormat::String => "字符串",
            AnonymousValueStringFormat::Binary => "二进制",
            AnonymousValueStringFormat::Decimal => "十进制",
            AnonymousValueStringFormat::Hexadecimal => "十六进制",
            AnonymousValueStringFormat::Address => "地址",
            AnonymousValueStringFormat::DataTypeRef => "数据类型引用",
            AnonymousValueStringFormat::Enumeration => "枚举",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::AnonymousValueStringFormatToStringConverter;
    use squalr_engine_api::structures::data_values::anonymous_value_string_format::AnonymousValueStringFormat;

    #[test]
    fn converts_every_display_format_to_a_label() {
        assert_eq!(
            AnonymousValueStringFormatToStringConverter::convert_anonymous_value_string_format_to_string(AnonymousValueStringFormat::Hexadecimal),
            "十六进制"
        );
        assert_eq!(
            AnonymousValueStringFormatToStringConverter::convert_anonymous_value_string_format_to_string(AnonymousValueStringFormat::Decimal),
            "十进制"
        );
        assert_eq!(
            AnonymousValueStringFormatToStringConverter::convert_anonymous_value_string_format_to_string(AnonymousValueStringFormat::Binary),
            "二进制"
        );
    }
}
