#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from tqdm import tqdm
from colorama import init, Fore, Style

# 初始化colorama
init()

class MissingFunctionProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-15ece1d22cf2433fa0dd4fcc874b6154",
            base_url="https://api.deepseek.com"
        )
        self.model = 'deepseek-chat'
        self.reflection_dir = Path("../../rule-reflection/output/reflection")
        self.output_dir = Path("../output/missing")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_existing_functions(self):
        """获取已存在的CAPL函数列表"""
        try:
            print(f"{Fore.CYAN}正在读取已存在的函数映射...{Style.RESET_ALL}")
            existing_functions = []
            
            # 遍历reflection目录下的所有txt文件
            for file_path in self.reflection_dir.glob("*.txt"):
                # 从文件名中提取CAPL函数名（-前面的部分）
                capl_name = file_path.stem.split("-")[0]
                existing_functions.append(capl_name)
            
            print(f"{Fore.GREEN}找到 {len(existing_functions)} 个已存在的函数映射{Style.RESET_ALL}")
            return existing_functions
        except Exception as e:
            print(f"{Fore.RED}错误：读取已存在函数失败 - {str(e)}{Style.RESET_ALL}")
            return []

    def analyze_missing_functions(self, existing_functions):
        """使用AI分析缺少的函数"""
        prompt = f"""CANOE公司的CAPL语法定义的函数和结构体中，除了以下已识别到的函数外，还有哪些？请保证全面性：

已存在的函数：
{', '.join(existing_functions)}

请列出所有Capl中定义了，但是未识别到的的函数和结构体。"""
        
        try:
            print(f"{Fore.CYAN}正在进行AI分析...{Style.RESET_ALL}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的CAPL语法专家，请全面分析并列出缺少的函数和结构体。"},
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

    def save_missing_functions(self, content):
        """保存缺少的函数列表"""
        try:
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"{timestamp}_missing.txt"
            
            print(f"{Fore.CYAN}正在保存缺少的函数列表到：{output_file}{Style.RESET_ALL}")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"{Fore.GREEN}缺少的函数列表保存成功{Style.RESET_ALL}")
            return output_file
        except Exception as e:
            print(f"{Fore.RED}错误：保存文件失败 - {str(e)}{Style.RESET_ALL}")
            return None

    def process(self):
        """处理主函数"""
        try:
            # 获取已存在的函数列表
            existing_functions = self.get_existing_functions()
            if not existing_functions:
                print(f"{Fore.RED}错误：未找到已存在的函数映射{Style.RESET_ALL}")
                return
            
            # AI分析缺少的函数
            missing_functions = self.analyze_missing_functions(existing_functions)
            if not missing_functions:
                print(f"{Fore.RED}错误：AI分析失败{Style.RESET_ALL}")
                return
            
            # 保存结果
            output_file = self.save_missing_functions(missing_functions)
            if output_file:
                print(f"\n{Fore.GREEN}处理完成！结果已保存到：{output_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}错误：处理过程中发生错误 - {str(e)}{Style.RESET_ALL}")

def main():
    print(f"{Fore.CYAN}开始运行函数映射查漏处理器...{Style.RESET_ALL}")
    processor = MissingFunctionProcessor()
    processor.process()

if __name__ == "__main__":
    main() 