"""SQLite 数据层：代码片段与脚本，元数据存库而非代码注释。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "snippets.db"
SCRIPTS_IMPORT_DIR = PROJECT_ROOT / "data" / "scripts"

SCRIPT_EXTENSIONS = {
    ".bat": ("batch", "windows"),
    ".cmd": ("batch", "windows"),
    ".ps1": ("powershell", "windows"),
    ".sh": ("shell", "linux"),
    ".bash": ("shell", "linux"),
    ".py": ("python", "cross"),
    ".reg": ("registry", "windows"),
}


class CodeSnippet(Base):
    __tablename__ = "code_snippets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False, default="text")
    tags = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    script_type = Column(String(50), nullable=False, default="batch")
    platform = Column(String(50), nullable=False, default="windows")
    category = Column(String(200))
    tags = Column(String(500))
    source_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def create_engine_for_db(db_path: Path | str | None = None):
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path.as_posix()}"
    return create_engine(url, echo=False)


def init_database(db_path: Path | str | None = None):
    engine = create_engine_for_db(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session()


def _detect_script_meta(file_path: Path) -> tuple[str, str]:
    ext = file_path.suffix.lower()
    return SCRIPT_EXTENSIONS.get(ext, ("text", "cross"))


def import_scripts_from_filesystem(session, root: Path | None = None) -> int:
    """将 data/scripts 下的文件导入数据库（仅当 scripts 表为空时）。"""
    if session.query(Script).count() > 0:
        return 0

    root = root or SCRIPTS_IMPORT_DIR
    if not root.is_dir():
        return 0

    imported = 0
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SCRIPT_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="gbk", errors="replace")

        script_type, platform = _detect_script_meta(file_path)
        try:
            category = str(file_path.parent.relative_to(root)).replace("\\", "/")
            if category == ".":
                category = ""
        except ValueError:
            category = ""

        rel = file_path.relative_to(PROJECT_ROOT)
        session.add(
            Script(
                title=file_path.stem,
                content=content,
                script_type=script_type,
                platform=platform,
                category=category,
                source_path=str(rel).replace("\\", "/"),
            )
        )
        imported += 1

    if imported:
        session.commit()
    return imported
