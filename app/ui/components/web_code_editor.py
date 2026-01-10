from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Signal, Slot, QUrl
import json
import os


class CodeEditorBridge(QObject):
    """JavaScript与Python之间的桥接对象"""

    # 信号定义
    code_changed = Signal(str)
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._code = ""
        self._language = "python"
        self._metadata = {}

    @Slot(str)
    def on_code_changed(self, code):
        """当代码内容改变时调用"""
        self._code = code
        self.code_changed.emit(code)

    @Slot(str)
    def on_language_changed(self, language):
        """当语言改变时调用"""
        self._language = language
        self.language_changed.emit(language)

    @Slot(str)
    def set_code(self, code):
        """设置代码内容"""
        self._code = code

    @Slot(str)
    def set_language(self, language):
        """设置编程语言"""
        self._language = language

    @Slot(str)
    def set_metadata(self, metadata_json):
        """设置元数据"""
        try:
            self._metadata = json.loads(metadata_json)
        except:
            self._metadata = {}

    @Slot(result=str)
    def get_code(self):
        """获取代码内容"""
        return self._code

    @Slot(result=str)
    def get_language(self):
        """获取编程语言"""
        return self._language

    @Slot(result=str)
    def get_metadata(self):
        """获取元数据"""
        return json.dumps(self._metadata)


class WebCodeEditor(QWidget):
    """基于WebView和Monaco Editor的代码编辑器"""

    code_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge = CodeEditorBridge()
        self.web_view = None
        self.current_language = "python"
        self.setup_ui()
        self.setup_web_channel()
        self.load_editor()

        # 连接信号
        self.bridge.code_changed.connect(self.code_changed.emit)

    def setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建WebView
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

    def setup_web_channel(self):
        """设置Web通道用于JavaScript与Python通信"""
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

    def load_editor(self):
        """加载Monaco Editor"""
        html_content = self.get_editor_html()

        # 创建临时HTML文件
        temp_dir = "data/temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, "monaco_editor.html")

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 加载HTML文件
        self.web_view.load(QUrl.fromLocalFile(temp_file))

    def get_editor_html(self):
        """生成简化的代码编辑器HTML内容"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Code Editor</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        #container {
            width: 100vw;
            height: 100vh;
            padding: 10px;
            box-sizing: border-box;
        }
        #editor {
            width: 100%;
            height: 100%;
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: none;
            outline: none;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            resize: none;
            tab-size: 4;
            white-space: pre;
            overflow-wrap: normal;
            overflow-x: auto;
        }
        .line-numbers {
            position: absolute;
            left: 0;
            top: 10px;
            width: 50px;
            background-color: #252526;
            color: #858585;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            text-align: right;
            padding-right: 10px;
            user-select: none;
            border-right: 1px solid #3e3e42;
        }
        #editor-container {
            position: relative;
            width: 100%;
            height: 100%;
        }
        #editor-text {
            margin-left: 60px;
            width: calc(100% - 60px);
            height: 100%;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="editor-container">
            <div class="line-numbers" id="line-numbers">1</div>
            <textarea id="editor" spellcheck="false" placeholder="在这里输入代码..."></textarea>
        </div>
    </div>
    
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    
    <script>
        let bridge;
        let editor = document.getElementById('editor');
        let lineNumbers = document.getElementById('line-numbers');
        
        // 初始化WebChannel
        new QWebChannel(qt.webChannelTransport, function(channel) {
            bridge = channel.objects.bridge;
            initializeEditor();
        });
        
        function initializeEditor() {
            // 监听内容变化
            editor.addEventListener('input', function() {
                updateLineNumbers();
                if (bridge) {
                    bridge.on_code_changed(editor.value);
                }
            });
            
            // 监听键盘事件
            editor.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    const start = editor.selectionStart;
                    const end = editor.selectionEnd;
                    editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
                    editor.selectionStart = editor.selectionEnd = start + 4;
                    updateLineNumbers();
                }
            });
            
            // 监听滚动事件
            editor.addEventListener('scroll', function() {
                lineNumbers.scrollTop = editor.scrollTop;
            });
            
            updateLineNumbers();
        }
        
        function updateLineNumbers() {
            const lines = editor.value.split('\n');
            const lineCount = lines.length;
            let lineNumbersText = '';
            for (let i = 1; i <= lineCount; i++) {
                lineNumbersText += i + '\n';
            }
            lineNumbers.textContent = lineNumbersText;
        }
        
        // 提供给Python调用的函数
        window.setCode = function(code) {
            if (editor) {
                editor.value = code;
                updateLineNumbers();
            }
        };
        
        window.setLanguage = function(language) {
            // 简化版本，不实现语法高亮
            console.log('Language set to:', language);
        };
        
        window.getCode = function() {
            return editor ? editor.value : '';
        };
        
        window.setTheme = function(theme) {
            console.log('Theme set to:', theme);
        };
        
        window.insertText = function(text) {
            if (editor) {
                const start = editor.selectionStart;
                const end = editor.selectionEnd;
                editor.value = editor.value.substring(0, start) + text + editor.value.substring(end);
                editor.selectionStart = editor.selectionEnd = start + text.length;
                updateLineNumbers();
            }
        };
        
        window.focus = function() {
            if (editor) {
                editor.focus();
            }
        };
    </script>
</body>
</html>
        '''

    def set_code(self, code):
        """设置代码内容"""
        self.bridge.set_code(code)
        self.web_view.page().runJavaScript(f"window.setCode({json.dumps(code)});")

    def get_code(self):
        """获取代码内容"""
        return self.bridge.get_code()

    def set_language(self, language):
        """设置编程语言"""
        self.current_language = language.lower()
        self.bridge.set_language(self.current_language)

        # 映射语言名称到Monaco Editor支持的语言ID
        language_map = {
            'python': 'python',
            'javascript': 'javascript',
            'js': 'javascript',
            'typescript': 'typescript',
            'ts': 'typescript',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'c++': 'cpp',
            'csharp': 'csharp',
            'c#': 'csharp',
            'php': 'php',
            'ruby': 'ruby',
            'go': 'go',
            'rust': 'rust',
            'swift': 'swift',
            'kotlin': 'kotlin',
            'scala': 'scala',
            'r': 'r',
            'perl': 'perl',
            'lua': 'lua',
            'shell': 'shell',
            'bash': 'shell',
            'powershell': 'powershell',
            'batch': 'bat',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'less': 'less',
            'xml': 'xml',
            'json': 'json',
            'yaml': 'yaml',
            'sql': 'sql',
            'dockerfile': 'dockerfile',
            'markdown': 'markdown',
            'md': 'markdown'
        }

        monaco_language = language_map.get(self.current_language, 'plaintext')
        self.web_view.page().runJavaScript(f"window.setLanguage('{monaco_language}');")

    def set_theme(self, theme='vs-dark'):
        """设置编辑器主题"""
        self.web_view.page().runJavaScript(f"window.setTheme('{theme}');")

    def insert_text(self, text):
        """在当前位置插入文本"""
        self.web_view.page().runJavaScript(f"window.insertText({json.dumps(text)});")

    def focus(self):
        """聚焦到编辑器"""
        self.web_view.page().runJavaScript("window.focus();")

    def set_metadata(self, metadata):
        """设置元数据"""
        self.bridge.set_metadata(json.dumps(metadata))

    def get_metadata(self):
        """获取元数据"""
        try:
            return json.loads(self.bridge.get_metadata())
        except:
            return {}

    def new_snippet(self):
        """创建新代码片段"""
        template = '''/* title: 新建代码片段 */
/* language: python */
/* tags: tag1, tag2 */
/* description: 在这里添加描述 */

# 在这里编写代码
print("Hello, World!")
'''
        self.set_code(template)
