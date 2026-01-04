import copy
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QTabWidget, QWidget, 
                             QPushButton, QListWidget, QFormLayout, QFileDialog, QMessageBox, QComboBox, QStyle,
                             QKeySequenceEdit, QCheckBox)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt
from app.config.settings import settings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(600, 450)
        self.settings = settings
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Presets Tab
        self.presets_tab = QWidget()
        self.init_presets_tab()
        self.tabs.addTab(self.presets_tab, "预设")
        
        # Shortcuts Tab
        self.shortcuts_tab = QWidget()
        self.init_shortcuts_tab()
        self.tabs.addTab(self.shortcuts_tab, "快捷键")
        
        # Audio/General Tab
        self.general_tab = QWidget()
        self.init_general_tab()
        self.tabs.addTab(self.general_tab, "常规")
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def init_presets_tab(self):
        layout = QHBoxLayout(self.presets_tab)
        
        # List
        self.preset_list = QListWidget()
        # Connect signal to slot
        self.preset_list.currentItemChanged.connect(self.on_list_selection_changed)
        layout.addWidget(self.preset_list)
        
        # Details
        details_layout = QFormLayout()
        self.preset_name = QLineEdit()
        self.preset_name.editingFinished.connect(self.update_current_preset_data)
        
        self.preset_duration = QSpinBox()
        self.preset_duration.setRange(1, 36000)
        self.preset_duration.valueChanged.connect(self.update_current_preset_data)
        
        self.preset_alert = QSpinBox()
        self.preset_alert.setRange(0, 36000)
        self.preset_alert.valueChanged.connect(self.update_current_preset_data)

        self.preset_flash = QSpinBox()
        self.preset_flash.setRange(0, 36000)
        self.preset_flash.valueChanged.connect(self.update_current_preset_data)
        
        self.preset_music = QLineEdit()
        self.preset_music.editingFinished.connect(self.update_current_preset_data)
        
        btn_browse = QPushButton()
        btn_browse.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        btn_browse.setFixedWidth(30)
        btn_browse.clicked.connect(self.browse_music)
        
        music_layout = QHBoxLayout()
        music_layout.addWidget(self.preset_music)
        music_layout.addWidget(btn_browse)
        
        details_layout.addRow("名称:", self.preset_name)
        details_layout.addRow("时长 (秒):", self.preset_duration)
        details_layout.addRow("提醒 (秒):", self.preset_alert)
        details_layout.addRow("开始闪烁 (秒):", self.preset_flash)
        details_layout.addRow("音乐:", music_layout)
        
        # Add/Remove buttons
        btn_box = QHBoxLayout()
        btn_add = QPushButton("添加")
        btn_add.clicked.connect(self.add_preset)
        btn_remove = QPushButton("删除")
        btn_remove.clicked.connect(self.remove_preset)
        btn_box.addWidget(btn_add)
        btn_box.addWidget(btn_remove)

        # Import/Export buttons
        io_box = QHBoxLayout()
        btn_import = QPushButton("导入")
        btn_import.clicked.connect(self.import_presets)
        btn_export = QPushButton("导出")
        btn_export.clicked.connect(self.export_presets)
        io_box.addWidget(btn_import)
        io_box.addWidget(btn_export)
        
        right_panel = QVBoxLayout()
        right_panel.addLayout(details_layout)
        right_panel.addLayout(btn_box)
        right_panel.addLayout(io_box)
        right_panel.addStretch()
        
        layout.addLayout(right_panel)
        
        self.load_presets_to_list()

    def init_shortcuts_tab(self):
        layout = QFormLayout(self.shortcuts_tab)
        self.shortcut_inputs = {}
        shortcuts = self.settings.get("shortcuts")
        
        # Mapping for Chinese labels
        shortcut_labels = {
            "start_pause": "开始/暂停",
            "reset": "重置",
            "next_preset": "下一组",
            "prev_preset": "上一组",
            "toggle_window": "显示/隐藏窗口",
            "toggle_top": "切换置顶",
            "opacity_up": "增加不透明度",
            "opacity_down": "减少不透明度",
            "mute": "静音/取消静音"
        }
        
        for key, value in shortcuts.items():
            edit = QKeySequenceEdit(QKeySequence(value))
            self.shortcut_inputs[key] = edit
            label_text = shortcut_labels.get(key, key)
            layout.addRow(label_text + ":", edit)

    def init_general_tab(self):
        layout = QFormLayout(self.general_tab)
        
        # Audio Volume
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(int(self.settings.get("audio.volume") * 100))
        layout.addRow("音量 (%):", self.volume_spin)
        
        # Fade Duration
        self.fade_spin = QSpinBox()
        self.fade_spin.setRange(0, 10000)
        self.fade_spin.setValue(self.settings.get("audio.fade_duration"))
        layout.addRow("淡入时长 (ms):", self.fade_spin)

        # Meeting Prompts
        self.prompt_regular = QLineEdit(self.settings.get("audio.prompt_regular", ""))
        btn_browse_reg = QPushButton()
        btn_browse_reg.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        btn_browse_reg.setFixedWidth(30)
        btn_browse_reg.clicked.connect(lambda: self.browse_prompt(self.prompt_regular))
        layout_reg = QHBoxLayout()
        layout_reg.addWidget(self.prompt_regular)
        layout_reg.addWidget(btn_browse_reg)
        layout.addRow("常规会议提示音:", layout_reg)

        self.prompt_confidential = QLineEdit(self.settings.get("audio.prompt_confidential", ""))
        btn_browse_conf = QPushButton()
        btn_browse_conf.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        btn_browse_conf.setFixedWidth(30)
        btn_browse_conf.clicked.connect(lambda: self.browse_prompt(self.prompt_confidential))
        layout_conf = QHBoxLayout()
        layout_conf.addWidget(self.prompt_confidential)
        layout_conf.addWidget(btn_browse_conf)
        layout.addRow("保密会议提示音:", layout_conf)
        
        # Flash Color
        self.flash_color = QLineEdit(self.settings.get("reminder.flash_color"))
        layout.addRow("闪烁颜色 (Hex):", self.flash_color)

        # Time Format
        self.time_format = QComboBox()
        self.time_format.addItems(["min_sec", "seconds", "percent"])
        current_fmt = self.settings.get("display.format", "min_sec")
        idx = self.time_format.findText(current_fmt)
        if idx >= 0:
            self.time_format.setCurrentIndex(idx)
        layout.addRow("时间格式:", self.time_format)

        # Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(20, 500)
        self.font_size_spin.setValue(self.settings.get("display.font_size", 150))
        layout.addRow("字体大小:", self.font_size_spin)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        current_theme = self.settings.get("theme", "dark")
        idx_t = self.theme_combo.findText(current_theme)
        if idx_t >= 0:
            self.theme_combo.setCurrentIndex(idx_t)
        layout.addRow("主题:", self.theme_combo)
        
        # Always on Top
        self.topmost_check = QCheckBox("窗口置顶")
        self.topmost_check.setChecked(self.settings.get("window.topmost", False))
        layout.addRow("显示:", self.topmost_check)

    def load_presets_to_list(self):
        self.preset_list.blockSignals(True)
        self.preset_list.clear()
        self.current_presets = copy.deepcopy(self.settings.get("presets"))
        
        for p in self.current_presets:
            self.preset_list.addItem(p["name"])
        
        self.preset_list.blockSignals(False)
        
        if self.current_presets:
            self.preset_list.setCurrentRow(0)

    def on_list_selection_changed(self, current, previous):
        if not current:
            return
        row = self.preset_list.row(current)
        self.load_preset_details(row)

    def load_preset_details(self, row):
        if row < 0 or row >= len(self.current_presets):
            return
        p = self.current_presets[row]
        
        # Block signals to prevent feedback loop
        self.preset_name.blockSignals(True)
        self.preset_duration.blockSignals(True)
        self.preset_alert.blockSignals(True)
        self.preset_flash.blockSignals(True)
        self.preset_music.blockSignals(True)
        
        self.preset_name.setText(p["name"])
        self.preset_duration.setValue(p["duration"])
        self.preset_alert.setValue(p["alert_time"])
        self.preset_flash.setValue(p.get("flash_time", 5))
        self.preset_music.setText(p.get("music", ""))
        
        self.preset_name.blockSignals(False)
        self.preset_duration.blockSignals(False)
        self.preset_alert.blockSignals(False)
        self.preset_flash.blockSignals(False)
        self.preset_music.blockSignals(False)

    def update_current_preset_data(self):
        row = self.preset_list.currentRow()
        if row < 0: return
        
        p = self.current_presets[row]
        p["name"] = self.preset_name.text()
        p["duration"] = self.preset_duration.value()
        p["alert_time"] = self.preset_alert.value()
        p["flash_time"] = self.preset_flash.value()
        p["music"] = self.preset_music.text()
        
        # Update list item text
        item = self.preset_list.item(row)
        if item.text() != p["name"]:
            item.setText(p["name"])

    def add_preset(self):
        new_preset = {"name": "新预设", "duration": 300, "alert_time": 60, "flash_time": 10, "music": "app/source/time.mp3"}
        self.current_presets.append(new_preset)
        self.preset_list.addItem(new_preset["name"])
        self.preset_list.setCurrentRow(len(self.current_presets) - 1)

    def remove_preset(self):
        row = self.preset_list.currentRow()
        if row < 0: return
        self.current_presets.pop(row)
        self.preset_list.takeItem(row)

    def browse_music(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择音乐", "", "Audio Files (*.mp3 *.wav *.ogg)")
        if file:
            self.preset_music.setText(file)
            self.update_current_preset_data()

    def browse_prompt(self, line_edit):
        file, _ = QFileDialog.getOpenFileName(self, "选择提示音", "", "Audio Files (*.mp3 *.wav *.ogg)")
        if file:
            line_edit.setText(file)

    def import_presets(self):
        file, _ = QFileDialog.getOpenFileName(self, "导入预设", "", "JSON Files (*.json)")
        if not file:
            return
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Validate basic structure if needed, or just assume correct
                    self.current_presets = data
                    self.load_presets_to_list()
                    QMessageBox.information(self, "成功", "预设导入成功。")
                else:
                    QMessageBox.warning(self, "错误", "格式无效：根元素必须是列表。")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入失败：{e}")

    def export_presets(self):
        file, _ = QFileDialog.getSaveFileName(self, "导出预设", "presets.json", "JSON Files (*.json)")
        if not file:
            return
            
        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(self.current_presets, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "成功", "预设导出成功。")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败：{e}")

    def save_settings(self):
        # Save presets
        self.settings.set("presets", self.current_presets)
        
        # Save shortcuts
        new_shortcuts = {}
        for key, edit in self.shortcut_inputs.items():
            seq = edit.keySequence().toString(QKeySequence.PortableText)
            new_shortcuts[key] = seq.lower()
        self.settings.set("shortcuts", new_shortcuts)
        
        # Save general
        self.settings.set("audio.volume", self.volume_spin.value() / 100.0)
        self.settings.set("audio.fade_duration", self.fade_spin.value())
        self.settings.set("audio.prompt_regular", self.prompt_regular.text())
        self.settings.set("audio.prompt_confidential", self.prompt_confidential.text())
        self.settings.set("reminder.flash_color", self.flash_color.text())
        self.settings.set("display.format", self.time_format.currentText())
        self.settings.set("display.font_size", self.font_size_spin.value())
        self.settings.set("theme", self.theme_combo.currentText())
        
        # Save topmost setting
        is_top = self.topmost_check.isChecked()
        self.settings.set("window.topmost", is_top)
        
        # We need to apply this setting immediately on the main window
        if self.parent():
            self.parent().set_topmost(is_top)
        
        self.accept()
