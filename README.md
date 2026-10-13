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
- `Ctrl+1`, `Ctrl+2`, `Ctrl+3`: select and paste English, Japanese, or Korean when its current translation is ready.
- `Esc`: close without modifying the target application.

## Basic tests

Run the full automated suite from the repository root:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest -q
```

The suite covers provider parsing and fallback behavior, Chinese/English source modes, target-language selection, stale-result protection, IME preedit handling, keyboard shortcuts, X11 paste safety, the 25% glass token, and user-local installer backups.

For a safe live check that does not paste into another application:

```bash
PYTHONPATH=src python3 -m quick_translate.app --preview
```

The preview disables the global shortcut and automatic paste. `Esc` or the close button hides its window; choose `Quit` from its tray menu to stop the preview process.

## Manual acceptance checklist

1. Press `Ctrl+Alt+Z` and confirm the floating glass window opens.
2. Enter a Chinese paragraph and check that the enabled target rows update independently.
3. Choose `English` as the source mode, enter an English sentence, and verify the targets update.
4. Toggle a target language off and confirm its row disappears; use `Add language` to enable another target.
5. Select a target and press `Enter` in a scratch editor to verify paste.
6. Press `Esc` and confirm the target editor is unchanged.

## Troubleshooting

- **Shortcut does nothing:** confirm the session is X11 (`echo $XDG_SESSION_TYPE`), and make sure an older Quick Translate process is not also running. The installer does not stop unrelated legacy instances.
- **The window is translucent but not blurred:** enable the desktop compositor's blur effect. The application requests KDE blur for its own window but does not change global compositor settings.
- **Chinese input is incomplete:** wait for the IME candidate composition to finish before pressing `Enter`; composing `Enter`, `Tab`, and arrow keys are intentionally left to the input method/editor.
- **Translation unavailable:** the free endpoints may throttle requests or be temporarily unavailable. Retry later; the app will not paste an invalid or stale result.
- **Terminal paste is blocked:** multiline terminal paste is intentionally clipboard-only to prevent translated text from executing as commands. Paste manually after reviewing it.

## Rollback and uninstall

Every installer run creates a backup under `~/.local/share/translation-desk-backups/`. First choose `Quit` from the tray menu. To remove the installed application without touching the repository:

```bash
rm -rf ~/.local/share/translation-desk ~/.local/bin/translation-desk ~/.config/autostart/translation-desk.desktop ~/.local/share/applications/translation-desk.desktop
```

Restore the previous installation by copying the desired backup directory back to the paths listed above. Do not delete the backup until the replacement has been verified.

## Network and privacy

Text is sent to Google's GTX endpoint. If it fails, text is sent to MyMemory as a fallback. Neither is a local/offline translation engine. No account or API key is stored by this application. These services can throttle or reject requests, and availability and free quotas are not guaranteed. Do not enter confidential text unless sending it to both providers is acceptable to you.

## Limitations

This release targets X11. True compositor-level refraction depends on the desktop compositor; the application supplies translucent layers, blur-compatible window attributes, bright rims, and shadows without changing global desktop settings. Terminal multiline paste is guarded to avoid accidentally executing translated commands.
