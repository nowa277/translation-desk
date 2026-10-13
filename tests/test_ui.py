import os

import pytest
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent, QInputMethodEvent
from PyQt6.QtTest import QSignalSpy, QTest
from PyQt6.QtWidgets import QApplication

from quick_translate.ui import TranslationWindow


@pytest.fixture(scope="session")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def window(qapp):
    widget = TranslationWindow()
    widget.show()
    qapp.processEvents()
    yield widget
    widget.close()
    widget.deleteLater()
    qapp.processEvents()


def test_default_targets_and_source_modes(window):
    assert window.visible_target_codes() == ("en", "ja", "ko")
    assert window.source_codes() == ("auto", "zh", "en")
    assert window.source_code() == "auto"


def test_target_toggle_and_selection(window):
    window.toggle_target("ja")
    assert window.visible_target_codes() == ("en", "ko")
    window.select_target("ko")
    assert window.selected_target() == "ko"
    window.toggle_target("en")
    window.toggle_target("ko")
    assert window.visible_target_codes() == ("ko",)


def test_freshness_invalidates_paste_readiness(window):
    window.set_results({"en": "ready"})
    window.select_target("en")
    assert window.can_paste() is True
    revision = window.invalidate_translation()
    assert revision == 1
    assert window.can_paste() is False


def test_out_of_order_result_is_ignored(window):
    first = window.invalidate_translation()
    second = window.invalidate_translation()
    window.apply_result(first, "en", "old")
    assert window.result_for("en") == ""
    window.apply_result(second, "en", "new")
    assert window.result_for("en") == "new"


def test_error_for_one_target_does_not_erase_other_results(window):
    revision = window.invalidate_translation()
    window.apply_result(revision, "en", "English")
    window.apply_error(revision, "ja", "Translation unavailable")
    assert window.result_for("en") == "English"
    assert window.result_for("ja") == ""
    assert window.status_text() == "Translation unavailable"
    assert window.can_paste() is True


def test_long_result_is_scrollable(window):
    window.set_results({"en": "line\n" * 200})
    assert window.result_view("en").isVisible()
    assert window.result_view("en").verticalScrollBar() is not None


def test_ime_preedit_enter_is_not_paste(window):
    window.set_results({"en": "ready"})
    window.select_target("en")
    editor = window.source_editor
    editor.setFocus()
    spy = QSignalSpy(window.paste_requested)
    QApplication.sendEvent(editor, QInputMethodEvent("composing", []))
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert len(spy) == 0
    assert editor.composing


def test_enter_pastes_only_valid_current_result(window):
    window.set_results({"en": "ready"})
    window.select_target("en")
    spy = QSignalSpy(window.paste_requested)
    window.trigger_paste()
    assert list(spy) == [["en"]]
    window.invalidate_translation()
    window.trigger_paste()
    assert list(spy) == [["en"]]


def test_shortcuts_cycle_and_fixed_target_mapping(window):
    window.select_target("en")
    window.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier))
    assert window.selected_target() == "ja"
    window.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_3, Qt.KeyboardModifier.ControlModifier))
    assert window.selected_target() == "ko"
