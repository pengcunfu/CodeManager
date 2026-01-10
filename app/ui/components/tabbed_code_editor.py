from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTextEdit, QPlainTextEdit
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from app.ui.components.enhanced_code_editor import EnhancedCodeEditor, SyntaxHighlighter
from app.utils.config_manager import config_manager


class MetadataEditor(QTextEdit):
    """元信息编辑器"""
    
    metadata_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.textChanged.connect(self.on_text_changed)
        
    def setup_ui(self):
        """设置UI"""
        # 设置字体
        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # 设置占位符文本
        self.setPlaceholderText("请输入代码片段的元信息...\n\n示例：\ntitle: 我的代码片段\nlanguage: python\ntags: 工具, 示例\ndescription: 这是一个示例代码片段")
        
    def on_text_changed(self):
        """文本改变时解析元信息"""
        metadata = self.parse_metadata()
        self.metadata_changed.emit(metadata)
        
    def parse_metadata(self):
        """解析元信息文本为字典"""
        text = self.toPlainText().strip()
        metadata = {}
        
        if not text:
            return metadata
            
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    metadata[key] = value
                    
        return metadata
        
    def set_metadata(self, metadata):
        """设置元信息"""
        if not metadata:
            self.clear()
            return
            
        lines = []
        for key, value in metadata.items():
            if value:  # 只显示有值的字段
                lines.append(f"{key}: {value}")
                
        self.setPlainText('\n'.join(lines))
        
    def get_metadata(self):
        """获取元信息"""
        return self.parse_metadata()


class SourceCodeEditor(QPlainTextEdit):
    """源码编辑器"""
    
    code_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_language = "python"
        self.setup_ui()
        self.textChanged.connect(self.on_text_changed)
        
        # 语法高亮器
        self.highlighter = SyntaxHighlighter(self.document())
        self.highlighter.set_language(self.current_language)
        
    def setup_ui(self):
        """设置UI"""
        # 设置字体
        font = QFont("Consolas", 12)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # 设置制表符宽度
        self.setTabStopDistance(40)  # 4个字符的宽度
        
        # 设置占位符文本
        self.setPlaceholderText("请输入源代码...")
        
    def on_text_changed(self):
        """文本改变时发出信号"""
        self.code_changed.emit(self.toPlainText())
        
    def set_code(self, code):
        """设置代码内容"""
        self.setPlainText(code)
        
    def get_code(self):
        """获取代码内容"""
        return self.toPlainText()
        
    def set_language(self, language):
        """设置编程语言"""
        self.current_language = language.lower()
        if self.highlighter:
            self.highlighter.set_language(self.current_language)


class TabbedCodeEditor(QWidget):
    """带Tab的代码编辑器，分离元信息和源码"""
    
    code_changed = Signal(str)
    metadata_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_language = "python"
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建Tab控件 - 使用原生样式
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(False)
        
        # 创建元信息编辑器
        self.metadata_editor = MetadataEditor()
        self.tab_widget.addTab(self.metadata_editor, "元信息")
        
        # 创建源码编辑器
        self.source_editor = SourceCodeEditor()
        self.tab_widget.addTab(self.source_editor, "源码")
        
        layout.addWidget(self.tab_widget)
        
    def connect_signals(self):
        """连接信号"""
        self.metadata_editor.metadata_changed.connect(self.metadata_changed.emit)
        self.source_editor.code_changed.connect(self.code_changed.emit)
        
    def set_code(self, code):
        """设置代码内容"""
        self.source_editor.set_code(code)
        
    def get_code(self):
        """获取代码内容"""
        return self.source_editor.get_code()
        
    def set_language(self, language):
        """设置编程语言"""
        self.current_language = language
        self.source_editor.set_language(language)
        
    def set_metadata(self, metadata):
        """设置元信息"""
        self.metadata_editor.set_metadata(metadata)
        
    def get_metadata(self):
        """获取元信息"""
        return self.metadata_editor.get_metadata()
        
    def new_snippet(self):
        """创建新代码片段"""
        # 设置默认元信息
        default_metadata = {
            'title': '新建代码片段',
            'language': 'python',
            'tags': 'tag1, tag2',
            'description': '在这里添加描述'
        }
        self.set_metadata(default_metadata)
        
        # 设置默认代码
        default_code = '''# 在这里编写代码
print("Hello, World!")'''
        self.set_code(default_code)
        
        # 切换到元信息Tab
        self.tab_widget.setCurrentIndex(0)
        
    def apply_config(self, config):
        """应用编辑器配置"""
        # 这里可以根据需要应用配置到两个编辑器
        pass