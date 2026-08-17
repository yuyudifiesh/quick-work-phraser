from __future__ import annotations

import sys
import json
import os
import time
from pathlib import Path
from typing import override

os.environ["QT_ENABLE_HIGHDHDPI_SCALING"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLineEdit, QScrollArea, QDialog,
        QLabel, QMessageBox, QFrame, QSizePolicy,
        QToolButton, QMenu, QSystemTrayIcon,
        QPlainTextEdit
    )
    from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QEvent, QRect
    from PySide6.QtGui import QColor, QFont, QIcon, QAction, QPixmap, QPainter, QBrush, QMouseEvent, QEnterEvent, QCloseEvent
except ImportError:
    print("缺少 PySide6，请执行: pip install PySide6")
    sys.exit(1)

try:
    import pyperclip
except ImportError:
    print("缺少 pyperclip，请执行: pip install pyperclip")
    sys.exit(1)

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    print("缺少 pyautogui，请执行: pip install pyautogui")
    sys.exit(1)

try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

DEFAULT_PHRASES = [
    "好的", "收到", "明白", "谢谢", "稍等",
    "我马上处理", "请问有什么可以帮您？", "久等了",
    "确认无误", "已安排", "已完成", "请查收",
    "没问题", "不客气", "再见", "稍后再联系",
    "麻烦您了", "不辛苦", "祝好", "收到请回复",
    "1", "🌹", "对不起", "抱歉", "辛苦"
]

# 浅色主题配色
COLORS = {
    "bg": "#f5f6fa",
    "surface": "#ffffff",
    "card": "#ffffff",
    "card_hover": "#eef1f8",
    "primary": "#5279FB",
    "primary_hover": "#7a98fd",
    "secondary": "#e8edff",
    "text": "#1f2328",
    "text_secondary": "#6b7280",
    "border": "#d8dce6",
    "success": "#34c759",
    "danger": "#e5484d",
    "shadow": "#000000"
}


def get_data_path() -> Path:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    return base_path / "phrases.json"


def load_phrases() -> list[str]:
    data_path = get_data_path()
    if data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data: object = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return [p for p in data if isinstance(p, str)]
        except Exception:
            pass
    return DEFAULT_PHRASES.copy()


def save_phrases(phrases: list[str]) -> bool:
    data_path = get_data_path()
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(phrases, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        return False


class ModernLineEdit(QLineEdit):
    """现代风格输入框"""
    def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFont(QFont("Microsoft YaHei", 11))
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['surface']};
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 14px;
                color: {COLORS['text']};
                selection-background-color: {COLORS['primary']};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)


class PhraseCard(QFrame):
    """短语卡片"""
    def __init__(self, phrase: str, parent: QuickInputWindow | None = None) -> None:
        super().__init__(parent)
        self.phrase: str = phrase
        self.parent_window: QuickInputWindow | None = parent
        self._original_geo: QRect = self.geometry()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(52)

        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 12, 10)

        self.label = QLabel(phrase)
        self.label.setFont(QFont("Microsoft YaHei", 11))
        self.label.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        self.del_btn = QToolButton(self)
        self.del_btn.setText("×")
        self.del_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet(f"""
            QToolButton {{
                color: {COLORS['text_secondary']};
                border: none;
                background: transparent;
                width: 28px;
                height: 28px;
                border-radius: 14px;
            }}
            QToolButton:hover {{
                color: {COLORS['danger']};
                background: rgba(243, 139, 168, 0.15);
            }}
        """)
        self.del_btn.setVisible(False)
        _ = self.del_btn.clicked.connect(self.on_delete)
        layout.addWidget(self.del_btn)

        # 样式
        self.setStyleSheet(f"""
            PhraseCard {{
                background-color: {COLORS['card']};
                border-radius: 12px;
                border: 1px solid transparent;
            }}
            PhraseCard:hover {{
                background-color: {COLORS['card_hover']};
                border: 1px solid {COLORS['primary']};
            }}
        """)

        # 点击动画
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(100)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self.del_btn.setVisible(True)
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self.del_btn.setVisible(False)
        super().leaveEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        geo = self.geometry()
        self._original_geo = geo
        self.anim.setStartValue(geo)
        self.anim.setEndValue(geo.adjusted(2, 2, -2, -2))
        self.anim.start()
        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(self._original_geo)
        self.anim.start()

        if self.rect().contains(event.position().toPoint()):
            self.send_phrase()
        super().mouseReleaseEvent(event)

    def send_phrase(self) -> None:
        if self.parent_window:
            self.parent_window.send_text(self.phrase)

    def on_delete(self) -> None:
        if self.parent_window:
            self.parent_window.delete_phrase(self.phrase)


class AddPhraseDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("添加短语")
        self.setFixedSize(420, 220)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg']};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("✨ 添加新短语")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(title)

        self.edit = QPlainTextEdit()
        self.edit.setPlaceholderText("输入短语内容...")
        self.edit.setFont(QFont("Microsoft YaHei", 12))
        self.edit.setMaximumBlockCount(3)
        self.edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {COLORS['surface']};
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px;
                color: {COLORS['text']};
            }}
            QPlainTextEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 20px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['surface']};
                color: {COLORS['text']};
            }}
        """)
        _ = cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: {COLORS['bg']};
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        _ = save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_phrase(self) -> str:
        return self.edit.toPlainText().strip()


# ========== 主窗口 ==========
class QuickInputWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.phrases: list[str] = load_phrases()
        self.last_foreground_window: int | None = None
        self.is_sending: bool = False
        self._original_clipboard: str = ""
        self._target_hwnd: int | None = None
        self._text_to_send: str = ""

        flags = (
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)

        self.setWindowTitle("快捷短语")
        self.setFixedSize(480, 640)

        # 全局样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg']};
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QMessageBox {{
                background-color: {COLORS['bg']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text']};
            }}
            QMessageBox QPushButton {{
                background: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 16px;
            }}
        """)

        self.init_ui()
        self.init_tray()
        self.init_animations()

        if WIN32_AVAILABLE:
            self.focus_timer = QTimer(self)
            _ = self.focus_timer.timeout.connect(self.record_focus)
            self.focus_timer.start(300)

        if WIN32_AVAILABLE:
            QTimer.singleShot(100, self._remove_maximize_button)
            QTimer.singleShot(100, self._remove_window_icon)

    def _remove_maximize_button(self) -> None:
        try:
            hwnd = int(self.winId())
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style &= ~win32con.WS_MAXIMIZEBOX
            _ = win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            _ = win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                                      win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
        except Exception:
            pass

    def _remove_window_icon(self) -> None:
        try:
            hwnd = int(self.winId())
            WM_SETICON = 0x0080
            ICON_SMALL = 0      # 标题栏图标
            ICON_SMALL2 = 2
            _ = win32gui.SendMessage(hwnd, WM_SETICON, ICON_SMALL, 0)
            _ = win32gui.SendMessage(hwnd, WM_SETICON, ICON_SMALL2, 0)
        except Exception:
            pass

    def init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)

        header = QHBoxLayout()

        title = QLabel("快捷短语")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        header.addWidget(title)

        header.addStretch()

        # 短语计数
        self.count_label = QLabel(f"{len(self.phrases)} 条")
        self.count_label.setFont(QFont("Microsoft YaHei", 10))
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header.addWidget(self.count_label)

        main_layout.addLayout(header)

        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border-radius: 12px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 8, 8, 8)

        self.search_edit = ModernLineEdit("搜索短语...")
        _ = self.search_edit.textChanged.connect(self.filter_phrases)
        search_layout.addWidget(self.search_edit)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(36, 36)
        add_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: {COLORS['bg']};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _ = add_btn.clicked.connect(self.show_add_dialog)
        search_layout.addWidget(add_btn)

        main_layout.addWidget(search_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 12px;")
        self.flow_layout = QVBoxLayout(self.scroll_content)
        self.flow_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.flow_layout.setSpacing(10)
        self.flow_layout.setContentsMargins(2, 2, 2, 2)

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll)

        footer = QHBoxLayout()

        reset_btn = QPushButton("↺ 恢复默认")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_secondary']};
                border: none;
                background: transparent;
                font-size: 11px;
                padding: 4px;
            }}
            QPushButton:hover {{
                color: {COLORS['primary']};
            }}
        """)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _ = reset_btn.clicked.connect(self.reset_default)
        footer.addWidget(reset_btn)

        footer.addStretch()

        clear_btn = QPushButton("清空自定义")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_secondary']};
                border: none;
                background: transparent;
                font-size: 11px;
                padding: 4px;
            }}
            QPushButton:hover {{
                color: {COLORS['danger']};
            }}
        """)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _ = clear_btn.clicked.connect(self.clear_custom)
        footer.addWidget(clear_btn)
        main_layout.addLayout(footer)
        self.refresh_phrases()
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    def init_tray(self) -> None:
        """系统托盘（带程序化图标，解决 No Icon 警告）"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        # 创建程序化图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(COLORS['primary'])))
        painter.setPen(Qt.PenStyle.NoPen)
        _ = painter.drawRoundedRect(8, 8, 48, 48, 12, 12)
        painter.setPen(QColor(COLORS['bg']))
        font = QFont("Microsoft YaHei", 22, QFont.Weight.Bold)
        painter.setFont(font)
        _ = painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "快")
        painter.end()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("快捷短语输入器")

        tray_menu = QMenu()
        show_action = QAction("显示", self)
        _ = show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)

        quit_action = QAction("退出", self)
        _ = quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        _ = self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()

    def show_from_tray(self) -> None:
        self.setWindowOpacity(0.0)
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def init_animations(self) -> None:
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(150)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def record_focus(self) -> None:
        if WIN32_AVAILABLE and not self.isActiveWindow():
            try:
                self.last_foreground_window = win32gui.GetForegroundWindow()
            except Exception:
                pass

    def refresh_phrases(self, filter_text: str = "") -> None:
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()

        filter_lower = filter_text.lower().strip()
        filtered = [p for p in self.phrases if not filter_lower or filter_lower in p.lower()]

        for phrase in filtered:
            card = PhraseCard(phrase, self)
            self.flow_layout.addWidget(card)

        self.count_label.setText(f"{len(filtered)}/{len(self.phrases)} 条")

    def filter_phrases(self, text: str) -> None:
        self.refresh_phrases(text)

    def show_add_dialog(self) -> None:
        dialog = AddPhraseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            phrase = dialog.get_phrase()
            if phrase and phrase not in self.phrases:
                self.phrases.append(phrase)
                if save_phrases(self.phrases):
                    self.refresh_phrases(self.search_edit.text())
            elif phrase in self.phrases:
                _ = QMessageBox.information(self, "提示", "该短语已存在")

    def delete_phrase(self, phrase: str) -> None:
        reply = QMessageBox.question(
            self, "确认删除", f"删除「{phrase}」？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if phrase in self.phrases:
                self.phrases.remove(phrase)
                _ = save_phrases(self.phrases)
                self.refresh_phrases(self.search_edit.text())

    def clear_custom(self) -> None:
        reply = QMessageBox.question(
            self, "确认清空", "清空所有自定义短语？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.phrases = [p for p in self.phrases if p in DEFAULT_PHRASES]
            _ = save_phrases(self.phrases)
            self.refresh_phrases(self.search_edit.text())

    def reset_default(self) -> None:
        reply = QMessageBox.question(
            self, "确认恢复", "恢复默认短语？自定义短语将丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.phrases = DEFAULT_PHRASES.copy()
            _ = save_phrases(self.phrases)
            self.refresh_phrases(self.search_edit.text())

    def send_text(self, text: str) -> None:
        if not text or self.is_sending:
            return
        self.is_sending = True
        self._text_to_send = text
        try:
            self._original_clipboard = pyperclip.paste()
        except Exception:
            self._original_clipboard = ""
        self._target_hwnd = None
        if WIN32_AVAILABLE and self.last_foreground_window:
            self._target_hwnd = self.last_foreground_window
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self._on_fade_out_done)
        self.fade_anim.start()

    def _on_fade_out_done(self) -> None:
        _ = self.fade_anim.finished.disconnect(self._on_fade_out_done)
        self.hide()
        self.setWindowOpacity(1.0)

        QTimer.singleShot(120, self._do_paste)

    def _do_paste(self) -> None:
        """执行粘贴操作"""
        if WIN32_AVAILABLE and self._target_hwnd:
            try:
                win32gui.SetForegroundWindow(self._target_hwnd)
                time.sleep(0.05)
            except Exception:
                pass

        try:
            pyperclip.copy(self._text_to_send)
            time.sleep(0.04)
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('v')
            pyautogui.keyUp('v')
            pyautogui.keyUp('ctrl')
            time.sleep(0.06)
        except Exception as e:
            print(f"粘贴失败: {e}")

        # 恢复剪贴板
        QTimer.singleShot(300, self._restore_clipboard)

    def _restore_clipboard(self) -> None:
        """恢复原始剪贴板并释放锁"""
        try:
            pyperclip.copy(self._original_clipboard)
        except Exception:
            pass
        self.is_sending = False
        self._text_to_send = ""

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        _ = save_phrases(self.phrases)
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        event.accept()

    def quit_app(self) -> None:
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    _ = app.setStyle("Fusion")

    window = QuickInputWindow()
    window.show()
    sys.exit(app.exec())
