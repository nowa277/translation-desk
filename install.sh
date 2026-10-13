#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 - "$ROOT" <<'PY'
from pathlib import Path
import os
import shlex
import shutil
import sys
import tempfile

root = Path(sys.argv[1])
home = Path.home()
install = home / '.local/share/translation-desk'
launcher = home / '.local/bin/translation-desk'
autostart = home / '.config/autostart/translation-desk.desktop'
application = home / '.local/share/applications/translation-desk.desktop'
backup_root = home / '.local/share/translation-desk-backups'
backup_root.mkdir(parents=True, exist_ok=True)
backup = Path(tempfile.mkdtemp(prefix='install-', dir=backup_root))
for original, name in ((install, 'translation-desk'), (launcher, 'launcher'), (autostart, 'autostart.desktop'), (application, 'application.desktop')):
    if original.is_dir():
        shutil.copytree(original, backup / name)
    elif original.is_file():
        shutil.copy2(original, backup / name)

install.mkdir(parents=True, exist_ok=True)
for folder in ('src', 'assets'):
    shutil.copytree(root / folder, install / folder, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
for path in (launcher, autostart, application):
    path.parent.mkdir(parents=True, exist_ok=True)
launcher.write_text('#!/usr/bin/env bash\nset -euo pipefail\nexport PYTHONPATH=' + shlex.quote(str(install / 'src')) + '\nexec ' + shlex.quote(sys.executable) + ' -m quick_translate.app "$@"\n')
launcher.chmod(0o755)
def desktop_escape(value):
    return str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
entry = ('[Desktop Entry]\nType=Application\nName=Translation Desk\n'
         'Comment=Live translation with selectable targets and automatic paste\n'
         f'Exec="{desktop_escape(launcher)}"\nIcon={install / "assets/application-icon.webp"}\n'
         'Terminal=false\nCategories=Utility;\nStartupNotify=false\nX-GNOME-Autostart-enabled=true\n')
for path in (autostart, application):
    path.write_text(entry)
print('Installed:', install)
print('Backup:', backup)
print('Launch:', launcher)
print('Existing running applications were not stopped. Do not run two global-hotkey instances together.')
PY
