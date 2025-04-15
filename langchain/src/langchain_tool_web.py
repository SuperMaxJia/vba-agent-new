import os
import sys
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, OpenAIFunctionsAgent
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from colorama import Fore, Style

class WebResearchAgent:
    """网页研究代理"""

    def __init__(self):
        """初始化代理"""
        # 初始化OpenAI模型
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",  # 指定使用GPT-3.5-turbo模型
            temperature=0,
            api_key="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"  # 直接设置API key
        )

        # 创建系统消息
        self.system_message = SystemMessage(
            content="你是一个网页研究员，通过查找互联网上的信息并检索有用文档的内容来回答用户问题。请引用你的信息来源。"
        )

        # 创建工具
        self.tools = [
            self.search_and_contents,
            self.find_similar_and_contents
        ]

        # 创建代理
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )

    @tool
    def search_and_contents(self, query: str) -> List[Dict[str, Any]]:
        """根据查询搜索网页并检索其内容"""
        print(f"{Fore.CYAN}正在搜索: {query}{Style.RESET_ALL}")
        # 这里暂时返回模拟数据
        return [{
            "title": "示例搜索结果",
            "url": "https://example.com",
            "content": "这是一个示例搜索结果的内容。"
        }]

    @tool
    def find_similar_and_contents(self, url: str) -> List[Dict[str, Any]]:
        """搜索与给定URL相似的网页并检索其内容"""
        print(f"{Fore.CYAN}正在查找与 {url} 相似的页面...{Style.RESET_ALL}")
        # 这里暂时返回模拟数据
        return [{
            "title": "相似页面示例",
            "url": "https://example.com/similar",
            "content": "这是一个相似页面的示例内容。"
        }]

    def _create_agent(self) -> OpenAIFunctionsAgent:
        """创建OpenAI函数代理"""
        agent_prompt = OpenAIFunctionsAgent.create_prompt(self.system_message)
        return OpenAIFunctionsAgent(
            llm=self.llm,
            tools=self.tools,
            prompt=agent_prompt
        )

    def research(self, query: str) -> str:
        """执行研究查询

        Args:
            query: 研究查询

        Returns:
            str: 研究结果
        """
        try:
            print(f"{Fore.GREEN}开始研究查询: {query}{Style.RESET_ALL}")
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"研究过程中出错: {str(e)}"

def main():
    """主函数"""
    try:
        # 创建代理
        agent = WebResearchAgent()

        # 示例查询
        queries = [
            "为我总结一篇关于猫的有趣文章",
            "查找关于人工智能最新发展的文章",
            "搜索关于Python编程的最佳实践"
        ]
        
        # 执行查询
        for query in queries:
            print(f"\n{Fore.YELLOW}查询: {query}{Style.RESET_ALL}")
            result = agent.research(query)
            print(f"\n{Fore.GREEN}结果:{Style.RESET_ALL}\n{result}")
            
    except Exception as e:
        print(f"{Fore.RED}错误: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
