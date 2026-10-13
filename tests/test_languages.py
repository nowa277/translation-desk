import pytest

from quick_translate.languages import TargetSelection


def test_default_targets_are_ordered():
    assert TargetSelection().ordered() == ("en", "ja", "ko")


def test_toggle_removes_and_readds_target_in_default_order():
    selection = TargetSelection()
    selection.toggle("ja")
    assert selection.ordered() == ("en", "ko")
    selection.toggle("ja")
    assert selection.ordered() == ("en", "ja", "ko")


def test_selection_never_becomes_empty():
    selection = TargetSelection(("en",))
    selection.toggle("en")
    assert selection.ordered() == ("en",)


def test_chinese_and_extra_targets_can_be_selected():
    selection = TargetSelection()
    for code in ("zh", "de", "fr", "es"):
        selection.toggle(code)
        assert selection.is_enabled(code)
    assert selection.ordered() == ("en", "ja", "ko", "de", "fr", "es", "zh")


def test_unknown_target_is_rejected():
    with pytest.raises(ValueError):
        TargetSelection(("xx",))
