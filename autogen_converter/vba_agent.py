from openai import OpenAI
import os
import json
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
"""
初版：支持转换
规则：txt 来自：html_extract
"""

class VBAAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-15ece1d22cf2433fa0dd4fcc874b6154",
            base_url="https://api.deepseek.com"
        )
        self.rules_dir = "/Users/cuisijia/Downloads/Hirain_PDF-2/html/html/txt"  # VBA 语法规则文件夹

    def read_pdf_content(self, pdf_path: str) -> str:
        """
        读取 PDF 文件内容

        Args:
            pdf_path (str): PDF 文件路径

        Returns:
            str: PDF 文件内容
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"警告：读取 PDF 文件 {pdf_path} 时出错: {str(e)}")
            return ""

    def read_html_content(self, html_path: str) -> str:
        """
        按行读取 HTML 文件内容

        Args:
            html_path (str): HTML 文件路径

        Returns:
            str: HTML 文件内容
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                # 按行读取HTML内容
                lines = f.readlines()

            # 使用BeautifulSoup解析HTML
            html_content = ''.join(lines)
            soup = BeautifulSoup(html_content, 'html.parser')

            # 提取所有文本内容，保持行结构
            text_content = []
            for line in soup.stripped_strings:
                text_content.append(line)

            return '\n'.join(text_content)
        except Exception as e:
            print(f"警告：读取 HTML 文件 {html_path} 时出错: {str(e)}")
            return ""

    def load_vba_rules(self):
        """加载 VBA 语法规则"""
        rules = {}
        if not os.path.exists(self.rules_dir):
            print(f"错误：规则文件夹不存在: {self.rules_dir}")
            return rules
        print(f"正在从文件夹 {self.rules_dir} 读取规则文件...")
        print("发现以下文件:")
        for item in os.listdir(self.rules_dir):
            print(f"- {item}")
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.pdf'):
                function_name = os.path.splitext(filename)[0]
                pdf_path = os.path.join(self.rules_dir, filename)
                pdf_content = self.read_pdf_content(pdf_path)

                if pdf_content:
                    rules[function_name] = pdf_content
                    print(f"成功读取 {filename} 的内容")
                else:
                    rules[function_name] = f"无法读取 {filename} 的内容"
            elif filename.endswith('.html'):
                function_name = os.path.splitext(filename)[0]
                html_path = os.path.join(self.rules_dir, filename)
                html_content = self.read_html_content(html_path)

                if html_content:
                    rules[function_name] = html_content
                    print(f"成功读取 {filename} 的内容")
                    print(html_content)
                else:
                    rules[function_name] = f"无法读取 {filename} 的内容"
            elif filename.endswith('.txt'):
                function_name = os.path.splitext(filename)[0]
                txt_path = os.path.join(self.rules_dir, filename)
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        txt_content = f.read()
                    if txt_content:
                        rules[function_name] = txt_content
                        print(f"成功读取 {filename} 的内容")
                    else:
                        rules[function_name] = f"无法读取 {filename} 的内容"
                except Exception as e:
                    print(f"警告：读取 TXT 文件 {filename} 时出错: {str(e)}")
                    rules[function_name] = f"无法读取 {filename} 的内容"
            else:
                print(f"发现非 PDF、HTML 或 TXT 文件: {filename}")

        if not rules:
            print(f"警告：在 {self.rules_dir} 中没有找到 PDF、HTML 或 TXT 文件")
        else:
            print(f"已加载 {len(rules)} 个 VBA 语法规则")

        return rules

    def convert_capl_to_vba(self, capl_file_path: str) -> str:
        """
        将 Capl 代码转换为 VBA 代码

        Args:
            capl_file_path (str): Capl 文件路径

        Returns:
            str: 转换后的 VBA 代码
        """
        try:
            # 读取 Capl 文件内容
            with open(capl_file_path, 'r', encoding='utf-8') as f:
                capl_code = f.read()

            # 加载 VBA 语法规则
            vba_rules = self.load_vba_rules()

            # 构建系统提示
            system_prompt = """你是一个专业的代码转换助手。请按照以下步骤将 Capl 代码转换为 Python-VBA库 代码，Python-VBA库是基于python定义的一套自定义语言，其中自定义了很多库：

            步骤1：函数和变量定义转换
            - 将 Capl 的 Sub/End Sub 转换为 Python 的 def 函数定义
            - 将 VBA 的 Dim 变量声明转换为 Python 的变量赋值
            - 保持代码结构清晰

            步骤2：类型定义转换
            - 将 Capl 的message 转换为 Python-VBA 的 CANMessage 类型定义
            # - 将 Set 语句转换为直接赋值
            - 确保类型转换的准确性

            步骤3：函数转换
            - msTimer 函数转换为sendPeriodMsg 周期函数发送
            - setTimer 函数，使用 `sendPeriodMsg` 替代定时器功能
            - output 函数转换为 sendMsg
            - on start 转换为 onStartEvent
            - on key 转换为 onKeyEvent
            - write 转换为 writeInfo
            - this.Byte(0) 使用 `getData()[0]` 替代
            - 函数的语法详细定义在文档中查找，参照示例修改
            - 函数的参数不明确时，添加注释说明，并作为风险提示

            步骤4：语法修改
            - 使用 Python 的语法特性
            - 注释使用 # 而不是 '
            - 数组使用 [] 而不是 Array()
            - 移除所有 VBA 特有的语法（如 Set, Dim 等）
            - 使用 Python 的命名规范（下划线命名法）

            步骤5：缺失部分检查
            - 检查转换过程中可能缺失的部分
            - 列出所有缺失的函数或变量
            - 提供缺失部分的替代方案

            转换规则：
            1. 保持代码逻辑不变
            2. 严格遵循 Python-VBA 语法规范（即规则中定义的形式，规则中给出的函数及结构体已经定义，无需再次声明）
            3. 添加必要的错误处理
            4. 添加清晰的注释
            5. 遵循以下 Python 语法规则：
               - 使用 def 定义函数
               - 使用 # 作为注释
               - 使用 [] 定义数组
               - 使用直接赋值而不是 Set
               - 使用下划线命名法
               
            """

            # 添加 VBA 语法规则
            for func_name, rule in vba_rules.items():
                system_prompt += f"\n{func_name}: {rule}"

            # 添加用户提示
            user_prompt = f"""请将以下 Capl 代码转换为 Python 代码，并按照上述步骤进行转换。
            特别注意：
            1. 使用 def 而不是 Sub/End Sub
            2. 使用直接赋值而不是 Set
            3. 使用 # 作为注释
            4. 使用 [] 而不是 Array()
            5. 移除所有 CAPL 特有的语法
            6. 注释掉不支持的属性和方法 并标注
            7. 变量命名以python习惯为准

            Capl 代码：
            {capl_code}

            请按照以下格式输出：
            
            1. 缺失部分检查结果：
            [缺失部分检查结果]

            最终代码：
            [完整的转换后代码]
            """

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"转换代码时出现错误: {str(e)}"

class CAPLConverter:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-15ece1d22cf2433fa0dd4fcc874b6154",
            base_url="https://api.deepseek.com"
        )

    def read_html_content(self, html_path: str) -> str:
        """
        读取 HTML 文件内容
        
        Args:
            html_path (str): HTML 文件路径
            
        Returns:
            str: HTML 文件内容
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取所有文本内容
            text_content = soup.get_text(separator='\n', strip=True)
            return text_content.strip()
        except Exception as e:
            print(f"警告：读取 HTML 文件 {html_path} 时出错: {str(e)}")
            return ""
        
    def load_capl_rules(self):
        """加载 VBA 语法规则"""
        rules = {}
        if not os.path.exists(self.rules_dir):
            print(f"错误：规则文件夹不存在: {self.rules_dir}")
            return rules
        print(f"正在从文件夹 {self.rules_dir} 读取规则文件...")
        print("发现以下文件:")
        for item in os.listdir(self.rules_dir):
            print(f"- {item}")
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.html'):
                function_name = os.path.splitext(filename)[0]
                html_path = os.path.join(self.rules_dir, filename)
                html_content = self.read_html_content(html_path)
                
                if html_content:
                    rules[function_name] = html_content
                    print(f"成功读取 {filename} 的内容")
                else:
                    rules[function_name] = f"无法读取 {filename} 的内容"
            else:
                print(f"发现非 HTML 文件: {filename}")
            
        if not rules:
            print(f"警告：在 {self.rules_dir} 中没有找到 HTML 文件")
        else:
            print(f"已加载 {len(rules)} 个 VBA 语法规则")
                
        return rules
        
    def convert_capl_to_python(self, capl_file_path: str) -> str:
        """
        将 CAPL 代码转换为 Python 代码
        
        Args:
            capl_file_path (str): CAPL 文件路径
            
        Returns:
            str: 转换后的 Python 代码
        """
        try:
            # 读取 CAPL 文件内容
            with open(capl_file_path, 'r', encoding='utf-8') as f:
                capl_code = f.read()
                
            # 加载 CAPL 语法规则
            capl_rules = self.load_capl_rules()
            
            # 构建系统提示
            system_prompt = """你是一个专业的代码转换助手。请按照以下步骤将 CAPL 代码转换为 Python 代码：

            步骤1：函数和变量定义转换
            - 将 CAPL 的函数定义转换为 Python 的 def 函数定义
            - 将 CAPL 的变量声明转换为 Python 的变量赋值
            - 保持代码结构清晰

            步骤2：类型定义转换
            - 将 CAPL 的 message 类型转换为 Python 的类定义
            - 将 CAPL 的数据类型转换为对应的 Python 类型
            - 确保类型转换的准确性

            步骤3：函数转换
            - 定时器函数转换为周期函数发送
            - output 函数转换为 sendMsg
            - on start 转换为 onStartEvent
            - on key 转换为 onKeyEvent
            - write 转换为 writeInfo
            - 函数的详细定义在文档中查找

            步骤4：语法修改
            - 使用 Python 的语法特性
            - 注释使用 # 而不是 //
            - 数组使用 [] 而不是 Array()
            - 移除所有 CAPL 特有的语法
            - 使用 Python 的命名规范（下划线命名法）

            步骤5：缺失部分检查
            - 检查转换过程中可能缺失的部分
            - 列出所有缺失的函数或变量
            - 提供缺失部分的替代方案

            转换规则：
            1. 保持代码逻辑不变
            2. 严格遵循 Python 语法规范
            3. 添加必要的错误处理
            4. 添加清晰的注释
            5. 遵循以下 Python 语法规则：
               - 使用 def 定义函数
               - 使用 # 作为注释
               - 使用 [] 定义数组
               - 使用 Python 的命名规范
               - 移除所有 CAPL 特有的语法
            """
            
            # 添加 CAPL 语法规则
            for func_name, rule in capl_rules.items():
                system_prompt += f"\n{func_name}: {rule}"
            
            # 添加用户提示
            user_prompt = f"""请将以下 CAPL 代码转换为 Python 代码，并按照上述步骤进行转换。
            特别注意：
            1. 使用 def 定义函数
            2. 使用 # 作为注释
            3. 使用 [] 定义数组
            4. 使用 Python 的命名规范
            5. 移除所有 CAPL 特有的语法

            CAPL 代码：
            {capl_code}

            请按照以下格式输出：
            
            1. 缺失部分检查结果：
            [缺失部分检查结果]

            最终代码：
            [完整的转换后代码]
            """
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"转换代码时出现错误: {str(e)}"

def main():
    agent = VBAAgent()
    converter = CAPLConverter()
    default_file = "/Users/cuisijia/Downloads/Hirain_PDF/capl.txt"
    
    print("欢迎使用 Capl 到 VBA 的代码转换助手！输入'q'退出。")
    while True:
        file_path = input(f"\n请输入要转换的 Capl 文件路径 (直接回车使用默认路径 {default_file}): ").strip()
        if file_path.lower() == 'q':
            break
            
        if not file_path:  # 如果用户直接回车，使用默认路径
            file_path = default_file
            
        if not os.path.exists(file_path):
            print(f"错误：文件不存在！")
            continue
            
        # 转换代码
        code = agent.convert_capl_to_vba(file_path)
        
        # 生成输出文件路径
        output_file = os.path.splitext(file_path)[0] + '.py'

        # 保存转换后的代码到文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"\n转换结果已保存到: {output_file}")
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")
            
        print(f"\n转换结果:\n{code}")

if __name__ == "__main__":
    main() 