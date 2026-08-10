"""フォーム定義に対する入力検証。"""

from __future__ import annotations

import pytest

from app.services.form_validation import validate_form


def field(**overrides):
    return {"key": "amount", "label": "金額", "type": "number", "required": True, **overrides}


def test_required_fields_must_be_present():
    assert validate_form([field()], {}) == {"amount": "金額は必須項目です"}


def test_optional_fields_may_be_omitted():
    assert validate_form([field(required=False)], {}) == {}


def test_numbers_must_be_numeric():
    assert "数値" in validate_form([field()], {"amount": "たくさん"})["amount"]


def test_numeric_strings_are_accepted():
    assert validate_form([field()], {"amount": "12,000"}) == {}


def test_bounds_are_enforced():
    assert validate_form([field(min=100)], {"amount": 50}) != {}
    assert validate_form([field(max=1000)], {"amount": 5000}) != {}
    assert validate_form([field(min=100, max=1000)], {"amount": 500}) == {}


def test_unset_bounds_are_ignored():
    """API 経由で作られたフォームは min/max を ``None`` として持つ。

    ``"min" in field`` だけで判定すると ``None`` と比較して TypeError になり、
    入力検証が 500 エラーになっていた。
    """
    definition = field(min=None, max=None, max_length=None)

    assert validate_form([definition], {"amount": 5000}) == {}


def test_unset_max_length_is_ignored_for_text():
    definition = {"key": "memo", "label": "備考", "type": "text", "max_length": None}

    assert validate_form([definition], {"memo": "長さの制限がない自由記述"}) == {}


def test_max_length_is_enforced_when_set():
    definition = {"key": "memo", "label": "備考", "type": "text", "max_length": 5}

    assert validate_form([definition], {"memo": "123456"}) != {}


@pytest.mark.parametrize("value", ["2026-08-09"])
def test_iso_dates_are_accepted(value):
    assert validate_form([{"key": "d", "label": "日付", "type": "date"}], {"d": value}) == {}


@pytest.mark.parametrize("value", ["2026/08/09", "2026-13-01", "きょう"])
def test_malformed_dates_are_rejected(value):
    assert validate_form([{"key": "d", "label": "日付", "type": "date"}], {"d": value}) != {}


def test_select_values_must_come_from_the_options():
    definition = {"key": "c", "label": "費目", "type": "select", "options": ["交通費", "会議費"]}

    assert validate_form([definition], {"c": "交通費"}) == {}
    assert validate_form([definition], {"c": "宇宙旅行"}) != {}
