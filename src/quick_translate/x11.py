import time

from Xlib import X, display, protocol
from pynput.keyboard import Key

TERMINAL_CLASSES = {"konsole", "gnome-terminal", "kitty", "alacritty", "xterm", "wezterm", "foot"}


class PasteSafetyError(RuntimeError):
    pass


def active_window_info():
    d = display.Display()
    root = d.screen().root
    prop = root.get_full_property(d.intern_atom("_NET_ACTIVE_WINDOW"), X.AnyPropertyType)
    if not prop or not prop.value or not prop.value[0]:
        return None, False
    wid = prop.value[0]
    cls = d.create_resource_object("window", wid).get_wm_class() or ()
    return wid, any(item.lower() in TERMINAL_CLASSES for item in cls)


def request_blur(window_id, width, height):
    d = display.Display()
    win = d.create_resource_object("window", window_id)
    win.change_property(d.intern_atom("_KDE_NET_WM_BLUR_BEHIND_REGION"), d.intern_atom("CARDINAL"), 32, [0, 0, width, height])
    d.flush()
    d.close()


def paste_to_window(window_id, is_terminal, keyboard, text="", activate=None, focus_check=None):
    if not window_id:
        raise PasteSafetyError("Target window is unavailable")
    if is_terminal and "\n" in text:
        raise PasteSafetyError("Multiline terminal paste is disabled for safety")
    if activate is None:
        d = display.Display()
        root = d.screen().root
        atom = d.intern_atom("_NET_ACTIVE_WINDOW")
        event = protocol.event.ClientMessage(window=window_id, client_type=atom, data=(32, [1, X.CurrentTime, 0, 0, 0]))
        root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        d.flush()
        time.sleep(0.12)
        activate = lambda _: True
        def verify_focus(target):
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                prop = root.get_full_property(atom, X.AnyPropertyType)
                if prop and prop.value and prop.value[0] == target:
                    return True
                time.sleep(0.02)
            return False
        focus_check = verify_focus
    if not activate(window_id):
        raise PasteSafetyError("Target window could not be activated")
    if focus_check is not None and not focus_check(window_id):
        raise PasteSafetyError("Target focus could not be verified")
    for key in (Key.ctrl, Key.shift):
        try:
            keyboard.release(key)
        except Exception:
            pass
    if is_terminal:
        keyboard.key_down("ctrl") if hasattr(keyboard, "key_down") else keyboard.press(Key.ctrl)
        keyboard.key_down("shift") if hasattr(keyboard, "key_down") else keyboard.press(Key.shift)
        keyboard.press("v")
        if hasattr(keyboard, "key_up"):
            keyboard.key_up("v"); keyboard.key_up("shift"); keyboard.key_up("ctrl")
        else:
            keyboard.release("v"); keyboard.release(Key.shift); keyboard.release(Key.ctrl)
    else:
        keyboard.key_down("ctrl") if hasattr(keyboard, "key_down") else keyboard.press(Key.ctrl)
        keyboard.press("v")
        if hasattr(keyboard, "key_up"):
            keyboard.key_up("v"); keyboard.key_up("ctrl")
        else:
            keyboard.release("v"); keyboard.release(Key.ctrl)
    if 'd' in locals():
        d.close()
