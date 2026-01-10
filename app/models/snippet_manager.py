from typing import List, Optional
from dataclasses import dataclass
import json
import os

@dataclass
class CodeSnippet:
    title: str
    content: str
    language: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class SnippetManager:
    def __init__(self, storage_path: str = "snippets.json"):
        self.storage_path = storage_path
        self.snippets: List[CodeSnippet] = []
        self.load_snippets()

    def load_snippets(self):
        """从存储文件加载代码片段"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.snippets = [
                        CodeSnippet(**snippet) for snippet in data
                    ]
            except Exception as e:
                print(f"加载代码片段失败: {e}")
                self.snippets = []

    def save_snippets(self):
        """保存代码片段到存储文件"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([snippet.__dict__ for snippet in self.snippets],
                         f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存代码片段失败: {e}")
            return False

    def add_snippet(self, snippet: CodeSnippet) -> bool:
        """添加新的代码片段"""
        self.snippets.append(snippet)
        return self.save_snippets()

    def update_snippet(self, index: int, snippet: CodeSnippet) -> bool:
        """更新指定索引的代码片段"""
        if 0 <= index < len(self.snippets):
            self.snippets[index] = snippet
            return self.save_snippets()
        return False

    def delete_snippet(self, index: int) -> bool:
        """删除指定索引的代码片段"""
        if 0 <= index < len(self.snippets):
            self.snippets.pop(index)
            return self.save_snippets()
        return False

    def search_snippets(self, keyword: Optional[str] = None,
                       language: Optional[str] = None,
                       tag: Optional[str] = None) -> List[CodeSnippet]:
        """搜索代码片段
        
        Args:
            keyword: 搜索关键词，匹配标题、描述和内容
            language: 编程语言过滤
            tag: 标签过滤

        Returns:
            匹配的代码片段列表
        """
        results = self.snippets

        if keyword:
            keyword = keyword.lower()
            results = [
                snippet for snippet in results
                if keyword in snippet.title.lower()
                or (snippet.description and keyword in snippet.description.lower())
                or keyword in snippet.content.lower()
            ]

        if language:
            results = [
                snippet for snippet in results
                if snippet.language.lower() == language.lower()
            ]

        if tag:
            results = [
                snippet for snippet in results
                if snippet.tags and tag.lower() in [t.lower() for t in snippet.tags]
            ]

        return results

    def get_all_languages(self) -> List[str]:
        """获取所有使用的编程语言"""
        languages = set(snippet.language for snippet in self.snippets)
        return sorted(list(languages))

    def get_all_tags(self) -> List[str]:
        """获取所有使用的标签"""
        tags = set()
        for snippet in self.snippets:
            if snippet.tags:
                tags.update(snippet.tags)
        return sorted(list(tags))

    def export_snippet(self, index: int, file_path: str) -> bool:
        """导出指定代码片段到文件"""
        if 0 <= index < len(self.snippets):
            try:
                snippet = self.snippets[index]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(snippet.content)
                return True
            except Exception as e:
                print(f"导出代码片段失败: {e}")
        return False