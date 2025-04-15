import os
import json
from openai import OpenAI
import re
from bs4 import BeautifulSoup
import time
import logging
import colorlog
from tqdm import tqdm

class VBARuleProcessor:
    def __init__(self):
        # 配置日志
        self._setup_logging()
        self.logger.info("初始化VBA规则处理器...")
        
        self.client = OpenAI(
            api_key="sk-15ece1d22cf2433fa0dd4fcc874b6154",
            base_url="https://api.deepseek.com"
        )
        self.model = 'deepseek-chat'
        self.output_dir = os.path.join(os.path.dirname(__file__), 'output', 'vba-rules-txt')
        self.input_dir = os.path.join(os.path.dirname(__file__), 'input')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.input_dir, exist_ok=True)
        self.logger.info(f"输入目录: {self.input_dir}")
        self.logger.info(f"输出目录: {self.output_dir}")

    def _setup_logging(self):
        """配置彩色日志系统"""
        self.logger = logging.getLogger('VBARuleProcessor')
        self.logger.setLevel(logging.INFO)
        
        # 如果已经有处理器，不重复添加
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 彩色格式化器
            color_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
            
            # 添加处理器
            self.logger.addHandler(console_handler)

    def process_file(self, file_path):
        """
        处理单个VBA文档文件
        
        Args:
            file_path (str): 文档文件路径
        """
        try:
            # 获取文件名（不含扩展名）作为函数名
            function_name = os.path.splitext(os.path.basename(file_path))[0]
            self.logger.info(f"开始处理文件: {os.path.basename(file_path)}")
            self.logger.info(f"提取的函数名: {function_name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.logger.info(f"读取到的HTML文件大小: {len(html_content)} 字节")
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取文本内容
            content = soup.get_text(separator='\n', strip=True)
            self.logger.info(f"提取的文本内容大小: {len(content)} 字符")
            
            # 构建系统提示
            system_prompt = """你是一个专业的VBA文档分析助手。请从输入内容中提取VBA函数或结构体的详细信息，包括：
            1. 函数名； 2. 函数描述； 3. 函数体； 4. 返回值； 5. 参数； 6. 内置函数； 7.示例
            8.其他和函数或变量强相关的内容，其中1、2、3、7必须要有，4、5、6详细看文件，尽可能提取出来
            请去除目录等与函数无关的信息，只保留函数相关的有效内容。
            
            返回格式：
            1. 函数名
            2. 函数描述
            3. 函数体（保留输入内容中关于函数题的全部描述信息）
            4. 返回值
            5. 参数（参数或者输出参数，多行用表给返回值，注意对其，列头为名称、类型、描述）
            6. 内置函数（多行用表给返回值，注意对其，列头为函数名称、函数描述，内置函数中涉及到的参数说明）
            7. 示例（包括示例功能、示例代码、代码注释）
            8. 其他和函数或变量强相关的内容
            
            
            请以自然语言格式返回结果，适合按行写入txt文件。"""

            # 打印发送给AI的数据大小
            self.logger.info(f"发送给AI的系统提示大小: {len(system_prompt)} 字符")
            self.logger.info(f"发送给AI的用户内容大小: {len(content)} 字符")

            self.logger.info(f"发送请求到AI模型 {self.model}...")
            start_time = time.time()
            
            # 发送请求到AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                stream=False
            )
            
            end_time = time.time()
            self.logger.info(f"AI响应时间: {end_time - start_time:.2f} 秒")
            
            # 获取AI返回的结果
            result = response.choices[0].message.content
            self.logger.info(f"AI返回结果大小: {len(result)} 字符")
            
            # 保存结果，传入原始文件路径以保留文件夹结构
            self._save_result(result, function_name, file_path)
            
        except Exception as e:
            self.logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _save_result(self, result, function_name, original_file_path):
        """
        保存处理结果到文件，保留原始文件夹结构
        
        Args:
            result (str): AI返回的处理结果
            function_name (str): 函数名
            original_file_path (str): 原始文件路径，用于保留文件夹结构
        """
        try:
            # 获取相对路径，保留原始文件夹结构
            rel_path = os.path.relpath(original_file_path, self.input_dir)
            rel_dir = os.path.dirname(rel_path)
            
            # 构建输出目录路径，保留原始文件夹结构
            output_subdir = os.path.join(self.output_dir, rel_dir)
            os.makedirs(output_subdir, exist_ok=True)
            
            # 构建输出文件路径
            output_file = os.path.join(output_subdir, f"{function_name}.txt")
            
            # 检查是否存在同名文件，如果存在则删除
            if os.path.exists(output_file):
                self.logger.info(f"发现同名文件，正在删除: {output_file}")
                try:
                    os.remove(output_file)
                    self.logger.debug(f"成功删除同名文件: {output_file}")
                except Exception as e:
                    self.logger.warning(f"无法删除同名文件 {output_file}: {str(e)}")
                    self.logger.info("将尝试覆盖该文件")
            
            # 写入文件
            self.logger.info(f"保存结果到文件: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                # 直接写入AI返回的自然语言结果
                f.write(result)
                
            self.logger.info(f"已成功保存函数 {function_name} 的规则到 {output_file}")
            
        except Exception as e:
            self.logger.error(f"保存结果时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def process_directory(self, directory=None):
        """
        处理指定目录下的所有HTML文件，包括子目录，跳过index.html文件
        
        Args:
            directory (str, optional): 要处理的目录路径，默认为input目录
        """
        if directory is None:
            directory = self.input_dir
            
        self.logger.info(f"开始处理目录: {directory}")
        
        # 统计信息
        total_files = 0
        processed_files = 0
        skipped_files = 0
        
        # 首先计算需要处理的文件总数
        html_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                total_files += 1
                if file.lower() == 'index.html':
                    skipped_files += 1
                elif file.endswith('.html'):
                    # 构建输出文件路径
                    function_name = os.path.splitext(file)[0]
                    rel_path = os.path.relpath(root, self.input_dir)
                    output_subdir = os.path.join(self.output_dir, rel_path)
                    output_file = os.path.join(output_subdir, f"{function_name}.txt")
                    
                    # 检查输出文件是否存在，但如果在TestChecks文件夹中则不跳过
                    if os.path.exists(output_file) and "TestChecks" not in root:
                        self.logger.info(f"跳过已存在的输出文件: {output_file}")
                        skipped_files += 1
                        continue
                    
                    html_files.append(os.path.join(root, file))
        
        # 使用tqdm创建进度条
        self.logger.info(f"找到 {len(html_files)} 个HTML文件需要处理")
        for file_path in tqdm(html_files, desc="处理HTML文件", unit="文件"):
            self.logger.debug(f"处理文件: {file_path}")
            self.process_file(file_path)
            processed_files += 1
        
        # 打印统计信息
        self.logger.info(f"处理完成: 共扫描 {total_files} 个文件，处理 {processed_files} 个文件，跳过 {skipped_files} 个文件")

def main():
    print("=" * 50)
    print("VBA规则处理器启动")
    print("=" * 50)
    
    processor = VBARuleProcessor()
    
    # 处理input目录下的所有HTML文件（包括子目录）
    processor.process_directory()
    
    print("\n" + "=" * 50)
    print("所有文件处理完成")
    print("=" * 50)

if __name__ == "__main__":
    main() 