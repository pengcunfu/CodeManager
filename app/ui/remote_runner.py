from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QTextEdit, QPushButton, QLabel,
                             QFrame, QSplitter, QDialog, QLineEdit, QFormLayout,
                             QMessageBox, QHeaderView)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

class ServerConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("服务器配置")
        self.setStyleSheet("""
            QDialog {
                background-color: #282A36;
            }
            QLabel {
                color: #F8F8F2;
            }
            QLineEdit {
                background-color: #44475A;
                color: #F8F8F2;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
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

        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addRow("名称:", self.name_input)
        layout.addRow("主机:", self.host_input)
        layout.addRow("端口:", self.port_input)
        layout.addRow("用户名:", self.username_input)
        layout.addRow("密码:", self.password_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5555;
                color: #F8F8F2;
            }
            QPushButton:hover {
                background-color: #FF6E6E;
            }
            QPushButton:pressed {
                background-color: #E64747;
            }
        """)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow("", btn_layout)

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

class RemoteRunnerWidget(QWidget):
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

        # 添加服务器按钮
        self.add_server_btn = QPushButton("添加服务器")
        self.add_server_btn.setStyleSheet("""
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

        # 删除服务器按钮
        self.remove_server_btn = QPushButton("删除服务器")
        self.remove_server_btn.setStyleSheet("""
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

        toolbar_layout.addWidget(self.add_server_btn)
        toolbar_layout.addWidget(self.remove_server_btn)
        toolbar_layout.addStretch()

        layout.addWidget(toolbar)

        # 创建主分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧服务器列表
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(4)
        self.server_table.setHorizontalHeaderLabels(["名称", "主机", "端口", "状态"])
        self.server_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.server_table.setStyleSheet("""
            QTableWidget {
                background-color: #282A36;
                color: #F8F8F2;
                border: none;
                border-radius: 5px;
                gridline-color: #44475A;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #6272A4;
            }
            QHeaderView::section {
                background-color: #44475A;
                color: #F8F8F2;
                padding: 5px;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #282A36;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #44475A;
                border-radius: 5px;
            }
        """)

        # 右侧面板
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #282A36; border-radius: 5px; }")
        right_layout = QVBoxLayout(right_panel)

        # 命令输入区域
        command_frame = QFrame()
        command_frame.setStyleSheet("QFrame { background-color: #44475A; border-radius: 5px; }")
        command_layout = QVBoxLayout(command_frame)

        command_label = QLabel("命令输入")
        command_label.setStyleSheet("QLabel { color: #F8F8F2; }")

        self.command_edit = QTextEdit()
        self.command_edit.setStyleSheet("""
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
        font = QFont("Consolas", 13)
        font.setFixedPitch(True)
        self.command_edit.setFont(font)

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

        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_edit)
        command_layout.addWidget(self.run_btn)

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

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_text)

        right_layout.addWidget(command_frame)
        right_layout.addWidget(output_frame)

        splitter.addWidget(self.server_table)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # 连接信号
        self.add_server_btn.clicked.connect(self.show_server_config_dialog)

    def show_server_config_dialog(self):
        dialog = ServerConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 添加服务器到列表
            row = self.server_table.rowCount()
            self.server_table.insertRow(row)
            self.server_table.setItem(row, 0, QTableWidgetItem(dialog.name_input.text()))
            self.server_table.setItem(row, 1, QTableWidgetItem(dialog.host_input.text()))
            self.server_table.setItem(row, 2, QTableWidgetItem(dialog.port_input.text()))
            self.server_table.setItem(row, 3, QTableWidgetItem("未连接"))