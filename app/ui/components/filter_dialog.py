from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QCheckBox,
                             QGroupBox, QRadioButton, QButtonGroup, QFrame,
                             QDateEdit, QSpinBox, QSlider, QFormLayout)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont
from ...utils.config_manager import config_manager

class FilterDialog(QDialog):
    """高级筛选对话框"""
    
    # 定义信号，用于传递筛选条件
    filter_applied = Signal(dict)
    
    def __init__(self, snippet_manager, parent=None):
        super().__init__(parent)
        self.snippet_manager = snippet_manager
        self.init_ui()
        self.load_filter_options()
        self.load_last_filter_conditions()
        
    def init_ui(self):
        self.setWindowTitle("高级筛选")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 基本筛选条件组
        basic_group = QGroupBox("基本筛选条件")
        basic_layout = QFormLayout(basic_group)
        
        # 关键词搜索
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入关键词搜索标题、描述或代码内容...")
        basic_layout.addRow("关键词:", self.keyword_input)
        
        # 语言筛选
        self.language_combo = QComboBox()
        basic_layout.addRow("编程语言:", self.language_combo)
        
        # 标签筛选
        self.tag_combo = QComboBox()
        basic_layout.addRow("标签:", self.tag_combo)
        
        # 分类筛选
        self.category_combo = QComboBox()
        basic_layout.addRow("分类:", self.category_combo)
        
        layout.addWidget(basic_group)
        
        # 时间筛选组
        time_group = QGroupBox("时间筛选")
        time_layout = QFormLayout(time_group)
        
        # 创建时间范围
        self.enable_time_filter = QCheckBox("启用时间筛选")
        time_layout.addRow(self.enable_time_filter)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.start_date.setEnabled(False)
        time_layout.addRow("开始日期:", self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)
        time_layout.addRow("结束日期:", self.end_date)
        
        # 连接时间筛选复选框
        self.enable_time_filter.toggled.connect(self.start_date.setEnabled)
        self.enable_time_filter.toggled.connect(self.end_date.setEnabled)
        
        layout.addWidget(time_group)
        
        # 代码长度筛选组
        length_group = QGroupBox("代码长度筛选")
        length_layout = QFormLayout(length_group)
        
        self.enable_length_filter = QCheckBox("启用长度筛选")
        length_layout.addRow(self.enable_length_filter)
        
        # 最小长度
        self.min_length = QSpinBox()
        self.min_length.setRange(0, 100000)
        self.min_length.setValue(0)
        self.min_length.setSuffix(" 字符")
        self.min_length.setEnabled(False)
        length_layout.addRow("最小长度:", self.min_length)
        
        # 最大长度
        self.max_length = QSpinBox()
        self.max_length.setRange(0, 100000)
        self.max_length.setValue(10000)
        self.max_length.setSuffix(" 字符")
        self.max_length.setEnabled(False)
        length_layout.addRow("最大长度:", self.max_length)
        
        # 连接长度筛选复选框
        self.enable_length_filter.toggled.connect(self.min_length.setEnabled)
        self.enable_length_filter.toggled.connect(self.max_length.setEnabled)
        
        layout.addWidget(length_group)
        
        # 排序选项组
        sort_group = QGroupBox("排序选项")
        sort_layout = QVBoxLayout(sort_group)
        
        # 排序字段
        sort_field_layout = QHBoxLayout()
        sort_field_layout.addWidget(QLabel("排序字段:"))
        
        self.sort_field_combo = QComboBox()
        self.sort_field_combo.addItems([
            "创建时间", "修改时间", "标题", "语言", "代码长度", "使用频率"
        ])
        sort_field_layout.addWidget(self.sort_field_combo)
        sort_layout.addLayout(sort_field_layout)
        
        # 排序方向
        sort_order_layout = QHBoxLayout()
        self.sort_order_group = QButtonGroup()
        
        self.sort_asc = QRadioButton("升序")
        self.sort_desc = QRadioButton("降序")
        self.sort_desc.setChecked(True)  # 默认降序
        
        self.sort_order_group.addButton(self.sort_asc, 0)
        self.sort_order_group.addButton(self.sort_desc, 1)
        
        sort_order_layout.addWidget(self.sort_asc)
        sort_order_layout.addWidget(self.sort_desc)
        sort_order_layout.addStretch()
        
        sort_layout.addLayout(sort_order_layout)
        layout.addWidget(sort_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self.reset_filters)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 应用按钮
        apply_btn = QPushButton("应用筛选")
        apply_btn.clicked.connect(self.apply_filters)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
    def load_filter_options(self):
        """加载筛选选项"""
        if not self.snippet_manager:
            return
            
        # 加载语言选项
        self.language_combo.clear()
        self.language_combo.addItem("全部语言", None)
        languages = self.snippet_manager.get_all_languages()
        for lang in languages:
            self.language_combo.addItem(lang, lang)
            
        # 加载标签选项
        self.tag_combo.clear()
        self.tag_combo.addItem("全部标签", None)
        tags = self.snippet_manager.get_all_tags()
        for tag in tags:
            self.tag_combo.addItem(tag, tag)
            
        # 加载分类选项（如果有的话）
        self.category_combo.clear()
        self.category_combo.addItem("全部分类", None)
        # 这里可以添加分类逻辑，暂时使用一些常见分类
        categories = ["算法", "数据结构", "工具函数", "API调用", "配置文件", "其他"]
        for category in categories:
            self.category_combo.addItem(category, category)
            
    def reset_filters(self):
        """重置所有筛选条件"""
        self.keyword_input.clear()
        self.language_combo.setCurrentIndex(0)
        self.tag_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        
        self.enable_time_filter.setChecked(False)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date.setDate(QDate.currentDate())
        
        self.enable_length_filter.setChecked(False)
        self.min_length.setValue(0)
        self.max_length.setValue(10000)
        
        self.sort_field_combo.setCurrentIndex(0)
        self.sort_desc.setChecked(True)
        
    def apply_filters(self):
        """应用筛选条件"""
        filter_conditions = {
            'keyword': self.keyword_input.text().strip() or None,
            'language': self.language_combo.currentData(),
            'tag': self.tag_combo.currentData(),
            'category': self.category_combo.currentData(),
            'enable_time_filter': self.enable_time_filter.isChecked(),
            'start_date': self.start_date.date().toPython() if self.enable_time_filter.isChecked() else None,
            'end_date': self.end_date.date().toPython() if self.enable_time_filter.isChecked() else None,
            'enable_length_filter': self.enable_length_filter.isChecked(),
            'min_length': self.min_length.value() if self.enable_length_filter.isChecked() else None,
            'max_length': self.max_length.value() if self.enable_length_filter.isChecked() else None,
            'sort_field': self.sort_field_combo.currentText(),
            'sort_order': 'asc' if self.sort_asc.isChecked() else 'desc'
        }
        
        # 发射信号传递筛选条件
        self.filter_applied.emit(filter_conditions)
        self.accept()
        
    def load_last_filter_conditions(self):
        """加载上次使用的筛选条件"""
        last_filter = config_manager.get_last_filter()
        if not last_filter:
            return
            
        # 恢复关键词
        if last_filter.get('keyword'):
            self.keyword_input.setText(last_filter['keyword'])
            
        # 恢复语言选择
        if last_filter.get('language'):
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == last_filter['language']:
                    self.language_combo.setCurrentIndex(i)
                    break
                    
        # 恢复标签选择
        if last_filter.get('tag'):
            for i in range(self.tag_combo.count()):
                if self.tag_combo.itemData(i) == last_filter['tag']:
                    self.tag_combo.setCurrentIndex(i)
                    break
                    
        # 恢复分类选择
        if last_filter.get('category'):
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == last_filter['category']:
                    self.category_combo.setCurrentIndex(i)
                    break
                    
        # 恢复时间筛选
        if last_filter.get('enable_time_filter'):
            self.enable_time_filter.setChecked(True)
            if last_filter.get('start_date'):
                self.start_date.setDate(QDate.fromString(str(last_filter['start_date']), Qt.ISODate))
            if last_filter.get('end_date'):
                self.end_date.setDate(QDate.fromString(str(last_filter['end_date']), Qt.ISODate))
                
        # 恢复长度筛选
        if last_filter.get('enable_length_filter'):
            self.enable_length_filter.setChecked(True)
            if last_filter.get('min_length') is not None:
                self.min_length.setValue(last_filter['min_length'])
            if last_filter.get('max_length') is not None:
                self.max_length.setValue(last_filter['max_length'])
                
        # 恢复排序设置
        sort_field = last_filter.get('sort_field', '创建时间')
        for i in range(self.sort_field_combo.count()):
            if self.sort_field_combo.itemText(i) == sort_field:
                self.sort_field_combo.setCurrentIndex(i)
                break
                
        sort_order = last_filter.get('sort_order', 'desc')
        if sort_order == 'asc':
            self.sort_asc.setChecked(True)
        else:
            self.sort_desc.setChecked(True)
    
    def get_filter_conditions(self):
        """获取当前筛选条件"""
        return {
            'keyword': self.keyword_input.text().strip() or None,
            'language': self.language_combo.currentData(),
            'tag': self.tag_combo.currentData(),
            'category': self.category_combo.currentData(),
            'enable_time_filter': self.enable_time_filter.isChecked(),
            'start_date': self.start_date.date().toPython() if self.enable_time_filter.isChecked() else None,
            'end_date': self.end_date.date().toPython() if self.enable_time_filter.isChecked() else None,
            'enable_length_filter': self.enable_length_filter.isChecked(),
            'min_length': self.min_length.value() if self.enable_length_filter.isChecked() else None,
            'max_length': self.max_length.value() if self.enable_length_filter.isChecked() else None,
            'sort_field': self.sort_field_combo.currentText(),
            'sort_order': 'asc' if self.sort_asc.isChecked() else 'desc'
        }