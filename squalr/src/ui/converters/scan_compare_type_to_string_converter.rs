use squalr_engine_api::structures::scanning::comparisons::{
    scan_compare_type::ScanCompareType, scan_compare_type_delta::ScanCompareTypeDelta, scan_compare_type_immediate::ScanCompareTypeImmediate,
    scan_compare_type_relative::ScanCompareTypeRelative,
};

pub struct ScanCompareTypeToStringConverter {}

impl ScanCompareTypeToStringConverter {
    pub fn convert_scan_compare_type_immediate_to_string(scan_compare_type_immediate: &ScanCompareTypeImmediate) -> &'static str {
        match scan_compare_type_immediate {
            ScanCompareTypeImmediate::Equal => "等于",
            ScanCompareTypeImmediate::NotEqual => "不等于",
            ScanCompareTypeImmediate::GreaterThan => "大于",
            ScanCompareTypeImmediate::GreaterThanOrEqual => "大于等于",
            ScanCompareTypeImmediate::LessThan => "小于",
            ScanCompareTypeImmediate::LessThanOrEqual => "小于等于",
        }
    }

    pub fn convert_scan_compare_type_delta_to_string(scan_compare_type_delta: &ScanCompareTypeDelta) -> &'static str {
        match scan_compare_type_delta {
            ScanCompareTypeDelta::IncreasedByX => "增加 x",
            ScanCompareTypeDelta::DecreasedByX => "减少 x",
            ScanCompareTypeDelta::MultipliedByX => "乘以 x",
            ScanCompareTypeDelta::DividedByX => "除以 x",
            ScanCompareTypeDelta::ModuloByX => "取模 x",
            ScanCompareTypeDelta::ShiftLeftByX => "左移 x",
            ScanCompareTypeDelta::ShiftRightByX => "右移 x",
            ScanCompareTypeDelta::LogicalAndByX => "逻辑与 x",
            ScanCompareTypeDelta::LogicalOrByX => "逻辑或 x",
            ScanCompareTypeDelta::LogicalXorByX => "逻辑异或 x",
        }
    }

    pub fn convert_scan_compare_type_relative_to_string(scan_compare_type_relative: &ScanCompareTypeRelative) -> &'static str {
        match scan_compare_type_relative {
            ScanCompareTypeRelative::Changed => "已变化",
            ScanCompareTypeRelative::Unchanged => "未变化",
            ScanCompareTypeRelative::Increased => "增大",
            ScanCompareTypeRelative::Decreased => "减小",
        }
    }

    pub fn convert_scan_compare_type_to_string(scan_compare_type: &ScanCompareType) -> &'static str {
        match scan_compare_type {
            ScanCompareType::Immediate(im) => Self::convert_scan_compare_type_immediate_to_string(im),
            ScanCompareType::Delta(delta) => Self::convert_scan_compare_type_delta_to_string(delta),
            ScanCompareType::Relative(rel) => Self::convert_scan_compare_type_relative_to_string(rel),
        }
    }
}
