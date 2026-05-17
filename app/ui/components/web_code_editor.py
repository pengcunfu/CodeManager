from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget, QVBoxLayout

import json

from app.utils.config_manager import config_manager

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EDITOR_HTML = PROJECT_ROOT / "resources" / "editor" / "code_editor.html"

DEFAULT_EDITOR_CONFIG = {
    "font": {
        "family": "Cascadia Code",
        "size": 13,
        "bold": False,
        "italic": False,
    },
    "colors": {
        "background": "#282A36",
        "text": "#F8F8F2",
        "keyword": "#FF79C6",
        "string": "#F1FA8C",
        "comment": "#6272A4",
        "number": "#BD93F9",
        "current_line": "rgba(68, 71, 90, 0.45)",
        "line_number": "#6272A4",
        "line_number_bg": "#21222C",
    },
    "behavior": {
        "tab_size": 4,
        "use_spaces": True,
        "auto_indent": True,
        "show_line_numbers": True,
        "highlight_current_line": True,
        "word_wrap": False,
    },
}


class CodeEditorBridge(QObject):
    """JavaScript 与 Python 之间的桥接对象。"""

    code_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._code = ""
        self._language = "python"

    @Slot(str)
    def on_code_changed(self, code: str):
        self._code = code
        self.code_changed.emit(code)

    @Slot(str)
    def set_code(self, code: str):
        self._code = code

    @Slot(str)
    def set_language(self, language: str):
        self._language = language

    @Slot(result=str)
    def get_code(self) -> str:
        return self._code

    @Slot(result=str)
    def get_language(self) -> str:
        return self._language


class WebCodeEditor(QWidget):
    """基于 QWebEngineView + Ace Editor 的代码编辑器。"""

    code_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge = CodeEditorBridge()
        self.web_view = QWebEngineView()
        self.current_language = "python"
        self._page_ready = False
        self._pending_code: str | None = None
        self._pending_language: str | None = None
        self._pending_config: dict | None = None
        self._pending_placeholder: str | None = None

        self.setup_ui()
        self.setup_web_channel()
        self.load_editor()
        self.bridge.code_changed.connect(self.code_changed.emit)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)

    def setup_web_channel(self):
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        self.web_view.loadFinished.connect(self._on_load_finished)

    def _editor_html_path(self) -> Path:
        if EDITOR_HTML.is_file():
            return EDITOR_HTML
        fallback = Path("resources/editor/code_editor.html")
        if fallback.is_file():
            return fallback.resolve()
        raise FileNotFoundError(f"找不到编辑器 HTML: {EDITOR_HTML}")

    def load_editor(self):
        html_path = self._editor_html_path()
        self.web_view.load(QUrl.fromLocalFile(str(html_path)))

    def _on_load_finished(self, ok: bool):
        if not ok:
            return
        self._page_ready = True
        config = self._normalize_config(config_manager.get_editor_config())
        self._run_js(f"window.applyConfig({json.dumps(config)});")
        if self._pending_placeholder is not None:
            self._run_js(f"window.setPlaceholder({json.dumps(self._pending_placeholder)});")
        if self._pending_language:
            self.set_language(self._pending_language)
        if self._pending_code is not None:
            self.set_code(self._pending_code)
        elif self.bridge._code:
            self.set_code(self.bridge._code)
        if self._pending_config:
            self.apply_config(self._pending_config)

    def _run_js(self, script: str):
        if self._page_ready:
            self.web_view.page().runJavaScript(script)

    @staticmethod
    def _normalize_config(config: dict | None) -> dict:
        if not config:
            return DEFAULT_EDITOR_CONFIG.copy()

        if "font" in config or "colors" in config or "behavior" in config:
            merged = {
                "font": {**DEFAULT_EDITOR_CONFIG["font"], **config.get("font", {})},
                "colors": {**DEFAULT_EDITOR_CONFIG["colors"], **config.get("colors", {})},
                "behavior": {**DEFAULT_EDITOR_CONFIG["behavior"], **config.get("behavior", {})},
            }
            return merged

        return {
            "font": {
                "family": config.get("font_family", DEFAULT_EDITOR_CONFIG["font"]["family"]),
                "size": config.get("font_size", DEFAULT_EDITOR_CONFIG["font"]["size"]),
            },
            "colors": DEFAULT_EDITOR_CONFIG["colors"],
            "behavior": {
                "tab_size": config.get("tab_size", 4),
                "show_line_numbers": config.get("line_numbers", True),
                "word_wrap": config.get("word_wrap", False),
                "auto_indent": config.get("auto_indent", True),
                "highlight_current_line": True,
            },
        }

    def set_code(self, code: str):
        self.bridge.set_code(code)
        payload = json.dumps(code or "")
        if self._page_ready:
            self.web_view.page().runJavaScript(f"window.setCode({payload});")
        else:
            self._pending_code = code

    def get_code(self) -> str:
        return self.bridge.get_code()

    def set_language(self, language: str):
        self.current_language = (language or "text").lower()
        self.bridge.set_language(self.current_language)
        monaco_lang = self._map_language(self.current_language)
        if self._page_ready:
            self.web_view.page().runJavaScript(f"window.setLanguage({json.dumps(monaco_lang)});")
        else:
            self._pending_language = self.current_language

    def setPlaceholderText(self, text: str):
        if self._page_ready:
            self.web_view.page().runJavaScript(f"window.setPlaceholder({json.dumps(text)});")
        else:
            self._pending_placeholder = text

    def apply_config(self, config: dict):
        normalized = self._normalize_config(config)
        if self._page_ready:
            self.web_view.page().runJavaScript(f"window.applyConfig({json.dumps(normalized)});")
        else:
            self._pending_config = normalized

    def load_saved_config(self):
        self.apply_config(config_manager.get_editor_config())

    def insert_text(self, text: str):
        self.web_view.page().runJavaScript(f"window.insertText({json.dumps(text)});")

    def focusEditor(self):
        self.web_view.page().runJavaScript("window.focus();")

    def focus(self):
        self.focusEditor()

    @staticmethod
    def _map_language(language: str) -> str:
        """返回 Ace 编辑器识别的语言键（见 code_editor.html LANG_MODES）。"""
        language_map = {
            "python": "python",
            "javascript": "javascript",
            "js": "javascript",
            "typescript": "typescript",
            "ts": "typescript",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "c++": "cpp",
            "csharp": "csharp",
            "c#": "csharp",
            "php": "php",
            "ruby": "ruby",
            "go": "go",
            "rust": "rust",
            "swift": "swift",
            "kotlin": "kotlin",
            "scala": "scala",
            "r": "r",
            "perl": "perl",
            "lua": "lua",
            "shell": "bash",
            "bash": "bash",
            "powershell": "powershell",
            "batch": "batch",
            "bat": "batch",
            "cmd": "batch",
            "html": "html",
            "htm": "html",
            "css": "css",
            "scss": "scss",
            "less": "less",
            "xml": "xml",
            "json": "json",
            "yaml": "yaml",
            "yml": "yaml",
            "sql": "sql",
            "dockerfile": "dockerfile",
            "markdown": "markdown",
            "md": "markdown",
            "text": "text",
            "plaintext": "text",
        }
        return language_map.get((language or "text").lower(), "text")
