import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QLockFile, QStandardPaths
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from .translation import translate_text
from .ui import TranslationWindow, ASSET


class Bridge(QObject):
    result = pyqtSignal(int, str, str)
    error = pyqtSignal(int, str, str)
    toggle = pyqtSignal()


class TranslationController:
    def __init__(self, translate_func=translate_text):
        self.translate_func = translate_func
        self.revision = 0
        self.results = {}
        self.targets = ()

    def begin_request(self, text, source, targets):
        self.revision += 1
        self.targets = targets
        self.results.clear()
        return self.revision

    def request(self, text, source, targets):
        return self.begin_request(text, source, targets)

    def receive_result(self, revision, target, text):
        if revision == self.revision and target in self.targets:
            self.results[target] = text

    def receive_error(self, revision, target, error):
        if revision == self.revision:
            self.results.pop(target, None)

    def result_for(self, target):
        return self.results.get(target, '')

    def can_paste(self, target):
        return bool(self.result_for(target).strip())


class Controller:
    def __init__(self, window):
        self.window = window
        self.bridge = Bridge()
        self.pool = ThreadPoolExecutor(max_workers=3)
        self.pending = {}
        self.closed = False
        self.bridge.result.connect(window.apply_result)
        self.bridge.error.connect(window.apply_error)
        window.translate_requested.connect(self.request)

    def request(self, text, source, targets, revision):
        for future in self.pending.values():
            future.cancel()
        self.pending.clear()
        for target in targets:
            self.pending[target] = self.pool.submit(self.run_target, text, source, target, revision)

    def run_target(self, text, source, target, revision):
        if self.closed or revision != self.window.revision:
            return
        try:
            result = translate_text(text, source, target)
            if not self.closed:
                self.bridge.result.emit(revision, target, result)
        except Exception:
            if not self.closed:
                self.bridge.error.emit(revision, target, 'Translation unavailable')

    def close(self):
        self.closed = True
        self.pool.shutdown(wait=False, cancel_futures=True)


class QuickTranslateApp:
    def __init__(self, app, preview=False):
        self.app = app
        self.preview = preview
        self.window = TranslationWindow()
        self.controller = Controller(self.window)
        self.window.paste_requested.connect(self.paste)
        self.target = (None, False)
        self.controller.bridge.toggle.connect(self.toggle)
        self.tray = QSystemTrayIcon(QIcon(str(ASSET)), app)
        self.tray.setToolTip('Translation Desk · Ctrl+Alt+Z')
        menu = QMenu()
        menu.addAction('Open Translation Desk', self.toggle)
        menu.addAction('Quit', app.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.toggle() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()
        self.hotkeys = None
        if not preview:
            from pynput.keyboard import GlobalHotKeys, Controller as Keyboard
            self.keyboard = Keyboard()
            self.hotkeys = GlobalHotKeys({'<ctrl>+<alt>+z': self.controller.bridge.toggle.emit})
            self.hotkeys.start()
        app.aboutToQuit.connect(self.close)

    def close(self):
        self.controller.close()
        if self.hotkeys:
            self.hotkeys.stop()

    def toggle(self):
        if self.window.isVisible():
            self.window.hide()
            return
        if not self.preview:
            from .x11 import active_window_info
            self.target = active_window_info()
        screen = self.app.primaryScreen().availableGeometry()
        self.window.move(screen.center() - self.window.rect().center())
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.window.source_editor.setFocus()

    def paste(self, target):
        if self.preview:
            self.window.status.setText('Preview only — paste disabled')
            return
        text = self.window.result_for(target)
        if not text.strip():
            return
        clipboard = self.app.clipboard()
        clipboard.setText(text)
        clipboard.setText(text, clipboard.Mode.Selection)
        if self.target[1] and '\n' in text:
            self.window.status.setText('Copied only — multiline terminal paste blocked')
            return
        self.window.hide()
        QTimer.singleShot(140, lambda: self._paste(text))

    def _paste(self, text):
        from .x11 import paste_to_window
        try:
            paste_to_window(*self.target, self.keyboard, text)
        except Exception:
            self.window.status.setText('Copied only — target could not be activated')
            self.window.show()


def main():
    parser = argparse.ArgumentParser(description='Translation Desk')
    parser.add_argument('--preview', action='store_true', help='Show without global shortcut or automatic paste')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName('Translation Desk')
    server = None
    lock = None
    if not args.preview:
        path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.RuntimeLocation)
        lock = QLockFile(path + '/translation-desk-v2.lock')
        if not lock.tryLock(100):
            client = QLocalSocket()
            client.connectToServer('translation-desk-v2')
            if not client.waitForConnected(1500):
                print('Translation Desk is starting or unavailable', file=sys.stderr)
                return 1
            client.write(b'toggle')
            client.waitForBytesWritten(1000)
            return 0
        QLocalServer.removeServer('translation-desk-v2')
        server = QLocalServer()
        server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        if not server.listen('translation-desk-v2'):
            print('Could not start local control socket', file=sys.stderr)
            return 1
    desk = QuickTranslateApp(app, args.preview)
    if server:
        def accept():
            client = server.nextPendingConnection()
            client.readyRead.connect(lambda: (desk.toggle(), client.disconnectFromServer()))
        server.newConnection.connect(accept)
    if args.preview:
        QTimer.singleShot(100, desk.toggle)
    print('Translation Desk ready', flush=True)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
