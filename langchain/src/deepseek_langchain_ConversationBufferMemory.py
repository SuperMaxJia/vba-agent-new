from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from colorama import Fore, Style
import sys

class DeepSeekLangChainDemo:
    def __init__(self):
        """初始化DeepSeek LangChain演示"""
        # 初始化LLM
        self.llm = BaseChatOpenAI(
            model='deepseek-chat',
            openai_api_key='sk-15ece1d22cf2433fa0dd4fcc874b6154',
            openai_api_base='https://api.deepseek.com',
        )
        # max_tokens = 1024
        # 初始化对话记忆
        self.memory = ConversationBufferMemory()
        
        # 创建对话链
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=True
        )
        
        print(f"{Fore.CYAN}DeepSeek LangChain演示已启动{Style.RESET_ALL}")
        print(f"{Fore.CYAN}输入 'exit' 或 'quit' 退出对话{Style.RESET_ALL}")
        print(f"{Fore.CYAN}输入 'clear' 清除对话记忆{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    def get_response(self, user_input):
        """获取DeepSeek的响应"""
        try:
            # 显示等待提示
            print(f"\n{Fore.YELLOW}正在等待大模型响应，请稍候...{Style.RESET_ALL}")
            
            # 发送请求到DeepSeek
            response = self.conversation.predict(input=user_input)
            
            return response
            
        except Exception as e:
            print(f"{Fore.RED}错误：获取响应时发生错误 - {str(e)}{Style.RESET_ALL}")
            return None

    def display_response(self, content):
        """显示DeepSeek的响应"""
        if content:
            print(f"\n{Fore.GREEN}回答：{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{content}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    def clear_memory(self):
        """清除对话记忆"""
        self.memory.clear()
        print(f"{Fore.YELLOW}对话记忆已清除{Style.RESET_ALL}")

    def start_chat(self):
        """开始对话循环"""
        while True:
            try:
                # 获取用户输入
                user_input = input(f"{Fore.BLUE}请输入您的问题：{Style.RESET_ALL}").strip()
                
                # 检查是否退出
                if user_input.lower() in ['exit', 'quit']:
                    print(f"{Fore.CYAN}对话结束，感谢使用！{Style.RESET_ALL}")
                    break
                
                # 检查是否清除记忆
                if user_input.lower() == 'clear':
                    self.clear_memory()
                    continue
                
                # 获取并显示响应
                content = self.get_response(user_input)
                self.display_response(content)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.CYAN}对话已中断{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}错误：对话过程中发生错误 - {str(e)}{Style.RESET_ALL}")
                continue

    def run_examples(self):
        """运行示例对话"""
        examples = [
            "你好，请介绍一本书",
            "书中最精彩的部分是啥?",
            "这个部分对结局的影响有啥"
        ]
        
        print(f"\n{Fore.CYAN}开始运行示例对话...{Style.RESET_ALL}")
        for example in examples:
            print(f"\n{Fore.MAGENTA}示例问题：{example}{Style.RESET_ALL}")
            content = self.get_response(example)
            self.display_response(content)

def main():
    """主函数"""
    try:
        demo = DeepSeekLangChainDemo()
        
        # 运行示例对话
        demo.run_examples()
        
        # 开始交互式对话
        demo.start_chat()
        
    except Exception as e:
        print(f"{Fore.RED}错误：程序运行出错 - {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main() 