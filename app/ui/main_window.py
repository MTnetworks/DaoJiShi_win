import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QProgressBar, QApplication, QSizeGrip,
                             QSystemTrayIcon, QMenu, QAction, QStyle)
from PyQt5.QtCore import Qt, QPoint, pyqtSlot, QRect
from PyQt5.QtGui import QColor, QPalette, QMouseEvent, QIcon, QCursor

from app.config.settings import settings
from app.core.timer import CountdownTimer
from app.core.audio import AudioPlayer
from app.core.shortcut import ShortcutManager
from app.ui.styles import DARK_THEME, LIGHT_THEME
from app.ui.settings_dialog import SettingsDialog
from app.utils import get_resource_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = settings
        self.timer = CountdownTimer()
        self.audio = AudioPlayer()
        self.shortcuts = ShortcutManager()
        
        self.current_preset_index = 0
        self.drag_position = QPoint()
        self.resize_margin = 5
        self.resize_mode = None
        self.start_geometry = None
        
        self.normal_geometry = None
        self.simple_geometry = None
        
        self.is_simple_mode = False
        
        self.init_ui()
        self.connect_signals()
        self.load_settings()
        self.setup_shortcuts()
        
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setMouseTracking(True)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        self.preset_label = QLabel("预设")
        self.preset_label.setObjectName("PresetLabel")
        header_layout.addWidget(self.preset_label)
        header_layout.addStretch()
        
        self.btn_min = QPushButton()
        self.btn_min.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.clicked.connect(self.showMinimized)
        
        self.btn_close = QPushButton()
        self.btn_close.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.clicked.connect(self.close)
        
        header_layout.addWidget(self.btn_min)
        header_layout.addWidget(self.btn_close)
        self.main_layout.addLayout(header_layout)
        
        # Time
        self.time_container = QWidget()
        self.time_container.setObjectName("TimeContainer")
        self.time_layout = QHBoxLayout(self.time_container)
        self.time_layout.setContentsMargins(5, 5, 5, 5)
        self.time_layout.setSpacing(0)
        
        self.lbl_min = QLabel("00")
        self.lbl_min.setObjectName("TimeLabelPart")
        self.lbl_min.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.lbl_sep = QLabel(":")
        self.lbl_sep.setObjectName("TimeLabelPart")
        self.lbl_sep.setAlignment(Qt.AlignCenter)
        
        self.lbl_sec = QLabel("00")
        self.lbl_sec.setObjectName("TimeLabelPart")
        self.lbl_sec.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.time_layout.addWidget(self.lbl_min)
        self.time_layout.addWidget(self.lbl_sep)
        self.time_layout.addWidget(self.lbl_sec)

        # Add with alignment to prevent stretching, keeping background tight to text
        self.main_layout.addWidget(self.time_container, 0, Qt.AlignCenter)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.main_layout.addWidget(self.progress_bar)
        
        # Controls
        self.controls_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始")
        self.btn_start.clicked.connect(self.toggle_timer)
        self.btn_reset = QPushButton("重置")
        self.btn_reset.clicked.connect(self.reset_timer)
        
        self.btn_settings = QPushButton("设置")
        self.btn_settings.clicked.connect(self.open_settings)
        
        # Prompt Menu Button
        self.btn_prompt = QPushButton("温馨提示")
        self.prompt_menu = QMenu(self)
        self.action_prompt_reg = QAction("播放常规会议提示", self)
        self.action_prompt_reg.triggered.connect(lambda: self.play_prompt("regular"))
        self.action_prompt_conf = QAction("播放保密会议提示", self)
        self.action_prompt_conf.triggered.connect(lambda: self.play_prompt("confidential"))
        self.prompt_menu.addAction(self.action_prompt_reg)
        self.prompt_menu.addAction(self.action_prompt_conf)
        self.btn_prompt.setMenu(self.prompt_menu)
        
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.btn_start)
        self.controls_layout.addWidget(self.btn_reset)
        self.controls_layout.addWidget(self.btn_prompt)
        self.controls_layout.addWidget(self.btn_settings)
        self.controls_layout.addStretch()
        self.main_layout.addLayout(self.controls_layout)
        
        # Resize grip removed in favor of edge resizing
        # self.sizegrip = QSizeGrip(self) ...

        self.init_tray()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        from PyQt5.QtWidgets import QStyle
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        tray_menu = QMenu()
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def update_background(self):
        theme = self.settings.get("theme")
        opacity = self.settings.get("window.opacity")
        
        # Determine base color based on theme
        # Dark: #2b2b2b (43, 43, 43)
        # Light: #f0f0f0 (240, 240, 240)
        if theme == "dark":
            r, g, b = 43, 43, 43
        else:
            r, g, b = 240, 240, 240
            
        # Apply transparency ONLY if in Simple Mode (buttons hidden)
        # We use self.is_simple_mode as the indicator
        
        if self.is_simple_mode:
            alpha = int(opacity * 255)
            # In Simple Mode, CentralWidget is transparent, TimeContainer has background
            self.central_widget.setStyleSheet(f"#CentralWidget {{ background-color: transparent; }}")
            self.time_container.setStyleSheet(f"#TimeContainer {{ background-color: rgba({r}, {g}, {b}, {alpha}); border-radius: 10px; }}")
        else:
            alpha = 255 # Fully opaque when not running/paused (Normal Mode)
            # In Normal Mode, CentralWidget has background, TimeContainer is transparent
            self.central_widget.setStyleSheet(f"#CentralWidget {{ background-color: rgba({r}, {g}, {b}, {alpha}); border-radius: 10px; }}")
            self.time_container.setStyleSheet(f"#TimeContainer {{ background-color: transparent; }}")

        # Apply Font Size
        font_size = self.settings.get("display.font_size", 150)
        font = self.lbl_min.font()
        font.setPixelSize(font_size)
        self.lbl_min.setFont(font)
        self.lbl_sep.setFont(font)
        self.lbl_sec.setFont(font)
        
        # Adjust colon position (padding-bottom) to move it up
        # Try 15% of font size
        offset = int(font_size * 0.15)
        self.lbl_sep.setStyleSheet(f"padding-bottom: {offset}px; background-color: transparent;")
        self.lbl_min.setStyleSheet("background-color: transparent;")
        self.lbl_sec.setStyleSheet("background-color: transparent;")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def connect_signals(self):
        self.timer.time_updated.connect(self.update_time_display)
        self.timer.finished.connect(self.on_timer_finished)
        self.timer.alert_triggered.connect(self.on_alert_triggered)
        self.timer.flash_triggered.connect(self.on_flash_triggered)
        self.shortcuts.triggered.connect(self.on_shortcut_triggered)

    def load_settings(self):
        # Window
        w = self.settings.get("window.width")
        h = self.settings.get("window.height")
        x = self.settings.get("window.x")
        y = self.settings.get("window.y")
        self.resize(w, h)
        if x is not None and y is not None:
            self.move(x, y)
        
        opacity = self.settings.get("window.opacity")
        # self.setWindowOpacity(opacity) # Deprecated in favor of background transparency
        
        topmost = self.settings.get("window.topmost")
        self.set_topmost(topmost)
        
        # Theme
        theme = self.settings.get("theme")
        self.setStyleSheet(DARK_THEME if theme == "dark" else LIGHT_THEME)
        
        self.update_background()
        
        # Load presets
        self.presets = self.settings.get("presets")
        if self.presets:
            self.load_preset(0)

    def setup_shortcuts(self):
        s = self.settings.get("shortcuts")
        self.shortcuts.register("start_pause", s.get("start_pause"))
        self.shortcuts.register("reset", s.get("reset"))
        self.shortcuts.register("next_preset", s.get("next_preset"))
        self.shortcuts.register("prev_preset", s.get("prev_preset"))
        self.shortcuts.register("toggle_window", s.get("toggle_window"))
        self.shortcuts.register("toggle_top", s.get("toggle_top"))
        self.shortcuts.register("opacity_up", s.get("opacity_up"))
        self.shortcuts.register("opacity_down", s.get("opacity_down"))
        self.shortcuts.register("mute", s.get("mute"))

    def load_preset(self, index):
        if 0 <= index < len(self.presets):
            self.current_preset_index = index
            preset = self.presets[index]
            self.preset_label.setText(preset["name"])
            self.timer.set_config(preset["duration"], preset.get("alert_time", 0), preset.get("flash_time", 5))
            self.progress_bar.setRange(0, preset["duration"] * 1000)
            self.progress_bar.setValue(preset["duration"] * 1000)
            self.update_time_display(preset["duration"] * 1000)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.load_settings()
            self.setup_shortcuts()
            # Reload current preset to reflect changes if any (e.g. music)
            # But don't reset timer if it's just a setting change?
            # User might want to change preset params on the fly.
            # Safe to reload preset if we are not running.
            if not self.timer.is_running:
                 self.load_preset(self.current_preset_index)

    def set_simple_mode(self, enabled):
        self.is_simple_mode = enabled
        # Save geometry of the current mode before switching
        if enabled:
            # Switching TO Simple Mode (leaving Normal)
            self.normal_geometry = self.saveGeometry()
        else:
            # Switching TO Normal Mode (leaving Simple)
            self.simple_geometry = self.saveGeometry()

        self.btn_start.setVisible(not enabled)
        self.btn_reset.setVisible(not enabled)
        self.btn_prompt.setVisible(not enabled)
        self.btn_settings.setVisible(not enabled)
        self.preset_label.setVisible(not enabled)
        self.btn_min.setVisible(not enabled)
        self.btn_close.setVisible(not enabled)
        if enabled:
            self.progress_bar.hide()
        else:
            self.progress_bar.show()
        
        # Restore geometry of the new mode
        if enabled:
            if self.simple_geometry:
                self.restoreGeometry(self.simple_geometry)
        else:
            if self.normal_geometry:
                self.restoreGeometry(self.normal_geometry)

        # Update background opacity based on mode
        self.update_background()

    def toggle_timer(self):
        self.timer.toggle()
        self.btn_start.setText("暂停" if self.timer.is_running else "开始")
        self.update_background()

    def reset_timer(self):
        self.timer.reset()
        self.btn_start.setText("开始")
        self.audio.stop()
        # Reset style to theme
        theme = self.settings.get("theme")
        self.setStyleSheet(DARK_THEME if theme == "dark" else LIGHT_THEME)
        self.update_background()

    def update_time_display(self, remaining_ms):
        self.progress_bar.setValue(remaining_ms)
        
        fmt = self.settings.get("display.format", "min_sec")
        
        if fmt == "percent":
            total = self.progress_bar.maximum()
            if total > 0:
                pct = (remaining_ms / total) * 100
                text = f"{pct:.1f}%"
            else:
                text = "0.0%"
            self.lbl_min.hide()
            self.lbl_sep.hide()
            self.lbl_sec.show()
            self.lbl_sec.setText(text)
            self.lbl_sec.setAlignment(Qt.AlignCenter)
            
        elif fmt == "seconds":
            seconds = (remaining_ms + 999) // 1000
            self.lbl_min.hide()
            self.lbl_sep.hide()
            self.lbl_sec.show()
            self.lbl_sec.setText(f"{seconds}")
            self.lbl_sec.setAlignment(Qt.AlignCenter)
            
        else: # min_sec
            seconds = (remaining_ms + 999) // 1000
            mins = seconds // 60
            secs = seconds % 60
            self.lbl_min.show()
            self.lbl_sep.show()
            self.lbl_sec.show()
            self.lbl_min.setText(f"{mins:02}")
            self.lbl_sec.setText(f"{secs:02}")
            self.lbl_min.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lbl_sec.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def on_timer_finished(self):
        self.btn_start.setText("开始")
        # Ensure final state
        self.update_time_display(0)

    def on_alert_triggered(self):
        preset = self.presets[self.current_preset_index]
        music_path = preset.get("music")
        if music_path:
            vol = self.settings.get("audio.volume") * 100
            self.audio.set_volume(int(vol))
            self.audio.play(music_path, fade_in_duration=self.settings.get("audio.fade_duration"))

    def play_prompt(self, prompt_type):
        """
        Play the pre-meeting prompt.
        prompt_type: 'regular' or 'confidential'
        """
        # Stop any currently playing audio
        self.audio.stop()
        
        path = ""
        if prompt_type == "regular":
            path = self.settings.get("audio.prompt_regular")
        elif prompt_type == "confidential":
            path = self.settings.get("audio.prompt_confidential")
            
        if path:
            vol = self.settings.get("audio.volume") * 100
            self.audio.set_volume(int(vol))
            # No fade in for prompts usually, or maybe short fade
            self.audio.play(path, fade_in_duration=0)
        else:
            # Maybe show a warning if no path is set? Or just ignore.
            # For user experience, better to warn if empty.
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "未设置提示音文件，请在设置中配置。")

    def on_flash_triggered(self, state):
        if state:
            color = self.settings.get("reminder.flash_color")
            # Apply color to TimeContainer background in simple mode, or CentralWidget in normal mode
            
            if self.is_simple_mode:
                self.time_container.setStyleSheet(f"#TimeContainer {{ background-color: {color}; border-radius: 10px; }}")
            else:
                self.central_widget.setStyleSheet(f"#CentralWidget {{ background-color: {color}; border-radius: 10px; }}")
        else:
            # Revert to default background
            self.update_background()

    def on_shortcut_triggered(self, action):
        if action == "start_pause":
            self.toggle_timer()
            if self.timer.is_running:
                self.set_simple_mode(True)
            else:
                self.set_simple_mode(False)
        elif action == "reset":
            self.reset_timer()
            self.set_simple_mode(False)
        elif action == "next_preset":
            self.load_preset((self.current_preset_index + 1) % len(self.presets))
        elif action == "prev_preset":
            self.load_preset((self.current_preset_index - 1) % len(self.presets))
        elif action == "toggle_window":
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()
        elif action == "toggle_top":
            is_top = self.windowFlags() & Qt.WindowStaysOnTopHint
            self.set_topmost(not is_top)
        elif action == "opacity_up":
            op = min(1.0, self.settings.get("window.opacity") + 0.1)
            # self.setWindowOpacity(op)
            self.settings.set("window.opacity", op)
            # Only update visually if running
            self.update_background()
        elif action == "opacity_down":
            op = max(0.2, self.settings.get("window.opacity") - 0.1)
            # self.setWindowOpacity(op)
            self.settings.set("window.opacity", op)
            # Only update visually if running
            self.update_background()
        elif action == "mute":
            # Toggle mute logic (not implemented in AudioPlayer yet but straightforward)
            pass

    def set_topmost(self, enable):
        flags = self.windowFlags()
        if enable:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.settings.set("window.topmost", enable)
        if self.isVisible():
            self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check for resize
            x, y = event.pos().x(), event.pos().y()
            w, h = self.width(), self.height()
            margin = self.resize_margin
            
            mode = []
            if y < margin: mode.append("top")
            if y > h - margin: mode.append("bottom")
            if x < margin: mode.append("left")
            if x > w - margin: mode.append("right")
            
            if mode:
                self.resize_mode = "-".join(mode)
                self.start_geometry = self.geometry()
                self.drag_position = event.globalPos()
            else:
                self.resize_mode = None
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
            event.accept()

    def mouseReleaseEvent(self, event):
        self.resize_mode = None
        self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        # Update cursor shape
        x, y = event.pos().x(), event.pos().y()
        w, h = self.width(), self.height()
        margin = self.resize_margin
        
        if not event.buttons() & Qt.LeftButton:
            mode = []
            if y < margin: mode.append("top")
            if y > h - margin: mode.append("bottom")
            if x < margin: mode.append("left")
            if x > w - margin: mode.append("right")
            
            mode_str = "-".join(mode)
            if mode_str == "top-left" or mode_str == "bottom-right":
                self.setCursor(Qt.SizeFDiagCursor)
            elif mode_str == "top-right" or mode_str == "bottom-left":
                self.setCursor(Qt.SizeBDiagCursor)
            elif "top" in mode or "bottom" in mode:
                self.setCursor(Qt.SizeVerCursor)
            elif "left" in mode or "right" in mode:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            return

        if event.buttons() & Qt.LeftButton:
            if self.resize_mode:
                delta = event.globalPos() - self.drag_position
                rect = QRect(self.start_geometry)
                
                if "top" in self.resize_mode:
                    rect.setTop(rect.top() + delta.y())
                if "bottom" in self.resize_mode:
                    rect.setBottom(rect.bottom() + delta.y())
                if "left" in self.resize_mode:
                    rect.setLeft(rect.left() + delta.x())
                if "right" in self.resize_mode:
                    rect.setRight(rect.right() + delta.x())
                
                # Minimum size check
                if rect.width() > 100 and rect.height() > 50:
                    self.setGeometry(rect)
            else:
                self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def closeEvent(self, event):
        self.shortcuts.clear()
        self.settings.set("window.width", self.width())
        self.settings.set("window.height", self.height())
        self.settings.set("window.x", self.x())
        self.settings.set("window.y", self.y())
        event.accept()
