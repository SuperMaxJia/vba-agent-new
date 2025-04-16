from autogen import AssistantAgent
from ..data.rule_loader import RuleLoader
from ..config.llm_config import OPENAI_CONFIG

class PythonSyntaxCheckerAgent(AssistantAgent):
    """语法检查器，负责检查生成的Python-VBA代码是否符合语法规则"""
    def __init__(self, rule_loader: RuleLoader):
        super().__init__(
            name="syntax_checker",
            description="负责检查生成的Python-VBA代码是否符合语法规则，确保代码的正确性和可执行性",
            system_message="""你是一个Python-VBA语法检查专家，负责检查生成的Python-VBA代码是否符合语法规则。
            请遵循以下规则：
            1. 检查代码的缩进是否正确
            2. 检查函数定义的位置是否正确
            3. 检查导入语句的位置是否正确
            4. 检查类定义的位置是否正确
            5. 检查消息处理函数的定义是否正确
            6. 检查定时器处理的实现是否正确
            7. 对照VBA规则文档检查代码实现
            
            如果发现语法错误，请指出错误并给出修正建议。
            如果代码语法正确，请添加"SYNTAX_CORRECT"标记。
            
            请按照以下格式输出：
            1. 如果发现错误：
               - 指出错误位置
               - 说明错误原因
               - 给出修正建议
            2. 如果语法正确：
               - 输出"SYNTAX_CORRECT"
               - 可以给出代码优化建议""",
            llm_config=OPENAI_CONFIG
        ) 