import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """配置管理器 - 统一管理所有应用配置"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            project_root = Path(__file__).resolve().parents[2]
            self.config_dir = project_root / "resources" / "config"
        else:
            self.config_dir = Path(config_dir)
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.config_files = {
            'editor': self.config_dir / 'editor.yaml',
            'window': self.config_dir / 'window.yaml',
            'filter': self.config_dir / 'filter.yaml',
            'general': self.config_dir / 'general.yaml'
        }
        
        # 默认配置
        self.default_configs = {
            'editor': {
                'font_family': 'Consolas',
                'font_size': 12,
                'tab_size': 4,
                'word_wrap': True,
                'line_numbers': True,
                'syntax_highlighting': True,
                'auto_indent': True,
                'bracket_matching': True,
                'auto_save': True,
                'auto_save_interval': 30  # 秒
            },
            'window': {
                'width': 900,
                'height': 600,
                'maximized': False,
                'position': {'x': -1, 'y': -1},  # -1 表示居中
                'splitter_sizes': [300, 700],
                'remember_size': True,
                'remember_position': True
            },
            'filter': {
                'last_used': {
                    'keyword': '',
                    'language': None,
                    'tag': None,
                    'category': None,
                    'sort_field': '创建时间',
                    'sort_order': 'desc'
                },
                'quick_filters': [
                    {'name': '最近创建', 'sort_field': '创建时间', 'sort_order': 'desc'},
                    {'name': '最常用', 'sort_field': '使用频率', 'sort_order': 'desc'},
                    {'name': '按标题', 'sort_field': '标题', 'sort_order': 'asc'}
                ]
            },
            'general': {
                'language': 'zh_CN',
                'startup_tab': 0,
                'show_tips': True,
                'check_updates': True,
                'backup_enabled': True,
                'backup_interval': 24,  # 小时
                'max_recent_files': 10
            }
        }
        
        # 初始化配置文件
        self._initialize_configs()
    
    def ensure_config_directory(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_configs(self):
        """初始化配置文件，如果不存在则创建默认配置"""
        for config_type, file_path in self.config_files.items():
            if not file_path.exists():
                self._save_config(config_type, self.default_configs[config_type])
    
    def _load_config(self, config_type: str) -> Dict[str, Any]:
        """加载指定类型的配置"""
        file_path = self.config_files.get(config_type)
        if not file_path or not file_path.exists():
            return self.default_configs.get(config_type, {})
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                # 合并默认配置，确保所有必要的键都存在
                default = self.default_configs.get(config_type, {})
                return self._merge_configs(default, config)
        except Exception as e:
            print(f"加载配置文件失败 {file_path}: {e}")
            return self.default_configs.get(config_type, {})
    
    def _save_config(self, config_type: str, config: Dict[str, Any]):
        """保存指定类型的配置"""
        file_path = self.config_files.get(config_type)
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        except Exception as e:
            print(f"保存配置文件失败 {file_path}: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和用户配置"""
        result = default.copy()
        for key, value in user.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    # 编辑器配置
    def get_editor_config(self) -> Dict[str, Any]:
        """获取编辑器配置"""
        return self._load_config('editor')
    
    def save_editor_config(self, config: Dict[str, Any]):
        """保存编辑器配置"""
        self._save_config('editor', config)
    
    def get_editor_setting(self, key: str, default=None):
        """获取编辑器特定设置"""
        return self.get_editor_config().get(key, default)
    
    def set_editor_setting(self, key: str, value: Any):
        """设置编辑器特定设置"""
        config = self.get_editor_config()
        config[key] = value
        self.save_editor_config(config)
    
    # 窗口配置
    def get_window_config(self) -> Dict[str, Any]:
        """获取窗口配置"""
        return self._load_config('window')
    
    def save_window_config(self, config: Dict[str, Any]):
        """保存窗口配置"""
        self._save_config('window', config)
    
    def get_window_geometry(self) -> Dict[str, Any]:
        """获取窗口几何信息"""
        config = self.get_window_config()
        return {
            'width': config.get('width', 900),
            'height': config.get('height', 600),
            'maximized': config.get('maximized', False),
            'position': config.get('position', {'x': -1, 'y': -1})
        }
    
    def save_window_geometry(self, width: int, height: int, x: int, y: int, maximized: bool = False):
        """保存窗口几何信息"""
        config = self.get_window_config()
        if config.get('remember_size', True):
            config['width'] = width
            config['height'] = height
            config['maximized'] = maximized
        if config.get('remember_position', True):
            config['position'] = {'x': x, 'y': y}
        self.save_window_config(config)
    
    def get_splitter_sizes(self) -> list:
        """获取分割器尺寸"""
        return self.get_window_config().get('splitter_sizes', [300, 700])
    
    def save_splitter_sizes(self, sizes: list):
        """保存分割器尺寸"""
        config = self.get_window_config()
        config['splitter_sizes'] = sizes
        self.save_window_config(config)
    
    # 筛选配置
    def get_filter_config(self) -> Dict[str, Any]:
        """获取筛选配置"""
        return self._load_config('filter')
    
    def save_filter_config(self, config: Dict[str, Any]):
        """保存筛选配置"""
        self._save_config('filter', config)
    
    def get_last_filter(self) -> Dict[str, Any]:
        """获取上次使用的筛选条件"""
        return self.get_filter_config().get('last_used', {})
    
    def save_last_filter(self, filter_conditions: Dict[str, Any]):
        """保存上次使用的筛选条件"""
        config = self.get_filter_config()
        config['last_used'] = filter_conditions
        self.save_filter_config(config)
    
    def get_quick_filters(self) -> list:
        """获取快速筛选选项"""
        return self.get_filter_config().get('quick_filters', [])
    
    # 通用配置
    def get_general_config(self) -> Dict[str, Any]:
        """获取通用配置"""
        return self._load_config('general')
    
    def save_general_config(self, config: Dict[str, Any]):
        """保存通用配置"""
        self._save_config('general', config)
    
    def get_general_setting(self, key: str, default=None):
        """获取通用设置"""
        return self.get_general_config().get(key, default)
    
    def set_general_setting(self, key: str, value: Any):
        """设置通用设置"""
        config = self.get_general_config()
        config[key] = value
        self.save_general_config(config)
    
    # 配置重置
    def reset_config(self, config_type: str):
        """重置指定类型的配置为默认值"""
        if config_type in self.default_configs:
            self._save_config(config_type, self.default_configs[config_type])
    
    def reset_all_configs(self):
        """重置所有配置为默认值"""
        for config_type in self.default_configs:
            self.reset_config(config_type)
    
    # 配置导入导出
    def export_config(self, export_path: str, config_types: list = None):
        """导出配置到指定路径"""
        if config_types is None:
            config_types = list(self.config_files.keys())
        
        export_data = {}
        for config_type in config_types:
            if config_type in self.config_files:
                export_data[config_type] = self._load_config(config_type)
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str, config_types: list = None):
        """从指定路径导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = yaml.safe_load(f) or {}
            
            if config_types is None:
                config_types = list(import_data.keys())
            
            for config_type in config_types:
                if config_type in import_data and config_type in self.config_files:
                    self._save_config(config_type, import_data[config_type])
            
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False

# 全局配置管理器实例
config_manager = ConfigManager()