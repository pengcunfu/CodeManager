# 代码管家（Code Manager）

一个基于PySide6开发的代码片段管理工具，帮助开发者高效管理和组织代码片段、BAT脚本等开发资源。

代码管理工具，后续迁移成Web版本。

服务端使用Node.js开发，数据库使用MongoDB。





## 主要功能

* 代码片段管理：存储、检索和组织常用的代码片段
* BAT脚本管理：集中管理和执行Windows批处理脚本
* 代码转换工具：进制转换、编码转换等实用功能

## 技术栈

* 前端界面：PySide6（Qt for Python）
* 数据存储：SQLite + SQLAlchemy
* 开发语言：Python 3.9+

## 安装说明

1. 克隆项目到本地：
```bash
git clone [项目地址]
cd code-management
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行程序：
```bash
python main.py
```

## 项目结构

```
├── app/                    # 应用主目录
│   ├── common/            # 公共模块
│   │   └── db.py         # 数据库操作
│   ├── component/        # 组件
│   └── view/             # 视图
│       └── main_window.py # 主窗口
├── data/                  # 数据目录
│   ├── data.db           # SQLite数据库
│   └── scripts/          # 脚本存储
├── resource/             # 资源文件
├── test/                 # 测试目录
├── main.py               # 程序入口
└── requirements.txt      # 依赖清单
```

## 开发说明

本项目使用Python 3.9+开发，采用PySide6构建GUI界面，SQLAlchemy作为ORM框架，SQLite作为数据存储。

## 许可证

MIT License

