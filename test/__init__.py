# ===========================
# 兼容VSCode和PyCharm可以直接执行测试代码
import os
from pathlib import Path

# 获取当前脚本的父目录并设置为工作目录
current_path = Path.cwd()
if current_path.name == "test":
    os.chdir(current_path.parent)
# ===========================
