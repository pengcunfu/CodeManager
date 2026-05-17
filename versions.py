"""应用版本信息。BUILD_NUMBER 由 build.py 在打包时自动递增。"""

VERSION = "1.0.0"
BUILD_NUMBER = 1
def version_string() -> str:
    """完整版本号，例如 1.0.0.42"""
    return f"{VERSION}.{BUILD_NUMBER}"


def display_version() -> str:
    """界面展示用，例如 1.0.0 (Build 42)"""
    return f"{VERSION} (Build {BUILD_NUMBER})"
