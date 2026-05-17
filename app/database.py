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


def _read_script_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="gbk", errors="replace")


def sync_scripts_from_filesystem(session, root: Path | None = None) -> dict[str, int]:
    """按 source_path 将 data/scripts 同步到 scripts 表（插入/更新）。"""
    root = root or SCRIPTS_IMPORT_DIR
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}
    if not root.is_dir():
        return stats

    by_path = {
        row.source_path: row
        for row in session.query(Script).filter(Script.source_path.isnot(None)).all()
    }

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SCRIPT_EXTENSIONS:
            continue

        content = _read_script_file(file_path)
        script_type, platform = _detect_script_meta(file_path)
        try:
            category = str(file_path.parent.relative_to(root)).replace("\\", "/")
            if category == ".":
                category = ""
        except ValueError:
            category = ""

        rel = file_path.relative_to(PROJECT_ROOT)
        source_path = str(rel).replace("\\", "/")
        title = file_path.stem
        row = by_path.get(source_path)

        if row is None:
            session.add(
                Script(
                    title=title,
                    content=content,
                    script_type=script_type,
                    platform=platform,
                    category=category or None,
                    source_path=source_path,
                )
            )
            stats["inserted"] += 1
        elif (row.content or "") != content:
            row.title = title
            row.content = content
            row.script_type = script_type
            row.platform = platform
            row.category = category or None
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    session.commit()
    return stats


def import_scripts_from_filesystem(session, root: Path | None = None) -> int:
    """应用启动时同步脚本目录（兼容旧调用，返回新增条数）。"""
    return sync_scripts_from_filesystem(session, root)["inserted"]
