"""脚本管理：SQLite 存储 + 表单元数据。"""
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .script_storage import ScriptManager
from .tabbed_code_editor import TabbedCodeEditor

UNCATEGORIZED_LABEL = "未分类"


class _FolderNode:
  """内存中的文件夹树节点。"""

  def __init__(self, name: str):
    self.name = name
    self.children: Dict[str, "_FolderNode"] = {}
    self.scripts: List = []


def _normalize_category(category: Optional[str]) -> str:
  if not category:
    return ""
  return category.replace("\\", "/").strip("/")


def _build_folder_tree(scripts: List) -> tuple[_FolderNode, List]:
  root = _FolderNode("")
  uncategorized: List = []
  for script in scripts:
    path = _normalize_category(script.category)
    if not path:
      uncategorized.append(script)
      continue
    node = root
    for part in path.split("/"):
      if part not in node.children:
        node.children[part] = _FolderNode(part)
      node = node.children[part]
    node.scripts.append(script)
  return root, uncategorized


class ScriptTreeItem(QTreeWidgetItem):
  def __init__(self, script):
    super().__init__()
    self.script = script
    self.is_folder = False
    self.setText(0, script.title)
    self.setToolTip(
      f"类型：{script.script_type}\n平台：{script.platform}\n"
      f"分类：{script.category or '无'}\n描述：{script.description or '无'}"
    )


class ScriptFolderItem(QTreeWidgetItem):
  def __init__(self, name: str, folder_path: str):
    super().__init__()
    self.script = None
    self.is_folder = True
    self.folder_path = folder_path
    self.setText(0, name)
    self.setToolTip(folder_path or UNCATEGORIZED_LABEL)
    self.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)


class ScriptManagerWidget(QWidget):
  def __init__(self, session=None, parent=None):
    super().__init__(parent)
    self.script_manager = ScriptManager(session) if session else None
    self.current_script = None
    self._selected_script_id: Optional[int] = None
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

    tb.addStretch()

    new_btn = QPushButton("新建")
    new_btn.clicked.connect(self.new_script)
    tb.addWidget(new_btn)

    layout.addWidget(toolbar)

    splitter = QSplitter(Qt.Horizontal)

    list_frame = QFrame()
    list_layout = QVBoxLayout(list_frame)
    list_layout.setContentsMargins(2, 2, 2, 2)
    self.script_tree = QTreeWidget()
    self.script_tree.setHeaderHidden(True)
    self.script_tree.setRootIsDecorated(True)
    self.script_tree.setAnimated(True)
    self.script_tree.setIndentation(16)
    self.script_tree.itemClicked.connect(self.on_tree_item_clicked)
    self.script_tree.setContextMenuPolicy(Qt.CustomContextMenu)
    self.script_tree.customContextMenuRequested.connect(self.show_context_menu)
    list_layout.addWidget(self.script_tree)
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

  def _filtered_scripts(self):
    keyword = self.search_input.text().strip() or None
    platform = self.platform_combo.currentText()
    if platform == "全部平台":
      platform = None
    return self.script_manager.list_scripts(keyword=keyword, platform=platform)

  def _populate_tree_node(
    self, parent_item: QTreeWidgetItem | None, node: _FolderNode, path_prefix: str
  ):
    for name in sorted(node.children.keys(), key=str.casefold):
      child_node = node.children[name]
      folder_path = f"{path_prefix}/{name}" if path_prefix else name
      folder_item = ScriptFolderItem(name, folder_path)
      if parent_item is None:
        self.script_tree.addTopLevelItem(folder_item)
      else:
        parent_item.addChild(folder_item)
      for script in sorted(child_node.scripts, key=lambda s: s.title.casefold()):
        folder_item.addChild(ScriptTreeItem(script))
      self._populate_tree_node(folder_item, child_node, folder_path)

  def _rebuild_script_tree(self, scripts: List):
    expanded_paths = self._collect_expanded_folder_paths()
    self.script_tree.clear()
    root, uncategorized = _build_folder_tree(scripts)
    self._populate_tree_node(None, root, "")

    if uncategorized:
      unc_item = ScriptFolderItem(UNCATEGORIZED_LABEL, "__uncategorized__")
      self.script_tree.addTopLevelItem(unc_item)
      for script in sorted(uncategorized, key=lambda s: s.title.casefold()):
        unc_item.addChild(ScriptTreeItem(script))

    self._restore_expanded_folder_paths(expanded_paths)
    self.script_tree.expandAll()
    self._restore_script_selection()

  def _collect_expanded_folder_paths(self) -> set[str]:
    paths: set[str] = set()

    def walk(item: QTreeWidgetItem):
      if isinstance(item, ScriptFolderItem) and item.isExpanded():
        paths.add(item.folder_path)
      for i in range(item.childCount()):
        walk(item.child(i))

    for i in range(self.script_tree.topLevelItemCount()):
      walk(self.script_tree.topLevelItem(i))
    return paths

  def _restore_expanded_folder_paths(self, paths: set[str]):
    def walk(item: QTreeWidgetItem):
      if isinstance(item, ScriptFolderItem) and item.folder_path in paths:
        item.setExpanded(True)
      for i in range(item.childCount()):
        walk(item.child(i))

    for i in range(self.script_tree.topLevelItemCount()):
      walk(self.script_tree.topLevelItem(i))

  def _restore_script_selection(self):
    if self._selected_script_id is None:
      return

    def walk(item: QTreeWidgetItem) -> bool:
      if isinstance(item, ScriptTreeItem) and item.script.id == self._selected_script_id:
        self.script_tree.setCurrentItem(item)
        return True
      for i in range(item.childCount()):
        if walk(item.child(i)):
          return True
      return False

    for i in range(self.script_tree.topLevelItemCount()):
      if walk(self.script_tree.topLevelItem(i)):
        break

  def load_scripts(self):
    if not self.script_manager:
      return
    scripts = self._filtered_scripts()
    self._rebuild_script_tree(scripts)

    platform = self.platform_combo.currentText()
    self.platform_combo.blockSignals(True)
    self.platform_combo.clear()
    self.platform_combo.addItem("全部平台")
    self.platform_combo.addItems(self.script_manager.get_platforms())
    if platform in [
      self.platform_combo.itemText(i) for i in range(self.platform_combo.count())
    ]:
      self.platform_combo.setCurrentText(platform)
    self.platform_combo.blockSignals(False)

  def on_search(self):
    if not self.script_manager:
      return
    self._rebuild_script_tree(self._filtered_scripts())

  def on_tree_item_clicked(self, item: QTreeWidgetItem, _column: int):
    if isinstance(item, ScriptTreeItem):
      self._select_script(item.script)
    elif isinstance(item, ScriptFolderItem):
      item.setExpanded(not item.isExpanded())

  def _select_script(self, script):
    self.current_script = script
    self._selected_script_id = script.id
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
    self._selected_script_id = None
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
    category = _normalize_category(meta.get("category", "").strip()) or None
    payload = {
      "title": title,
      "content": content,
      "script_type": meta.get("script_type", "batch").strip(),
      "platform": meta.get("platform", "windows").strip(),
      "category": category,
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
        self._selected_script_id = self.current_script.id
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
        self._selected_script_id = self.current_script.id
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
        self._selected_script_id = None
        self.code_editor.new_snippet()
      self.load_scripts()
    except Exception as e:
      QMessageBox.critical(self, "错误", f"删除失败：{e}")

  def _script_item_at(self, pos) -> Optional[ScriptTreeItem]:
    item = self.script_tree.itemAt(pos)
    if isinstance(item, ScriptTreeItem):
      return item
    return None

  def show_context_menu(self, pos):
    item = self._script_item_at(pos)
    if not item:
      return
    menu = QMenu(self)
    run_action = menu.addAction("执行")
    delete_action = menu.addAction("删除")
    action = menu.exec_(self.script_tree.mapToGlobal(pos))
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

  def sync_from_directory(self, root_path: str) -> dict[str, int]:
    """从磁盘目录同步脚本到数据库，子目录映射为分类路径。"""
    from pathlib import Path

    from app.database import sync_scripts_from_filesystem

    if not self.script_manager:
      return {"inserted": 0, "updated": 0, "unchanged": 0}
    stats = sync_scripts_from_filesystem(
      self.script_manager.session, Path(root_path)
    )
    self.load_scripts()
    return stats
