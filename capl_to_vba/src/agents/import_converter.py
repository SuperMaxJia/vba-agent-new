from autogen import AssistantAgent

from ..config.llm_config import OPENAI_CONFIG
from ..data.rule_loader import RuleLoader

class ImportConverterAgent(AssistantAgent):
    """导入转换器，负责将CAPL的include语句转换为Python-VBA的导入语句"""
    def __init__(self, rule_loader: RuleLoader):
        super().__init__(
            name="import_converter",
            description="负责将CAPL代码中的include语句转换为Python-VBA代码的导入语句，确保所有必要的依赖被正确导入",
            system_message="""你是一个代码转换专家，负责将CAPL代码中的include语句转换为Python-VBA代码的导入语句。
            请专注于以下任务：
            1. 分析CAPL代码中的include语句
            2. 将这些include语句转换为对应的导入语句
            3. 确保所有必要的文件都被正确导入
            
            导入规则：
            1. VBA自定义包无需导入
            2. 引用的Python包需要导入
            3. 引用的其他文件需要导入文件名，并添加注释说明
            4. 对于多文件引用，需要添加"请手动导入到人软件"的注释
            
            请按照以下格式输出：
            1. 首先列出所有需要导入的文件
            2. 然后输出完整的导入语句
            3. 最后添加"IMPORTS_COMPLETE"标记
            
            示例输出格式：
            ```python
            # 需要导入的文件：
            # - numpy (Python包)
            # - pandas (Python包)
            # - utils (其他文件)
            # - common_functions (其他文件)
            # - message_handlers (其他文件)
            
            import numpy as np
            import pandas as pd
            import utils  # 请手动导入到人软件
            import common_functions  # 请手动导入到人软件
            import message_handlers  # 请手动导入到人软件
            
            # VBA自定义包无需导入
            # - writeinfo（）
            # - sendMsg（）
            ```
            
            IMPORTS_COMPLETE""",
            llm_config=OPENAI_CONFIG
        ) 