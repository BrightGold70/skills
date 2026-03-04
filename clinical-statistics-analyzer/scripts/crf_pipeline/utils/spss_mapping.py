"""SPSS value <-> code bidirectional mapping utilities."""

from typing import Any, Dict, Optional


def value_to_code(value: Any, mapping: Dict) -> Optional[int]:
    """Convert a text value to its SPSS numeric code."""
    if value is None:
        return None
    str_val = str(value)
    if str_val in mapping:
        result = mapping[str_val]
        if isinstance(result, (int, float)):
            return int(result)
    return None


def code_to_value(code: Any, mapping: Dict) -> Optional[str]:
    """Convert an SPSS numeric code to its text label."""
    if code is None:
        return None
    str_code = str(int(code)) if isinstance(code, float) else str(code)
    if str_code in mapping:
        result = mapping[str_code]
        if isinstance(result, str):
            return result
    return None


def build_bidirectional_mapping(mapping: Dict) -> Dict:
    """Ensure a mapping has both value->code and code->value entries."""
    result = dict(mapping)
    for key, value in list(mapping.items()):
        str_val = str(value)
        if str_val not in result:
            result[str_val] = key
    return result
