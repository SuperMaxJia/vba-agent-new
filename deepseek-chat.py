from openai import OpenAI
from colorama import Fore, Style
import sys

class DeepSeekChat:
    def __init__(self):
        """初始化DeepSeek聊天客户端"""
        self.client = OpenAI(
            api_key="sk-15ece1d22cf2433fa0dd4fcc874b6154",
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-reasoner"
        self.messages = []
        print(f"{Fore.CYAN}DeepSeek推理对话已启动{Style.RESET_ALL}")
        print(f"{Fore.CYAN}输入 'exit' 或 'quit' 退出对话{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    def get_response(self, user_input):
        """获取DeepSeek的响应"""
        try:
            # 添加用户输入到消息历史
            self.messages.append({"role": "user", "content": user_input})
            
            # 打印发送给大模型的内容
            print(f"\n{Fore.MAGENTA}发送给大模型的内容：{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
            for msg in self.messages:
                role = msg["role"]
                content = msg["content"]
                print(f"{Fore.MAGENTA}{role}: {content}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
            
            # 显示等待提示
            print(f"\n{Fore.YELLOW}正在等待大模型响应，请稍候...{Style.RESET_ALL}")
            
            # 发送请求到DeepSeek
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            
            # 获取推理内容和回答内容
            reasoning_content = response.choices[0].message.reasoning_content
            content = response.choices[0].message.content
            
            # 添加助手回答到消息历史
            self.messages.append({"role": "assistant", "content": content})
            
            return reasoning_content, content
            
        except Exception as e:
            print(f"{Fore.RED}错误：获取响应时发生错误 - {str(e)}{Style.RESET_ALL}")
            return None, None

    def display_response(self, reasoning_content, content):
        """显示DeepSeek的响应"""
        if reasoning_content:
            print(f"\n{Fore.YELLOW}推理过程：{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{reasoning_content}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")
        
        if content:
            print(f"\n{Fore.GREEN}回答：{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{content}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

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
                
                # 获取并显示响应
                reasoning_content, content = self.get_response(user_input)
                self.display_response(reasoning_content, content)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.CYAN}对话已中断{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}错误：对话过程中发生错误 - {str(e)}{Style.RESET_ALL}")
                continue

def main():
    """主函数"""
    try:
        chat = DeepSeekChat()
        chat.start_chat()
    except Exception as e:
        print(f"{Fore.RED}错误：程序运行出错 - {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main() 