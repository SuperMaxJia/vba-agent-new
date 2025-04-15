from typing import Dict, List, Optional
from openai import OpenAI
import json
import os
from dataclasses import dataclass
from enum import Enum

class AgentType(Enum):
    ANALYZER = "analyzer"
    IMPORTER = "importer"
    CLASS_CONVERTER = "class_converter"
    FUNCTION_CONVERTER = "function_converter"
    MAIN_CONVERTER = "main_converter"
    CODE_INTEGRATOR = "code_integrator"

@dataclass
class AgentConfig:
    role: str
    instructions: str
    model: str = "deepseek-chat"

class CodeAgent:
    def __init__(self, config: AgentConfig, client: OpenAI):
        self.config = config
        self.client = client
        
    def process(self, content: str, context: Dict = None) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.config.instructions},
                    {"role": "user", "content": content}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"警告：Agent处理出错: {str(e)}")
            return ""

class MultiAgentTransformer:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.rules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")
        self._ensure_rules_dir()
        self._initialize_agents()
        
    def _ensure_rules_dir(self):
        if not os.path.exists(self.rules_dir):
            os.makedirs(self.rules_dir)
            
    def _initialize_agents(self):
        """初始化所有Agent"""
        self.agents = {
            AgentType.ANALYZER: CodeAgent(
                AgentConfig(
                    role="代码分析专家",
                    instructions="分析代码结构，识别关键组件"
                ),
                self.client
            ),
            AgentType.IMPORTER: CodeAgent(
                AgentConfig(
                    role="导入转换专家",
                    instructions="转换导入语句，处理依赖关系"
                ),
                self.client
            ),
            AgentType.CLASS_CONVERTER: CodeAgent(
                AgentConfig(
                    role="类转换专家",
                    instructions="转换类定义，处理继承关系"
                ),
                self.client
            ),
            AgentType.FUNCTION_CONVERTER: CodeAgent(
                AgentConfig(
                    role="函数转换专家",
                    instructions="转换函数定义，处理参数和返回值"
                ),
                self.client
            ),
            AgentType.MAIN_CONVERTER: CodeAgent(
                AgentConfig(
                    role="主程序转换专家",
                    instructions="转换主程序入口，处理程序流程"
                ),
                self.client
            ),
            AgentType.CODE_INTEGRATOR: CodeAgent(
                AgentConfig(
                    role="代码整合专家",
                    instructions="整合所有转换后的代码，确保一致性"
                ),
                self.client
            )
        }
        
    def load_rules(self, source_lang: str, target_lang: str) -> Dict:
        rules_file = os.path.join(self.rules_dir, f"{source_lang}_to_{target_lang}.json")
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告：加载规则文件时出错: {str(e)}")
        return {}
        
    def convert_code(self, code: str, source_lang: str, target_lang: str) -> str:
        # 加载转换规则
        rules = self.load_rules(source_lang, target_lang)
        
        # 1. 分析代码结构
        analyzer = self.agents[AgentType.ANALYZER]
        structure_prompt = f"""分析以下{source_lang}代码的结构：
        {code}
        
        请输出JSON格式的结构分析结果，包含：
        - imports: 导入语句列表
        - globals: 全局变量列表
        - classes: 类定义列表
        - functions: 函数定义列表
        - main: 主程序入口
        """
        structure = json.loads(analyzer.process(structure_prompt))
        
        # 2. 转换各个部分
        converted_parts = {}
        
        # 转换导入语句
        if structure.get("imports"):
            importer = self.agents[AgentType.IMPORTER]
            import_prompt = f"""转换以下{source_lang}的导入语句到{target_lang}：
            {json.dumps(structure["imports"])}
            
            转换规则：
            {json.dumps(rules.get("imports", {}))}
            """
            converted_parts["imports"] = importer.process(import_prompt)
            
        # 转换类定义
        if structure.get("classes"):
            class_converter = self.agents[AgentType.CLASS_CONVERTER]
            class_prompt = f"""转换以下{source_lang}的类定义到{target_lang}：
            {json.dumps(structure["classes"])}
            
            转换规则：
            {json.dumps(rules.get("classes", {}))}
            """
            converted_parts["classes"] = class_converter.process(class_prompt)
            
        # 转换函数定义
        if structure.get("functions"):
            function_converter = self.agents[AgentType.FUNCTION_CONVERTER]
            function_prompt = f"""转换以下{source_lang}的函数定义到{target_lang}：
            {json.dumps(structure["functions"])}
            
            转换规则：
            {json.dumps(rules.get("functions", {}))}
            """
            converted_parts["functions"] = function_converter.process(function_prompt)
            
        # 转换主程序
        if structure.get("main"):
            main_converter = self.agents[AgentType.MAIN_CONVERTER]
            main_prompt = f"""转换以下{source_lang}的主程序到{target_lang}：
            {structure["main"]}
            
            转换规则：
            {json.dumps(rules.get("main", {}))}
            """
            converted_parts["main"] = main_converter.process(main_prompt)
            
        # 3. 整合代码
        integrator = self.agents[AgentType.CODE_INTEGRATOR]
        integrate_prompt = f"""整合以下{target_lang}代码的各个部分：
        {json.dumps(converted_parts)}
        
        请确保：
        1. 代码结构清晰
        2. 没有重复定义
        3. 依赖关系正确
        4. 添加必要的注释
        """
        return integrator.process(integrate_prompt)

def main():
    # 示例使用
    transformer = MultiAgentTransformer(api_key="your-api-key")
    
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