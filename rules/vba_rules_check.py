import os
import json
import re
import logging
import colorlog
from tqdm import tqdm

class VBARulesChecker:
    def __init__(self):
        # 配置日志
        self._setup_logging()
        self.logger.info("初始化VBA规则检查器...")
        
        # 设置输入输出目录
        self.output_dir = os.path.join(os.path.dirname(__file__), 'output', 'vba-rules-txt')
        self.input_dir = os.path.join(os.path.dirname(__file__), 'input')
        self.check_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'vba_rules_check')
        os.makedirs(self.check_output_dir, exist_ok=True)
        
        self.logger.info(f"输入目录: {self.input_dir}")
        self.logger.info(f"输出目录: {self.output_dir}")
        self.logger.info(f"检查结果输出目录: {self.check_output_dir}")
        
        # 存储检查失败的文件
        self.failed_files = []

    def _setup_logging(self):
        """配置彩色日志系统"""
        self.logger = logging.getLogger('VBARulesChecker')
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

    def check_file(self, file_path):
        """
        检查单个输出文件的内容是否符合要求
        
        Args:
            file_path (str): 输出文件路径
            
        Returns:
            bool: 检查是否通过
        """
        try:
            self.logger.info(f"检查文件: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查必要字段是否存在
            required_fields = ['函数名', '函数描述', '函数体', '示例']
            missing_fields = []
            
            # 定义无效内容的关键词
            invalid_keywords = ['未明确说明', '无', '无返回值', '无参数', '无示例']
            
            for field in required_fields:
                # 使用正则表达式查找字段，允许字段名后面跟着冒号或其他分隔符
                pattern = f"{field}[：:].*?(?=\n\n|\n[A-Za-z]|\Z)"
                match = re.search(pattern, content, re.DOTALL)
                
                if not match:
                    missing_fields.append(field)
                    continue
                
                # 提取字段内容
                field_content = match.group(0).split(':', 1)[1].strip() if ':' in match.group(0) else match.group(0).split('：', 1)[1].strip()
                
                # 检查字段内容是否为空（只包含空格）
                if not field_content or field_content.isspace():
                    missing_fields.append(field)
                    continue
                
                # 检查字段内容是否包含无效关键词
                for keyword in invalid_keywords:
                    if keyword in field_content:
                        missing_fields.append(f"{field}(包含无效内容: {keyword})")
                        break
            
            # 如果有缺失字段，则检查失败
            if missing_fields:
                self.logger.error(f"文件 {file_path} 检查失败，缺失字段: {', '.join(missing_fields)}")
                
                # 打印文件内容
                self.logger.info(f"文件内容:\n{content}")
                
                # 询问是否跳过
                user_input = input(f"文件 {file_path} 检查失败，是否跳过? (y/n): ").strip().lower()
                if user_input == 'y':
                    self.logger.info(f"用户选择跳过文件: {file_path}")
                    return True
                else:
                    self.logger.info(f"用户选择不跳过文件: {file_path}")
                    # 将失败的文件添加到列表中
                    self.failed_files.append(file_path)
                    return False
            
            self.logger.info(f"文件 {file_path} 检查通过")
            return True
            
        except Exception as e:
            self.logger.error(f"检查文件 {file_path} 时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def check_directory(self, directory=None):
        """
        检查指定目录下的所有输出文件
        
        Args:
            directory (str, optional): 要检查的目录路径，默认为input目录
        """
        if directory is None:
            directory = self.input_dir
            
        self.logger.info(f"开始检查目录: {directory}")
        
        # 统计信息
        total_files = 0
        checked_files = 0
        passed_files = 0
        failed_files = 0
        skipped_files = 0
        
        # 首先计算需要检查的文件总数
        html_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() == 'index.html':
                    continue
                    
                if file.endswith('.html'):
                    # 构建输出文件路径
                    function_name = os.path.splitext(file)[0]
                    rel_path = os.path.relpath(root, self.input_dir)
                    output_subdir = os.path.join(self.output_dir, rel_path)
                    output_file = os.path.join(output_subdir, f"{function_name}.txt")
                    
                    # 检查输出文件是否存在
                    if not os.path.exists(output_file):
                        self.logger.info(f"跳过不存在的输出文件: {output_file}")
                        skipped_files += 1
                        continue
                    
                    html_files.append((os.path.join(root, file), output_file))
                    total_files += 1
        
        # 使用tqdm创建进度条
        self.logger.info(f"找到 {len(html_files)} 个输出文件需要检查")
        for html_file, output_file in tqdm(html_files, desc="检查输出文件", unit="文件"):
            checked_files += 1
            if self.check_file(output_file):
                passed_files += 1
            else:
                failed_files += 1
        
        # 保存失败的文件列表
        if self.failed_files:
            missing_file = os.path.join(self.check_output_dir, 'missing.txt')
            self.logger.info(f"保存失败的文件列表到: {missing_file}")
            with open(missing_file, 'w', encoding='utf-8') as f:
                for file_path in self.failed_files:
                    f.write(f"{file_path}\n")
        
        # 打印统计信息
        self.logger.info(f"检查完成: 共扫描 {total_files} 个文件，检查 {checked_files} 个文件，通过 {passed_files} 个文件，失败 {failed_files} 个文件，跳过 {skipped_files} 个文件")

def main():
    print("=" * 50)
    print("VBA规则检查器启动")
    print("=" * 50)
    
    checker = VBARulesChecker()
    
    # 检查input目录下的所有HTML文件对应的输出文件
    checker.check_directory()
    
    print("\n" + "=" * 50)
    print("所有文件检查完成")
    print("=" * 50)

if __name__ == "__main__":
    main() 