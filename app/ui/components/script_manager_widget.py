"""脚本管理：SQLite 存储 + 表单元数据。"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QFrame,
    QMessageBox,
    QFileDialog,
    QMenu,
    QDialog,
    QPlainTextEdit,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from .tabbed_code_editor import TabbedCodeEditor
from .script_storage import ScriptManager
import os
import subprocess
import tempfile


class ScriptListItem(QListWidgetItem):
    def __init__(self, script):
        super().__init__()
        self.script = script
        cat = f"[{script.category}] " if script.category else ""
        self.setText(f"{cat}{script.title}")
        self.setToolTip(
            f"类型：{script.script_type}\n平台：{script.platform}\n"
            f"分类：{script.category or '无'}\n描述：{script.description or '无'}"
        )


class ScriptManagerWidget(QWidget):
    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.script_manager = ScriptManager(session) if session else None
        self.current_script = None
        self.init_ui()
        if self.script_manager:
            self.load_scripts()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)

        toolbar = QFrame()
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(6, 3, 6, 3)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索脚本...")
        self.search_input.textChanged.connect(self.on_search)
        tb.addWidget(self.search_input)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem("全部平台")
        self.platform_combo.currentTextChanged.connect(self.on_search)
        tb.addWidget(self.platform_combo)

        self.category_combo = QComboBox()
        self.category_combo.addItem("全部分类")
        self.category_combo.currentTextChanged.connect(self.on_search)
        tb.addWidget(self.category_combo)

        tb.addStretch()

        new_btn = QPushButton("新建")
        new_btn.clicked.connect(self.new_script)
        tb.addWidget(new_btn)

        layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Horizontal)

        list_frame = QFrame()
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(2, 2, 2, 2)
        self.script_list = QListWidget()
        self.script_list.itemClicked.connect(self.on_script_selected)
        self.script_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self.show_context_menu)
        list_layout.addWidget(self.script_list)
        splitter.addWidget(list_frame)

        edit_frame = QFrame()
        edit_layout = QVBoxLayout(edit_frame)
        self.code_editor = TabbedCodeEditor(mode="script")
        self.code_editor.code_changed.connect(self.auto_save)
        self.code_editor.metadata_changed.connect(self.auto_save)
        edit_layout.addWidget(self.code_editor)

        run_row = QHBoxLayout()
        self.run_btn = QPushButton("运行")
        self.run_btn.clicked.connect(self.run_current_script)
        run_row.addWidget(self.run_btn)
        run_row.addStretch()
        edit_layout.addLayout(run_row)

        splitter.addWidget(edit_frame)
        splitter.setSizes([240, 760])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 8)

        layout.addWidget(splitter, 1)

        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_script)

    def load_scripts(self):
        if not self.script_manager:
            return
        self.script_list.clear()
        for script in self._filtered_scripts():
            self.script_list.addItem(ScriptListItem(script))

        platform = self.platform_combo.currentText()
        self.platform_combo.blockSignals(True)
        self.platform_combo.clear()
        self.platform_combo.addItem("全部平台")
        self.platform_combo.addItems(self.script_manager.get_platforms())
        if platform in [self.platform_combo.itemText(i) for i in range(self.platform_combo.count())]:
            self.platform_combo.setCurrentText(platform)
        self.platform_combo.blockSignals(False)

        category = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("全部分类")
        self.category_combo.addItems(self.script_manager.get_categories())
        if category in [self.category_combo.itemText(i) for i in range(self.category_combo.count())]:
            self.category_combo.setCurrentText(category)
        self.category_combo.blockSignals(False)

    def _filtered_scripts(self):
        keyword = self.search_input.text().strip() or None
        platform = self.platform_combo.currentText()
        if platform == "全部平台":
            platform = None
        category = self.category_combo.currentText()
        if category == "全部分类":
            category = None
        return self.script_manager.list_scripts(
            keyword=keyword, platform=platform, category=category
        )

    def on_search(self):
        if not self.script_manager:
            return
        self.script_list.clear()
        for script in self._filtered_scripts():
            self.script_list.addItem(ScriptListItem(script))

    def on_script_selected(self, item):
        if not isinstance(item, ScriptListItem):
            return
        self.current_script = item.script
        self.code_editor.set_code(self.current_script.content or "")
        tags = self.current_script.tags or ""
        self.code_editor.set_metadata(
            {
                "title": self.current_script.title,
                "script_type": self.current_script.script_type,
                "platform": self.current_script.platform,
                "category": self.current_script.category or "",
                "description": self.current_script.description or "",
                "tags": tags,
            }
        )

    def new_script(self):
        self.current_script = None
        self.code_editor.new_snippet()

    def _read_editor(self):
        content = self.code_editor.get_code().strip()
        meta = self.code_editor.get_metadata()
        title = meta.get("title", "").strip()
        if not content:
            return None, None, "请输入脚本内容"
        if not title:
            return None, None, "请输入标题"
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        payload = {
            "title": title,
            "content": content,
            "script_type": meta.get("script_type", "batch").strip(),
            "platform": meta.get("platform", "windows").strip(),
            "category": meta.get("category", "").strip() or None,
            "description": meta.get("description", "").strip() or None,
            "tags": tags,
        }
        return payload, meta, None

    def save_script(self):
        if not self.script_manager:
            QMessageBox.warning(self, "错误", "数据库未初始化")
            return
        payload, _, err = self._read_editor()
        if err:
            QMessageBox.warning(self, "错误", err)
            return
        try:
            if self.current_script:
                self.script_manager.update_script(self.current_script.id, **payload)
            else:
                self.current_script = self.script_manager.create_script(**payload)
            self.load_scripts()
            QMessageBox.information(self, "成功", "保存成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def auto_save(self):
        if not self.script_manager:
            return
        payload, _, err = self._read_editor()
        if err:
            return
        try:
            if self.current_script:
                self.script_manager.update_script(self.current_script.id, **payload)
            else:
                self.current_script = self.script_manager.create_script(**payload)
        except Exception:
            pass

    def delete_script(self, script):
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除脚本「{script.title}」？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.script_manager.delete_script(script.id)
            if self.current_script and self.current_script.id == script.id:
                self.current_script = None
                self.code_editor.new_snippet()
            self.load_scripts()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{e}")

    def show_context_menu(self, pos):
        item = self.script_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        run_action = menu.addAction("执行")
        delete_action = menu.addAction("删除")
        action = menu.exec_(self.script_list.mapToGlobal(pos))
        if action == run_action:
            self.run_script(item.script)
        elif action == delete_action:
            self.delete_script(item.script)

    def run_current_script(self):
        if self.current_script:
            self.run_script(self.current_script)
        else:
            payload, _, err = self._read_editor()
            if err:
                QMessageBox.warning(self, "错误", err)
                return
            from app.database import Script

            tmp = Script(**payload)
            self.run_script(tmp)

    def run_script(self, script):
        st = (script.script_type or "").lower()
        content = script.content
        title = script.title
        try:
            if st == "python":
                self._run_file(content, ".py", ["python"])
            elif st in ("shell", "bash"):
                self._run_file(content, ".sh", ["bash"])
            elif st == "powershell":
                result = subprocess.run(
                    ["powershell", "-Command", content],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=120,
                )
                self._show_result(title, result.stdout, result.stderr, result.returncode)
            else:
                self._run_file(content, ".bat", None, shell=True)
        except Exception as e:
            QMessageBox.critical(self, "执行错误", str(e))

    def _run_file(self, content, suffix, cmd, shell=False):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        try:
            run_cmd = [path] if cmd is None else cmd + [path]
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120,
                shell=shell,
            )
            self._show_result(path, result.stdout, result.stderr, result.returncode)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _show_result(self, title, stdout, stderr, code):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"执行结果 - {title}")
        dlg.resize(720, 480)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"退出代码: {code}"))
        if stdout:
            out = QPlainTextEdit()
            out.setPlainText(stdout)
            out.setReadOnly(True)
            out.setFont(QFont("Consolas", 10))
            lay.addWidget(QLabel("标准输出"))
            lay.addWidget(out)
        if stderr:
            err = QPlainTextEdit()
            err.setPlainText(stderr)
            err.setReadOnly(True)
            err.setFont(QFont("Consolas", 10))
            lay.addWidget(QLabel("错误输出"))
            lay.addWidget(err)
        close = QPushButton("关闭")
        close.clicked.connect(dlg.accept)
        lay.addWidget(close)
        dlg.exec()

    def export_script_file(self, script):
        ext_map = {
            "batch": ".bat",
            "powershell": ".ps1",
            "shell": ".sh",
            "python": ".py",
            "registry": ".reg",
        }
        ext = ext_map.get(script.script_type, ".txt")
        path, _ = QFileDialog.getSaveFileName(
            self, "导出脚本", f"{script.title}{ext}", f"脚本 (*{ext})"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(script.content)
            QMessageBox.information(self, "成功", "已导出")
