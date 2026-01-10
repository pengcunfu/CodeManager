from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, 
    QPushButton, QButtonGroup, QGroupBox, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ThemeDialog(QDialog):
    """主题选择对话框"""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.current_theme = theme_manager.get_current_theme()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("主题设置")
        self.setFixedSize(480, 380)
        self.setModal(True)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # 标题区域
        title_container = QVBoxLayout()
        title_label = QLabel("🎨 主题设置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_container.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("选择您喜欢的应用主题")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #888888; margin-bottom: 10px;")
        title_container.addWidget(subtitle_label)
        
        layout.addLayout(title_container)
        
        # 主题选择组
        theme_group = QGroupBox("🌈 可用主题")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(12)
        theme_layout.setContentsMargins(15, 20, 15, 15)
        
        # 创建单选按钮组
        self.button_group = QButtonGroup(self)
        
        # 获取可用主题
        themes = self.theme_manager.get_available_themes()
        
        # 主题图标映射
        theme_icons = {
            "dark": "🌙",
            "light": "☀️", 
            "high_contrast": "🔆",
            "blue": "💙",
            "green": "💚"
        }
        
        # 创建主题选项
        self.theme_buttons = {}
        for theme_key, theme_name in themes.items():
            # 创建主题选项容器
            theme_item_widget = QWidget()
            theme_item_layout = QVBoxLayout(theme_item_widget)
            theme_item_layout.setContentsMargins(10, 8, 10, 8)
            theme_item_layout.setSpacing(4)
            
            # 主要选项行
            main_row = QHBoxLayout()
            main_row.setSpacing(10)
            
            radio_button = QRadioButton()
            radio_button.setObjectName(theme_key)
            
            # 主题标签（图标 + 名称）
            icon = theme_icons.get(theme_key, "🎨")
            theme_label = QLabel(f"{icon} {theme_name}")
            theme_label.setStyleSheet("""
                font-weight: bold; 
                font-size: 12px;
                color: #ffffff;
                padding-left: 5px;
            """)
            
            # 设置当前主题为选中状态
            if theme_key == self.current_theme:
                radio_button.setChecked(True)
            
            self.button_group.addButton(radio_button)
            self.theme_buttons[theme_key] = radio_button
            
            # 添加到主要行
            main_row.addWidget(radio_button)
            main_row.addWidget(theme_label)
            main_row.addStretch()
            
            theme_item_layout.addLayout(main_row)
            
            # 主题描述
            description = self._get_theme_description(theme_key)
            if description:
                radio_button.setToolTip(description)
                desc_label = QLabel(description)
                desc_label.setStyleSheet("""
                    color: #cccccc; 
                    font-size: 10px; 
                    padding-left: 30px;
                    margin-top: 2px;
                """)
                theme_item_layout.addWidget(desc_label)
            
            # 设置主题项样式
            theme_item_widget.setStyleSheet("""
                QWidget {
                    background-color: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 6px;
                    margin: 2px;
                }
                QWidget:hover {
                    background-color: #404040;
                    border-color: #0078d4;
                }
            """)
            
            theme_layout.addWidget(theme_item_widget)
        
        layout.addWidget(theme_group)
        
        # 预览按钮区域
        preview_layout = QHBoxLayout()
        preview_button = QPushButton("👁️ 预览主题")
        preview_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        preview_button.clicked.connect(self.preview_theme)
        preview_layout.addStretch()
        preview_layout.addWidget(preview_button)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)
        
        # 分隔线
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #444444; margin: 10px 0;")
        layout.addWidget(separator)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 重置按钮
        reset_button = QPushButton("🔄 重置为默认")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        reset_button.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_button)
        
        button_layout.addStretch()
        
        # 取消按钮
        cancel_button = QPushButton("❌ 取消")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # 确定按钮
        ok_button = QPushButton("✅ 确定")
        ok_button.setDefault(True)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        ok_button.clicked.connect(self.accept_theme)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: #2b2b2b;
            }
            QRadioButton {
                spacing: 10px;
                padding: 8px;
                color: #ffffff;
                font-size: 12px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #777777;
                border-radius: 9px;
                background-color: #2b2b2b;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #0078d4;
                border-radius: 9px;
                background-color: #0078d4;
            }
            QRadioButton::indicator:unchecked:hover {
                border-color: #999999;
                background-color: #3a3a3a;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
    
    def _get_theme_description(self, theme_key):
        """获取主题描述"""
        descriptions = {
            "dark": "经典深色主题，适合长时间编程",
            "light": "清爽浅色主题，适合白天使用",
            "high_contrast": "高对比度主题，提高可读性",
            "blue": "蓝色主题，专业商务风格",
            "green": "绿色主题，护眼舒适"
        }
        return descriptions.get(theme_key, "")
    
    def get_selected_theme(self):
        """获取选中的主题"""
        for theme_key, button in self.theme_buttons.items():
            if button.isChecked():
                return theme_key
        return self.current_theme
    
    def preview_theme(self):
        """预览主题"""
        selected_theme = self.get_selected_theme()
        if selected_theme:
            self.theme_manager.apply_theme(selected_theme)
    
    def accept_theme(self):
        """确定应用主题"""
        selected_theme = self.get_selected_theme()
        if selected_theme:
            self.theme_manager.apply_theme(selected_theme)
            QMessageBox.information(self, "成功", f"主题已切换为: {self.theme_manager.get_available_themes()[selected_theme]}")
        self.accept()
    
    def reset_to_default(self):
        """重置为默认主题"""
        # 设置深色主题为默认
        if "dark" in self.theme_buttons:
            self.theme_buttons["dark"].setChecked(True)
            self.theme_manager.apply_theme("dark")
    
    def reject(self):
        """取消操作，恢复原主题"""
        # 恢复到对话框打开前的主题
        self.theme_manager.apply_theme(self.current_theme)
        super().reject()