"""Validation of submitted form payloads against a template's field definitions."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.models.enums import FieldType

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_form(fields: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, str]:
    """Return a ``{field_key: message}`` mapping; empty means the payload is valid."""
    errors: dict[str, str] = {}

    for field in fields:
        key = field["key"]
        label = field.get("label", key)
        value = data.get(key)

        if _is_blank(value):
            if field.get("required"):
                errors[key] = f"{label}は必須項目です"
            continue

        field_type = _field_type(field.get("type"))
        if field_type is FieldType.NUMBER:
            number = _coerce_number(value)
            if number is None:
                errors[key] = f"{label}は数値で入力してください"
            elif "min" in field and number < field["min"]:
                errors[key] = f"{label}は{field['min']}以上で入力してください"
            elif "max" in field and number > field["max"]:
                errors[key] = f"{label}は{field['max']}以下で入力してください"
        elif field_type is FieldType.DATE:
            if not _is_iso_date(value):
                errors[key] = f"{label}はYYYY-MM-DD形式で入力してください"
        elif field_type is FieldType.SELECT:
            options = field.get("options") or []
            if value not in options:
                errors[key] = f"{label}は選択肢から選んでください"
        else:
            if not isinstance(value, str):
                errors[key] = f"{label}は文字列で入力してください"
            elif "max_length" in field and len(value) > field["max_length"]:
                errors[key] = f"{label}は{field['max_length']}文字以内で入力してください"

    return errors


def _field_type(raw: Any) -> FieldType:
    try:
        return FieldType(raw)
    except ValueError:
        return FieldType.TEXT


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def _is_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not _DATE_PATTERN.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
