from PySide6.QtWidgets import (QDialog, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QFileDialog, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt
import json
import os

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle("首选项")
        self.resize(600, 400)

        # 创建主布局
        layout = QVBoxLayout(self)

        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # 创建各个环境配置选项卡
        self.python_tab = EnvironmentTab("Python", ["python", "pip"])
        tab_widget.addTab(self.python_tab, "Python环境")

        self.java_tab = EnvironmentTab("Java", ["java", "javac", "mvn"])
        tab_widget.addTab(self.java_tab, "Java环境")

        self.nodejs_tab = EnvironmentTab("Node.js", ["node", "npm"])
        tab_widget.addTab(self.nodejs_tab, "Node.js环境")

        self.cpp_tab = EnvironmentTab("C/C++", ["gcc", "g++", "make", "cmake"])
        tab_widget.addTab(self.cpp_tab, "C/C++环境")

        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 保存按钮
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def load_settings(self):
        """加载配置"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "../../data/settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.python_tab.load_settings(settings.get("python", {}))
                    self.java_tab.load_settings(settings.get("java", {}))
                    self.nodejs_tab.load_settings(settings.get("nodejs", {}))
                    self.cpp_tab.load_settings(settings.get("cpp", {}))
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置失败：{str(e)}")

    def save_settings(self):
        """保存配置"""
        try:
            settings = {
                "python": self.python_tab.get_settings(),
                "java": self.java_tab.get_settings(),
                "nodejs": self.nodejs_tab.get_settings(),
                "cpp": self.cpp_tab.get_settings()
            }

            settings_file = os.path.join(os.path.dirname(__file__), "../../data/settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "成功", "配置已保存")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败：{str(e)}")

class EnvironmentTab(QWidget):
    def __init__(self, name, commands):
        super().__init__()
        self.name = name
        self.commands = commands
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # 环境路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        form_layout.addRow(f"{self.name}路径:", path_layout)

        # 命令路径
        self.command_edits = {}
        for cmd in self.commands:
            cmd_layout = QHBoxLayout()
            edit = QLineEdit()
            browse_button = QPushButton("浏览...")
            browse_button.clicked.connect(lambda checked, c=cmd: self.browse_command(c))
            cmd_layout.addWidget(edit)
            cmd_layout.addWidget(browse_button)
            form_layout.addRow(f"{cmd}命令:", cmd_layout)
            self.command_edits[cmd] = edit

        layout.addLayout(form_layout)
        layout.addStretch()

    def browse_path(self):
        """浏览环境路径"""
        path = QFileDialog.getExistingDirectory(self, f"选择{self.name}环境路径")
        if path:
            self.path_edit.setText(path)

    def browse_command(self, command):
        """浏览命令路径"""
        file_filter = "可执行文件 (*.exe);;所有文件 (*.*)" if os.name == "nt" else "所有文件 (*)"
        path, _ = QFileDialog.getOpenFileName(self, f"选择{command}命令", filter=file_filter)
        if path:
            self.command_edits[command].setText(path)

    def load_settings(self, settings):
        """加载环境配置"""
        self.path_edit.setText(settings.get("path", ""))
        for cmd, edit in self.command_edits.items():
            edit.setText(settings.get(f"{cmd}_path", ""))

    def get_settings(self):
        """获取环境配置"""
        settings = {"path": self.path_edit.text()}
        for cmd, edit in self.command_edits.items():
            settings[f"{cmd}_path"] = edit.text()
        return settings