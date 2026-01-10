from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# 创建 SQLite 数据库连接
DATABASE_URL = "sqlite:///data\\data.db"
engine = create_engine(DATABASE_URL, echo=True)

# 创建 ORM 基类
Base = declarative_base()


# 定义数据库表（模型）
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)  # ID
    code = Column(Text, nullable=False)  # 代码
    language = Column(String(50), nullable=False)  # 语言
    tag = Column(String(50), nullable=False)  # 标签


# 创建表
Base.metadata.create_all(engine)

# 创建会话
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()


# 插入数据
def add_document(code: str, language: str, tag: str):
    document = Document(code=code, language=language, tag=tag)
    session.add(document)
    session.commit()


# 查询数据
def get_documents():
    documents = session.query(Document).all()
    return documents


# 查询包含文件内容
def get_documents_by_content(content):
    documents = session.query(Document).filter(Document.code.contains(content)).all()
    return documents


# 更新数据
def update_document(document_id, code, language, tag):
    user = session.query(Document).filter(Document.id == document_id).first()
    if user:
        user.code = code
        user.language = language
        user.tag = tag
        session.commit()


# 删除数据
def delete_document(document_id):
    document = session.query(Document).filter(Document.id == document_id).first()
    if document:
        session.delete(document)
        session.commit()
