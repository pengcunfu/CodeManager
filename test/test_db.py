__import__("__init__")

if __name__ == '__main__':
    from app.common.db import session, add_document

    add_document("def main", "python", "这是一段Python代码")
