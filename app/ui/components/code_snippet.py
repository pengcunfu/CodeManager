from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

class CodeSnippet(Base):
    __tablename__ = 'code_snippets'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    tags = Column(String(200))  # 以逗号分隔的标签
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'code': self.code,
            'language': self.language,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def export_json(self):
        """导出为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def export_markdown(self):
        """导出为Markdown格式"""
        tags = ' '.join([f'`{tag}`' for tag in (self.tags.split(',') if self.tags else [])])
        return f"""# {self.title}

{self.description or ''}

## 标签
{tags}

## 代码
```{self.language}
{self.code}
```

> 创建时间：{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}
> 更新时间：{self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

class CodeSnippetManager:
    def __init__(self, session):
        self.session = session

    def create_snippet(self, title, code, language, description=None, tags=None):
        """创建代码片段"""
        snippet = CodeSnippet(
            title=title,
            code=code,
            language=language,
            description=description,
            tags=','.join(tags) if tags else None
        )
        self.session.add(snippet)
        self.session.commit()
        return snippet

    def get_snippet(self, snippet_id):
        """获取代码片段"""
        return self.session.query(CodeSnippet).get(snippet_id)

    def update_snippet(self, snippet_id, **kwargs):
        """更新代码片段"""
        snippet = self.get_snippet(snippet_id)
        if snippet:
            for key, value in kwargs.items():
                if key == 'tags' and isinstance(value, list):
                    value = ','.join(value)
                setattr(snippet, key, value)
            self.session.commit()
        return snippet

    def delete_snippet(self, snippet_id):
        """删除代码片段"""
        snippet = self.get_snippet(snippet_id)
        if snippet:
            self.session.delete(snippet)
            self.session.commit()
            return True
        return False

    def search_snippets(self, keyword=None, language=None, tag=None):
        """搜索代码片段"""
        query = self.session.query(CodeSnippet)

        if keyword:
            query = query.filter(
                (CodeSnippet.title.ilike(f'%{keyword}%')) |
                (CodeSnippet.description.ilike(f'%{keyword}%')) |
                (CodeSnippet.code.ilike(f'%{keyword}%'))
            )

        if language:
            query = query.filter(CodeSnippet.language == language)

        if tag:
            query = query.filter(CodeSnippet.tags.ilike(f'%{tag}%'))

        return query.order_by(CodeSnippet.updated_at.desc()).all()

    def get_all_languages(self):
        """获取所有使用的编程语言"""
        return [lang[0] for lang in self.session.query(CodeSnippet.language).distinct()]

    def get_all_tags(self):
        """获取所有标签"""
        tags = set()
        for snippet in self.session.query(CodeSnippet.tags).all():
            if snippet[0]:
                tags.update(tag.strip() for tag in snippet[0].split(','))
        return sorted(tags)

    def export_snippets(self, snippet_ids, format='json'):
        """导出代码片段"""
        snippets = self.session.query(CodeSnippet).filter(CodeSnippet.id.in_(snippet_ids)).all()
        
        if format == 'json':
            return json.dumps([s.to_dict() for s in snippets], ensure_ascii=False, indent=2)
        elif format == 'markdown':
            return '\n\n---\n\n'.join(s.export_markdown() for s in snippets)
        else:
            raise ValueError(f'Unsupported export format: {format}')