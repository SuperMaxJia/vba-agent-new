import os
import re
from bs4 import BeautifulSoup
import html2text
from typing import List, Dict
import time

class HtmlToMarkdownConverter:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0  # 不限制行宽
        
    def convert_file(self, html_file: str) -> str:
        """将单个HTML文件转换为Markdown"""
        print(f"正在转换文件: {html_file}")
        
        try:
            # 读取HTML文件
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 删除目录结构
            for nav in soup.find_all(['nav', 'div'], class_=re.compile(r'(toc|nav|menu|sidebar|目录|导航)', re.I)):
                nav.decompose()
            
            # 删除可能的目录链接
            for link in soup.find_all('a', href=re.compile(r'(toc|nav|menu|sidebar|目录|导航)', re.I)):
                link.decompose()
            
            # 清理HTML
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 特别处理pre标签
            for pre in soup.find_all('pre'):
                # 获取代码语言
                code_class = pre.get('class', [''])[0]
                lang = code_class.replace('language-', '') if code_class else ''
                
                # 获取代码内容
                code = pre.get_text()
                
                # 创建新的pre标签，使用markdown格式
                new_pre = soup.new_tag('pre')
                new_pre.string = f"```{lang}\n{code}\n```"
                pre.replace_with(new_pre)
            
            # 转换为Markdown
            markdown = self.h2t.handle(str(soup))
            
            # 清理Markdown
            markdown = self._clean_markdown(markdown)
            
            # 找到开始和结束位置
            start_index = markdown.find("VBA使用帮助文档")
            if start_index != -1:
                # 从标题后的换行符开始
                start_index = markdown.find('\n', start_index)
                if start_index != -1:
                    start_index += 1  # 跳过换行符
                    
                    # 找到结束位置
                    end_index = markdown.find("北京经纬恒润股份有限公司")
                    if end_index != -1:
                        # 找到该行的开始位置（上一个换行符）
                        line_start = markdown.rfind('\n', 0, end_index)
                        if line_start != -1:
                            markdown = markdown[start_index:line_start].strip()
                        else:
                            markdown = markdown[start_index:end_index].strip()
                    else:
                        markdown = markdown[start_index:].strip()
                else:
                    markdown = ""
            else:
                markdown = ""
            
            return markdown
            
        except Exception as e:
            print(f"转换文件 {html_file} 时出错: {str(e)}")
            return ""
    
    def _clean_markdown(self, markdown: str) -> str:
        """清理Markdown文本"""
        # 移除多余的空行
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # 移除行首和行尾的空白字符
        markdown = '\n'.join(line.strip() for line in markdown.split('\n'))
        
        # 移除HTML注释
        markdown = re.sub(r'<!--.*?-->', '', markdown, flags=re.DOTALL)
        
        # 移除目录相关的文本
        markdown = re.sub(r'^.*?(目录|导航|TOC|Table of Contents).*?$', '', markdown, flags=re.MULTILINE | re.IGNORECASE)
        
        # 移除空行
        markdown = re.sub(r'\n\s*\n', '\n\n', markdown)
        
        return markdown
    
    def save_markdown(self, markdown: str, output_file: str):
        """保存Markdown文件"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
                
            print(f"已保存: {output_file}")
            
        except Exception as e:
            print(f"保存文件 {output_file} 时出错: {str(e)}")
    
    def process_directory(self):
        """处理整个目录"""
        print(f"\n开始处理目录: {self.input_dir}")
        print(f"输出目录: {self.output_dir}")
        
        total_files = 0
        processed_files = 0
        start_time = time.time()
        
        # 首先计算总文件数
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.html'):
                    total_files += 1
        
        print(f"找到 {total_files} 个HTML文件需要处理")
        
        # 处理文件
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.html'):
                    processed_files += 1
                    html_file = os.path.join(root, file)
                    
                    # 计算相对路径
                    rel_path = os.path.relpath(html_file, self.input_dir)
                    # 将.html扩展名改为.md
                    md_file = os.path.join(self.output_dir, rel_path[:-5] + '.md')
                    
                    print(f"\n处理进度: [{processed_files}/{total_files}] - {(processed_files/total_files)*100:.1f}%")
                    print(f"处理文件: {rel_path}")
                    
                    # 转换文件
                    markdown = self.convert_file(html_file)
                    if markdown:
                        self.save_markdown(markdown, md_file)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*50)
        print("转换完成！")
        print(f"总文件数: {total_files}")
        print(f"成功转换: {processed_files}")
        print(f"耗时: {duration:.2f}秒")
        print("="*50)

def main():
    # 配置输入输出目录
    input_dir = '/Users/cuisijia/source/DB/rule/original_document'
    output_dir = '/Users/cuisijia/source/DB/rule/markdown_document'
    
    # 创建转换器实例
    converter = HtmlToMarkdownConverter(input_dir, output_dir)
    
    # 开始转换
    converter.process_directory()

if __name__ == '__main__':
    main()
