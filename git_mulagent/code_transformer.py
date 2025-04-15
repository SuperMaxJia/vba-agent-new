import os
from typing import Dict, List, Optional
from openai import OpenAI
from bs4 import BeautifulSoup
import json

class CodeTransformer:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化代码转换器
        
        Args:
            api_key (str): API密钥
            base_url (str): API基础URL
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.rules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")
        self._ensure_rules_dir()
        
    def _ensure_rules_dir(self):
        """确保规则目录存在"""
        if not os.path.exists(self.rules_dir):
            os.makedirs(self.rules_dir)
            
    def load_rules(self, source_lang: str, target_lang: str) -> Dict:
        """
        加载转换规则
        
        Args:
            source_lang (str): 源语言
            target_lang (str): 目标语言
            
        Returns:
            Dict: 转换规则
        """
        rules = {}
        rules_file = os.path.join(self.rules_dir, f"{source_lang}_to_{target_lang}.json")
        
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
            except Exception as e:
                print(f"警告：加载规则文件时出错: {str(e)}")
                
        return rules
        
    def analyze_code_structure(self, code: str, lang: str) -> Dict:
        """
        分析代码结构
        
        Args:
            code (str): 源代码
            lang (str): 编程语言
            
        Returns:
            Dict: 代码结构分析结果
        """
        prompt = f"""请分析以下{lang}代码的结构，将其分解为以下部分：
        1. 导入语句
        2. 全局变量声明
        3. 类定义
        4. 函数定义
        5. 主程序入口
        
        代码：
        {code}
        
        请按照以下格式输出JSON：
        {{
            "imports": [],
            "globals": [],
            "classes": [],
            "functions": [],
            "main": ""
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个代码分析专家，请分析代码结构。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"警告：分析代码结构时出错: {str(e)}")
            return {}
            
    def convert_code(self, code: str, source_lang: str, target_lang: str) -> str:
        """
        转换代码
        
        Args:
            code (str): 源代码
            source_lang (str): 源语言
            target_lang (str): 目标语言
            
        Returns:
            str: 转换后的代码
        """
        # 加载转换规则
        rules = self.load_rules(source_lang, target_lang)
        
        # 分析代码结构
        structure = self.analyze_code_structure(code, source_lang)
        
        # 分步转换
        converted_parts = {}
        
        # 1. 转换导入语句
        if structure.get("imports"):
            converted_parts["imports"] = self._convert_imports(
                structure["imports"], source_lang, target_lang, rules
            )
            
        # 2. 转换全局变量
        if structure.get("globals"):
            converted_parts["globals"] = self._convert_globals(
                structure["globals"], source_lang, target_lang, rules
            )
            
        # 3. 转换类定义
        if structure.get("classes"):
            converted_parts["classes"] = self._convert_classes(
                structure["classes"], source_lang, target_lang, rules
            )
            
        # 4. 转换函数定义
        if structure.get("functions"):
            converted_parts["functions"] = self._convert_functions(
                structure["functions"], source_lang, target_lang, rules
            )
            
        # 5. 转换主程序
        if structure.get("main"):
            converted_parts["main"] = self._convert_main(
                structure["main"], source_lang, target_lang, rules
            )
            
        # 整合转换后的代码
        return self._combine_code(converted_parts, target_lang)
        
    def _convert_imports(self, imports: List[str], source_lang: str, target_lang: str, rules: Dict) -> str:
        """转换导入语句"""
        prompt = f"""请将以下{source_lang}的导入语句转换为{target_lang}的导入语句：
        
        导入语句：
        {json.dumps(imports, ensure_ascii=False)}
        
        转换规则：
        {json.dumps(rules.get("imports", {}), ensure_ascii=False)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个代码转换专家，请转换导入语句。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"警告：转换导入语句时出错: {str(e)}")
            return ""
            
    def _convert_globals(self, globals: List[str], source_lang: str, target_lang: str, rules: Dict) -> str:
        """转换全局变量"""
        prompt = f"""请将以下{source_lang}的全局变量声明转换为{target_lang}的全局变量声明：
        
        全局变量：
        {json.dumps(globals, ensure_ascii=False)}
        
        转换规则：
        {json.dumps(rules.get("globals", {}), ensure_ascii=False)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个代码转换专家，请转换全局变量声明。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"警告：转换全局变量时出错: {str(e)}")
            return ""
            
    def _convert_classes(self, classes: List[str], source_lang: str, target_lang: str, rules: Dict) -> str:
        """转换类定义"""
        prompt = f"""请将以下{source_lang}的类定义转换为{target_lang}的类定义：
        
        类定义：
        {json.dumps(classes, ensure_ascii=False)}
        
        转换规则：
        {json.dumps(rules.get("classes", {}), ensure_ascii=False)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个代码转换专家，请转换类定义。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"警告：转换类定义时出错: {str(e)}")
            return ""
            
    def _convert_functions(self, functions: List[str], source_lang: str, target_lang: str, rules: Dict) -> str:
        """转换函数定义"""
        prompt = f"""请将以下{source_lang}的函数定义转换为{target_lang}的函数定义：
        
        函数定义：
        {json.dumps(functions, ensure_ascii=False)}
        
        转换规则：
        {json.dumps(rules.get("functions", {}), ensure_ascii=False)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个代码转换专家，请转换函数定义。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"警告：转换函数定义时出错: {str(e)}")
            return ""
            
    def _convert_main(self, main: str, source_lang: str, target_lang: str, rules: Dict) -> str:
        """转换主程序"""
        prompt = f"""请将以下{source_lang}的主程序转换为{target_lang}的主程序：
        
        主程序：
        {main}
        
        转换规则：
        {json.dumps(rules.get("main", {}), ensure_ascii=False)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个代码转换专家，请转换主程序。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"警告：转换主程序时出错: {str(e)}")
            return ""
            
    def _combine_code(self, parts: Dict, target_lang: str) -> str:
        """整合转换后的代码"""
        prompt = f"""请整合以下{target_lang}代码的各个部分，确保：
        1. 代码结构清晰
        2. 没有重复定义
        3. 依赖关系正确
        4. 添加必要的注释
        
        代码部分：
        {json.dumps(parts, ensure_ascii=False)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个代码整合专家，请整合所有代码。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"警告：整合代码时出错: {str(e)}")
            return ""

def main():
    # 示例使用
    transformer = CodeTransformer(api_key="your-api-key")
    
    # 示例代码
    source_code = """
    import sys
    
    class Calculator:
        def add(self, a, b):
            return a + b
            
    def main():
        calc = Calculator()
        print(calc.add(1, 2))
        
    if __name__ == "__main__":
        main()
    """
    
    # 转换代码
    converted_code = transformer.convert_code(
        code=source_code,
        source_lang="Python",
        target_lang="Java"
    )
    
    # 保存结果
    with open("output.java", "w", encoding="utf-8") as f:
        f.write(converted_code)

if __name__ == "__main__":
    main() 