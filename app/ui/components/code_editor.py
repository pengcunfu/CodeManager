from PySide6.QtWidgets import QTextEdit, QCompleter, QWidget, QPlainTextEdit, QFrame
from PySide6.QtCore import Qt, Signal, QStringListModel, QRect, QSize
from PySide6.QtGui import QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QPainter, QTextFormat, \
    QPalette, QFontMetrics
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from jedi import Script
import re


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    code_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.setup_completer()
        self.current_language = "python"
        self.highlighter = SyntaxHighlighter(self.document())
        self.metadata_pattern = re.compile(r'^/\*\s*(?P<key>\w+):\s*(?P<value>.+?)\s*\*/\s*$', re.MULTILINE)
        self.metadata_template = """/* title: 新建代码片段 */
/* language: text */
/* tags: tag1, tag2 */
/* description: 在这里添加描述 */

"""

        # 设置行号区域
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

        # 设置当前行高亮
        self.cursorPositionChanged.connect(self.highlight_current_line)

        # 括号匹配
        self.matching_pairs = {'{': '}', '[': ']', '(': ')'}
        self.matching_pairs.update({v: k for k, v in self.matching_pairs.items()})

    def setup_editor(self):
        """设置编辑器基本属性"""
        # 设置字体
        font = QFont("Consolas", 12)
        font.setFixedPitch(True)
        self.setFont(font)

        # 设置制表符宽度（4个空格）
        self.setTabStopDistance(QFontMetrics(font).horizontalAdvance(' ') * 4)

        # 设置行距
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # 设置自动缩进
        self.setAutoIndentation(True)

        # 连接文本变化信号
        self.textChanged.connect(self.on_text_changed)

    def setup_completer(self):
        """设置代码补全器"""
        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated[str].connect(self.insert_completion)

    def on_text_changed(self):
        """文本变化时更新代码补全和发送信号"""
        self.update_completer()
        self.code_changed.emit(self.toPlainText())

    def update_completer(self):
        """更新代码补全提示"""
        if self.current_language != "python":
            return

        cursor = self.textCursor()
        text = self.toPlainText()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber()

        # 使用jedi获取补全建议
        script = Script(text)
        completions = script.complete(line, column)
        suggestions = [c.name for c in completions]

        # 更新补全模型
        model = QStringListModel(suggestions)
        self.completer.setModel(model)

    def insert_completion(self, completion):
        """插入补全的代码"""
        cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        cursor.movePosition(QTextCursor.Left)
        cursor.movePosition(QTextCursor.EndOfWord)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)

    def set_language(self, language):
        """设置代码语言"""
        self.current_language = language.lower()
        self.highlighter.set_language(self.current_language)

    def get_metadata(self):
        """从代码中提取元数据"""
        text = self.toPlainText()
        metadata = {}
        for match in self.metadata_pattern.finditer(text):
            key = match.group('key')
            value = match.group('value')
            metadata[key] = value
        return metadata

    def set_metadata(self, metadata):
        """设置代码元数据"""
        text = self.toPlainText()
        # 找到第一个非元数据行的位置
        lines = text.split('\n')
        code_start = 0
        for i, line in enumerate(lines):
            if not line.strip().startswith('/*') and line.strip():
                code_start = i
                break
        # 保留代码部分
        code = '\n'.join(lines[code_start:])
        # 添加新元数据
        metadata_text = ''
        for key, value in metadata.items():
            metadata_text += f"/* {key}: {value} */\n"
        self.setPlainText(metadata_text + code)

    def new_snippet(self):
        """创建新代码片段"""
        self.setPlainText(self.metadata_template)

    def keyPressEvent(self, event):
        """处理按键事件"""
        # 如果补全窗口可见且按下了相关键
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return

        # 自动缩进和括号处理
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_return()
            return
        # 处理Tab键
        elif event.key() == Qt.Key_Tab:
            self.handle_tab()
            return
        # 处理括号匹配
        elif event.text() in self.matching_pairs:
            self.handle_bracket(event.text())
            return
        # 处理右括号
        elif event.text() in self.matching_pairs.values():
            self.handle_closing_bracket(event.text())
            return

        super().keyPressEvent(event)

        # 触发代码补全
        if event.key() in (Qt.Key_Period, Qt.Key_Space):
            self.update_completer()
            rect = self.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0)
                          + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)

    def line_number_area_width(self):
        """计算行号区域的宽度"""
        digits = len(str(max(1, self.blockCount())))
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
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(),
                                                self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        """绘制行号区域"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor('#2b2b2b'))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor('#7f7f7f'))
                painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(),
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
            line_color = QColor('#323232')
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def handle_return(self):
        """处理回车键，实现自动缩进"""
        cursor = self.textCursor()
        current_line = cursor.block().text()
        indent = ''
        # 获取当前行的缩进
        for char in current_line:
            if char.isspace():
                indent += char
            else:
                break
        # 如果当前行以冒号结尾，增加一级缩进
        if current_line.rstrip().endswith(':'):
            indent += '    '
        self.insertPlainText('\n' + indent)

    def handle_tab(self):
        """处理Tab键，插入4个空格"""
        self.insertPlainText('    ')

    def handle_bracket(self, bracket):
        """处理左括号，自动插入右括号"""
        cursor = self.textCursor()
        self.insertPlainText(bracket + self.matching_pairs[bracket])
        cursor.movePosition(QTextCursor.Left)
        self.setTextCursor(cursor)

    def handle_closing_bracket(self, bracket):
        """处理右括号"""
        cursor = self.textCursor()
        next_char = self.document().characterAt(cursor.position())
        if next_char == bracket:
            cursor.movePosition(QTextCursor.Right)
            self.setTextCursor(cursor)
        else:
            self.insertPlainText(bracket)

    def setAutoIndentation(self, enabled):
        """设置是否启用自动缩进"""
        self._auto_indent = enabled


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lexer = None
        self.formatter = HtmlFormatter(style='monokai')
        self.styles = {}
        self.setup_styles()

    def setup_styles(self):
        """设置语法高亮样式"""
        # 关键字
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#f92672"))
        keyword_format.setFontWeight(QFont.Bold)
        self.styles['Keyword'] = keyword_format

        # 字符串
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#e6db74"))
        self.styles['String'] = string_format

        # 注释
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#75715e"))
        comment_format.setFontItalic(True)
        self.styles['Comment'] = comment_format

        # 数字
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#ae81ff"))
        self.styles['Number'] = number_format

    def set_language(self, language):
        """设置代码语言"""
        try:
            self.lexer = get_lexer_by_name(language)
            self.rehighlight()
        except:
            self.lexer = None

    def highlightBlock(self, text):
        """高亮代码块"""
        if not self.lexer:
            return

        # 使用pygments进行语法高亮
        tokens = self.lexer.get_tokens(text)
        for token, value in tokens:
            format = QTextCharFormat()
            token_str = str(token)

            # 应用预定义样式
            if 'Keyword' in token_str:
                format = self.styles['Keyword']
            elif 'String' in token_str:
                format = self.styles['String']
            elif 'Comment' in token_str:
                format = self.styles['Comment']
            elif 'Number' in token_str:
                format = self.styles['Number']
            else:
                format.setForeground(QColor('#f8f8f2'))  # 默认文本颜色

            self.setFormat(self.currentBlock().position() + token.start,
                           len(value), format)
