from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QScrollArea
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from app.ui.components.enhanced_code_editor import EnhancedCodeEditor, SyntaxHighlighter
from .metadata_form import MetadataFormWidget


class SourceCodeEditor(EnhancedCodeEditor):
    """纯源码编辑器，不含注释元数据。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("请输入源代码...")

    def set_metadata(self, metadata):
        pass

    def get_metadata(self):
        return {}


class TabbedCodeEditor(QWidget):
    """代码编辑：元信息表单 + 源码，元数据存 SQLite。"""

    code_changed = Signal(str)
    metadata_changed = Signal(dict)

    def __init__(self, parent=None, *, mode: str = "snippet"):
        super().__init__(parent)
        self.mode = mode
        self.current_language = "python"
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(False)

        meta_scroll = QScrollArea()
        meta_scroll.setWidgetResizable(True)
        meta_scroll.setFrameShape(QScrollArea.NoFrame)
        self.metadata_editor = MetadataFormWidget(mode=self.mode)
        meta_scroll.setWidget(self.metadata_editor)
        self.tab_widget.addTab(meta_scroll, "元信息")

        self.source_editor = SourceCodeEditor()
        self.tab_widget.addTab(self.source_editor, "源码")

        layout.addWidget(self.tab_widget)

    def connect_signals(self):
        self.metadata_editor.metadata_changed.connect(self.metadata_changed.emit)
        self.source_editor.code_changed.connect(self.code_changed.emit)

    def set_code(self, code):
        self.source_editor.set_code(code)

    def get_code(self):
        return self.source_editor.get_code()

    def set_language(self, language):
        self.current_language = language
        self.source_editor.set_language(language)
        if self.mode == "snippet":
            meta = self.metadata_editor.get_metadata()
            meta["language"] = language
            self.metadata_editor.set_metadata(meta)

    def set_metadata(self, metadata):
        self.metadata_editor.set_metadata(metadata)

    def get_metadata(self):
        return self.metadata_editor.get_metadata()

    def new_snippet(self):
        self.metadata_editor.clear_form()
        default_code = (
            '# 在这里编写代码\nprint("Hello, World!")'
            if self.mode == "snippet"
            else "@echo off\necho Hello"
        )
        lang = "python" if self.mode == "snippet" else "batch"
        self.set_code(default_code)
        self.set_language(lang)
        self.tab_widget.setCurrentIndex(0)

    def apply_config(self, config):
        self.source_editor.apply_config(config)
