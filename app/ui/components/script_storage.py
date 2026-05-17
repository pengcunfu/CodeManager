"""脚本 SQLite 仓储。"""
from __future__ import annotations

import json
from typing import List, Optional

from app.database import Script


class ScriptManager:
    def __init__(self, session):
        self.session = session

    def create_script(
        self,
        title: str,
        content: str,
        script_type: str = "batch",
        platform: str = "windows",
        description: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source_path: Optional[str] = None,
    ) -> Script:
        script = Script(
            title=title,
            content=content,
            script_type=script_type,
            platform=platform,
            description=description,
            category=category,
            tags=",".join(tags) if tags else None,
            source_path=source_path,
        )
        self.session.add(script)
        self.session.commit()
        return script

    def get_script(self, script_id: int) -> Optional[Script]:
        return self.session.get(Script, script_id)

    def update_script(self, script_id: int, **kwargs):
        script = self.get_script(script_id)
        if not script:
            return None
        for key, value in kwargs.items():
            if key == "tags" and isinstance(value, list):
                value = ",".join(value)
            setattr(script, key, value)
        self.session.commit()
        return script

    def delete_script(self, script_id: int) -> bool:
        script = self.get_script(script_id)
        if not script:
            return False
        self.session.delete(script)
        self.session.commit()
        return True

    def list_scripts(
        self,
        keyword: Optional[str] = None,
        script_type: Optional[str] = None,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Script]:
        query = self.session.query(Script)

        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (Script.title.ilike(like))
                | (Script.description.ilike(like))
                | (Script.content.ilike(like))
                | (Script.category.ilike(like))
            )
        if script_type:
            query = query.filter(Script.script_type == script_type)
        if platform:
            query = query.filter(Script.platform == platform)
        if category:
            query = query.filter(Script.category == category)
        if tag:
            query = query.filter(Script.tags.ilike(f"%{tag}%"))

        return query.order_by(Script.category, Script.title).all()

    def get_categories(self) -> List[str]:
        rows = self.session.query(Script.category).distinct().all()
        cats = sorted({r[0] for r in rows if r[0]})
        return cats

    def get_script_types(self) -> List[str]:
        return [r[0] for r in self.session.query(Script.script_type).distinct().all() if r[0]]

    def get_platforms(self) -> List[str]:
        return [r[0] for r in self.session.query(Script.platform).distinct().all() if r[0]]

    def get_all_tags(self) -> List[str]:
        tags = set()
        for row in self.session.query(Script.tags).all():
            if row[0]:
                tags.update(t.strip() for t in row[0].split(",") if t.strip())
        return sorted(tags)

    def export_scripts(self, script_ids: List[int], fmt: str = "json") -> str:
        scripts = self.session.query(Script).filter(Script.id.in_(script_ids)).all()
        if fmt == "json":
            payload = []
            for s in scripts:
                payload.append(
                    {
                        "id": s.id,
                        "title": s.title,
                        "description": s.description,
                        "content": s.content,
                        "script_type": s.script_type,
                        "platform": s.platform,
                        "category": s.category,
                        "tags": s.tags.split(",") if s.tags else [],
                    }
                )
            return json.dumps(payload, ensure_ascii=False, indent=2)
        raise ValueError(f"Unsupported export format: {fmt}")
