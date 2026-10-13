import pytest

from quick_translate.x11 import PasteSafetyError, paste_to_window


class Keyboard:
    def __init__(self):
        self.events = []

    def key_down(self, key):
        self.events.append(f"{key}-down")

    def key_up(self, key):
        self.events.append(f"{key}-up")

    def press(self, key):
        self.events.append(key)


def test_regular_paste_uses_ctrl_v_after_captured_focus():
    keyboard = Keyboard()
    paste_to_window(123, False, keyboard, activate=lambda _: True, focus_check=lambda _: True)
    assert keyboard.events == ["ctrl-down", "v", "v-up", "ctrl-up"]


def test_terminal_paste_uses_ctrl_shift_v():
    keyboard = Keyboard()
    paste_to_window(123, True, keyboard, activate=lambda _: True, focus_check=lambda _: True)
    assert keyboard.events == ["ctrl-down", "shift-down", "v", "v-up", "shift-up", "ctrl-up"]


def test_missing_or_unverified_target_refuses_to_paste():
    with pytest.raises(PasteSafetyError):
        paste_to_window(None, False, Keyboard())
    with pytest.raises(PasteSafetyError):
        paste_to_window(123, False, Keyboard(), activate=lambda _: True, focus_check=lambda _: False)
