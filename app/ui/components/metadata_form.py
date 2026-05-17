"""元数据表单：字段存 SQLite，不从代码注释解析。"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QLabel,
)
from PySide6.QtCore import Signal

LANGUAGE_OPTIONS = [
    "python",
    "javascript",
    "typescript",
    "java",
    "php",
    "go",
    "rust",
    "csharp",
    "cpp",
    "c",
    "html",
    "css",
    "sql",
    "shell",
    "bash",
    "powershell",
    "batch",
    "text",
]

SCRIPT_TYPE_OPTIONS = ["batch", "powershell", "shell", "python", "registry", "text"]
PLATFORM_OPTIONS = ["windows", "linux", "cross"]


class MetadataFormWidget(QWidget):
    metadata_changed = Signal(dict)

    def __init__(self, parent=None, *, mode: str = "snippet"):
        super().__init__(parent)
        self.mode = mode
        self._block_signals = False
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        hint = QLabel(
            "元数据保存在数据库中，不会写入源码注释。"
            if self.mode == "snippet"
            else "脚本元数据保存在数据库中。"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("标题")
        form.addRow("标题 *", self.title_edit)

        if self.mode == "snippet":
            self.language_combo = QComboBox()
            self.language_combo.setEditable(True)
            self.language_combo.addItems(LANGUAGE_OPTIONS)
            form.addRow("语言", self.language_combo)
        else:
            self.script_type_combo = QComboBox()
            self.script_type_combo.setEditable(True)
            self.script_type_combo.addItems(SCRIPT_TYPE_OPTIONS)
            form.addRow("脚本类型", self.script_type_combo)

            self.platform_combo = QComboBox()
            self.platform_combo.addItems(PLATFORM_OPTIONS)
            form.addRow("平台", self.platform_combo)

            self.category_edit = QLineEdit()
            self.category_edit.setPlaceholderText("例如：服务管理工具")
            form.addRow("分类", self.category_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("描述（可选）")
        form.addRow("描述", self.description_edit)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("多个标签用英文逗号分隔")
        form.addRow("标签", self.tags_edit)

        layout.addLayout(form)
        layout.addStretch()

    def _connect_signals(self):
        self.title_edit.textChanged.connect(self._emit_metadata)
        self.description_edit.textChanged.connect(self._emit_metadata)
        self.tags_edit.textChanged.connect(self._emit_metadata)
        if self.mode == "snippet":
            self.language_combo.currentTextChanged.connect(self._emit_metadata)
        else:
            self.script_type_combo.currentTextChanged.connect(self._emit_metadata)
            self.platform_combo.currentTextChanged.connect(self._emit_metadata)
            self.category_edit.textChanged.connect(self._emit_metadata)

    def _emit_metadata(self):
        if self._block_signals:
            return
        self.metadata_changed.emit(self.get_metadata())

    def get_metadata(self) -> dict:
        data = {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "tags": self.tags_edit.text().strip(),
        }
        if self.mode == "snippet":
            data["language"] = self.language_combo.currentText().strip() or "text"
        else:
            data["script_type"] = self.script_type_combo.currentText().strip() or "batch"
            data["platform"] = self.platform_combo.currentText().strip() or "windows"
            data["category"] = self.category_edit.text().strip()
        return data

    def set_metadata(self, metadata: dict | None):
        metadata = metadata or {}
        self._block_signals = True
        self.title_edit.setText(metadata.get("title", ""))
        self.description_edit.setPlainText(metadata.get("description", ""))
        tags = metadata.get("tags", "")
        if isinstance(tags, list):
            tags = ", ".join(tags)
        self.tags_edit.setText(tags)

        if self.mode == "snippet":
            lang = metadata.get("language", "python")
            idx = self.language_combo.findText(lang)
            if idx >= 0:
                self.language_combo.setCurrentIndex(idx)
            else:
                self.language_combo.setEditText(lang)
        else:
            st = metadata.get("script_type", "batch")
            idx = self.script_type_combo.findText(st)
            self.script_type_combo.setCurrentIndex(idx if idx >= 0 else 0)
            if idx < 0:
                self.script_type_combo.setEditText(st)

            platform = metadata.get("platform", "windows")
            pidx = self.platform_combo.findText(platform)
            self.platform_combo.setCurrentIndex(pidx if pidx >= 0 else 0)

            self.category_edit.setText(metadata.get("category", ""))

        self._block_signals = False

    def clear_form(self):
        defaults = (
            {
                "title": "新建代码片段",
                "language": "python",
                "description": "",
                "tags": "",
            }
            if self.mode == "snippet"
            else {
                "title": "新建脚本",
                "script_type": "batch",
                "platform": "windows",
                "category": "",
                "description": "",
                "tags": "",
            }
        )
        self.set_metadata(defaults)
