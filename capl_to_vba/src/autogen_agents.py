import os
import openai
from colorama import init, Fore, Style
import re
import json
from typing import Dict, List, Optional, Tuple
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from pathlib import Path

# 初始化colorama
init()

# 颜色常量
COLOR_USER = Fore.GREEN  # 用户输入/关键信息
COLOR_ASSISTANT = Fore.BLUE  # 助手输出/名词
COLOR_SYSTEM = Fore.YELLOW  # 系统消息/流程旁白
COLOR_ERROR = Fore.RED  # 错误信息
COLOR_INFO = Fore.CYAN  # 一般信息
COLOR_DEBUG = Fore.MAGENTA  # 调试信息/整理出的内容
COLOR_RESET = Style.RESET_ALL

def print_colored(text: str, color: str) -> None:
    """打印带颜色的文本"""
    print(f"{color}{text}{COLOR_RESET}")

def print_message(message: Dict) -> None:
    """打印消息"""
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        print_colored(f"用户: {content}", COLOR_USER)
    elif role == "assistant":
        print_colored(f"助手: {content}", COLOR_ASSISTANT)
    elif role == "system":
        print_colored(f"系统: {content}", COLOR_SYSTEM)

# 配置OpenAI
OPENAI_CONFIG = {
    "config_list": [
        {
            "model": "gpt-3.5-turbo",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    ],
    "temperature": 0.7,
    "timeout": 120,
    "cache_seed": None
}

# 检查API密钥
if not OPENAI_CONFIG["config_list"][0]["api_key"]:
    print_colored("错误：未设置OpenAI API密钥", COLOR_ERROR)
    print_colored("请设置环境变量：export OPENAI_API_KEY='your-api-key'", COLOR_INFO)
    exit(1)

print_colored("API密钥检查：", COLOR_SYSTEM)
print_colored(f"- 环境变量名称: OPENAI_API_KEY", COLOR_USER)
print_colored(f"- 密钥长度: {len(OPENAI_CONFIG['config_list'][0]['api_key'])} 字符", COLOR_USER)
print_colored(f"- 密钥前缀: {OPENAI_CONFIG['config_list'][0]['api_key'][:10]}", COLOR_USER)
print_colored(f"- 密钥后缀: {OPENAI_CONFIG['config_list'][0]['api_key'][-10:]}", COLOR_USER)

class RuleLoader:
    """规则加载器类"""
    def __init__(self):
        self.capl_to_vba_map = {}
        self.vba_rule_map = {}
        
    def load_rules(self):
        """加载所有规则"""
        self._load_capl_to_vba_mapping()
        self._load_vba_rules()
        
    def _load_capl_to_vba_mapping(self):
        """加载CAPL到VBA的映射规则"""
        mapping_dir = "/Users/cuisijia/source/rule-reflection/output/reflection"
        for filename in os.listdir(mapping_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(mapping_dir, filename), "r") as f:
                    content = f.read()
                    # 解析文件名获取规则名称
                    rule_name = filename.replace(".txt", "")
                    self.capl_to_vba_map[rule_name] = content
                    
    def _load_vba_rules(self):
        """加载VBA规则"""
        vba_rules_dir = "/Users/cuisijia/source/rules/output/vba-rules-txt"
        for filename in os.listdir(vba_rules_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(vba_rules_dir, filename), "r") as f:
                    content = f.read()
                    rule_name = filename.replace(".txt", "")
                    self.vba_rule_map[rule_name] = content
                    
    def get_capl_mapping(self, capl_rule: str) -> Optional[str]:
        """获取CAPL规则的VBA映射"""
        return self.capl_to_vba_map.get(capl_rule)
        
    def get_vba_rule(self, vba_rule: str) -> Optional[str]:
        """获取VBA规则的详细说明"""
        return self.vba_rule_map.get(vba_rule)

class ConversationData:
    """对话数据管理类"""
    def __init__(self):
        self.capl_code = ""
        self.preprocess_section = ""
        self.code_snippets = []
        self.processing_queue = []
        self.converted_snippets = []
        
    def get_snippet(self) -> Optional[str]:
        """获取下一个要处理的代码片段"""
        if self.processing_queue:
            return self.processing_queue.pop(0)
        return None
        
    def add_snippet(self, snippet: str) -> None:
        """添加代码片段到处理队列"""
        self.processing_queue.append(snippet)
        
    def has_remaining_snippets(self) -> bool:
        """检查是否还有未处理的代码片段"""
        return len(self.processing_queue) > 0
        
    def clear(self) -> None:
        """清空所有数据"""
        self.capl_code = ""
        self.preprocess_section = ""
        self.code_snippets = []
        self.processing_queue = []
        self.converted_snippets = []



    def convert_code(self, capl_code: str) -> str:
        """转换CAPL代码为VBA代码"""
        print_colored("开始转换代码...", COLOR_SYSTEM)
        
        # 清空对话数据
        self.conversation_data.clear()
        
        # 存储CAPL代码
        self.conversation_data.capl_code = capl_code
        
        # 开始对话
        round_count = 0
        current_phase = "analysis"
        current_content = None
        
        while round_count < 15:  # 设置最大对话轮数
            round_count += 1
            print_colored(f"\n第{round_count}轮对话开始...", COLOR_SYSTEM)
            
            # 根据当前阶段选择下一个发言者
            current_agent = self.code_analyzer if round_count == 1 else self._get_next_agent(current_phase)
            if current_agent is None:
                break
                
            print_colored(f"选择下一个发言者: {current_agent.name}", COLOR_SYSTEM)
            
            # 生成回复
            print_colored("生成回复...", COLOR_SYSTEM)
            print_colored("\n发送给大模型的消息内容：", COLOR_SYSTEM)
            print_colored("="*50, COLOR_SYSTEM)
            print_colored("="*50, COLOR_SYSTEM)
            
            # 构建消息
            message = self._build_message(current_phase, current_content)
            if not message:
                break
                
            reply = current_agent.generate_reply(
                messages=[message],
                sender=self.user_proxy
            )
            
            # 处理收到的回复
            if reply:
                print_colored(f"收到回复，长度: {len(reply)} 字符", COLOR_SYSTEM)
                print_colored(f"回复内容：\n{reply}", COLOR_ASSISTANT)
                
                # 根据当前阶段处理回复
                next_phase, next_content = self._process_reply(current_phase, reply)
                if next_phase:
                    current_phase = next_phase
                    current_content = next_content
                    if current_phase == "complete":
                        break
        
        print_colored("\n转换完成！", COLOR_SYSTEM)
        print_colored("="*50, COLOR_SYSTEM)
        return reply if reply else "转换失败"

    def _get_next_agent(self, next_phase: str) -> AssistantAgent:
        """根据阶段名称获取下一个发言的智能体"""
        phase_to_agent = {
            "analysis": self.code_analyzer,
            "imports": self.importer,
            "syntax_recognize": self.syntax_recognizer,
            "conversion": self.converter,
            "syntax_check": self.syntax_checker,
            "integration": self.integrator,
            "final_check": self.final_checker,
            "complete": None
        }
        return phase_to_agent.get(next_phase)

class CodeAnalyzerAgent(AssistantAgent):
    """代码分析器，负责将CAPL代码分割成预处理部分和代码片段列表"""
    def __init__(self):
        super().__init__(
            name="code_analyzer",
            description="负责将CAPL代码分割成预处理部分和代码片段列表，确保每个函数和其使用的全局变量被正确提取",
            system_message="""你是一个CAPL代码分割专家，负责将CAPL脚本分割成预处理部分和代码片段列表。
            请专注于以下任务：
            1. 分割预处理部分
               - 只有下面的属于预处理指令 ：#include, #define
               - 保持原始格式和缩进
               - 不要添加任何注释或说明
            
            2. 分割代码片段
               - 每个函数必须作为独立的代码片段输出
               - 每个下面格式的内容视为一个函数，都必须作为一个代码片段输出
                 ```c
                 on name
                 {
                    
                 }
                 ```
                 
               - 对于每个函数，需要包含：
                 * 函数定义本身
                 * 函数内部使用的所有全局变量定义
               - 仔细查找函数内部使用的变量，每一个变量都一定有一个定义，如果定义在函数外部，则认为是全局变量，将全局变量的定义和函数放在一起
               - 保持原始格式和缩进
               - 不要添加任何注释或说明
            
            请按照以下格式输出分割结果：
            1. 预处理部分
               ```c
               预处理部分：
               [直接复制源代码中的预处理指令，保持原始格式，如果没有预处理指令，则输出：预处理部分：空]
               ```
            
            2. 代码片段列表
               ```c
               代码片段1：
               [直接复制源代码中的函数定义及其使用的全局变量定义，保持原始代码和格式，变量在前、函数在后]
               
               代码片段2：
               [直接复制源代码中的函数定义及其使用的全局变量定义，保持原始代码和格式，变量在前、函数在后]
               
               [继续输出其他代码片段...]
               ```
            
            重要说明：
            1. 必须直接复制源代码中的内容，不要修改或重新格式化
            2. 保持原始代码的缩进、空格和换行
            3. 不要添加任何额外的注释或说明
            4. 不要对代码进行任何美化或格式化
            5. 确保提取的内容与源代码完全一致
            6. 每个代码片段必须包含完整的函数定义及其使用的全局变量
            7. 不要遗漏任何函数或全局变量
            8. 不要输出任何分析结果或统计信息
            9. 每个代码片段之间用空行分隔
            10. 代码片段的标题格式为"代码片段X："，其中X从1开始递增
            11. 严格保持原始代码内容，不要添加任何注释或说明
            12. 每个函数必须作为独立的代码片段输出，不能合并多个函数到一个代码片段中
            
            分割完成后，请添加"ANALYSIS_COMPLETE"标记。""",
            llm_config=OPENAI_CONFIG
        )

class SyntaxRecognizerAgent(AssistantAgent):
    """语法识别器，负责识别CAPL代码中的特有类型和函数名"""
    def __init__(self):
        super().__init__(
            name="syntax_recognizer",
            description="负责识别CAPL代码中的特有类型和函数名，确保所有CAPL特有的语法元素被正确识别",
            system_message="""你是一个CAPL语法识别专家，负责识别CAPL脚本中使用的特有类型和函数名。
            请专注于以下任务：
            1. 识别使用的CAPL特有类型
               - 识别所有使用的内置类型（如message, timer, msTimer, byte等）
               - 识别所有使用的自定义类型（如自定义结构体、枚举等）
               - 识别所有使用的CAPL特有类型（如canMessage, envVar等）
            2. 识别使用的CAPL特有函数
               - 识别所有使用的消息处理函数（如on message等）
               - 识别所有使用的定时器函数（如setTimer, killTimer等）
               - 识别所有使用的环境变量函数（如getEnvVar, putEnvVar等）
               - 识别所有使用的CAN总线函数（如output, write等）
            
            请按照以下格式输出识别结果：
            ```c
            // 类型：
            message
            msTimer
            
            // 函数：
            output
            setTimer
            write
            ```
            
            重要说明：
            1. 不要识别基础类型（如int, char, float等）
            2. 只列出实际使用的CAPL特有类型和函数
            3. 保持原始名称，不要修改
            4. 确保完整性，不要遗漏
            5. 只输出名称，不要包含其他信息
            6. 严格按照示例格式输出，不要添加额外的注释或说明
            7. 不要输出导入相关的信息
            8. 不要输出任何Python相关的代码
            9. 不要输出任何VBA相关的代码
            10. 不要输出任何变量定义或函数实现
            11. 不要输出任何注释或说明
            12. 不要输出任何代码块
            
            识别完成后，请添加"SYNTAX_RECOGNIZED"标记。
            
            输出格式示例：
            ```c
            // 类型：
            message
            msTimer
            
            // 函数：
            output
            setTimer
            write
            
            SYNTAX_RECOGNIZED
            ```""",
            llm_config=OPENAI_CONFIG
        )

class ImportConverterAgent(AssistantAgent):
    """导入转换器，负责将CAPL的include语句转换为Python-VBA的导入语句"""
    def __init__(self):
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

class CodeConverterAgent(AssistantAgent):
    """代码转换器，负责将CAPL代码转换为Python-VBA代码"""
    def __init__(self):
        super().__init__(
            name="code_converter",
            description="负责将CAPL代码转换为Python-VBA代码，根据映射规则进行类型和函数的转换",
            system_message="""你是一个代码转换专家，负责将CAPL代码转换为Python-VBA代码。
            请遵循以下规则：
            1. 分析CAPL代码中的变量和函数定义
            2. 根据映射规则将CAPL代码转换为VBA代码：
               - 在 capl_to_vba_map 中查找CAPL类型和函数
               - 找到对应的VBA类型和函数映射
               - 根据 vba_rule_map 中的详细规则进行转换
            3. 使用映射规则转换变量定义
            4. 使用映射规则转换函数定义
            5. 使用映射规则转换函数参数
            6. 使用映射规则转换函数体
            7. 使用映射规则转换消息处理
            8. 使用映射规则转换定时器处理
            9. 使用Python-VBA的最佳实践
            
            转换步骤：
            1. 对于变量定义：
               - 在 capl_to_vba_map 中查找变量类型的映射规则
               - 根据映射规则找到VBA类型
               - 在 vba_rule_map 中查找该VBA类型的详细规则
               - 根据详细规则进行转换
            2. 对于函数定义：
               - 在 capl_to_vba_map 中查找函数名的映射规则
               - 根据映射规则找到VBA函数
               - 在 vba_rule_map 中查找该VBA函数的详细规则
               - 根据详细规则进行转换
            3. 对于函数参数：
               - 在 capl_to_vba_map 中查找参数类型的映射规则
               - 根据映射规则找到VBA类型
               - 在 vba_rule_map 中查找该VBA类型的详细规则
            4. 对于函数体：
               - 在 capl_to_vba_map 中查找函数体中使用的CAPL函数
               - 根据映射规则转换为VBA函数
               - 在 vba_rule_map 中查找该VBA函数的详细规则
            5. 对于消息处理：
               - 在 capl_to_vba_map 中查找消息处理函数的映射规则
               - 在 vba_rule_map 中查找该VBA消息处理函数的详细规则
            6. 对于定时器处理：
               - 在 capl_to_vba_map 中查找定时器函数的映射规则
               - 在 vba_rule_map 中查找该VBA定时器函数的详细规则
            
            请按照以下格式输出：
            1. 如果是变量定义：
               ```python
               # 变量定义
               [转换后的变量定义]
               ```
               然后添加"VARIABLES_COMPLETE"标记
            2. 如果是函数定义：
               ```python
               # 函数定义
               [转换后的函数定义]
               ```
               然后添加"FUNCTIONS_COMPLETE"标记
            
            重要说明：
            1. 必须严格按照映射规则进行转换
            2. 保持代码结构和命名规范
            3. 确保所有变量和函数都被正确转换
            4. 添加必要的注释说明转换依据
            5. 使用Python-VBA的最佳实践""",
            llm_config=OPENAI_CONFIG
        )

class PythonSyntaxCheckerAgent(AssistantAgent):
    """语法检查器，负责检查生成的Python-VBA代码是否符合语法规则"""
    def __init__(self):
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

class CodeIntegratorAgent(AssistantAgent):
    """代码集成器，负责将转换后的代码组件整合在一起"""
    def __init__(self):
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
            

            ```
            
            TERMINATE
            
            注意：必须包含完整的代码，不能只输出TERMINATE。""",
            llm_config=OPENAI_CONFIG
        )

class FinalCheckerAgent(AssistantAgent):
    """最终检查器，负责对转换后的代码进行最终检查"""
    def __init__(self):
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

class CodeConverter:
    """代码转换器类"""
    def __init__(self):
        self.rule_loader = RuleLoader()
        self.rule_loader.load_rules()
        
        # 初始化对话数据
        self.conversation_data = ConversationData()
        
        # 初始化各个代理
        self.code_analyzer = CodeAnalyzerAgent()
        self.importer = ImportConverterAgent()
        self.syntax_recognizer = SyntaxRecognizerAgent()
        self.converter = CodeConverterAgent()
        self.integrator = CodeIntegratorAgent()
        self.syntax_checker = PythonSyntaxCheckerAgent()
        self.final_checker = FinalCheckerAgent()
        
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            llm_config=OPENAI_CONFIG
        )
        
        # 创建群聊
        self.groupchat = GroupChat(
            agents=[
                self.user_proxy,
                self.code_analyzer,
                self.importer,
                self.syntax_recognizer,
                self.converter,
                self.integrator,
                self.syntax_checker,
                self.final_checker
            ],
            messages=[],
            max_round=50,
            speaker_selection_method="round_robin"
        )
        
        # 创建群聊管理器
        self.manager = GroupChatManager(
            groupchat=self.groupchat,
            llm_config=OPENAI_CONFIG
        )

    def read_capl_file(self, file_path: str) -> str:
        """读取CAPL文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取CAPL文件失败: {e}")
            return ""

    def save_python_vba_file(self, content: str, output_path: str) -> bool:
        """保存Python-VBA文件"""
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"保存Python-VBA文件失败: {e}")
            return False

    def process_directory(self, input_dir: str, output_dir: str) -> None:
        """处理整个目录的CAPL文件"""
        print(f"开始处理目录: {input_dir}")
        print(f"输出目录: {output_dir}")
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 遍历输入目录
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith('.can'):  # 支持大小写的CAN文件扩展名
                    # 构建输入和输出文件路径
                    input_file = os.path.join(root, file)
                    relative_path = os.path.relpath(input_file, input_dir)
                    output_file = os.path.join(output_dir, os.path.splitext(relative_path)[0] + '.py')
                    
                    print(f"\n处理文件: {input_file}")
                    print(f"输出文件: {output_file}")
                    
                    # 读取CAPL文件
                    capl_code = self.read_capl_file(input_file)
                    if not capl_code:
                        print(f"跳过文件 {input_file} - 读取失败")
                        continue
                        
                    # 转换代码
                    print("开始转换代码...")
                    python_vba_code = self.convert_code(capl_code)
                    
                    # 保存转换后的代码
                    if self.save_python_vba_file(python_vba_code, output_file):
                        print(f"成功保存转换后的代码到: {output_file}")
                    else:
                        print(f"保存转换后的代码失败: {output_file}")
        
    def _process_analysis_phase(self, reply: str) -> Tuple[str, str]:
        """处理分析阶段的结果"""
        if "ANALYSIS_COMPLETE" in reply:
            # 提取预处理部分
            preprocess_pattern = r"```c\n预处理部分：\n(.*?)\n```"
            preprocess_match = re.search(preprocess_pattern, reply, re.DOTALL)
            if preprocess_match:
                self.conversation_data.preprocess_section = preprocess_match.group(1).strip()
            
            # 提取代码片段
            code_snippet_pattern = r"```c\n代码片段\d+：\n(.*?)\n```"
            code_snippets = re.findall(code_snippet_pattern, reply, re.DOTALL)
            self.conversation_data.code_snippets = [snippet.strip() for snippet in code_snippets]
            self.conversation_data.processing_queue = self.conversation_data.code_snippets.copy()
            
            # 打印提取结果
            print_colored("\n提取的预处理部分：", COLOR_SYSTEM)
            print_colored(self.conversation_data.preprocess_section if self.conversation_data.preprocess_section else "空", COLOR_DEBUG)
            
            print_colored("\n提取的代码片段：", COLOR_SYSTEM)
            for i, snippet in enumerate(self.conversation_data.code_snippets, 1):
                print_colored(f"\n代码片段{i}：", COLOR_SYSTEM)
                print_colored(snippet, COLOR_DEBUG)
            
            # 确定下一阶段
            if self.conversation_data.preprocess_section:
                return "imports", self.conversation_data.preprocess_section
            else:
                if self.conversation_data.has_remaining_snippets():
                    return "syntax_recognize", self.conversation_data.get_snippet()
                else:
                    return "integration", self.conversation_data.converted_snippets
        return "analysis", None

    def _process_imports_phase(self, reply: str) -> Tuple[str, str]:
        """处理导入阶段的结果"""
        if "IMPORTS_COMPLETE" in reply:
            if self.conversation_data.has_remaining_snippets():
                return "syntax_recognize", self.conversation_data.get_snippet()
            else:
                return "integration", None
        return "integration", None

    def _process_syntax_recognize_phase(self, reply: str) -> Tuple[str, str]:
        """处理语法识别阶段的结果"""
        if "SYNTAX_RECOGNIZED" in reply:
            self.conversation_data.converted_snippets.append({
                "original": self.conversation_data.get_snippet(),
                "converted": reply
            })
            return "conversion", None  # 转向 converter 处理转换
        return "integration", None  # 如果没有识别到语法，直接进入集成阶段

    def _process_conversion_phase(self, reply: str) -> Tuple[str, str]:
        """处理转换阶段的结果"""
        if "CONVERSION_COMPLETE" in reply:
            if self.conversation_data.has_remaining_snippets():
                return "syntax_recognize", self.conversation_data.get_snippet()
            else:
                return "syntax_check", None
        return "integration", None

    def _process_syntax_check_phase(self, reply: str) -> str:
        """处理语法检查阶段的结果"""
        if "SYNTAX_CHECK_COMPLETE" in reply:
            if self.conversation_data.has_remaining_snippets():
                return "syntax_recognize"
            else:
                return "integration"
        return None

    def _process_integration_phase(self, reply: str) -> str:
        """处理集成阶段的结果"""
        if "INTEGRATION_COMPLETE" in reply:
            return "final_check"
        return None

    def _process_final_check_phase(self, reply: str) -> Tuple[str, str]:
        """处理最终检查阶段的结果"""
        if "FINAL_CHECK_COMPLETE" in reply:
            return "complete", None
        return "integration", None

    def _process_reply(self, current_phase: str, reply: str) -> Tuple[str, str]:
        """处理不同阶段的回复"""
        phase_handlers = {
            "analysis": self._process_analysis_phase,
            "imports": self._process_imports_phase,
            "syntax_recognize": self._process_syntax_recognize_phase,
            "conversion": self._process_conversion_phase,
            "syntax_check": self._process_syntax_check_phase,
            "integration": self._process_integration_phase,
            "final_check": self._process_final_check_phase
        }
        
        handler = phase_handlers.get(current_phase)
        if handler:
            return handler(reply)
        return None, None

    def convert_code(self, capl_code: str) -> str:
        """转换CAPL代码为VBA代码"""
        print_colored("开始转换代码...", COLOR_SYSTEM)
        
        # 清空对话数据
        self.conversation_data.clear()
        
        # 存储CAPL代码
        self.conversation_data.capl_code = capl_code
        
        # 开始对话
        round_count = 0
        current_phase = "analysis"
        current_content = None
        
        while round_count < 15:  # 设置最大对话轮数
            round_count += 1
            print_colored(f"\n第{round_count}轮对话开始...", COLOR_SYSTEM)
            
            # 根据当前阶段选择下一个发言者
            current_agent = self.code_analyzer if round_count == 1 else self._get_agent_from_phase(current_phase)
            if current_agent is None:
                break
                
            print_colored(f"当前发言者: {current_agent.name}", COLOR_SYSTEM)
            

            print_colored("\n发送给大模型的消息内容：", COLOR_SYSTEM)
            print_colored("="*50, COLOR_SYSTEM)
            print_colored("="*50, COLOR_SYSTEM)

            # 构建消息
            message = self._build_message(current_phase, current_content)
            if not message:
                break
            # 生成回复
            print_colored("发送给大模型，正在等待生成回复...", COLOR_SYSTEM)
                
            reply = current_agent.generate_reply(
                messages=[message],
                sender=self.user_proxy
            )
            
            # 处理收到的回复
            if reply:
                print_colored(f"收到回复，长度: {len(reply)} 字符", COLOR_SYSTEM)
                print_colored(f"回复内容：\n{reply}", COLOR_ASSISTANT)
                
                # 根据当前阶段处理回复
                next_phase, next_content = self._process_reply(current_phase, reply)
                if next_phase:
                    current_phase = next_phase
                    current_content = next_content
                    if current_phase == "complete":
                        break
        
        print_colored("\n转换完成！", COLOR_SYSTEM)
        print_colored("="*50, COLOR_SYSTEM)
        return reply if reply else "转换失败"

    def _get_agent_from_phase(self, next_phase: str) -> AssistantAgent:
        """根据阶段名称获取下一个发言的智能体"""
        phase_to_agent = {
            "analysis": self.code_analyzer,
            "imports": self.importer,
            "syntax_recognize": self.syntax_recognizer,
            "conversion": self.converter,
            "syntax_check": self.syntax_checker,
            "integration": self.integrator,
            "final_check": self.final_checker,
            "complete": None
        }
        return phase_to_agent.get(next_phase)

    def _build_message(self, current_phase: str, content: str = None) -> Dict:
        """根据当前阶段构建消息"""
        if current_phase == "analysis":
            return {
                "role": "user",
                "content": f"请将以下CAPL代码转换为VBA代码：\n\n{self.conversation_data.capl_code}"
            }
        elif current_phase == "imports":
            return {
                "role": "user",
                "content": f"请处理以下预处理部分：\n\n{content}"
            }
        elif current_phase == "syntax_recognize":
            return {
                "role": "user",
                "content": f"请识别以下CAPL代码中的语法：\n\n{content}"
            }
        elif current_phase == "conversion":
            return {
                "role": "user",
                "content": f"请将以下CAPL代码转换为VBA代码：\n\n{content}"
            }
        elif current_phase == "syntax_check":
            return {
                "role": "user",
                "content": f"请检查以下Python-VBA代码的语法：\n\n{content}"
            }
        elif current_phase == "integration":
            return {
                "role": "user",
                "content": f"请将以下代码片段集成为完整的Python-VBA代码：\n\n{self.conversation_data.converted_snippets}"
            }
        elif current_phase == "final_check":
            return {
                "role": "user",
                "content": f"请对以下Python-VBA代码进行最终检查：\n\n{content}"
            }
        return None

if __name__ == "__main__":
    # 设置输入和输出目录
    input_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input")  # CAPL文件目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")  # Python-VBA文件输出目录
    
    print("初始化代码转换器...")
    converter = CodeConverter()
    
    # 处理整个目录
    converter.process_directory(input_dir, output_dir)
    
    print("\n所有文件处理完成！") 