from typing import Optional

class ConversationData:
    """对话数据管理类"""
    def __init__(self):
        self.capl_code = ""
        self.preprocess_section = ""
        self.code_snippets = []
        self.processing_queue = []
        self.converted_snippets = []
        
    def get_snippet(self) -> Optional[str]:
        """获取下一个要处理的代码片段"""
        if self.processing_queue:
            return self.processing_queue.pop(0)
        return None
        
    def add_snippet(self, snippet: str) -> None:
        """添加代码片段到处理队列"""
        self.processing_queue.append(snippet)
        
    def has_remaining_snippets(self) -> bool:
        """检查是否还有未处理的代码片段"""
        return len(self.processing_queue) > 0
        
    def clear(self) -> None:
        """清空所有数据"""
        self.capl_code = ""
        self.preprocess_section = ""
        self.code_snippets = []
        self.processing_queue = []
        self.converted_snippets = [] 