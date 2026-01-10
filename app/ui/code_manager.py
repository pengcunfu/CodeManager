from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QTextEdit, QComboBox, QLineEdit, QPushButton,
                             QListWidgetItem, QMessageBox, QFrame, QScrollArea,
                             QLabel, QSplitter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QTextCharFormat, QSyntaxHighlighter, QColor, QFont
import keyword
import re

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Python关键字高亮
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF79C6"))
        keyword_format.setFontWeight(QFont.Bold)
        for word in keyword.kwlist:
            self.highlighting_rules.append((re.compile(f"\\b{word}\\b"), keyword_format))

        # 字符串高亮
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#F1FA8C"))
        self.highlighting_rules.append((re.compile('"[^"\\\n]*(?:\\.[^"\\\n]*)*"'), string_format))
        self.highlighting_rules.append((re.compile("'[^'\\\n]*(?:\\.[^'\\\n]*)*'"), string_format))

        # 注释高亮
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272A4"))
        self.highlighting_rules.append((re.compile("#[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.length(), format)

class TagButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

class TagCloud(QWidget):
    tag_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)

    def update_tags(self, tags):
        # 清除现有标签
        for i in reversed(range(self.layout.count())):  
            self.layout.itemAt(i).widget().deleteLater()

        # 添加新标签
        for tag in sorted(set(tags)):
            if tag.strip():
                btn = TagButton(tag)
                btn.clicked.connect(lambda checked, t=tag: self.tag_clicked.emit(t))
                self.layout.addWidget(btn)

class CodeManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 创建顶部工具栏
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索代码片段...")

        # 语言选择下拉框
        self.language_combo = QComboBox()
        self.language_combo.addItems(["全部", "Python", "Java", "JavaScript", "Shell", "Batch"])

        toolbar_layout.addWidget(self.search_box)
        toolbar_layout.addWidget(self.language_combo)
        layout.addWidget(toolbar)

        # 创建标签云
        self.tag_cloud = TagCloud()
        layout.addWidget(self.tag_cloud)

        # 创建主分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧代码片段列表
        self.document_list = QListWidget()

        # 右侧代码编辑区
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        # 代码编辑器
        self.code_edit = QTextEdit()
        font = QFont("Consolas", 13)
        font.setFixedPitch(True)
        self.code_edit.setFont(font)

        # 标签输入和保存按钮区域
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("输入标签，用逗号分隔")

        self.save_btn = QPushButton("保存")

        bottom_layout.addWidget(self.tag_input)
        bottom_layout.addWidget(self.save_btn)

        right_layout.addWidget(self.code_edit)
        right_layout.addWidget(bottom_frame)

        splitter.addWidget(self.document_list)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)