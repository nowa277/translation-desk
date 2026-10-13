import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_install_preserves_existing_launcher_without_install_directory(tmp_path):
    launcher = tmp_path / '.local/bin/translation-desk'
    launcher.parent.mkdir(parents=True)
    launcher.write_text('previous-launcher\n')
    result = subprocess.run(['bash', str(ROOT / 'install.sh')], env={**os.environ, 'HOME': str(tmp_path)}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    backups = list((tmp_path / '.local/share/translation-desk-backups').glob('*/launcher'))
    assert len(backups) == 1
    assert backups[0].read_text() == 'previous-launcher\n'


def test_repeat_install_creates_separate_backups_and_no_caches(tmp_path):
    env = {**os.environ, 'HOME': str(tmp_path)}
    for _ in range(3):
        result = subprocess.run(['bash', str(ROOT / 'install.sh')], env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    backups = list((tmp_path / '.local/share/translation-desk-backups').iterdir())
    assert len(backups) == 3
    install = tmp_path / '.local/share/translation-desk'
    assert not list(install.rglob('__pycache__'))
    assert (tmp_path / '.local/share/applications/translation-desk.desktop').exists()
    assert (tmp_path / '.local/bin/translation-desk').stat().st_mode & 0o111
