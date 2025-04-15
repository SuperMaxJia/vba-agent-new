import os
from bs4 import BeautifulSoup
from openai import OpenAI

class HTMLOptimizer:
    def __init__(self):
        """初始化HTML优化器"""
        self.default_dir = "/Users/cuisijia/Downloads/Hirain_PDF-2/html/html"  # 默认HTML文件夹路径
        self.client = OpenAI(
            api_key="sk-15ece1d22cf2433fa0dd4fcc874b6154",
            base_url="https://api.deepseek.com"
        )
        
    def read_html_file(self, html_path: str) -> str:
        """
        读取HTML文件内容
        
        Args:
            html_path (str): HTML文件路径
            
        Returns:
            str: HTML文件内容
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"警告：读取HTML文件 {html_path} 时出错: {str(e)}")
            return ""
            
    def optimize_html(self, html_content: str) -> str:
        """
        使用DeepSeek优化HTML代码
        
        Args:
            html_content (str): 原始HTML内容
            
        Returns:
            str: 优化后的HTML内容
        """
        try:
            # 使用OpenAI客户端发送请求
            response = self.client.chat.completions.create(
                model="deepseek-coder",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个HTML代码优化专家。请优化以下HTML代码，使其更加规范、简洁和高效。保持原有的功能和结构，但改进代码质量和可读性。"
                    },
                    {
                        "role": "user",
                        "content": html_content
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # 获取优化后的HTML内容
            optimized_html = response.choices[0].message.content
            
            return optimized_html
            
        except Exception as e:
            print(f"警告：优化HTML代码时出错: {str(e)}")
            return html_content
            
    def save_optimized_html(self, html_content: str, output_path: str):
        """
        保存优化后的HTML文件
        
        Args:
            html_content (str): 优化后的HTML内容
            output_path (str): 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"成功保存优化后的HTML文件: {output_path}")
        except Exception as e:
            print(f"保存优化后的HTML文件时出错: {str(e)}")
            
    def process_directory(self, input_dir: str = None):
        """
        处理指定目录下的所有HTML文件
        
        Args:
            input_dir (str): 输入目录路径，如果为None则使用默认路径
        """
        # 使用默认目录或用户指定的目录
        directory = input_dir if input_dir else self.default_dir
        
        if not os.path.exists(directory):
            print(f"错误：目录不存在: {directory}")
            return
            
        print(f"正在处理目录: {directory}")
        print("发现以下文件:")
        
        # 遍历目录下的所有文件
        for filename in os.listdir(directory):
            if filename.endswith('.html'):
                print(f"- {filename}")
                
                # 构建完整的文件路径
                html_path = os.path.join(directory, filename)
                
                # 读取HTML内容
                html_content = self.read_html_file(html_path)
                
                if html_content:
                    # 优化HTML代码
                    optimized_html = self.optimize_html(html_content)
                    
                    # 构建输出文件路径
                    output_filename = f"optimized_{filename}"
                    output_path = os.path.join(directory, output_filename)
                    
                    # 保存优化后的HTML文件
                    self.save_optimized_html(optimized_html, output_path)
                else:
                    print(f"警告：无法处理文件 {filename}")

def main():
    optimizer = HTMLOptimizer()
    default_dir = "/Users/cuisijia/Downloads/Hirain_PDF-2/html/html"
    
    print("欢迎使用HTML代码优化工具！")
    print(f"正在处理目录: {default_dir}")
    
    # 处理目录
    optimizer.process_directory(default_dir)
    print("\n处理完成！")

if __name__ == "__main__":
    main() 