use std::str::FromStr;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StructViewerContainerMode {
    Element,
    Array,
}

impl StructViewerContainerMode {
    pub const ALL: [Self; 2] = [Self::Element, Self::Array];

    pub fn label(&self) -> &'static str {
        match self {
            Self::Element => "元素",
            Self::Array => "数组",
        }
    }
}

impl FromStr for StructViewerContainerMode {
    type Err = String;

    fn from_str(string: &str) -> Result<Self, Self::Err> {
        // English aliases are kept so that values authored before localization still parse.
        match string.trim() {
            "元素" | "Element" => Ok(Self::Element),
            "数组" | "Array" => Ok(Self::Array),
            invalid_mode => Err(format!("结构查看器容器模式无效：{}", invalid_mode)),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::StructViewerContainerMode;
    use std::str::FromStr;

    #[test]
    fn parses_localized_and_english_container_modes() {
        assert_eq!(StructViewerContainerMode::from_str("元素"), Ok(StructViewerContainerMode::Element));
        assert_eq!(StructViewerContainerMode::from_str("Element"), Ok(StructViewerContainerMode::Element));
        assert_eq!(StructViewerContainerMode::from_str("数组"), Ok(StructViewerContainerMode::Array));
        assert_eq!(StructViewerContainerMode::from_str("Array"), Ok(StructViewerContainerMode::Array));
        assert!(StructViewerContainerMode::from_str("bogus").is_err());
    }
}
