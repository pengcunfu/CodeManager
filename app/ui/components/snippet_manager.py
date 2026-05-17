from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QTextEdit,
                             QListWidget, QListWidgetItem, QSplitter, QFrame,
                             QMessageBox, QFileDialog, QMenu, QScrollArea,
                             QDialog, QPlainTextEdit, QAbstractItemView)
from PySide6.QtCore import Qt, Signal, QProcess
from PySide6.QtGui import QAction, QCursor, QIcon, QFont, QShortcut, QKeySequence
import re
from .tabbed_code_editor import TabbedCodeEditor
from .code_snippet import CodeSnippetManager
from .filter_dialog import FilterDialog
from ...utils.config_manager import config_manager
import tempfile
import os
import subprocess

class SnippetListItem(QListWidgetItem):
    def __init__(self, snippet):
        super().__init__()
        self.snippet = snippet
        self.setText(snippet.title)
        self.setToolTip(f"语言：{snippet.language}\n描述：{snippet.description or '无'}\n标签：{snippet.tags or '无'}")
        # 设置样式
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
        # 设置图标或其他视觉标识
        self.setIcon(self._get_language_icon(snippet.language))
        
    def _get_language_icon(self, language):
        """获取语言对应的图标"""
        language = language.lower().strip()
        icon_map = {
            'python': 'python.svg',
            'py': 'python.svg',
            'javascript': 'javascript.svg',
            'js': 'javascript.svg',
            'html': 'html.svg',
            'htm': 'html.svg',
            'css': 'css.svg',
            'java': 'java.svg',
            'c++': 'cpp.svg',
            'cpp': 'cpp.svg',
            'cxx': 'cpp.svg',
            'c#': 'csharp.svg',
            'csharp': 'csharp.svg',
            'cs': 'csharp.svg',
            'typescript': 'typescript.svg',
            'ts': 'typescript.svg',
            # 其他语言的专用图标
             'php': 'php.svg',
             'ruby': 'ruby.svg',
             'rb': 'ruby.svg',
             'go': 'go.svg',
             'golang': 'go.svg',
             'rust': 'rust.svg',
             'rs': 'rust.svg',
            'sql': 'code.svg',
            'json': 'code.svg',
            'xml': 'code.svg',
            'yaml': 'code.svg',
            'yml': 'code.svg',
            'bash': 'code.svg',
            'sh': 'code.svg',
            'powershell': 'code.svg',
            'ps1': 'code.svg',
        }
        icon_path = f"resources/icons/languages/{icon_map.get(language, 'code.svg')}"
        return QIcon(icon_path)

class SnippetManagerWidget(QWidget):
    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.snippet_manager = CodeSnippetManager(session) if session else None
        self.current_snippet = None
        self.init_ui()
        if self.snippet_manager:
            self.load_snippets()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)  # 减少间距
        layout.setContentsMargins(3, 3, 3, 3)  # 减少边距

        # 顶部工具栏
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(6, 3, 6, 3)  # 减少边距
        toolbar_layout.setSpacing(6)  # 减少间距
        
        # 搜索框
        search_container = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索代码片段...")
        self.search_input.textChanged.connect(self.on_search)
        self.search_input.setMinimumWidth(200)
        search_container.addWidget(self.search_input)
        toolbar_layout.addLayout(search_container)

        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItem("全部语言")
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        self.language_combo.setMinimumWidth(120)
        toolbar_layout.addWidget(self.language_combo)

        # 标签选择
        self.tag_combo = QComboBox()
        self.tag_combo.addItem("全部标签")
        self.tag_combo.currentTextChanged.connect(self.on_tag_changed)
        self.tag_combo.setMinimumWidth(120)
        toolbar_layout.addWidget(self.tag_combo)

        toolbar_layout.addStretch()

        # 筛选按钮
        filter_btn = QPushButton("筛选")
        filter_btn.clicked.connect(self.show_filter_dialog)
        toolbar_layout.addWidget(filter_btn)
        
        # 新建按钮
        new_btn = QPushButton("新建")
        new_btn.clicked.connect(self.new_snippet)
        toolbar_layout.addWidget(new_btn)

        self.export_btn = QPushButton("导出")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_selected_snippets)
        toolbar_layout.addWidget(self.export_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected_snippets)
        toolbar_layout.addWidget(self.delete_btn)

        layout.addWidget(toolbar)

        # 主界面分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)  # 设置分割器手柄宽度为1像素

        # 左侧列表
        list_container = QFrame()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(2, 2, 2, 2)  # 减少边距
        list_layout.setSpacing(2)  # 减少间距
        
        self.snippet_list = QListWidget()
        self.snippet_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.snippet_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.snippet_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.snippet_list.customContextMenuRequested.connect(self.show_context_menu)
        self.snippet_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.snippet_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        list_layout.addWidget(self.snippet_list)
        
        splitter.addWidget(list_container)

        # 右侧编辑区
        edit_container = QFrame()
        edit_layout = QVBoxLayout(edit_container)
        edit_layout.setContentsMargins(6, 6, 6, 6)  # 适当的边距
        edit_layout.setSpacing(4)  # 适当的间距

        # 代码编辑器
        self.code_editor = TabbedCodeEditor()
        edit_layout.addWidget(self.code_editor)

        # 连接代码编辑器的文本变化信号到自动保存
        self.code_editor.code_changed.connect(self.auto_save)
        self.code_editor.metadata_changed.connect(self.auto_save)
        
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_snippet)
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.snippet_list)
        delete_shortcut.activated.connect(self.delete_selected_snippets)
        splitter.addWidget(edit_container)

        # 设置分割器比例，左侧20%，右侧80%
        splitter.setSizes([200, 800])
        # 确保比例设置生效
        splitter.setStretchFactor(0, 2)  # 左侧面板
        splitter.setStretchFactor(1, 8)  # 右侧面板

        layout.addWidget(splitter, 1)  # 设置拉伸因子为1，让分割器占据剩余空间


    def load_snippets(self):
        """加载所有代码片段"""
        if not self.snippet_manager:
            return
            
        self.snippet_list.clear()
        snippets = self.snippet_manager.search_snippets()
        for snippet in snippets:
            self.snippet_list.addItem(SnippetListItem(snippet))

        # 更新语言列表
        current_text = self.language_combo.currentText()
        self.language_combo.clear()
        self.language_combo.addItem("全部语言")
        languages = self.snippet_manager.get_all_languages()
        self.language_combo.addItems(languages)
        if current_text in languages:
            self.language_combo.setCurrentText(current_text)

        # 更新标签列表
        current_tag = self.tag_combo.currentText()
        self.tag_combo.clear()
        self.tag_combo.addItem("全部标签")
        tags = self.snippet_manager.get_all_tags()
        self.tag_combo.addItems(tags)
        if current_tag in tags:
            self.tag_combo.setCurrentText(current_tag)

        self._update_batch_action_state()

    def on_search(self):
        """搜索代码片段"""
        if not self.snippet_manager:
            return
            
        keyword = self.search_input.text()
        language = self.language_combo.currentText()
        tag = self.tag_combo.currentText()

        if language == "全部语言":
            language = None
        if tag == "全部标签":
            tag = None

        self.snippet_list.clear()
        snippets = self.snippet_manager.search_snippets(keyword, language, tag)
        for snippet in snippets:
            self.snippet_list.addItem(SnippetListItem(snippet))
        self._update_batch_action_state()

    def on_language_changed(self, language):
        """语言选择改变时更新列表"""
        self.on_search()
        if self.code_editor and language != "全部语言":
            self.code_editor.set_language(language)

    def on_tag_changed(self, _):
        """标签选择改变时更新列表"""
        self.on_search()
        
    def show_filter_dialog(self):
        """显示筛选对话框"""
        dialog = FilterDialog(self.snippet_manager, self)
        dialog.filter_applied.connect(self.apply_advanced_filter)
        dialog.exec_()
         
    def apply_advanced_filter(self, filter_conditions):
        """应用高级筛选条件"""
        if not self.snippet_manager:
            return
            
        # 保存筛选条件到配置
        config_manager.save_last_filter(filter_conditions)
            
        self.snippet_list.clear()
        
        # 获取所有代码片段
        all_snippets = self.snippet_manager.search_snippets()
        
        # 应用筛选条件
        filtered_snippets = self._filter_snippets(all_snippets, filter_conditions)
        
        # 应用排序
        sorted_snippets = self._sort_snippets(filtered_snippets, filter_conditions)
        
        # 更新列表显示
        for snippet in sorted_snippets:
            self.snippet_list.addItem(SnippetListItem(snippet))
            
    def _filter_snippets(self, snippets, conditions):
        """根据条件筛选代码片段"""
        filtered = []
        
        for snippet in snippets:
            # 关键词筛选
            if conditions.get('keyword'):
                keyword = conditions['keyword'].lower()
                if not any(keyword in str(getattr(snippet, field, '')).lower() 
                          for field in ['title', 'description', 'code', 'tags']):
                    continue
                    
            # 语言筛选
            if conditions.get('language'):
                if snippet.language != conditions['language']:
                    continue
                    
            # 标签筛选
            if conditions.get('tag'):
                snippet_tags = snippet.tags or ''
                if conditions['tag'] not in snippet_tags:
                    continue
                    
            # 分类筛选（基于标签或描述中的关键词）
            if conditions.get('category'):
                category = conditions['category'].lower()
                snippet_text = f"{snippet.tags or ''} {snippet.description or ''}".lower()
                if category not in snippet_text:
                    continue
                    
            # 时间筛选
            if conditions.get('enable_time_filter') and conditions.get('start_date') and conditions.get('end_date'):
                if hasattr(snippet, 'created_at') and snippet.created_at:
                    snippet_date = snippet.created_at.date()
                    if not (conditions['start_date'] <= snippet_date <= conditions['end_date']):
                        continue
                        
            # 代码长度筛选
            if conditions.get('enable_length_filter'):
                code_length = len(snippet.code or '')
                min_length = conditions.get('min_length', 0)
                max_length = conditions.get('max_length', float('inf'))
                if not (min_length <= code_length <= max_length):
                    continue
                    
            filtered.append(snippet)
            
        return filtered
        
    def _sort_snippets(self, snippets, conditions):
        """对代码片段进行排序"""
        sort_field = conditions.get('sort_field', '创建时间')
        sort_order = conditions.get('sort_order', 'desc')
        reverse = sort_order == 'desc'
        
        def get_sort_key(snippet):
            if sort_field == '创建时间':
                return getattr(snippet, 'created_at', None) or snippet.id
            elif sort_field == '修改时间':
                return getattr(snippet, 'updated_at', None) or getattr(snippet, 'created_at', None) or snippet.id
            elif sort_field == '标题':
                return snippet.title.lower()
            elif sort_field == '语言':
                return snippet.language.lower()
            elif sort_field == '代码长度':
                return len(snippet.code or '')
            elif sort_field == '使用频率':
                return getattr(snippet, 'usage_count', 0)
            else:
                return snippet.id
                
        try:
            return sorted(snippets, key=get_sort_key, reverse=reverse)
        except Exception:
            # 如果排序失败，返回原列表
            return snippets

    def get_selected_snippets(self):
        """返回当前选中的代码片段（支持 Shift/Ctrl 多选）。"""
        snippets = []
        for item in self.snippet_list.selectedItems():
            if isinstance(item, SnippetListItem):
                snippets.append(item.snippet)
        return snippets

    def _update_batch_action_state(self):
        count = len(self.snippet_list.selectedItems())
        enabled = count > 0
        self.export_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)

    def _load_snippet_into_editor(self, snippet):
        self.current_snippet = snippet
        self.code_editor.set_code(snippet.code or "")
        self.code_editor.set_language(snippet.language)
        self.code_editor.set_metadata({
            'title': snippet.title,
            'language': snippet.language,
            'description': snippet.description or '',
            'tags': snippet.tags or '',
        })

    def on_selection_changed(self):
        """选择变化时更新编辑区与批量操作按钮。"""
        self._update_batch_action_state()
        selected = self.get_selected_snippets()
        if len(selected) == 1:
            self._load_snippet_into_editor(selected[0])
            return
        if len(selected) > 1:
            current = self.snippet_list.currentItem()
            if isinstance(current, SnippetListItem) and current.isSelected():
                self._load_snippet_into_editor(current.snippet)
            return
        self.current_snippet = None

    def new_snippet(self):
        """新建代码片段"""
        self.current_snippet = None
        self.code_editor.new_snippet()
        language = self.language_combo.currentText()
        if language != "全部语言":
            metadata = self.code_editor.get_metadata()
            metadata['language'] = language
            self.code_editor.set_metadata(metadata)

    def save_snippet(self):
        """保存代码片段"""
        if not self.snippet_manager:
            QMessageBox.warning(self, "错误", "数据库连接未初始化")
            return
            
        code = self.code_editor.get_code().strip()
        if not code:
            QMessageBox.warning(self, "错误", "请输入代码")
            return

        metadata = self.code_editor.get_metadata()
        title = metadata.get('title', '').strip()
        if not title:
            QMessageBox.warning(self, "错误", "请在元信息中填写标题")
            return

        language = metadata.get('language', 'text').strip()
        description = metadata.get('description', '').strip()
        tags = [tag.strip() for tag in metadata.get('tags', '').split(',') if tag.strip()]

        try:
            if self.current_snippet:
                # 更新现有代码片段
                self.snippet_manager.update_snippet(
                    self.current_snippet.id,
                    title=title,
                    description=description,
                    code=code,
                    language=language,
                    tags=tags
                )
            else:
                # 创建新代码片段
                new_snippet = self.snippet_manager.create_snippet(
                    title=title,
                    description=description,
                    code=code,
                    language=language,
                    tags=tags
                )
                # 设置当前代码片段为新创建的代码片段
                self.current_snippet = new_snippet
            self.load_snippets()
            QMessageBox.information(self, "成功", "保存成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")

    def auto_save(self):
        """自动保存功能"""
        if not self.snippet_manager:
            return
            
        # 获取当前代码和元数据
        code = self.code_editor.get_code().strip()
        if not code:
            return
            
        metadata = self.code_editor.get_metadata()
        title = metadata.get('title', '').strip()
        if not title:
            return
            
        language = metadata.get('language', 'text').strip()
        description = metadata.get('description', '').strip()
        tags = [tag.strip() for tag in metadata.get('tags', '').split(',') if tag.strip()]
        
        try:
            if self.current_snippet:
                # 更新现有代码片段
                self.snippet_manager.update_snippet(
                    self.current_snippet.id,
                    title=title,
                    description=description,
                    code=code,
                    language=language,
                    tags=tags
                )
            else:
                # 创建新代码片段
                new_snippet = self.snippet_manager.create_snippet(
                    title=title,
                    description=description,
                    code=code,
                    language=language,
                    tags=tags
                )
                # 设置当前代码片段为新创建的代码片段
                self.current_snippet = new_snippet
        except Exception:
            # 自动保存失败时不显示错误消息
            pass

    def delete_selected_snippets(self):
        """删除选中的一个或多个代码片段。"""
        snippets = self.get_selected_snippets()
        if not snippets or not self.snippet_manager:
            return

        if len(snippets) == 1:
            message = f"确定要删除代码片段「{snippets[0].title}」吗？"
        else:
            message = f"确定要删除选中的 {len(snippets)} 个代码片段吗？"

        reply = QMessageBox.question(
            self,
            "确认删除",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        deleted_ids = {s.id for s in snippets}
        try:
            for snippet in snippets:
                self.snippet_manager.delete_snippet(snippet.id)
            self.load_snippets()
            if self.current_snippet and self.current_snippet.id in deleted_ids:
                self.current_snippet = None
                self.code_editor.new_snippet()
            QMessageBox.information(self, "成功", f"已删除 {len(snippets)} 个代码片段")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{str(e)}")

    def delete_snippet(self, snippet):
        """删除单个代码片段（右键菜单等）。"""
        if not snippet:
            return
        for i in range(self.snippet_list.count()):
            item = self.snippet_list.item(i)
            if isinstance(item, SnippetListItem) and item.snippet.id == snippet.id:
                item.setSelected(True)
                break
        self.delete_selected_snippets()

    def _safe_export_basename(self, title: str, snippet_id: int) -> str:
        name = re.sub(r'[<>:"/\\|?*]', "_", title.strip()) or "snippet"
        return f"{name}_{snippet_id}"

    def export_selected_snippets(self):
        """导出选中的一个或多个代码片段。"""
        snippets = self.get_selected_snippets()
        if not snippets:
            QMessageBox.warning(self, "提示", "请先选择要导出的代码片段")
            return

        format_menu = QMenu(self)
        source_action = format_menu.addAction("源码格式")
        json_action = format_menu.addAction("JSON 格式")
        markdown_action = format_menu.addAction("Markdown 格式")

        action = format_menu.exec_(QCursor.pos())
        if not action:
            return

        try:
            if action == source_action:
                self._export_snippets_as_source(snippets)
            elif action == json_action:
                self._export_snippets_as_bundle(snippets, "json")
            elif action == markdown_action:
                self._export_snippets_as_bundle(snippets, "markdown")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")

    def export_snippet(self):
        """导出当前片段（兼容旧入口）。"""
        if self.current_snippet:
            for i in range(self.snippet_list.count()):
                item = self.snippet_list.item(i)
                if isinstance(item, SnippetListItem) and item.snippet.id == self.current_snippet.id:
                    self.snippet_list.clearSelection()
                    item.setSelected(True)
                    break
        self.export_selected_snippets()

    def _export_snippets_as_source(self, snippets):
        if len(snippets) == 1:
            snippet = snippets[0]
            extension = self._get_file_extension(snippet.language)
            file_filter = f"{snippet.language.upper()} 文件 (*{extension})"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出源码",
                f"{snippet.title}{extension}",
                file_filter,
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(snippet.code or "")
                QMessageBox.information(self, "成功", "源码导出成功")
            return

        dir_path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not dir_path:
            return
        for snippet in snippets:
            ext = self._get_file_extension(snippet.language)
            filename = f"{self._safe_export_basename(snippet.title, snippet.id)}{ext}"
            path = os.path.join(dir_path, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(snippet.code or "")
        QMessageBox.information(self, "成功", f"已导出 {len(snippets)} 个源码文件")

    def _export_snippets_as_bundle(self, snippets, fmt: str):
        extension = ".json" if fmt == "json" else ".md"
        default_name = (
            f"{snippets[0].title}{extension}"
            if len(snippets) == 1
            else f"snippets_export{extension}"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出代码片段",
            default_name,
            f"{'JSON' if fmt == 'json' else 'Markdown'} 文件 (*{extension})",
        )
        if not file_path:
            return
        ids = [s.id for s in snippets]
        content = self.snippet_manager.export_snippets(ids, fmt)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        QMessageBox.information(self, "成功", f"已导出 {len(snippets)} 个代码片段")
    
    def _get_file_extension(self, language):
        """根据编程语言获取文件扩展名"""
        extension_map = {
            'python': '.py',
            'javascript': '.js',
            'js': '.js',
            'typescript': '.ts',
            'ts': '.ts',
            'java': '.java',
            'c': '.c',
            'cpp': '.cpp',
            'c++': '.cpp',
            'csharp': '.cs',
            'c#': '.cs',
            'php': '.php',
            'ruby': '.rb',
            'go': '.go',
            'rust': '.rs',
            'swift': '.swift',
            'kotlin': '.kt',
            'scala': '.scala',
            'r': '.r',
            'matlab': '.m',
            'perl': '.pl',
            'lua': '.lua',
            'shell': '.sh',
            'bash': '.sh',
            'sh': '.sh',
            'powershell': '.ps1',
            'ps1': '.ps1',
            'batch': '.bat',
            'bat': '.bat',
            'cmd': '.cmd',
            'html': '.html',
            'css': '.css',
            'scss': '.scss',
            'sass': '.sass',
            'less': '.less',
            'xml': '.xml',
            'json': '.json',
            'yaml': '.yaml',
            'yml': '.yml',
            'toml': '.toml',
            'ini': '.ini',
            'cfg': '.cfg',
            'conf': '.conf',
            'sql': '.sql',
            'dockerfile': '.dockerfile',
            'makefile': '.makefile',
            'cmake': '.cmake',
            'gradle': '.gradle',
            'maven': '.xml',
            'vue': '.vue',
            'react': '.jsx',
            'jsx': '.jsx',
            'tsx': '.tsx',
            'svelte': '.svelte',
            'dart': '.dart',
            'flutter': '.dart',
            'vb': '.vb',
            'vbnet': '.vb',
            'fsharp': '.fs',
            'f#': '.fs',
            'haskell': '.hs',
            'erlang': '.erl',
            'elixir': '.ex',
            'clojure': '.clj',
            'lisp': '.lisp',
            'scheme': '.scm',
            'prolog': '.pl',
            'fortran': '.f90',
            'cobol': '.cob',
            'pascal': '.pas',
            'delphi': '.pas',
            'assembly': '.asm',
            'asm': '.asm',
            'verilog': '.v',
            'vhdl': '.vhd',
            'latex': '.tex',
            'tex': '.tex',
            'markdown': '.md',
            'md': '.md',
            'text': '.txt',
            'txt': '.txt',
            'plain': '.txt'
        }
        
        return extension_map.get(language.lower(), '.txt')

    def show_context_menu(self, pos):
        """显示右键菜单"""
        clicked = self.snippet_list.itemAt(pos)
        if clicked and not clicked.isSelected():
            self.snippet_list.clearSelection()
            clicked.setSelected(True)

        selected = self.get_selected_snippets()
        if not selected:
            return

        count = len(selected)
        menu = QMenu(self)
        if count == 1:
            execute_action = menu.addAction("执行")
            menu.addSeparator()
            open_vscode_action = menu.addAction("在 VSCode 中打开")
            open_notepad_action = menu.addAction("在记事本中打开")
            menu.addSeparator()
        else:
            execute_action = open_vscode_action = open_notepad_action = None

        export_label = f"导出 ({count} 项)" if count > 1 else "导出"
        delete_label = f"删除 ({count} 项)" if count > 1 else "删除"
        export_action = menu.addAction(export_label)
        delete_action = menu.addAction(delete_label)

        action = menu.exec_(self.snippet_list.mapToGlobal(pos))
        if count == 1:
            snippet = selected[0]
            if action == execute_action:
                self.execute_snippet(snippet)
            elif action == open_vscode_action:
                self.open_in_vscode(snippet)
            elif action == open_notepad_action:
                self.open_in_notepad(snippet)
        if action == export_action:
            self.export_selected_snippets()
        elif action == delete_action:
            self.delete_selected_snippets()

    def open_in_vscode(self, snippet):
        """在VSCode中打开代码片段"""
        if not snippet:
            return
            
        try:
            # 创建临时文件
            extension = self._get_file_extension(snippet.language)
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False, encoding='utf-8') as f:
                f.write(snippet.code)
                temp_file = f.name
            
            # 使用VSCode打开文件
            subprocess.run(['code', temp_file], check=False)
            QMessageBox.information(self, "成功", f"已在VSCode中打开代码片段 '{snippet.title}'")
            
        except FileNotFoundError:
            QMessageBox.warning(self, "警告", "未找到VSCode，请确保VSCode已安装并添加到系统PATH中")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开VSCode失败：{str(e)}")
    
    def open_in_notepad(self, snippet):
        """在记事本中打开代码片段"""
        if not snippet:
            return
            
        try:
            # 创建临时文件
            extension = self._get_file_extension(snippet.language)
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False, encoding='utf-8') as f:
                f.write(snippet.code)
                temp_file = f.name
            
            # 使用记事本打开文件
            subprocess.run(['notepad.exe', temp_file], check=False)
            QMessageBox.information(self, "成功", f"已在记事本中打开代码片段 '{snippet.title}'")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开记事本失败：{str(e)}")

    def execute_snippet(self, snippet):
        """执行代码片段"""
        if not snippet:
            return
            
        # 根据语言选择执行方式
        language = snippet.language.lower()
        code = snippet.code
        
        try:
            if language == 'python':
                self._execute_python(code, snippet.title)
            elif language in ['javascript', 'js']:
                self._execute_javascript(code, snippet.title)
            elif language in ['batch', 'bat', 'cmd']:
                self._execute_batch(code, snippet.title)
            elif language in ['powershell', 'ps1']:
                self._execute_powershell(code, snippet.title)
            elif language in ['bash', 'sh']:
                self._execute_bash(code, snippet.title)
            else:
                QMessageBox.information(self, "提示", f"暂不支持执行 {language} 代码")
        except Exception as e:
            QMessageBox.critical(self, "执行错误", f"执行失败：{str(e)}")
    
    def _execute_python(self, code, title):
        """执行Python代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(['python', temp_file], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', timeout=30)
            self._show_execution_result(title, result.stdout, result.stderr, result.returncode)
        finally:
            os.unlink(temp_file)
    
    def _execute_javascript(self, code, title):
        """执行JavaScript代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(['node', temp_file], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', timeout=30)
            self._show_execution_result(title, result.stdout, result.stderr, result.returncode)
        finally:
            os.unlink(temp_file)
    
    def _execute_batch(self, code, title):
        """执行批处理代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run([temp_file], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', timeout=30, shell=True)
            self._show_execution_result(title, result.stdout, result.stderr, result.returncode)
        finally:
            os.unlink(temp_file)
    
    def _execute_powershell(self, code, title):
        """执行PowerShell代码"""
        try:
            result = subprocess.run(['powershell', '-Command', code], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', timeout=30)
            self._show_execution_result(title, result.stdout, result.stderr, result.returncode)
        except Exception as e:
            QMessageBox.critical(self, "执行错误", f"PowerShell执行失败：{str(e)}")
    
    def _execute_bash(self, code, title):
        """执行Bash代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = subprocess.run(['bash', temp_file], 
                                  capture_output=True, text=True, 
                                  encoding='utf-8', timeout=30)
            self._show_execution_result(title, result.stdout, result.stderr, result.returncode)
        finally:
            os.unlink(temp_file)
    
    def _show_execution_result(self, title, stdout, stderr, returncode):
        """显示执行结果"""
        dialog = ExecutionResultDialog(title, stdout, stderr, returncode, self)
        dialog.exec_()


class ExecutionResultDialog(QDialog):
    """执行结果对话框"""
    def __init__(self, title, stdout, stderr, returncode, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"执行结果 - {title}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 状态信息
        status_label = QLabel(f"退出代码: {returncode}")
        layout.addWidget(status_label)
        
        # 输出结果
        if stdout:
            layout.addWidget(QLabel("标准输出:"))
            stdout_text = QPlainTextEdit()
            stdout_text.setPlainText(stdout)
            stdout_text.setReadOnly(True)
            stdout_text.setFont(QFont("Consolas", 10))
            layout.addWidget(stdout_text)
        
        # 错误输出
        if stderr:
            layout.addWidget(QLabel("错误输出:"))
            stderr_text = QPlainTextEdit()
            stderr_text.setPlainText(stderr)
            stderr_text.setReadOnly(True)
            stderr_text.setFont(QFont("Consolas", 10))
            layout.addWidget(stderr_text)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)