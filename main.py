from PySide6.QtWidgets import QApplication, QMainWindow
from app.ui.main_window import MainWindow
from app.utils.config_manager import config_manager
import sys

# 初始化应用程序
app = QApplication(sys.argv)

# 设置 Windows Vista 风格
app.setStyle("WindowsVista")

# 确保配置目录存在
config_manager.ensure_config_directory()

# 创建主窗口
win = MainWindow()
win.show()

# 运行应用程序
sys.exit(app.exec())
