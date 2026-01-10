from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Optional
import json

Base = declarative_base()

class Document(Base):
    """代码文档模型"""
    __tablename__ = 'documents'

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