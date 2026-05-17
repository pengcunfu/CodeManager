from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer
from app.ui.main_window import MainWindow
from app.utils.config_manager import config_manager
import signal
import sys


def _install_sigint_handler(app: QApplication) -> QTimer:
    """让终端 Ctrl+C 能退出 Qt 事件循环（否则 SIGINT 可能被阻塞）。"""
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)
    return timer


# 初始化应用程序
app = QApplication(sys.argv)
_sigint_timer = _install_sigint_handler(app)

# 设置 Windows Vista 风格
app.setStyle("WindowsVista")

# 确保配置目录存在
config_manager.ensure_config_directory()

# 创建主窗口
win = MainWindow()
win.show()

# 运行应用程序
sys.exit(app.exec())
