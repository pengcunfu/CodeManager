from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QTextEdit,
                             QListWidget, QListWidgetItem, QSplitter, QFrame,
                             QMessageBox, QFileDialog, QMenu, QScrollArea,
                             QDialog, QPlainTextEdit)
from PySide6.QtCore import Qt, Signal, QProcess
from PySide6.QtGui import QAction, QCursor, QIcon, QFont
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
        icon_path = f"resource/icons/languages/{icon_map.get(language, 'code.svg')}"
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
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border: 1px solid #555;
                border-radius: 3px;
                background: #2b2b2b;
                color: #ffffff;
                font-size: 12px;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
                background-color: #404040;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(6, 3, 6, 3)  # 减少边距
        toolbar_layout.setSpacing(6)  # 减少间距
        
        # 搜索框
        search_container = QHBoxLayout()
        # 搜索图标
        search_icon = QLabel("🔍")
        search_container.addWidget(search_icon)
        
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
        filter_btn = QPushButton("🔍 筛选")
        filter_btn.clicked.connect(self.show_filter_dialog)
        toolbar_layout.addWidget(filter_btn)
        
        # 新建按钮
        new_btn = QPushButton("新建片段")
        new_btn.setText("➕ 新建")
        new_btn.clicked.connect(self.new_snippet)
        toolbar_layout.addWidget(new_btn)

        layout.addWidget(toolbar)

        # 主界面分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #0078d4;
            }
        """)
        splitter.setHandleWidth(1)  # 设置分割器手柄宽度为1像素

        # 左侧列表
        list_container = QFrame()
        list_container.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QListWidget {
                border: none;
                background-color: transparent;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-bottom: 1px solid #444;
                color: #ffffff;
                font-size: 12px;
                min-height: 18px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(2, 2, 2, 2)  # 减少边距
        list_layout.setSpacing(2)  # 减少间距
        
        self.snippet_list = QListWidget()
        self.snippet_list.itemClicked.connect(self.on_snippet_selected)
        self.snippet_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.snippet_list.customContextMenuRequested.connect(self.show_context_menu)
        self.snippet_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.snippet_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        list_layout.addWidget(self.snippet_list)
        
        splitter.addWidget(list_container)

        # 右侧编辑区
        edit_container = QFrame()
        edit_container.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton#deleteBtn {
                background-color: #d13438;
            }
            QPushButton#deleteBtn:hover {
                background-color: #b71c1c;
            }
        """)
        edit_layout = QVBoxLayout(edit_container)
        edit_layout.setContentsMargins(6, 6, 6, 6)  # 适当的边距
        edit_layout.setSpacing(4)  # 适当的间距

        # 代码编辑器
        self.code_editor = TabbedCodeEditor()
        edit_layout.addWidget(self.code_editor)

        # 连接代码编辑器的文本变化信号到自动保存
        self.code_editor.code_changed.connect(self.auto_save)
        self.code_editor.metadata_changed.connect(self.auto_save)
        
        # 添加Ctrl+S快捷键
        from PySide6.QtGui import QShortcut, QKeySequence
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_snippet)
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

    def on_snippet_selected(self, item):
        """选中代码片段时更新编辑区"""
        if isinstance(item, SnippetListItem):
            self.current_snippet = item.snippet
            # 设置代码内容
            self.code_editor.set_code(self.current_snippet.code)
            # 设置语言
            self.code_editor.set_language(self.current_snippet.language)
            # 设置元数据
            metadata = {
                'title': self.current_snippet.title,
                'language': self.current_snippet.language,
                'description': self.current_snippet.description or '',
                'tags': self.current_snippet.tags or ''
            }
            self.code_editor.set_metadata(metadata)

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
            QMessageBox.warning(self, "错误", "请在注释中指定标题")
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

    def delete_snippet(self, snippet):
        """删除代码片段"""
        if not snippet or not self.snippet_manager:
            return
            
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除代码片段 '{snippet.title}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.snippet_manager.delete_snippet(snippet.id)
                self.load_snippets()
                # 如果删除的是当前编辑的片段，清空编辑器
                if self.current_snippet and self.current_snippet.id == snippet.id:
                    self.current_snippet = None
                    self.code_editor.new_snippet()
                QMessageBox.information(self, "成功", "删除成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败：{str(e)}")

    def export_snippet(self):
        """导出代码片段"""
        if not self.current_snippet:
            QMessageBox.warning(self, "错误", "请先选择要导出的代码片段")
            return

        # 选择导出格式
        format_menu = QMenu(self)
        source_action = format_menu.addAction("源码格式")
        json_action = format_menu.addAction("JSON格式")
        markdown_action = format_menu.addAction("Markdown格式")

        action = format_menu.exec_(QCursor.pos())
        if not action:
            return

        if action == source_action:
            # 源码导出
            extension = self._get_file_extension(self.current_snippet.language)
            file_filter = f"{self.current_snippet.language.upper()} 文件 (*{extension})"
            default_name = f"{self.current_snippet.title}{extension}"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出源码",
                default_name,
                file_filter
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.current_snippet.code)
                    QMessageBox.information(self, "成功", "源码导出成功")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
        else:
            # JSON或Markdown导出
            format = 'json' if action == json_action else 'markdown'
            extension = '.json' if format == 'json' else '.md'
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出代码片段",
                f"{self.current_snippet.title}{extension}",
                f"{'JSON' if format == 'json' else 'Markdown'} 文件 (*{extension})"
            )
            
            if file_path:
                try:
                    content = self.snippet_manager.export_snippets([self.current_snippet.id], format)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    QMessageBox.information(self, "成功", "导出成功")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
    
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
        item = self.snippet_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        execute_action = menu.addAction("▶️ 执行")
        menu.addSeparator()
        
        # 添加在外部编辑器中打开的选项
        open_vscode_action = menu.addAction("📝 在VSCode中打开")
        open_notepad_action = menu.addAction("📄 在记事本中打开")
        menu.addSeparator()
        
        export_action = menu.addAction("📤 导出")
        delete_action = menu.addAction("🗑️ 删除")

        action = menu.exec_(self.snippet_list.mapToGlobal(pos))
        if action == execute_action:
            self.execute_snippet(item.snippet)
        elif action == open_vscode_action:
            self.open_in_vscode(item.snippet)
        elif action == open_notepad_action:
            self.open_in_notepad(item.snippet)
        elif action == export_action:
            self.current_snippet = item.snippet
            self.export_snippet()
        elif action == delete_action:
            self.delete_snippet(item.snippet)

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

    def delete_snippet(self, snippet):
        """删除代码片段"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除代码片段 '{snippet.title}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.snippet_manager.delete_snippet(snippet.id)
                self.load_snippets()
                QMessageBox.information(self, "成功", "删除成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败：{str(e)}")


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
        status_label.setStyleSheet(f"color: {'green' if returncode == 0 else 'red'}; font-weight: bold;")
        layout.addWidget(status_label)
        
        # 输出结果
        if stdout:
            layout.addWidget(QLabel("标准输出:"))
            stdout_text = QPlainTextEdit()
            stdout_text.setPlainText(stdout)
            stdout_text.setReadOnly(True)
            stdout_text.setFont(QFont("Consolas", 10))
            stdout_text.setStyleSheet("background-color: #2b2b2b; color: #ffffff; border: 1px solid #555;")
            layout.addWidget(stdout_text)
        
        # 错误输出
        if stderr:
            layout.addWidget(QLabel("错误输出:"))
            stderr_text = QPlainTextEdit()
            stderr_text.setPlainText(stderr)
            stderr_text.setReadOnly(True)
            stderr_text.setFont(QFont("Consolas", 10))
            stderr_text.setStyleSheet("background-color: #2b2b2b; color: #ff6b6b; border: 1px solid #555;")
            layout.addWidget(stderr_text)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)