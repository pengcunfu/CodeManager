from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QVBoxLayout
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QTextFormat, QFont, QPalette, QSyntaxHighlighter, QTextCharFormat
from app.utils.config_manager import config_manager
import re

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return self.code_editor.line_number_area_width()

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class EnhancedCodeEditor(QPlainTextEdit):
    """增强的代码编辑器，基于QPlainTextEdit但具有更好的功能"""
    
    code_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.current_language = "python"
        self.metadata = {}
        
        # 设置字体
        font = QFont("Consolas", 12)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # 设置制表符宽度
        self.setTabStopDistance(40)  # 4个字符的宽度
        
        # 连接信号
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.on_text_changed)
        
        # 初始化
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # 语法高亮器
        self.highlighter = SyntaxHighlighter(self.document())
        self.highlighter.set_language(self.current_language)
        
        # 加载保存的配置
        self.load_saved_config()
        
        # 自动缩进
        self.auto_indent_enabled = True
        
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
            
    def set_metadata(self, metadata):
        """设置元数据"""
        self.metadata = metadata.copy() if metadata else {}
        
    def get_metadata(self):
        """获取元数据（仅内存字段，不从注释解析）。"""
        return self.metadata.copy()

    def new_snippet(self):
        """创建新代码片段（纯代码，元数据由表单/SQLite 管理）。"""
        self.setPlainText('# 在这里编写代码\nprint("Hello, World!")')
    
    def apply_config(self, config):
        """应用编辑器配置"""
        try:
            # 应用字体配置
            if 'font' in config:
                font_config = config['font']
                font = QFont()
                font.setFamily(font_config.get('family', 'Consolas'))
                font.setPointSize(font_config.get('size', 12))
                font.setBold(font_config.get('bold', False))
                font.setItalic(font_config.get('italic', False))
                self.setFont(font)
            
            # 应用颜色配置
            if 'colors' in config:
                colors = config['colors']
                palette = self.palette()
                
                # 设置背景色和文本色
                bg_color = QColor(colors.get('background', '#282A36'))
                text_color = QColor(colors.get('text', '#F8F8F2'))
                
                palette.setColor(QPalette.Base, bg_color)
                palette.setColor(QPalette.Text, text_color)
                self.setPalette(palette)
                
                # 更新语法高亮器颜色
                if self.highlighter:
                    self.highlighter.update_colors(colors)
            
            # 应用行为配置
            if 'behavior' in config:
                behavior = config['behavior']
                
                # Tab大小
                tab_size = behavior.get('tab_size', 4)
                self.setTabStopDistance(tab_size * self.fontMetrics().horizontalAdvance(' '))
                
                # 自动换行
                if behavior.get('word_wrap', False):
                    self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
                else:
                    self.setLineWrapMode(QPlainTextEdit.NoWrap)
                
                # 行号显示
                self.line_number_area.setVisible(behavior.get('show_line_numbers', True))
                
                # 当前行高亮
                if behavior.get('highlight_current_line', True):
                    self.highlight_current_line()
            
            # 应用语言配置
            if 'languages' in config:
                default_lang = config['languages'].get('default', 'python')
                self.set_language(default_lang)
            
            # 更新显示
            self.update()
            self.update_line_number_area_width(0)
            
        except Exception as e:
            print(f"应用编辑器配置时出错: {e}")
    
    def load_saved_config(self):
        """加载保存的配置"""
        try:
            # 从配置管理器加载编辑器配置
            config = config_manager.get_editor_config()
            if config:
                self.apply_config(config)
        except Exception as e:
            print(f"加载编辑器配置时出错: {e}")
        
    def insert_text(self, text):
        """在当前位置插入文本"""
        cursor = self.textCursor()
        cursor.insertText(text)
        
    def focus(self):
        """聚焦到编辑器"""
        self.setFocus()
        
    def line_number_area_width(self):
        """计算行号区域宽度"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """更新行号区域宽度"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """更新行号区域"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        """绘制行号区域"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(60, 60, 60))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(block_number + 1)
                painter.setPen(QColor(150, 150, 150))
                painter.drawText(0, int(top), self.line_number_area.width(), height,
                               Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        """高亮当前行"""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(68, 71, 90).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)
        
    def keyPressEvent(self, event):
        """按键事件处理"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.auto_indent_enabled:
                self.handle_return()
                return
        elif event.key() == Qt.Key_Tab:
            self.handle_tab()
            return
        elif event.text() in '({[':
            self.handle_bracket(event.text())
            return
        elif event.text() in ')}]':
            self.handle_closing_bracket(event.text())
            return
            
        super().keyPressEvent(event)
        
    def handle_return(self):
        """处理回车键"""
        cursor = self.textCursor()
        cursor.insertText('\n')
        
        # 获取上一行的缩进
        block = cursor.block().previous()
        if block.isValid():
            text = block.text()
            indent = ''
            for char in text:
                if char in ' \t':
                    indent += char
                else:
                    break
            
            # 如果上一行以冒号结尾，增加缩进
            if text.rstrip().endswith(':'):
                indent += '    '
                
            cursor.insertText(indent)
            
    def handle_tab(self):
        """处理Tab键"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # 如果有选择，缩进选中的行
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(cursor.StartOfBlock)
            
            while cursor.position() < end:
                cursor.insertText('    ')
                cursor.movePosition(cursor.NextBlock)
                if cursor.atEnd():
                    break
        else:
            # 插入4个空格
            cursor.insertText('    ')
            
    def handle_bracket(self, bracket):
        """处理左括号"""
        cursor = self.textCursor()
        cursor.insertText(bracket)
        
        # 自动插入对应的右括号
        bracket_map = {'(': ')', '{': '}', '[': ']'}
        if bracket in bracket_map:
            cursor.insertText(bracket_map[bracket])
            cursor.movePosition(cursor.Left)
            self.setTextCursor(cursor)
            
    def handle_closing_bracket(self, bracket):
        """处理右括号"""
        cursor = self.textCursor()
        
        # 检查光标后面是否已经有对应的括号
        next_char = ''
        if not cursor.atEnd():
            cursor.movePosition(cursor.Right, cursor.KeepAnchor)
            next_char = cursor.selectedText()
            cursor.clearSelection()
            
        if next_char == bracket:
            # 如果后面已经有对应的括号，只移动光标
            cursor.movePosition(cursor.Right)
            self.setTextCursor(cursor)
        else:
            # 否则插入括号
            cursor.insertText(bracket)

class SyntaxHighlighter(QSyntaxHighlighter):
    """简化的语法高亮器"""
    def __init__(self, document):
        super().__init__(document)
        self.language = "python"
        self.setup_highlighting_rules()
        
    def setup_highlighting_rules(self):
        """设置高亮规则"""
        self.highlighting_rules = []
        
        # Python关键字高亮
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF79C6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'import', 'from', 'return', 'yield', 'lambda', 'with', 'as', 'pass', 'break', 'continue']
        for word in keywords:
            pattern = re.compile(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, keyword_format))
        
        # 字符串高亮
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#F1FA8C"))
        self.highlighting_rules.append((re.compile('"[^"\\\\n]*(?:\\\\.[^"\\\\n]*)*"'), string_format))
        self.highlighting_rules.append((re.compile("'[^'\\\\n]*(?:\\\\.[^'\\\\n]*)*'"), string_format))
        
        # 注释高亮
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272A4"))
        self.highlighting_rules.append((re.compile('#[^\\n]*'), comment_format))
        
    def highlightBlock(self, text):
        """高亮文本块"""
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)
        
    def set_language(self, language):
        self.language = language.lower()
        # 重新设置高亮规则（可以根据语言调整）
        self.setup_highlighting_rules()
        self.rehighlight()
    
    def update_colors(self, colors):
        """更新语法高亮颜色"""
        try:
            # 重新设置高亮规则，使用新的颜色
            self.highlighting_rules = []
            
            # Python关键字高亮
            keyword_format = QTextCharFormat()
            keyword_format.setForeground(QColor(colors.get('keyword', '#FF79C6')))
            keyword_format.setFontWeight(QFont.Weight.Bold)
            keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'import', 'from', 'return', 'yield', 'lambda', 'with', 'as', 'pass', 'break', 'continue']
            for word in keywords:
                pattern = re.compile(f"\\b{word}\\b")
                self.highlighting_rules.append((pattern, keyword_format))
            
            # 字符串高亮
            string_format = QTextCharFormat()
            string_format.setForeground(QColor(colors.get('string', '#F1FA8C')))
            self.highlighting_rules.append((re.compile('"[^"\\\\n]*(?:\\\\.[^"\\\\n]*)*"'), string_format))
            self.highlighting_rules.append((re.compile("'[^'\\\\n]*(?:\\\\.[^'\\\\n]*)*'"), string_format))
            
            # 注释高亮
            comment_format = QTextCharFormat()
            comment_format.setForeground(QColor(colors.get('comment', '#6272A4')))
            self.highlighting_rules.append((re.compile('#[^\\n]*'), comment_format))
            
            # 数字高亮
            number_format = QTextCharFormat()
            number_format.setForeground(QColor(colors.get('number', '#BD93F9')))
            self.highlighting_rules.append((re.compile('\\b\\d+(\\.\\d+)?\\b'), number_format))
            
            # 重新高亮
            self.rehighlight()
        except Exception as e:
            print(f"更新语法高亮颜色时出错: {e}")