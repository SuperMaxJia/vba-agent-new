from typing import Dict, List, Optional
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import json
import os

# Ollama配置
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "deepseek-r1:1.5b"  # 使用本地deepseek模型

class CodeAnalyzerAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="code_analyzer",
            system_message="""你是一个代码分析专家，负责分析代码结构。
            请识别代码中的：
            1. 导入语句
            2. 全局变量
            3. 类定义
            4. 函数定义
            5. 主程序入口
            
            请以JSON格式输出分析结果。""",
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )

class ImportConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="import_converter",
            system_message="""你是一个导入转换专家，负责转换导入语句。
            请根据目标语言的规则转换导入语句。
            确保：
            1. 正确处理依赖关系
            2. 使用正确的包名
            3. 处理版本兼容性""",
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )

class ClassConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="class_converter",
            system_message="""你是一个类转换专家，负责转换类定义。
            请处理：
            1. 类名转换
            2. 继承关系
            3. 访问修饰符
            4. 构造函数
            5. 成员变量和方法""",
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )

class FunctionConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="function_converter",
            system_message="""你是一个函数转换专家，负责转换函数定义。
            请处理：
            1. 函数名转换
            2. 参数类型
            3. 返回值类型
            4. 函数体转换
            5. 异常处理""",
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )

class MainConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="main_converter",
            system_message="""你是一个主程序转换专家，负责转换主程序入口。
            请处理：
            1. 主函数定义
            2. 程序流程
            3. 命令行参数
            4. 程序退出""",
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )

class CodeIntegratorAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="code_integrator",
            system_message="""你是一个代码整合专家，负责整合所有转换后的代码。
            请确保：
            1. 代码结构清晰
            2. 没有重复定义
            3. 依赖关系正确
            4. 添加必要的注释
            5. 保持代码风格一致""",
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )

class AutoGenTransformer:
    def __init__(self):
        # 创建用户代理
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            system_message="你是一个代码转换项目的协调者。",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={
                "work_dir": "workspace",
                "use_docker": False  # 禁用Docker执行
            },
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )
        
        # 创建专家Agent
        self.agents = {
            "analyzer": CodeAnalyzerAgent(),
            "importer": ImportConverterAgent(),
            "class_converter": ClassConverterAgent(),
            "function_converter": FunctionConverterAgent(),
            "main_converter": MainConverterAgent(),
            "integrator": CodeIntegratorAgent()
        }
        
        # 创建群聊
        self.groupchat = GroupChat(
            agents=[self.user_proxy] + list(self.agents.values()),
            messages=[],
            max_round=50
        )
        
        # 创建群聊管理器
        self.manager = GroupChatManager(
            groupchat=self.groupchat,
            llm_config={
                "config_list": [{
                    "model": MODEL_NAME,
                    "base_url": OLLAMA_BASE_URL,
                    "api_type": "ollama"
                }]
            }
        )
        
    def load_rules(self, source_lang: str, target_lang: str) -> Dict:
        rules_file = os.path.join("rules", f"{source_lang}_to_{target_lang}.json")
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
        
        # 构建初始消息
        initial_message = f"""请将以下{source_lang}代码转换为{target_lang}代码。
        转换规则：
        {json.dumps(rules, indent=2)}
        
        源代码：
        {code}
        
        请按照以下步骤进行转换：
        1. 分析代码结构
        2. 转换各个组件
        3. 整合最终代码
        
        完成后请回复"TERMINATE"。"""
        
        # 启动群聊
        self.user_proxy.initiate_chat(
            self.manager,
            message=initial_message
        )
        
        # 获取转换结果
        messages = self.groupchat.messages
        for msg in reversed(messages):
            if msg["role"] == "assistant" and msg["name"] == "code_integrator":
                return msg["content"]
        
        return "转换失败，未能生成结果。"

def main():
    # 创建转换器实例
    transformer = AutoGenTransformer()
    
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