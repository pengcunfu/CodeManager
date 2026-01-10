from PySide6.QtWidgets import (QDialog, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QSpinBox, QColorDialog, QFormLayout,
                             QGroupBox, QCheckBox, QMessageBox, QFontDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette
from app.utils.config_manager import config_manager
import json
import os

class EditorConfigDialog(QDialog):
    """编辑器配置对话框"""
    
    config_changed = Signal(dict)  # 配置改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self.load_default_config()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑器配置")
        self.resize(500, 600)
        self.setModal(True)

        # 创建主布局
        layout = QVBoxLayout(self)

        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # 字体设置选项卡
        self.font_tab = FontSettingsTab()
        tab_widget.addTab(self.font_tab, "字体")

        # 颜色设置选项卡
        self.color_tab = ColorSettingsTab()
        tab_widget.addTab(self.color_tab, "颜色")

        # 语言设置选项卡
        self.language_tab = LanguageSettingsTab()
        tab_widget.addTab(self.language_tab, "语言")

        # 编辑器行为选项卡
        self.behavior_tab = BehaviorSettingsTab()
        tab_widget.addTab(self.behavior_tab, "行为")

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 重置按钮
        reset_button = QPushButton("重置默认")
        reset_button.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_button)

        # 应用按钮
        apply_button = QPushButton("应用")
        apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_button)

        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(ok_button)

        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def load_default_config(self):
        """加载默认配置"""
        return {
            "font": {
                "family": "Consolas",
                "size": 12,
                "bold": False,
                "italic": False
            },
            "colors": {
                "background": "#282A36",
                "text": "#F8F8F2",
                "keyword": "#FF79C6",
                "string": "#F1FA8C",
                "comment": "#6272A4",
                "number": "#BD93F9",
                "current_line": "#44475A",
                "line_number": "#6272A4",
                "line_number_bg": "#21222C"
            },
            "languages": {
                "default": "python",
                "supported": ["python", "javascript", "java", "cpp", "html", "css", "json", "xml", "sql", "bash"]
            },
            "behavior": {
                "tab_size": 4,
                "use_spaces": True,
                "auto_indent": True,
                "show_line_numbers": True,
                "highlight_current_line": True,
                "word_wrap": False,
                "auto_complete": True,
                "bracket_matching": True
            }
        }

    def load_settings(self):
        """加载配置"""
        try:
            # 从配置管理器加载编辑器配置
            saved_config = config_manager.get_editor_config()
            if saved_config:
                # 合并配置，保留默认值
                self.merge_config(self.config, saved_config)
            
            # 将配置应用到各个选项卡
            self.font_tab.load_config(self.config["font"])
            self.color_tab.load_config(self.config["colors"])
            self.language_tab.load_config(self.config["languages"])
            self.behavior_tab.load_config(self.config["behavior"])
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载编辑器配置失败：{str(e)}")

    def merge_config(self, default, saved):
        """合并配置"""
        for key, value in saved.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self.merge_config(default[key], value)
                else:
                    default[key] = value

    def save_settings(self):
        """保存配置"""
        try:
            # 收集所有配置
            self.config["font"] = self.font_tab.get_config()
            self.config["colors"] = self.color_tab.get_config()
            self.config["languages"] = self.language_tab.get_config()
            self.config["behavior"] = self.behavior_tab.get_config()

            # 通过配置管理器保存编辑器配置
            config_manager.save_editor_config(self.config)

            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存编辑器配置失败：{str(e)}")
            return False

    def apply_settings(self):
        """应用设置"""
        if self.save_settings():
            # 收集当前配置
            current_config = {
                "font": self.font_tab.get_config(),
                "colors": self.color_tab.get_config(),
                "languages": self.language_tab.get_config(),
                "behavior": self.behavior_tab.get_config()
            }
            # 发送配置改变信号
            self.config_changed.emit(current_config)
            QMessageBox.information(self, "成功", "配置已应用")

    def accept_settings(self):
        """确定设置"""
        if self.save_settings():
            # 收集当前配置
            current_config = {
                "font": self.font_tab.get_config(),
                "colors": self.color_tab.get_config(),
                "languages": self.language_tab.get_config(),
                "behavior": self.behavior_tab.get_config()
            }
            # 发送配置改变信号
            self.config_changed.emit(current_config)
            self.accept()

    def reset_to_default(self):
        """重置为默认配置"""
        reply = QMessageBox.question(self, "确认", "确定要重置为默认配置吗？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config = self.load_default_config()
            self.font_tab.load_config(self.config["font"])
            self.color_tab.load_config(self.config["colors"])
            self.language_tab.load_config(self.config["languages"])
            self.behavior_tab.load_config(self.config["behavior"])


class FontSettingsTab(QWidget):
    """字体设置选项卡"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 字体选择组
        font_group = QGroupBox("字体设置")
        font_layout = QFormLayout(font_group)

        # 字体族
        self.font_family_combo = QComboBox()
        self.font_family_combo.setEditable(True)
        common_fonts = ["Consolas", "Monaco", "Courier New", "Source Code Pro", 
                       "Fira Code", "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono"]
        self.font_family_combo.addItems(common_fonts)
        font_layout.addRow("字体族:", self.font_family_combo)

        # 字体大小
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(12)
        font_layout.addRow("字体大小:", self.font_size_spin)

        # 字体样式
        style_layout = QHBoxLayout()
        self.bold_check = QCheckBox("粗体")
        self.italic_check = QCheckBox("斜体")
        style_layout.addWidget(self.bold_check)
        style_layout.addWidget(self.italic_check)
        style_layout.addStretch()
        font_layout.addRow("样式:", style_layout)

        # 字体预览按钮
        preview_button = QPushButton("选择字体...")
        preview_button.clicked.connect(self.choose_font)
        font_layout.addRow("预览:", preview_button)

        layout.addWidget(font_group)
        layout.addStretch()

    def choose_font(self):
        """选择字体"""
        current_font = QFont()
        current_font.setFamily(self.font_family_combo.currentText())
        current_font.setPointSize(self.font_size_spin.value())
        current_font.setBold(self.bold_check.isChecked())
        current_font.setItalic(self.italic_check.isChecked())
        
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.font_family_combo.setCurrentText(font.family())
            self.font_size_spin.setValue(font.pointSize())
            self.bold_check.setChecked(font.bold())
            self.italic_check.setChecked(font.italic())

    def load_config(self, config):
        """加载配置"""
        self.font_family_combo.setCurrentText(config.get("family", "Consolas"))
        self.font_size_spin.setValue(config.get("size", 12))
        self.bold_check.setChecked(config.get("bold", False))
        self.italic_check.setChecked(config.get("italic", False))

    def get_config(self):
        """获取配置"""
        return {
            "family": self.font_family_combo.currentText(),
            "size": self.font_size_spin.value(),
            "bold": self.bold_check.isChecked(),
            "italic": self.italic_check.isChecked()
        }


class ColorSettingsTab(QWidget):
    """颜色设置选项卡"""
    
    def __init__(self):
        super().__init__()
        self.color_buttons = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 颜色设置组
        color_group = QGroupBox("颜色设置")
        color_layout = QFormLayout(color_group)

        # 定义颜色项
        color_items = [
            ("background", "背景色"),
            ("text", "文本色"),
            ("keyword", "关键字"),
            ("string", "字符串"),
            ("comment", "注释"),
            ("number", "数字"),
            ("current_line", "当前行"),
            ("line_number", "行号"),
            ("line_number_bg", "行号背景")
        ]

        for key, label in color_items:
            button = QPushButton()
            button.setFixedSize(50, 30)
            button.clicked.connect(lambda checked, k=key: self.choose_color(k))
            self.color_buttons[key] = button
            color_layout.addRow(f"{label}:", button)

        layout.addWidget(color_group)
        layout.addStretch()

    def choose_color(self, color_key):
        """选择颜色"""
        current_color = self.color_buttons[color_key].palette().button().color()
        color = QColorDialog.getColor(current_color, self)
        if color.isValid():
            self.set_button_color(color_key, color.name())

    def set_button_color(self, key, color_hex):
        """设置按钮颜色"""
        button = self.color_buttons[key]
        button.setText(color_hex)

    def load_config(self, config):
        """加载配置"""
        for key, color_hex in config.items():
            if key in self.color_buttons:
                self.set_button_color(key, color_hex)

    def get_config(self):
        """获取配置"""
        config = {}
        for key, button in self.color_buttons.items():
            config[key] = button.text() if button.text().startswith('#') else "#282A36"
        return config


class LanguageSettingsTab(QWidget):
    """语言设置选项卡"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 语言设置组
        lang_group = QGroupBox("语言设置")
        lang_layout = QFormLayout(lang_group)

        # 默认语言
        self.default_lang_combo = QComboBox()
        languages = ["python", "javascript", "java", "cpp", "html", "css", "json", "xml", "sql", "bash"]
        self.default_lang_combo.addItems(languages)
        lang_layout.addRow("默认语言:", self.default_lang_combo)

        layout.addWidget(lang_group)
        layout.addStretch()

    def load_config(self, config):
        """加载配置"""
        default_lang = config.get("default", "python")
        index = self.default_lang_combo.findText(default_lang)
        if index >= 0:
            self.default_lang_combo.setCurrentIndex(index)

    def get_config(self):
        """获取配置"""
        return {
            "default": self.default_lang_combo.currentText(),
            "supported": ["python", "javascript", "java", "cpp", "html", "css", "json", "xml", "sql", "bash"]
        }


class BehaviorSettingsTab(QWidget):
    """行为设置选项卡"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 缩进设置组
        indent_group = QGroupBox("缩进设置")
        indent_layout = QFormLayout(indent_group)

        # Tab大小
        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(1, 8)
        self.tab_size_spin.setValue(4)
        indent_layout.addRow("Tab大小:", self.tab_size_spin)

        # 使用空格
        self.use_spaces_check = QCheckBox("使用空格代替Tab")
        indent_layout.addRow("", self.use_spaces_check)

        # 自动缩进
        self.auto_indent_check = QCheckBox("自动缩进")
        indent_layout.addRow("", self.auto_indent_check)

        layout.addWidget(indent_group)

        # 显示设置组
        display_group = QGroupBox("显示设置")
        display_layout = QFormLayout(display_group)

        # 显示行号
        self.show_line_numbers_check = QCheckBox("显示行号")
        display_layout.addRow("", self.show_line_numbers_check)

        # 高亮当前行
        self.highlight_current_line_check = QCheckBox("高亮当前行")
        display_layout.addRow("", self.highlight_current_line_check)

        # 自动换行
        self.word_wrap_check = QCheckBox("自动换行")
        display_layout.addRow("", self.word_wrap_check)

        layout.addWidget(display_group)

        # 编辑设置组
        edit_group = QGroupBox("编辑设置")
        edit_layout = QFormLayout(edit_group)

        # 自动完成
        self.auto_complete_check = QCheckBox("自动完成")
        edit_layout.addRow("", self.auto_complete_check)

        # 括号匹配
        self.bracket_matching_check = QCheckBox("括号匹配")
        edit_layout.addRow("", self.bracket_matching_check)

        layout.addWidget(edit_group)
        layout.addStretch()

    def load_config(self, config):
        """加载配置"""
        self.tab_size_spin.setValue(config.get("tab_size", 4))
        self.use_spaces_check.setChecked(config.get("use_spaces", True))
        self.auto_indent_check.setChecked(config.get("auto_indent", True))
        self.show_line_numbers_check.setChecked(config.get("show_line_numbers", True))
        self.highlight_current_line_check.setChecked(config.get("highlight_current_line", True))
        self.word_wrap_check.setChecked(config.get("word_wrap", False))
        self.auto_complete_check.setChecked(config.get("auto_complete", True))
        self.bracket_matching_check.setChecked(config.get("bracket_matching", True))

    def get_config(self):
        """获取配置"""
        return {
            "tab_size": self.tab_size_spin.value(),
            "use_spaces": self.use_spaces_check.isChecked(),
            "auto_indent": self.auto_indent_check.isChecked(),
            "show_line_numbers": self.show_line_numbers_check.isChecked(),
            "highlight_current_line": self.highlight_current_line_check.isChecked(),
            "word_wrap": self.word_wrap_check.isChecked(),
            "auto_complete": self.auto_complete_check.isChecked(),
            "bracket_matching": self.bracket_matching_check.isChecked()
        }