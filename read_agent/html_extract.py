import os
import html2text
from bs4 import BeautifulSoup

class HTMLExtractor:
    def __init__(self):
        """初始化提取器"""
        self.default_dir = "/Users/cuisijia/Downloads/Hirain_PDF-2/html/html"  # 默认HTML文件夹路径
        self.h = html2text.HTML2Text()
        self.h.ignore_links = True
        self.h.ignore_images = True
        self.h.ignore_tables = False
        self.h.body_width = 0  # 不限制行宽
        
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
            
    def process_html_content(self, html_content: str) -> list:
        """
        处理HTML内容，提取文本并保持结构
        
        Args:
            html_content (str): HTML内容
            
        Returns:
            list: 处理后的内容列表
        """
        try:
            # 使用BeautifulSoup处理特定元素
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            headers = []
            for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = h.get_text().strip()
                if text:
                    headers.append(text)
            
            # 提取pre标签内容
            pre_contents = []
            for pre in soup.find_all('pre'):
                text = pre.get_text().strip()
                if text:
                    # 保持pre标签中的换行
                    pre_contents.extend(text.split('\n'))
            
            # 提取表格内容
            tables = []
            for table in soup.find_all('table'):
                # 处理表头
                thead = table.find('thead')
                if thead:
                    header_row = []
                    for th in thead.find_all('th'):
                        text = th.get_text().strip()
                        if text:
                            header_row.append(text)
                    if header_row:
                        tables.append('     '.join(header_row))
                
                # 处理表格内容
                tbody = table.find('tbody')
                if tbody:
                    for tr in tbody.find_all('tr'):
                        row = []
                        for td in tr.find_all('td'):
                            text = td.get_text().strip()
                            if text:
                                row.append(text)
                        if row:
                            tables.append('     '.join(row))
            
            # 使用html2text转换其他HTML内容
            # 移除pre标签，避免重复处理
            for pre in soup.find_all('pre'):
                pre.decompose()
            text_content = self.h.handle(str(soup))
            
            # 将转换后的文本按行分割
            lines = text_content.split('\n')
            
            # 合并所有内容
            content_lines = []
            
            # 添加标题
            content_lines.extend(headers)
            
            # 添加pre标签内容
            content_lines.extend(pre_contents)
            
            # 添加表格内容
            content_lines.extend(tables)
            
            # 添加其他文本内容
            for line in lines:
                line = line.strip()
                if line and line not in content_lines:  # 避免重复内容
                    content_lines.append(line)
            
            return content_lines
            
        except Exception as e:
            print(f"警告：处理HTML内容时出错: {str(e)}")
            return []
            
    def save_to_text(self, content: list, output_path: str):
        """
        保存内容到文本文件
        
        Args:
            content (list): 文本内容列表
            output_path (str): 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in content:
                    f.write(line + '\n')
            print(f"成功保存文本文件: {output_path}")
            
        except Exception as e:
            print(f"保存文本文件时出错: {str(e)}")
            
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
            
        # 创建txt子文件夹
        txt_dir = os.path.join(directory, 'txt')
        if not os.path.exists(txt_dir):
            try:
                os.makedirs(txt_dir)
                print(f"创建txt文件夹: {txt_dir}")
            except Exception as e:
                print(f"创建txt文件夹时出错: {str(e)}")
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
                    # 处理HTML内容
                    content_lines = self.process_html_content(html_content)
                    
                    if content_lines:
                        # 构建输出文件路径（在txt子文件夹中）
                        output_filename = os.path.splitext(filename)[0] + '.txt'
                        output_path = os.path.join(txt_dir, output_filename)
                        
                        # 如果txt文件已存在，则删除
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                                print(f"删除已存在的文件: {output_filename}")
                            except Exception as e:
                                print(f"删除文件 {output_filename} 时出错: {str(e)}")
                        
                        # 保存文本文件
                        self.save_to_text(content_lines, output_path)
                    else:
                        print(f"警告：文件 {filename} 没有可处理的内容")
                else:
                    print(f"警告：无法处理文件 {filename}")

def main():
    extractor = HTMLExtractor()
    default_dir = "/Users/cuisijia/Downloads/Hirain_PDF-2/html/html"
    
    print("欢迎使用HTML提取工具！")
    print(f"正在处理目录: {default_dir}")
    
    # 处理目录
    extractor.process_directory(default_dir)
    print("\n处理完成！")

if __name__ == "__main__":
    main() 