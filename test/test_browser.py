from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtCore import QUrl

import sys
import os

__import__('__init__')


# os.environ["QT_PLUGIN_PATH"] = os.path.realpath("./resources/plugins")
# 确保 Qt WebEngine 被正确初始化
# os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"
# os.environ["QTWEBENGINEPROCESS_PATH"] = os.path.realpath("./resources/plugins/QtWebEngineProcess.exe")

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QWebEngineView 测试")
        self.setGeometry(100, 100, 800, 600)

        # 创建 QWebEngineView 组件
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        # 启用 JS & 其他 Web 功能
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)

        # 直接加载 HTML
        html = """
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <title>测试 QWebEngineView</title>
            <script>
                document.addEventListener("DOMContentLoaded", function() {
                    document.body.innerHTML += "<p>JS 运行成功！</p>";
                });
            </script>
        </head>
        <body>
            <h1>Hello, QWebEngineView!</h1>
        </body>
        </html>
        """
        self.browser.setHtml(html)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec())
