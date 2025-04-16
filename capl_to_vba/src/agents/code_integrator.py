from autogen import AssistantAgent
from ..data.rule_loader import RuleLoader

class CodeIntegratorAgent(AssistantAgent):
    """代码集成器，负责将转换后的代码组件整合在一起"""
    def __init__(self, rule_loader: RuleLoader):
        super().__init__(
            name="code_integrator",
            description="负责将转换后的Python-VBA代码组件整合在一起，确保代码的完整性和一致性",
            system_message="""你是一个代码集成专家，负责将转换后的Python-VBA代码组件整合在一起。
            请遵循以下规则：
            1. 确保所有导入语句位于文件顶部
            2. 正确排序类定义和函数定义
            3. 正确实现消息处理函数
            4. 正确实现定时器处理
            5. 检查并解决任何依赖关系问题
            6. 对照VBA规则文档检查最终实现
            
            请按照以下格式输出：
            1. 首先输出完整的集成后的Python-VBA代码
            2. 在代码之后添加一个空行
            3. 最后添加"TERMINATE"标记
            
            注意：必须包含完整的代码，不能只输出TERMINATE。""",
            llm_config=rule_loader.OPENAI_CONFIG
        ) 