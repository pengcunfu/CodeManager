from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                               QToolBar, QMessageBox, QMenuBar, QMenu,
                               QFileDialog, QStyle, QSplitter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (QSyntaxHighlighter, QTextCharFormat, QColor, QFont,
                           QAction, QIcon)
import re
import keyword
from .remote_runner import RemoteRunnerWidget
from .preferences_dialog import PreferencesDialog
from .editor_config_dialog import EditorConfigDialog
from .components import SnippetManagerWidget
from .components.script_manager_widget import ScriptManagerWidget
from .components.filter_dialog import FilterDialog
from ..database import init_database, import_scripts_from_filesystem
from ..utils.config_manager import config_manager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session = self.init_database()

        self.init_ui()
        self.setup_shortcuts()

    def init_database(self):
        """初始化 SQLite 并导入 data/scripts 中的脚本（首次）。"""
        _engine, session = init_database()
        import_scripts_from_filesystem(session)
        return session

    def init_ui(self):
        # 设置窗口标题
        self.setWindowTitle("代码管理工具")
        
        # 从配置恢复窗口状态
        self.restore_window_state()

        # 窗口居中显示（如果是首次运行）
        geometry = config_manager.get_window_geometry()
        if geometry['position']['x'] == -1 or geometry['position']['y'] == -1:
            self.center_window()

        # 创建菜单栏
        self.create_menu_bar()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(2, 2, 2, 2)  # 减少边距
        layout.setSpacing(1)  # 减少间距

        # 创建主分割器
        self.main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.main_splitter)
        
        # 创建选项卡，设置为左侧显示
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.West)
        self.main_splitter.addWidget(self.tab_widget)
        
        # 恢复分割器状态
        splitter_sizes = config_manager.get_splitter_sizes()
        self.main_splitter.setSizes(splitter_sizes)

        # 添加代码片段管理选项卡
        self.snippet_manager = SnippetManagerWidget(self.session)
        code_icon = QIcon("resources/icons/languages/code.svg")
        self.tab_widget.addTab(self.snippet_manager, code_icon, "")
        self.tab_widget.setTabToolTip(0, "代码片段管理")

        # 脚本管理（SQLite）
        self.script_manager = ScriptManagerWidget(self.session)
        script_icon = QIcon("resources/icons/languages/code.svg")
        self.tab_widget.addTab(self.script_manager, script_icon, "")
        self.tab_widget.setTabToolTip(1, "脚本管理")

        # 添加远程操作选项卡
        self.remote_runner = RemoteRunnerWidget()
        remote_icon = QIcon("resources/icons/export.svg")
        self.tab_widget.addTab(self.remote_runner, remote_icon, "")
        self.tab_widget.setTabToolTip(2, "远程操作")
        
        # 恢复上次选中的标签页
        startup_tab = config_manager.get_general_setting('startup_tab', 0)
        if 0 <= startup_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(startup_tab)

        # 创建状态栏
        status_bar = self.statusBar()
        status_bar.showMessage("就绪")

    def center_window(self):
        """将窗口居中显示"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def setup_shortcuts(self):
        # 搜索快捷键
        search_action = QAction(self)
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(lambda: self.search_input.setFocus())
        self.addAction(search_action)

        # 清空搜索快捷键
        clear_search_action = QAction(self)
        clear_search_action.setShortcut("Esc")
        clear_search_action.triggered.connect(self.clear_search)
        self.addAction(clear_search_action)

    def new_file(self):
        """新建文件"""
        pass  # TODO: 实现新建文件功能

    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "打开文件", "", "所有文件 (*.*)")
        if file_path:
            pass  # TODO: 实现打开文件功能

    def open_folder(self):
        """打开文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "打开文件夹")
        if folder_path:
            pass  # TODO: 实现打开文件夹功能

    def show_preferences(self):
        """显示首选项对话框"""
        dialog = PreferencesDialog(self)
        dialog.exec_()

    def show_editor_config(self):
        """显示编辑器配置对话框"""
        dialog = EditorConfigDialog(self)
        # 连接配置改变信号
        dialog.config_changed.connect(self.apply_editor_config)
        dialog.exec_()

    def apply_editor_config(self, config):
        """应用编辑器配置"""
        # 将配置应用到代码片段管理器的编辑器
        if hasattr(self.snippet_manager, 'code_editor'):
            self.snippet_manager.code_editor.apply_config(config)
        
        # 配置已经在EditorConfigDialog中通过config_manager保存了
        # 这里只需要应用到当前的编辑器实例

    def create_system_tools_menu(self, menu):
        """创建系统工具菜单"""
        # 文件管理器
        explorer_action = QAction("📁 文件管理器", self)
        explorer_action.triggered.connect(lambda: self.open_system_tool("explorer"))
        menu.addAction(explorer_action)

        # 任务管理器
        taskmgr_action = QAction("⚙️ 任务管理器", self)
        taskmgr_action.triggered.connect(lambda: self.open_system_tool("taskmgr"))
        menu.addAction(taskmgr_action)

        # 记事本
        notepad_action = QAction("📝 记事本", self)
        notepad_action.triggered.connect(lambda: self.open_system_tool("notepad"))
        menu.addAction(notepad_action)

        # 计算器
        calc_action = QAction("🧮 计算器", self)
        calc_action.triggered.connect(lambda: self.open_system_tool("calc"))
        menu.addAction(calc_action)

        menu.addSeparator()

        # 控制面板
        control_action = QAction("🎛️ 控制面板", self)
        control_action.triggered.connect(lambda: self.open_system_tool("control"))
        menu.addAction(control_action)

        # 设备管理器
        devmgmt_action = QAction("🔧 设备管理器", self)
        devmgmt_action.triggered.connect(lambda: self.open_system_tool("devmgmt.msc"))
        menu.addAction(devmgmt_action)

        # 服务管理
        services_action = QAction("⚡ 服务管理", self)
        services_action.triggered.connect(lambda: self.open_system_tool("services.msc"))
        menu.addAction(services_action)

        # 注册表编辑器
        regedit_action = QAction("📋 注册表编辑器", self)
        regedit_action.triggered.connect(lambda: self.open_system_tool("regedit"))
        menu.addAction(regedit_action)

        menu.addSeparator()

        # 系统信息
        msinfo_action = QAction("ℹ️ 系统信息", self)
        msinfo_action.triggered.connect(lambda: self.open_system_tool("msinfo32"))
        menu.addAction(msinfo_action)

        # 环境变量
        env_action = QAction("🌍 环境变量", self)
        env_action.triggered.connect(lambda: self.open_system_tool("rundll32 sysdm.cpl,EditEnvironmentVariables"))
        menu.addAction(env_action)

        # 电源选项
        power_action = QAction("🔋 电源选项", self)
        power_action.triggered.connect(lambda: self.open_system_tool("powercfg.cpl"))
        menu.addAction(power_action)

        # 网络连接
        network_action = QAction("🌐 网络连接", self)
        network_action.triggered.connect(lambda: self.open_system_tool("ncpa.cpl"))
        menu.addAction(network_action)

        menu.addSeparator()

        # 命令提示符
        cmd_action = QAction("💻 命令提示符", self)
        cmd_action.triggered.connect(lambda: self.open_system_tool("cmd"))
        menu.addAction(cmd_action)

        # PowerShell
        powershell_action = QAction("🔷 PowerShell", self)
        powershell_action.triggered.connect(lambda: self.open_system_tool("powershell"))
        menu.addAction(powershell_action)

    def open_system_tool(self, tool_command):
        """打开系统工具"""
        try:
            import subprocess
            if tool_command.startswith("rundll32"):
                # 对于rundll32命令，需要特殊处理
                subprocess.Popen(tool_command, shell=True)
            else:
                subprocess.Popen(tool_command, shell=True)
            
            # 显示成功消息（可选）
            self.statusBar().showMessage(f"已启动: {tool_command}", 2000)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法启动工具: {tool_command}\n错误: {str(e)}")

    def show_about(self):
        """显示关于对话框"""
        from versions import display_version

        QMessageBox.about(
            self,
            "关于",
            f"""
            <h3>代码管理工具</h3>
            <p>版本：{display_version()}</p>
            <p>一个简单而强大的代码片段管理工具。</p>
            """,
        )

    def show_filter_dialog(self):
        """显示筛选对话框"""
        dialog = FilterDialog(self.snippet_manager.snippet_manager, self)
        dialog.filter_applied.connect(self.snippet_manager.apply_advanced_filter)
        dialog.exec_()

    def clear_search(self):
        """清空搜索框并重置列表"""
        self.search_input.clear()
        self.load_documents()

    def create_menu_bar(self):
        menubar = QMenuBar()
        self.setMenuBar(menubar)

        # 文件菜单
        file_menu = QMenu("文件(&F)", self)
        menubar.addMenu(file_menu)

        new_file_action = QAction("新建文件(&N)", self)
        new_file_action.setShortcut("Ctrl+N")
        new_file_action.triggered.connect(self.new_file)
        file_menu.addAction(new_file_action)

        open_file_action = QAction("打开文件(&O)", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)

        open_folder_action = QAction("打开文件夹(&F)", self)
        open_folder_action.setShortcut("Ctrl+K Ctrl+O")
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 代码菜单
        code_menu = QMenu("代码(&C)", self)
        menubar.addMenu(code_menu)

        new_snippet_action = QAction("新建代码片段(&S)", self)
        new_snippet_action.setShortcut("Ctrl+Alt+N")
        new_snippet_action.triggered.connect(lambda: self.snippet_manager.new_snippet())
        code_menu.addAction(new_snippet_action)
        
        code_menu.addSeparator()
        
        # 高级筛选
        filter_action = QAction("高级筛选(&F)", self)
        filter_action.setShortcut("Ctrl+Shift+F")
        filter_action.triggered.connect(self.show_filter_dialog)
        code_menu.addAction(filter_action)

        # 工具菜单
        tools_menu = QMenu("工具(&T)", self)
        menubar.addMenu(tools_menu)

        # 编辑器配置
        editor_config_action = QAction("编辑器配置(&E)", self)
        editor_config_action.setShortcut("Ctrl+Alt+,")
        editor_config_action.triggered.connect(self.show_editor_config)
        tools_menu.addAction(editor_config_action)

        tools_menu.addSeparator()

        # 系统工具子菜单
        system_tools_menu = QMenu("系统工具(&S)", self)
        tools_menu.addMenu(system_tools_menu)

        # 添加系统工具选项
        self.create_system_tools_menu(system_tools_menu)

        tools_menu.addSeparator()

        preferences_action = QAction("首选项(&P)", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)

        # 帮助菜单
        help_menu = QMenu("帮助(&H)", self)
        menubar.addMenu(help_menu)

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # 移除工具栏创建方法，不再需要工具栏

    def restore_window_state(self):
        """恢复窗口状态"""
        geometry = config_manager.get_window_geometry()
        
        # 恢复窗口大小
        self.resize(geometry['width'], geometry['height'])
        
        # 恢复窗口位置
        if geometry['position']['x'] != -1 and geometry['position']['y'] != -1:
            self.move(geometry['position']['x'], geometry['position']['y'])
        
        # 恢复最大化状态
        if geometry['maximized']:
            self.showMaximized()
    
    def save_window_state(self):
        """保存窗口状态"""
        if not self.isMaximized():
            # 只在非最大化状态下保存位置和大小
            geometry = self.geometry()
            config_manager.save_window_geometry(
                geometry.width(),
                geometry.height(),
                geometry.x(),
                geometry.y(),
                False
            )
        else:
            # 最大化状态
            config_manager.save_window_geometry(
                900, 600,  # 默认大小
                -1, -1,    # 居中位置
                True
            )
        
        # 保存分割器状态
        if hasattr(self, 'main_splitter'):
            config_manager.save_splitter_sizes(self.main_splitter.sizes())
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存窗口状态
        self.save_window_state()
        
        # 保存当前选中的标签页
        config_manager.set_general_setting('startup_tab', self.tab_widget.currentIndex())
        
        # 关闭数据库连接
        if hasattr(self, 'session'):
            self.session.close()
        
        event.accept()
    
    # 移除了工具栏相关的方法，这些功能现在由代码片段管理组件内部处理
