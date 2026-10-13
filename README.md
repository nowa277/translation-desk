# Translation Desk

A free Linux desktop translation desk for Chinese and English input. It previews selected target languages in a translucent liquid-glass window and can paste the active translation into the previously focused application.

## Features

- Chinese or English source input with automatic detection.
- English, Japanese, Korean, German, French, Spanish, and Chinese targets.
- English interface with keyboard-first controls.
- Default glass clarity: 25% surface opacity, with bright edge highlights and a refractive highlight layer.
- Google GTX and MyMemory free translation endpoints; no API key is required.
- Stale asynchronous responses are discarded; provider failures never paste an invalid result.
- X11 focus restoration and paste support for normal applications and terminal emulators.

## Requirements

- Linux with KDE/X11 or another X11 desktop.
- Python 3.10+.
- PyQt6, requests, python-xlib, pynput.
- A configured X11 input method is recommended for Chinese composition.

## Install

Install the runtime dependencies into your chosen Python environment first:

```bash
python3 -m pip install PyQt6 requests python-xlib pynput
```

On Ubuntu, prefer distribution packages or a virtual environment rather than overriding an externally managed Python installation. Run the user-local installer with the same Python interpreter that has these dependencies available:

```bash
./install.sh
```

It installs under `~/.local/share/translation-desk`, adds `~/.local/bin/translation-desk`, and registers menu/autostart desktop entries. Existing Translation Desk files are copied to a unique backup directory before replacement. It does not stop running programs or remove a separate legacy Quick Translate installation; avoid starting both global-hotkey instances together.

## Controls

- `Ctrl+Alt+Z`: show or hide the desk.
- `Enter`: paste the selected translation.
- `Shift+Enter`: insert a newline.
- `Tab` / `Shift+Tab`: switch enabled targets.
- `Ctrl+1`, `Ctrl+2`, `Ctrl+3`: select English, Japanese, or Korean.
- `Esc`: close without modifying the target application.

## Network and privacy

Text is sent to Google's GTX endpoint. If it fails, text is sent to MyMemory as a fallback. Neither is a local/offline translation engine. No account or API key is stored by this application. These services can throttle or reject requests, and availability and free quotas are not guaranteed. Do not enter confidential text unless sending it to both providers is acceptable to you.

## Limitations

This release targets X11. True compositor-level refraction depends on the desktop compositor; the application supplies translucent layers, blur-compatible window attributes, bright rims, and shadows without changing global desktop settings. Terminal multiline paste is guarded to avoid accidentally executing translated commands.
