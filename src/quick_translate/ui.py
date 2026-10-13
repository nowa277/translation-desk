from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QPixmap, QPen
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QMenu, QScrollArea,
)

from .languages import SOURCE_LANGUAGES, TARGET_LANGUAGES, TARGET_BY_CODE, TargetSelection
from .theme import GLASS_CLARITY

ASSET = Path(__file__).resolve().parents[2] / 'assets/application-icon.webp'


class SourceEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.composing = False
        self.owner = parent

    def inputMethodEvent(self, event):
        self.composing = bool(event.preeditString())
        super().inputMethodEvent(event)

    def keyPressEvent(self, event):
        if not self.composing and self.owner.handle_key(event):
            return
        super().keyPressEvent(event)


class GlassPanel(QFrame):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        shape = QPainterPath()
        shape.addRoundedRect(bounds, 30, 30)
        painter.setClipPath(shape)
        base = QColor(205, 230, 237)
        base.setAlphaF(GLASS_CLARITY)
        painter.fillPath(shape, base)
        sheen = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        for stop, alpha in ((0, 76), (.15, 8), (.5, 0), (.8, 12), (1, 40)):
            sheen.setColorAt(stop, QColor(255, 255, 255, alpha))
        painter.fillPath(shape, sheen)
        painter.setPen(QPen(QColor(255, 255, 255, 218), 1.4))
        painter.drawPath(shape)
        painter.setPen(QPen(QColor(255, 255, 255, 74), 1))
        painter.drawRoundedRect(bounds.adjusted(3, 3, -3, -3), 27, 27)


class TranslationWindow(QWidget):
    paste_requested = pyqtSignal(str)
    translate_requested = pyqtSignal(str, str, object, int)

    def __init__(self):
        super().__init__()
        self.revision = 0
        self.target_selection = TargetSelection()
        self._selected = 'en'
        self._results = {}
        self._rows = {}
        self.setWindowTitle('Translation Desk')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(740, 710)
        self.setMinimumSize(600, 620)
        self.setStyleSheet('''
            QLabel { background: transparent; color: #eff8fa; }
            QScrollArea { background: transparent; border: none; }
            QTextEdit { background: rgba(255,255,255,24); border: 1px solid rgba(255,255,255,115);
                border-radius: 14px; padding: 10px; color: #f6fcfd; font-size: 17px; }
            QTextEdit:focus { border: 1px solid rgba(255,255,255,220); }
            QPushButton { background: rgba(255,255,255,38); border: 1px solid rgba(255,255,255,125);
                border-radius: 9px; padding: 7px 11px; color: #f3fbfc; font-size: 11px; }
            QPushButton:checked { background: rgba(255,255,255,150); color: #214858; border-color: white; }
            QPushButton:hover { background: rgba(255,255,255,95); }
            QPushButton#paste { background: rgba(255,255,255,220); border-radius: 22px;
                padding: 13px 19px; color: #204e63; font-weight: 600; }
            QPushButton#paste:disabled { color: #536874; background: rgba(255,255,255,90); }
            QComboBox { background: rgba(255,255,255,45); border: 1px solid rgba(255,255,255,130);
                border-radius: 8px; padding: 6px 10px; color: #f3fbfc; min-width: 110px; }
            QComboBox QAbstractItemView { background: #233944; color: #eff8fa; selection-background-color: #426273; }
            QMenu { background: #233944; color: #eff8fa; border: 1px solid #819ca8; padding: 7px; }
            QMenu::item { padding: 8px 16px; } QMenu::item:selected { background: #496673; }
            QScrollBar:vertical { background: transparent; width: 5px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,100); border-radius: 2px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        ''')
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        self.panel = GlassPanel()
        outer.addWidget(self.panel)
        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(15)
        top = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap(str(ASSET)).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon.setFixedSize(38, 38)
        top.addWidget(icon)
        title = QLabel('Translation Desk')
        title.setStyleSheet('font-size: 14px; font-weight: 600;')
        top.addWidget(title)
        top.addStretch()
        self.status = QLabel('Ready')
        self.status.setStyleSheet('font-size: 11px;')
        top.addWidget(self.status)
        close = QPushButton('×')
        close.setFixedSize(28, 28)
        close.setStyleSheet('border-radius: 14px; padding: 0; font-size: 17px;')
        close.clicked.connect(self.hide)
        top.addWidget(close)
        layout.addLayout(top)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet('background: rgba(255,255,255,65);')
        layout.addWidget(line)
        source_row = QHBoxLayout()
        self.source_selector = QComboBox()
        for item in SOURCE_LANGUAGES:
            self.source_selector.addItem(item.label, item.code)
        source_row.addWidget(self.source_selector)
        source_row.addStretch()
        source_row.addWidget(QLabel('SOURCE TEXT'))
        layout.addLayout(source_row)
        self.source_editor = SourceEditor(self)
        self.source_editor.setAcceptRichText(False)
        self.source_editor.setPlaceholderText('Type Chinese or English here…')
        self.source_editor.setFixedHeight(106)
        layout.addWidget(self.source_editor)
        note = QHBoxLayout()
        note.addWidget(QLabel('Live translation'))
        note.addStretch()
        note.addWidget(QLabel('Shift ↵ New line'))
        layout.addLayout(note)
        layout.addWidget(QLabel('TRANSLATE TO'))
        chips = QHBoxLayout()
        self.chips = {}
        for item in TARGET_LANGUAGES[:3]:
            button = QPushButton(item.label)
            button.setCheckable(True)
            button.setChecked(True)
            button.clicked.connect(lambda checked, code=item.code: self.toggle_target(code))
            self.chips[item.code] = button
            chips.addWidget(button)
        add = QPushButton('+ Add language')
        menu = QMenu(add)
        for item in TARGET_LANGUAGES[3:]:
            action = menu.addAction(item.label)
            action.setCheckable(True)
            action.toggled.connect(lambda checked, code=item.code: self.toggle_target(code))
        add.setMenu(menu)
        chips.addWidget(add)
        chips.addStretch()
        layout.addLayout(chips)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        content = QWidget()
        content.setStyleSheet('background: transparent;')
        self.result_layout = QVBoxLayout(content)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(6)
        self.scroll.setWidget(content)
        layout.addWidget(self.scroll, 1)
        self._rebuild_rows()
        footer = QHBoxLayout()
        footer.addWidget(QLabel('Tab Switch target  ·  Enter Paste selected\nEsc Close  ·  Ctrl 1 / 2 / 3 Quick paste'))
        footer.addStretch()
        self.paste_button = QPushButton('Paste English  ↵')
        self.paste_button.setObjectName('paste')
        self.paste_button.clicked.connect(self.trigger_paste)
        footer.addWidget(self.paste_button)
        layout.addLayout(footer)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(220)
        self.timer.timeout.connect(self._request)
        self.source_editor.textChanged.connect(self._changed)
        self.source_selector.currentIndexChanged.connect(self._changed)
        self._refresh()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            from .x11 import request_blur
            request_blur(int(self.winId()), self.width(), self.height())
        except (ImportError, RuntimeError, OSError):
            pass

    def _rebuild_rows(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows = {}
        for code in self.visible_target_codes():
            row = QFrame()
            box = QVBoxLayout(row)
            box.setContentsMargins(16, 12, 16, 10)
            header = QHBoxLayout()
            select = QPushButton(TARGET_BY_CODE[code].label)
            select.setStyleSheet('background: transparent; border: none; padding: 0; text-align: left; font-weight: 600;')
            select.clicked.connect(lambda checked, c=code: self.select_target(c))
            header.addWidget(select)
            header.addStretch()
            shortcut = QLabel(TARGET_BY_CODE[code].shortcut)
            header.addWidget(shortcut)
            box.addLayout(header)
            view = QTextEdit()
            view.setReadOnly(True)
            view.setAcceptRichText(False)
            view.setPlainText(self._results.get(code, ''))
            view.setPlaceholderText('Waiting for input…')
            view.setMinimumHeight(75)
            view.setMaximumHeight(145)
            box.addWidget(view)
            self.result_layout.addWidget(row)
            self._rows[code] = (row, view, select, shortcut)
        self.result_layout.addStretch()

    def _refresh(self):
        for code, (row, view, select, shortcut) in self._rows.items():
            active = code == self._selected
            row.setStyleSheet('QFrame {border-radius: 18px; border: 1px solid ' + ('rgba(255,255,255,235); background: rgba(255,255,255,160);}' if active else 'rgba(255,255,255,30); background: rgba(255,255,255,12);}') )
            color = '#173b4b' if active else '#eff8fa'
            view.setStyleSheet(f'QTextEdit {{background: transparent; border: none; padding: 0; color: {color}; font-size: 15px;}}')
            select.setStyleSheet(f'background: transparent; border: none; padding: 0; text-align: left; color: {color}; font-weight: 600;')
            shortcut.setStyleSheet(f'background: transparent; color: {color}; font-size: 10px;')
        if hasattr(self, 'paste_button'):
            self.paste_button.setText('Paste ' + TARGET_BY_CODE[self._selected].label + '  ↵')
            self.paste_button.setEnabled(self.can_paste())

    def source_codes(self):
        return tuple(item.code for item in SOURCE_LANGUAGES)

    def source_code(self):
        return self.source_selector.currentData()

    def visible_target_codes(self):
        return self.target_selection.ordered()

    def selected_target(self):
        return self._selected

    def select_target(self, code):
        if code in self.visible_target_codes():
            self._selected = code
            self._refresh()

    def toggle_target(self, code):
        self.target_selection.toggle(code)
        if self._selected not in self.visible_target_codes():
            self._selected = self.visible_target_codes()[0]
        for c, button in self.chips.items():
            button.setChecked(self.target_selection.is_enabled(c))
        self._rebuild_rows()
        self._changed()

    def invalidate_translation(self):
        self.revision += 1
        self._results.clear()
        for row, view, _, _ in self._rows.values():
            view.clear()
        self._refresh()
        return self.revision

    def _changed(self, *args):
        self.invalidate_translation()
        self.timer.stop()
        self.status.setText('Translating…' if self.source_editor.toPlainText().strip() else 'Ready')
        if self.source_editor.toPlainText().strip():
            self.timer.start()

    def _request(self):
        self.translate_requested.emit(self.source_editor.toPlainText(), self.source_code(), self.visible_target_codes(), self.revision)

    def set_results(self, results):
        for code, text in results.items():
            self.apply_result(self.revision, code, text)

    def apply_result(self, revision, code, text):
        if revision != self.revision or code not in self._rows:
            return
        self._results[code] = text
        self._rows[code][1].setPlainText(text)
        self.status.setText('Ready')
        self._refresh()

    def apply_error(self, revision, code, error):
        if revision != self.revision or code not in self._rows:
            return
        self._results.pop(code, None)
        self._rows[code][1].setPlaceholderText('Translation unavailable')
        self.status.setText('Translation unavailable')
        self._refresh()

    def result_for(self, code):
        return self._results.get(code, '')

    def result_view(self, code):
        return self._rows[code][1]

    def status_text(self):
        return self.status.text()

    def can_paste(self):
        return bool(self.result_for(self._selected).strip())

    def trigger_paste(self):
        if self.can_paste():
            self.paste_requested.emit(self._selected)

    def handle_key(self, event):
        key, modifiers = event.key(), event.modifiers()
        if key == Qt.Key.Key_Escape:
            self.hide()
        elif key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            targets = self.visible_target_codes()
            step = -1 if key == Qt.Key.Key_Backtab or modifiers & Qt.KeyboardModifier.ShiftModifier else 1
            self.select_target(targets[(targets.index(self._selected) + step) % len(targets)])
        elif modifiers & Qt.KeyboardModifier.ControlModifier and key in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3):
            code = ('en', 'ja', 'ko')[key - Qt.Key.Key_1]
            if code in self.visible_target_codes():
                self.select_target(code)
                self.trigger_paste()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.trigger_paste()
        else:
            return False
        event.accept()
        return True

    def keyPressEvent(self, event):
        if not self.handle_key(event):
            super().keyPressEvent(event)
