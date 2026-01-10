from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
import qdarkstyle
import json
import os
from ..utils.config_manager import config_manager

class ThemeManager(QObject):
    """主题管理器"""
    
    theme_changed = Signal(str)  # 主题改变信号
    
    def __init__(self):
        super().__init__()
        self.current_theme = config_manager.get_current_theme()
        self.config_file = "data/theme_config.json"  # 保留兼容性
        # 不再需要load_theme_config，直接从config_manager获取
        
    def get_available_themes(self):
        """获取可用主题列表"""
        return {
            "dark": "深色主题",
            "light": "浅色主题",
            "high_contrast": "高对比度",
            "blue": "蓝色主题",
            "green": "绿色主题"
        }
    
    def get_theme_stylesheet(self, theme_name):
        """获取主题样式表"""
        if theme_name == "dark":
            return qdarkstyle.load_stylesheet_pyside6()
        elif theme_name == "light":
            return self._get_light_theme_stylesheet()
        elif theme_name == "high_contrast":
            return self._get_high_contrast_stylesheet()
        elif theme_name == "blue":
            return self._get_blue_theme_stylesheet()
        elif theme_name == "green":
            return self._get_green_theme_stylesheet()
        else:
            return qdarkstyle.load_stylesheet_pyside6()  # 默认深色主题
    
    def _get_light_theme_stylesheet(self):
        """浅色主题样式"""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        QMenuBar {
            background-color: #f0f0f0;
            color: #000000;
            border-bottom: 1px solid #d0d0d0;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        QMenu {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
        }
        QMenu::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        QTabWidget::pane {
            border: 1px solid #d0d0d0;
            background-color: #ffffff;
        }
        QTabBar::tab {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #d0d0d0;
            padding: 8px 12px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 1px solid #ffffff;
        }
        QListWidget {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
        }
        QListWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
        }
        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #106ebe;
        }
        QLineEdit, QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            padding: 4px;
        }
        QStatusBar {
            background-color: #f0f0f0;
            color: #000000;
            border-top: 1px solid #d0d0d0;
        }
        """
    
    def _get_high_contrast_stylesheet(self):
        """高对比度主题样式"""
        return """
        QMainWindow {
            background-color: #000000;
            color: #ffffff;
        }
        QMenuBar {
            background-color: #000000;
            color: #ffffff;
            border-bottom: 2px solid #ffffff;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 6px 10px;
            border: 1px solid transparent;
        }
        QMenuBar::item:selected {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #ffffff;
        }
        QMenu {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
        }
        QMenu::item:selected {
            background-color: #ffffff;
            color: #000000;
        }
        QTabWidget::pane {
            border: 2px solid #ffffff;
            background-color: #000000;
        }
        QTabBar::tab {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
            padding: 10px 15px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #000000;
        }
        QListWidget {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
        }
        QListWidget::item:selected {
            background-color: #ffffff;
            color: #000000;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
        }
        QPushButton {
            background-color: #ffffff;
            color: #000000;
            border: 2px solid #ffffff;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #000000;
            color: #ffffff;
        }
        QLineEdit, QComboBox {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
            padding: 6px;
        }
        QStatusBar {
            background-color: #000000;
            color: #ffffff;
            border-top: 2px solid #ffffff;
        }
        """
    
    def _get_blue_theme_stylesheet(self):
        """蓝色主题样式"""
        return """
        QMainWindow {
            background-color: #1e3a5f;
            color: #ffffff;
        }
        QMenuBar {
            background-color: #2c5282;
            color: #ffffff;
            border-bottom: 1px solid #4a90c2;
        }
        QMenuBar::item:selected {
            background-color: #4a90c2;
        }
        QMenu {
            background-color: #2c5282;
            color: #ffffff;
            border: 1px solid #4a90c2;
        }
        QMenu::item:selected {
            background-color: #4a90c2;
        }
        QTabWidget::pane {
            border: 1px solid #4a90c2;
            background-color: #1e3a5f;
        }
        QTabBar::tab {
            background-color: #2c5282;
            color: #ffffff;
            border: 1px solid #4a90c2;
            padding: 8px 12px;
        }
        QTabBar::tab:selected {
            background-color: #4a90c2;
        }
        QListWidget {
            background-color: #1e3a5f;
            color: #ffffff;
            border: 1px solid #4a90c2;
        }
        QListWidget::item:selected {
            background-color: #4a90c2;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #1e3a5f;
            color: #ffffff;
            border: 1px solid #4a90c2;
        }
        QPushButton {
            background-color: #4a90c2;
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #5ba3d4;
        }
        QLineEdit, QComboBox {
            background-color: #1e3a5f;
            color: #ffffff;
            border: 1px solid #4a90c2;
            padding: 4px;
        }
        QStatusBar {
            background-color: #2c5282;
            color: #ffffff;
            border-top: 1px solid #4a90c2;
        }
        """
    
    def _get_green_theme_stylesheet(self):
        """绿色主题样式"""
        return """
        QMainWindow {
            background-color: #1a4d3a;
            color: #ffffff;
        }
        QMenuBar {
            background-color: #2d7d32;
            color: #ffffff;
            border-bottom: 1px solid #4caf50;
        }
        QMenuBar::item:selected {
            background-color: #4caf50;
        }
        QMenu {
            background-color: #2d7d32;
            color: #ffffff;
            border: 1px solid #4caf50;
        }
        QMenu::item:selected {
            background-color: #4caf50;
        }
        QTabWidget::pane {
            border: 1px solid #4caf50;
            background-color: #1a4d3a;
        }
        QTabBar::tab {
            background-color: #2d7d32;
            color: #ffffff;
            border: 1px solid #4caf50;
            padding: 8px 12px;
        }
        QTabBar::tab:selected {
            background-color: #4caf50;
        }
        QListWidget {
            background-color: #1a4d3a;
            color: #ffffff;
            border: 1px solid #4caf50;
        }
        QListWidget::item:selected {
            background-color: #4caf50;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #1a4d3a;
            color: #ffffff;
            border: 1px solid #4caf50;
        }
        QPushButton {
            background-color: #4caf50;
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #66bb6a;
        }
        QLineEdit, QComboBox {
            background-color: #1a4d3a;
            color: #ffffff;
            border: 1px solid #4caf50;
            padding: 4px;
        }
        QStatusBar {
            background-color: #2d7d32;
            color: #ffffff;
            border-top: 1px solid #4caf50;
        }
        """
    
    def apply_theme(self, theme_name, app=None):
        """应用主题"""
        if app is None:
            app = QApplication.instance()
        
        if app:
            stylesheet = self.get_theme_stylesheet(theme_name)
            app.setStyleSheet(stylesheet)
            self.current_theme = theme_name
            self.save_theme_config()
            self.theme_changed.emit(theme_name)
    
    def get_current_theme(self):
        """获取当前主题"""
        return self.current_theme
    
    def load_theme_config(self):
        """加载主题配置（已迁移到config_manager）"""
        self.current_theme = config_manager.get_current_theme()
    
    def save_theme_config(self):
        """保存主题配置（已迁移到config_manager）"""
        config_manager.set_current_theme(self.current_theme)