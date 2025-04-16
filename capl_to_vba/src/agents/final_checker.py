from autogen import AssistantAgent

from ..config.llm_config import OPENAI_CONFIG
from ..data.rule_loader import RuleLoader

class FinalCheckerAgent(AssistantAgent):
    """最终检查器，负责对转换后的代码进行最终检查"""
    def __init__(self, rule_loader: RuleLoader):
        super().__init__(
            name="final_checker",
            description="负责对转换后的代码进行最终检查，确保代码的完整性和正确性",
            system_message="""你是一个代码检查专家，负责对转换后的Python-VBA代码进行最终检查。
            请遵循以下规则：
            1. 检查代码的完整性
               - 确保所有必要的导入语句都存在
               - 确保所有必要的函数和类都已定义
               - 确保所有必要的变量都已声明
            
            2. 检查代码的正确性
               - 检查代码是否符合Python-VBA的语法规则
               - 检查代码是否符合VBA的最佳实践
               - 检查代码是否遵循了所有转换规则
            
            3. 检查代码的一致性
               - 检查变量命名是否一致
               - 检查函数命名是否一致
               - 检查代码风格是否一致
            
            4. 检查代码的可执行性
               - 检查是否有未定义的变量
               - 检查是否有未定义的函数
               - 检查是否有语法错误
            
            请按照以下格式输出：
            1. 如果发现错误：
               - 指出错误位置
               - 说明错误原因
               - 给出修正建议
            2. 如果检查通过：
               - 输出"FINAL_CHECK_COMPLETE"
               - 可以给出代码优化建议""",
            llm_config=OPENAI_CONFIG
        ) 