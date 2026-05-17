#!/usr/bin/env python3
"""使用 PyInstaller 将 CodeManager 打包为 Windows 可执行文件。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "CodeManager"
ENTRY = ROOT / "main.py"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
SPEC_FILE = ROOT / f"{APP_NAME}.spec"


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("未检测到 PyInstaller，正在安装…")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            cwd=ROOT,
        )


def data_sep() -> str:
    return ";" if sys.platform == "win32" else ":"


def collect_add_data() -> list[str]:
    """将静态资源打入包内（运行目录仍会额外复制一份，见 post_copy_runtime_dirs）。"""
    args: list[str] = []
    sep = data_sep()
    resources = ROOT / "resources"
    if resources.is_dir():
        args.extend(["--add-data", f"{resources}{sep}resources"])
    return args


def collect_hidden_imports() -> list[str]:
    modules = [
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebChannel",
        "sqlalchemy.dialects.sqlite",
        "pygments",
        "pygments.lexers",
        "pygments.formatters",
        "jedi",
        "yaml",
    ]
    args: list[str] = []
    for name in modules:
        args.extend(["--hidden-import", name])
    return args


def build_pyinstaller_args(
    *,
    onefile: bool,
    console: bool,
    clean: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        APP_NAME,
        "--noconfirm",
        str(ENTRY),
        # Qt WebEngine 依赖较多二进制与资源，collect-all 更稳妥
        "--collect-all",
        "PySide6",
        "--collect-submodules",
        "pygments.lexers",
        "--collect-submodules",
        "jedi",
        *collect_add_data(),
        *collect_hidden_imports(),
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if console:
        cmd.append("--console")
    else:
        cmd.append("--windowed")

    if clean:
        cmd.append("--clean")

    return cmd


def output_dir(onefile: bool) -> Path:
    if onefile:
        return DIST_DIR
    return DIST_DIR / APP_NAME


def exe_path(onefile: bool) -> Path:
    base = output_dir(onefile)
    return base / f"{APP_NAME}.exe"


def post_copy_runtime_dirs(target: Path) -> None:
    """
    应用使用相对路径访问 resources/、data/，将目录复制到 exe 同级。
    数据库文件不复制，避免覆盖用户数据。
    """
    def ignore_db(_dir: str, names: list[str]) -> set[str]:
        return {n for n in names if n.endswith((".db", ".sqlite", ".sqlite3"))}

    for dirname in ("resources", "data"):
        src = ROOT / dirname
        if not src.is_dir():
            continue
        dest = target / dirname
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=ignore_db)
        print(f"已复制运行时目录: {dest}")


def clean_artifacts(*, dist: bool, build: bool, spec: bool) -> None:
    if dist and DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"已删除 {DIST_DIR}")
    if build and BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"已删除 {BUILD_DIR}")
    if spec and SPEC_FILE.exists():
        SPEC_FILE.unlink()
        print(f"已删除 {SPEC_FILE}")


def run_build(
    *,
    onefile: bool = False,
    console: bool = False,
    clean: bool = True,
    skip_install_check: bool = False,
) -> Path:
    if not ENTRY.is_file():
        raise FileNotFoundError(f"入口文件不存在: {ENTRY}")

    if not skip_install_check:
        ensure_pyinstaller()

    if clean:
        clean_artifacts(dist=True, build=True, spec=False)

    cmd = build_pyinstaller_args(onefile=onefile, console=console, clean=clean)
    print("执行打包命令:")
    print(" ", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)

    target = output_dir(onefile)
    post_copy_runtime_dirs(target)

    built_exe = exe_path(onefile)
    if not built_exe.is_file():
        raise FileNotFoundError(f"未找到生成的可执行文件: {built_exe}")

    print()
    print("打包完成:")
    print(f"  {built_exe}")
    return built_exe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用 PyInstaller 将 CodeManager 编译为 Windows exe",
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="单文件 exe（体积大、启动慢；默认 onedir 目录模式，更适合 Qt WebEngine）",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="显示控制台窗口（便于调试）",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="打包前不清理 build/、dist/",
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="仅清理 build/、dist/ 与 spec 文件后退出",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.clean_only:
        clean_artifacts(dist=True, build=True, spec=True)
        return

    run_build(
        onefile=args.onefile,
        console=args.console,
        clean=not args.no_clean,
    )


if __name__ == "__main__":
    main()
