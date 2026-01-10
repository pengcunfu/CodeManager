from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QTextEdit, QPushButton, QLabel,
                             QFrame, QSplitter, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

class OutputHighlighter:
    def __init__(self, text_edit):
        self.text_edit = text_edit
        self.error_color = QColor("#FF5555")
        self.success_color = QColor("#50FA7B")
        self.warning_color = QColor("#FFB86C")
        self.info_color = QColor("#8BE9FD")

    def append_text(self, text, text_type="info"):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.End)
        format = cursor.charFormat()
        
        if text_type == "error":
            format.setForeground(self.error_color)
        elif text_type == "success":
            format.setForeground(self.success_color)
        elif text_type == "warning":
            format.setForeground(self.warning_color)
        else:  # info
            format.setForeground(self.info_color)

        cursor.setCharFormat(format)
        cursor.insertText(text + "\n")
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

class ScriptRunnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 创建顶部工具栏
        toolbar = QFrame()
        toolbar.setStyleSheet("QFrame { background-color: #282A36; border-radius: 5px; }")
        toolbar_layout = QHBoxLayout(toolbar)

        # 环境选择下拉框
        self.env_combo = QComboBox()
        self.env_combo.addItems(["本地环境", "Python环境", "JDK环境"])
        self.env_combo.setStyleSheet("""
            QComboBox {
                background-color: #44475A;
                color: #F8F8F2;
                border: none;
                border-radius: 5px;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(resource/icons/down-arrow.svg);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #282A36;
                color: #F8F8F2;
                selection-background-color: #44475A;
            }
        """)

        # 运行按钮
        self.run_btn = QPushButton("运行")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #50FA7B;
                color: #282A36;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5AF78E;
            }
            QPushButton:pressed {
                background-color: #42CF6A;
            }
        """)

        # 停止按钮
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5555;
                color: #F8F8F2;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6E6E;
            }
            QPushButton:pressed {
                background-color: #E64747;
            }
        """)

        toolbar_layout.addWidget(self.env_combo)
        toolbar_layout.addWidget(self.run_btn)
        toolbar_layout.addWidget(self.stop_btn)
        toolbar_layout.addStretch()

        layout.addWidget(toolbar)

        # 创建主分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧脚本树
        self.script_tree = QTreeWidget()
        self.script_tree.setHeaderLabel("脚本列表")
        self.script_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #282A36;
                color: #F8F8F2;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 5px;
                margin: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #6272A4;
            }
            QTreeWidget::item:hover {
                background-color: #44475A;
            }
            QTreeWidget::branch {
                background-color: #282A36;
            }
        """)

        # 右侧面板
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #282A36; border-radius: 5px; }")
        right_layout = QVBoxLayout(right_panel)

        # 脚本内容查看器
        self.script_viewer = QTextEdit()
        self.script_viewer.setReadOnly(True)
        self.script_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #282A36;
                color: #F8F8F2;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                selection-background-color: #44475A;
            }
        """)
        font = QFont("Consolas", 13)
        font.setFixedPitch(True)
        self.script_viewer.setFont(font)

        # 输出区域
        output_frame = QFrame()
        output_frame.setStyleSheet("QFrame { background-color: #44475A; border-radius: 5px; }")
        output_layout = QVBoxLayout(output_frame)

        output_label = QLabel("执行输出")
        output_label.setStyleSheet("QLabel { color: #F8F8F2; }")

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #282A36;
                color: #F8F8F2;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }
        """)
        self.output_text.setFont(font)
        self.output_highlighter = OutputHighlighter(self.output_text)

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_text)

        right_layout.addWidget(self.script_viewer, stretch=1)
        right_layout.addWidget(output_frame, stretch=1)

        splitter.addWidget(self.script_tree)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)