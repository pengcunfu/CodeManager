"""代码片段 SQLite 仓储。"""
from __future__ import annotations

import json
from typing import List, Optional

from app.database import Base, CodeSnippet


class CodeSnippetManager:
    def __init__(self, session):
        self.session = session

    def create_snippet(
        self,
        title: str,
        code: str,
        language: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> CodeSnippet:
        snippet = CodeSnippet(
            title=title,
            code=code,
            language=language,
            description=description,
            tags=",".join(tags) if tags else None,
        )
        self.session.add(snippet)
        self.session.commit()
        return snippet

    def get_snippet(self, snippet_id: int) -> Optional[CodeSnippet]:
        return self.session.get(CodeSnippet, snippet_id)

    def update_snippet(self, snippet_id: int, **kwargs):
        snippet = self.get_snippet(snippet_id)
        if not snippet:
            return None
        for key, value in kwargs.items():
            if key == "tags" and isinstance(value, list):
                value = ",".join(value)
            setattr(snippet, key, value)
        self.session.commit()
        return snippet

    def delete_snippet(self, snippet_id: int) -> bool:
        snippet = self.get_snippet(snippet_id)
        if not snippet:
            return False
        self.session.delete(snippet)
        self.session.commit()
        return True

    def search_snippets(
        self,
        keyword: Optional[str] = None,
        language: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[CodeSnippet]:
        query = self.session.query(CodeSnippet)

        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (CodeSnippet.title.ilike(like))
                | (CodeSnippet.description.ilike(like))
                | (CodeSnippet.code.ilike(like))
            )
        if language:
            query = query.filter(CodeSnippet.language == language)
        if tag:
            query = query.filter(CodeSnippet.tags.ilike(f"%{tag}%"))

        return query.order_by(CodeSnippet.updated_at.desc()).all()

    def get_all_languages(self) -> List[str]:
        return [
            row[0]
            for row in self.session.query(CodeSnippet.language).distinct().all()
            if row[0]
        ]

    def get_all_tags(self) -> List[str]:
        tags = set()
        for row in self.session.query(CodeSnippet.tags).all():
            if row[0]:
                tags.update(t.strip() for t in row[0].split(",") if t.strip())
        return sorted(tags)

    def export_snippets(self, snippet_ids: List[int], format: str = "json") -> str:
        snippets = (
            self.session.query(CodeSnippet).filter(CodeSnippet.id.in_(snippet_ids)).all()
        )
        if format == "json":
            return json.dumps(
                [
                    {
                        "id": s.id,
                        "title": s.title,
                        "description": s.description,
                        "code": s.code,
                        "language": s.language,
                        "tags": s.tags.split(",") if s.tags else [],
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                    }
                    for s in snippets
                ],
                ensure_ascii=False,
                indent=2,
            )
        if format == "markdown":
            parts = []
            for s in snippets:
                tag_line = ", ".join(s.tags.split(",")) if s.tags else ""
                parts.append(
                    f"# {s.title}\n\n{s.description or ''}\n\n"
                    f"**语言:** {s.language}  **标签:** {tag_line}\n\n"
                    f"```{s.language}\n{s.code}\n```"
                )
            return "\n\n---\n\n".join(parts)
        raise ValueError(f"Unsupported export format: {format}")
