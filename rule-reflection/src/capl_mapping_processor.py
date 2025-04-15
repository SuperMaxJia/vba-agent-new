#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from colorama import init, Fore, Style

# 初始化colorama
init()

class CaplMappingProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-15ece1d22cf2433fa0dd4fcc874b6154",
            base_url="https://api.deepseek.com"
        )
        self.model = 'deepseek-chat'  # 将model参数单独设置
        self.input_dir = Path("../../rules/output/vba-rules-txt")
        self.output_dir = Path("../output/reflection")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # # 清理output目录中的所有文件
        # print(f"{Fore.CYAN}开始清理输出目录：{self.output_dir}{Style.RESET_ALL}")
        # try:
        #     # 删除所有文件
        #     for file in self.output_dir.glob("*"):
        #         if file.is_file():
        #             file.unlink()
        #             print(f"{Fore.YELLOW}已删除文件：{file.name}{Style.RESET_ALL}")
        #     print(f"{Fore.GREEN}输出目录清理完成{Style.RESET_ALL}")
        # except Exception as e:
        #     print(f"{Fore.RED}警告：清理输出目录时发生错误 - {str(e)}{Style.RESET_ALL}")

    def read_vba_file(self, filename):
        """读取VBA规则文件"""
        try:
            # 使用绝对路径
            file_path = Path(filename)
            print(f"{Fore.CYAN}正在读取文件：{file_path}{Style.RESET_ALL}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"{Fore.GREEN}文件读取成功{Style.RESET_ALL}")
            return content
        except Exception as e:
            print(f"{Fore.RED}错误：无法读取文件 {filename} - {str(e)}{Style.RESET_ALL}")
            return None

    def analyze_with_ai(self, content, function_name):
        """使用AI分析内容并生成映射规则"""
        prompt = f"""请作为CAPL和Python-VBA语法映射专家，分析以下Python-VBA函数，并在CAPL语法中找到最准确的对应关系。

函数名：{function_name}

VBA函数定义：
{content}

请按照以下格式返回分析结果（每个部分内部不要有空行，部分之间用空行分隔）：

##功能##
[详细描述该函数的具体功能和用途，包括其在实际应用中的场景]

##vba规范##
[详细说明Python-VBA中的函数定义、参数类型、返回值类型等，涵盖入参的全部内容]


##capl规范##
[详细说明CAPL中的对应函数定义、参数类型、返回值类型，并提供至少2个完整的使用示例]

##capl名##
[参考##capl规范##中给出的函数定义仅给出一个最准确的CAPL对应名称，必须是英文单词，必须保证原本的大小写，若多个单词保留空格，若没有返回为：！！！]


##转换须知##
[列出从CAPL转换到VBA时需要注意的所有重要事项，包括：
1. 参数类型和数量的差异
2. 返回值类型的差异
3. 函数行为的差异
4. 特殊情况的处理方法]

##转换示例##
[提供一个完整的转换示例，展示如何将CAPL代码转换为等效的VBA代码，包括：
1. CAPL原始代码
2. 转换后的VBA代码
3. 关键转换步骤的说明]
"""
        try:
            print(f"{Fore.CYAN}正在进行AI分析...{Style.RESET_ALL}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的CAPL和Python-VBA语法映射专家。请确保返回的capl名部分只包含一个英文单词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            print(f"{Fore.GREEN}AI分析完成{Style.RESET_ALL}")
            return result
        except Exception as e:
            print(f"{Fore.RED}错误：AI分析失败 - {str(e)}{Style.RESET_ALL}")
            return None

    def extract_capl_name(self, analysis):
        """从分析结果中提取CAPL名称"""
        try:
            lines = analysis.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == '##capl名##':
                    if i + 1 < len(lines):
                        capl_name = lines[i + 1].strip()
                        print(f"{Fore.GREEN}提取的CAPL名称：{capl_name}{Style.RESET_ALL}")
                        return capl_name
            print(f"{Fore.RED}错误：未找到CAPL名称部分{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}错误：无法从分析结果中提取CAPL名称 - {str(e)}{Style.RESET_ALL}")
            return None

    def save_mapping(self, content, capl_name, vba_name, relative_path):
        """保存映射规则到文件，保持原始文件夹结构"""
        try:
            # 创建对应的输出目录结构
            output_subdir = self.output_dir / relative_path.parent
            output_subdir.mkdir(parents=True, exist_ok=True)
            
            # 构建输出文件路径
            output_file = output_subdir / f"{capl_name}-{vba_name}.txt"
            print(f"{Fore.CYAN}正在保存映射规则到：{output_file}{Style.RESET_ALL}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"{Fore.GREEN}映射规则保存成功{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}错误：无法保存映射规则 - {str(e)}{Style.RESET_ALL}")

    def process_all_files(self, input_dir: str, output_dir: str) -> None:
        """处理指定目录下的所有文件
        
        Args:
            input_dir: 输入目录路径
            output_dir: 输出目录路径
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取输出目录中的所有文件
        output_files = set()
        for root, _, files in os.walk(output_dir):
            for file in files:
                if '-' in file and file.endswith('.txt'):
                    # 获取"-"后面的部分，并去掉.txt后缀
                    match_str = file.split('-', 1)[1].rsplit('.', 1)[0]
                    output_files.add(match_str)
        
        # 处理输入目录中的所有文件
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.txt'):
                    input_file_path = os.path.join(root, file)
                    # 获取不带扩展名的文件名
                    file_name_without_ext = os.path.splitext(file)[0]
                    
                    # 检查是否需要跳过
                    if file_name_without_ext.lower().startswith('demo'):
                        print(f"{Fore.YELLOW}跳过文件 {input_file_path}，因为文件名以demo开头{Style.RESET_ALL}")
                        continue
                    if file_name_without_ext in output_files:
                        print(f"{Fore.YELLOW}跳过文件 {input_file_path}，因为已存在对应的输出文件{Style.RESET_ALL}")
                        continue
                    
                    try:
                        # 读取文件内容
                        content = self.read_vba_file(input_file_path)
                        if not content:
                            continue
                            
                        # 分析内容
                        analysis = self.analyze_with_ai(content, file_name_without_ext)
                        if not analysis:
                            continue
                            
                        # 提取CAPL名称
                        capl_name = self.extract_capl_name(analysis)
                        if not capl_name:
                            continue
                            
                        # 保存映射规则
                        self.save_mapping(analysis, capl_name, file_name_without_ext, Path(input_file_path).relative_to(input_dir))
                        
                    except Exception as e:
                        print(f"{Fore.RED}处理文件 {input_file_path} 时出错: {str(e)}{Style.RESET_ALL}")
                        continue

def main():
    """主函数"""
    print(f"{Fore.CYAN}开始运行CAPL映射处理器...{Style.RESET_ALL}")
    processor = CaplMappingProcessor()
    # 使用类中定义的目录路径
    processor.process_all_files(str(processor.input_dir), str(processor.output_dir))

if __name__ == "__main__":
    main() 