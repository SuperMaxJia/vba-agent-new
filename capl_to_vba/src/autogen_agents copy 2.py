import os
from typing import Dict, List, Optional
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import openai
from pathlib import Path
from colorama import Fore, Style, init

# 初始化colorama
init()

# 定义颜色常量
COLOR_USER = Fore.CYAN
COLOR_ASSISTANT = Fore.YELLOW
COLOR_SYSTEM = Fore.GREEN
COLOR_ERROR = Fore.RED
COLOR_INFO = Fore.WHITE
COLOR_DEBUG = Fore.MAGENTA

def print_colored(text: str, color: str = COLOR_INFO, prefix: str = ""):
    """打印带颜色的文本"""
    print(f"{color}{prefix}{text}{Style.RESET_ALL}")

def print_message(msg: dict):
    """打印消息内容"""
    role = msg["role"]
    content = msg["content"]
    
    if role == "user":
        print_colored(f"用户消息:", COLOR_USER)
    else:
        print_colored(f"助手消息 ({msg.get('name', 'unknown')}):", COLOR_ASSISTANT)
    
    print_colored(content, COLOR_INFO)
    print_colored("-"*50, COLOR_INFO)

# OpenAI配置
OPENAI_API_KEY = "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"
MODEL_NAME = "gpt-3.5-turbo"

# 配置OpenAI
openai.api_key = OPENAI_API_KEY

# 定义OpenAI配置
OPENAI_CONFIG = {
    "config_list": [{
        "model": MODEL_NAME,
        "api_key": OPENAI_API_KEY,
        "base_url": "https://api.openai.com/v1"
    }]
}

class RuleLoader:
    def __init__(self):
        """初始化规则加载器"""
        self.capl_to_vba_map = {}  # CAPL到VBA的映射规则
        self.vba_rule_map = {}     # VBA规则文档
        
    def load_rules(self):
        """加载所有规则"""
        self._load_capl_to_vba_mapping()
        self._load_vba_rules()
        
    def _load_capl_to_vba_mapping(self):
        """加载CAPL到VBA的映射规则"""
        mapping_dir = Path("/Users/cuisijia/source/rule-reflection/output/reflection")
        # print(f"\n开始加载CAPL到VBA的映射规则...")
        # print(f"映射规则目录: {mapping_dir}")
        
        # 遍历映射规则目录及其所有子目录
        for file_path in mapping_dir.rglob("*.txt"):
            # 解析文件名获取规则映射
            file_name = file_path.stem
            parts = file_name.split("-")
            if len(parts) != 2:
                continue
                
            capl_rule = parts[0]
            vba_rule = parts[1]
            
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            # 存储映射规则
            if capl_rule not in self.capl_to_vba_map:
                self.capl_to_vba_map[capl_rule] = []
            self.capl_to_vba_map[capl_rule].append({
                "vba_rule": vba_rule,
                "content": content
            })
            
            # print(f"加载映射规则: {capl_rule} -> {vba_rule}")
            
        # print(f"\n共加载 {len(self.capl_to_vba_map)} 个CAPL规则的映射")
        
    def _load_vba_rules(self):
        """加载VBA规则文档"""
        rules_dir = Path("/Users/cuisijia/source/rules/output/vba-rules-txt")
        # print(f"\n开始加载VBA规则文档...")
        # print(f"VBA规则目录: {rules_dir}")
        
        # 遍历VBA规则目录及其所有子目录
        for file_path in rules_dir.rglob("*.txt"):
            # 获取规则名
            rule_name = file_path.stem
            
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            # 存储规则文档
            self.vba_rule_map[rule_name] = content
            
            # print(f"加载VBA规则文件: {file_path.name}")
            
        # print(f"\n共加载 {len(self.vba_rule_map)} 个VBA规则")
        
    def get_capl_mapping(self, capl_rule: str) -> List[dict]:
        """获取CAPL规则的映射"""
        return self.capl_to_vba_map.get(capl_rule, [])
        
    def get_vba_rule(self, vba_rule: str) -> str:
        """获取VBA规则的文档"""
        return self.vba_rule_map.get(vba_rule, "")

class CodeAnalyzerAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="code_analyzer",
            system_message="""你是一个CAPL代码分析专家，负责分割和提取CAPL脚本的内容。
            请专注于以下任务：
            1. 分割预处理部分
               - 提取#include指令
               - 提取#define宏定义
               - 提取typedef类型定义
            2. 分割变量定义部分
               - 提取全局变量定义
               - 提取局部变量定义
            3. 分割函数定义部分
               - 提取函数声明和定义
               - 提取函数体
            4. 分割结构体定义部分
               - 提取struct定义
               - 提取union定义
            
            请按照以下格式输出分割结果：
            1. 预处理部分
               ```c
               // 预处理指令：
               [直接复制源代码中的预处理指令，保持原始格式]
               ```
            2. 变量定义部分
               ```c
               // 变量定义：
               [直接复制源代码中的变量定义，保持原始格式]
               ```
            3. 函数定义部分
               ```c
               // 函数定义：
               [直接复制源代码中的函数定义，保持原始格式]
               ```
            4. 结构体定义部分
               ```c
               // 结构体定义：
               [直接复制源代码中的结构体定义，保持原始格式]
               ```
            
            重要说明：
            1. 必须直接复制源代码中的内容，不要修改或重新格式化
            2. 保持原始代码的缩进、空格和换行
            3. 不要添加任何额外的注释或说明
            4. 不要对代码进行任何美化或格式化
            5. 确保提取的内容与源代码完全一致
            
            分割完成后，请添加"ANALYSIS_COMPLETE"标记。""",
            llm_config=OPENAI_CONFIG
        )

class SyntaxRecognizerAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="syntax_recognizer",
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
    def __init__(self):
        super().__init__(
            name="import_converter",
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

class VariableConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="variable_converter",
            system_message="""你是一个代码转换专家，负责将CAPL代码中的全局变量和结构体定义转换为Python-VBA代码。
            请遵循以下规则：
            1. 分析CAPL代码中的全局变量定义
            2. 分析CAPL代码中的结构体定义
            3. 根据映射规则将CAPL类型转换为VBA类型：
               - 在 capl_to_vba_map 中查找CAPL类型
               - 找到对应的VBA类型映射
               - 根据 vba_rule_map 中的详细规则进行转换
            4. 保持代码结构和命名规范
            5. 使用Python-VBA的最佳实践
            
            转换步骤：
            1. 查找CAPL代码中的全局变量定义
            2. 查找CAPL代码中的结构体定义
            3. 对每个变量和结构体：
               - 在 capl_to_vba_map 中查找对应的映射规则
               - 根据映射规则找到VBA类型
               - 在 vba_rule_map 中查找该VBA类型的详细规则
               - 根据详细规则进行转换
            4. 确保所有变量和类都被正确转换
            
            请按照以下格式输出：
            1. 首先输出全局变量定义，并添加注释说明转换依据
            2. 然后输出结构体类定义，并添加注释说明转换依据
            3. 最后添加"VARIABLES_COMPLETE"标记
            
            示例输出格式：
            ```python
            # 全局变量定义
            global_var1 = 0
            global_var2 = ""
            global_var3 = None
            
            # 结构体类定义（如果有）
            class MyStruct:
                def __init__(self):
                    self.member1 = 0
                    self.member2 = ""
                    self.member3 = None
            
            class MyUnion:
                def __init__(self):
                    self.int_val = 0
                    self.float_val = 0.0
            ```
            
            VARIABLES_COMPLETE""",
            llm_config=OPENAI_CONFIG
        )

class FunctionConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="function_converter",
            system_message="""你是一个代码转换专家，负责将CAPL函数转换为Python-VBA函数。
            请遵循以下规则：
            1. 分析CAPL函数定义
            2. 根据映射规则将CAPL函数转换为VBA函数：
               - 在 capl_to_vba_map 中查找CAPL函数
               - 找到对应的VBA函数映射
               - 根据 vba_rule_map 中的详细规则进行转换
            3. 使用映射规则转换函数参数
            4. 使用映射规则转换函数体
            5. 使用映射规则转换消息处理
            6. 使用映射规则转换所有函数（包括定时器函数）
            7. 使用Python-VBA的最佳实践
            
            转换步骤：
            1. 查找CAPL函数定义
            2. 对每个函数：
               - 在 capl_to_vba_map 中查找对应的映射规则
               - 根据映射规则找到VBA函数
               - 在 vba_rule_map 中查找该VBA函数的详细规则
               - 根据详细规则进行转换
            3. 转换函数参数：
               - 在 capl_to_vba_map 中查找参数类型的映射规则
               - 根据映射规则找到VBA类型
               - 在 vba_rule_map 中查找该VBA类型的详细规则
            4. 转换函数体：
               - 在 capl_to_vba_map 中查找函数体中使用的CAPL函数
               - 根据映射规则转换为VBA函数
               - 在 vba_rule_map 中查找该VBA函数的详细规则
            5. 转换消息处理：
               - 在 capl_to_vba_map 中查找消息处理函数的映射规则
               - 在 vba_rule_map 中查找该VBA消息处理函数的详细规则
            6. 转换定时器函数：
               - 在 capl_to_vba_map 中查找定时器函数的映射规则
               - 在 vba_rule_map 中查找该VBA定时器函数的详细规则
            
            请只输出转换后的Python-VBA函数定义，并添加注释说明转换依据。
            转换完成后，请添加"FUNCTIONS_COMPLETE"标记。""",
            llm_config=OPENAI_CONFIG
        )

class PythonSyntaxCheckerAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="syntax_checker",
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
    def __init__(self):
        super().__init__(
            name="code_integrator",
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

class CodeConverter:
    def __init__(self):
        """初始化代码转换器"""
        print("初始化代码转换器...")
        
        # 加载规则
        self.rule_loader = RuleLoader()
        self.rule_loader.load_rules()
        print("规则加载完成...")
        
        # 获取所有规则
        self.all_rules = {
            "capl_to_vba_map": self.rule_loader.capl_to_vba_map,
            "vba_rule_map": self.rule_loader.vba_rule_map
        }
        
        # 初始化各个agent，并传入规则
        self.analyzer = CodeAnalyzerAgent()
        self.importer = ImportConverterAgent()
        self.syntax_recognizer = SyntaxRecognizerAgent()
        self.variable_converter = VariableConverterAgent()
        self.function_converter = FunctionConverterAgent()
        self.integrator = CodeIntegratorAgent()
        self.syntax_checker = PythonSyntaxCheckerAgent()
        
        # 将规则添加到每个agent的system_message中
        for agent in [self.variable_converter, self.function_converter]:
            agent.update_system_message(agent.system_message + f"\n\n可用规则：\n{str(self.all_rules)}")
            
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
                self.analyzer,
                self.importer,
                self.syntax_recognizer,
                self.variable_converter,
                self.function_converter,
                self.integrator,
                self.syntax_checker
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
                    python_vba_code = self.convert_code(capl_code, "CAPL", "Python-VBA")
                    
                    # 保存转换后的代码
                    if self.save_python_vba_file(python_vba_code, output_file):
                        print(f"成功保存转换后的代码到: {output_file}")
                    else:
                        print(f"保存转换后的代码失败: {output_file}")
        
    def convert_code(self, code: str, source_lang: str, target_lang: str) -> str:
        """转换代码的主方法"""
        print_colored(f"\n开始转换代码：从{source_lang}到{target_lang}", COLOR_SYSTEM)
        print_colored("="*50, COLOR_SYSTEM)
        
        # 初始化对话
        self.groupchat.messages = []
        print_colored("初始化对话...", COLOR_SYSTEM)
        
        # 添加初始消息
        initial_message = {
            "role": "user",
            "content": f"请将以下{source_lang}代码转换为{target_lang}代码：\n\n{code}"
        }
        self.groupchat.messages.append(initial_message)
        print_colored("添加初始消息...", COLOR_SYSTEM)
        print_colored(f"初始消息内容：\n{initial_message['content']}", COLOR_INFO)
        
        # 开始对话
        last_speaker = self.user_proxy
        round_count = 0
        current_phase = "analysis"  # 当前处理阶段
        
        # 存储语法识别结果
        recognized_types = []
        recognized_functions = []
        
        # 存储分析出的函数列表
        analyzed_functions = []
        
        while len(self.groupchat.messages) < self.groupchat.max_round:
            round_count += 1
            print_colored(f"\n第{round_count}轮对话开始...", COLOR_SYSTEM)
            
            # 根据当前阶段选择下一个发言者
            if current_phase == "analysis":
                next_agent = self.analyzer
            elif current_phase == "imports":
                next_agent = self.importer
            elif current_phase == "syntax_recognize":
                next_agent = self.syntax_recognizer
            elif current_phase == "variables":
                next_agent = self.variable_converter
            elif current_phase == "functions":
                # 如果还有未处理的函数，继续处理
                if analyzed_functions:
                    next_agent = self.function_converter
                    # 获取下一个要处理的函数
                    current_function = analyzed_functions.pop(0)
                    # 更新消息内容为当前函数
                    self.groupchat.messages[-1]["content"] = f"请转换以下函数：\n\n{current_function}"
                    print_colored(f"处理函数: {current_function.split('{')[0].strip()}", COLOR_DEBUG)
                else:
                    current_phase = "integration"
                    next_agent = self.integrator
            elif current_phase == "integration":
                next_agent = self.integrator
            else:
                next_agent = self.syntax_checker
                
            print_colored(f"选择下一个发言者: {next_agent.name}", COLOR_SYSTEM)
            
            # 只保留最近的消息，限制在5条以内
            recent_messages = self.groupchat.messages[-5:] if len(self.groupchat.messages) > 5 else self.groupchat.messages
            
            # 生成回复
            print_colored("生成回复...", COLOR_SYSTEM)
            print_colored("\n发送给大模型的消息内容：", COLOR_SYSTEM)
            print_colored("="*50, COLOR_SYSTEM)
            for msg in recent_messages:
                print_message(msg)
            print_colored("="*50, COLOR_SYSTEM)
            
            reply = next_agent.generate_reply(
                messages=recent_messages,
                sender=self.user_proxy
            )
            
            # 添加回复到消息历史
            if reply:
                print_colored(f"收到回复，长度: {len(reply)} 字符", COLOR_DEBUG)
                print_colored(f"回复内容：\n{reply}", COLOR_INFO)
                self.groupchat.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "name": next_agent.name
                })
                last_speaker = next_agent
                
                # 处理分析结果
                if current_phase == "analysis" and "ANALYSIS_COMPLETE" in reply:
                    # 提取函数定义部分
                    import re
                    function_pattern = r"```c\n// 函数定义：\n(.*?)\n```"
                    function_match = re.search(function_pattern, reply, re.DOTALL)
                    if function_match:
                        function_content = function_match.group(1)
                        # 分割各个函数
                        function_pattern = r"on\s+\w+\s*\([^)]*\)\s*{[^}]*}"
                        functions = re.findall(function_pattern, function_content, re.DOTALL)
                        analyzed_functions = functions
                        print_colored(f"分析出 {len(analyzed_functions)} 个函数", COLOR_DEBUG)
                        current_phase = "imports"
                
                # 处理导入转换结果
                elif current_phase == "imports" and "IMPORTS_COMPLETE" in reply:
                    current_phase = "syntax_recognize"
                
                # 处理语法识别结果
                elif current_phase == "syntax_recognize" and "SYNTAX_RECOGNIZED" in reply:
                    current_phase = "variables"
                
                # 处理变量转换结果
                elif current_phase == "variables" and "VARIABLES_COMPLETE" in reply:
                    current_phase = "functions"
                
                # 处理函数转换结果
                elif current_phase == "functions" and "FUNCTIONS_COMPLETE" in reply:
                    if not analyzed_functions:  # 所有函数都已处理完
                        current_phase = "integration"
                
                # 处理集成结果
                elif current_phase == "integration" and "INTEGRATION_COMPLETE" in reply:
                    current_phase = "syntax_check"
                
                # 处理语法检查结果
                elif current_phase == "syntax_check" and "SYNTAX_CHECK_COMPLETE" in reply:
                    print_colored("\n代码转换完成！", COLOR_SYSTEM)
                    return reply
        
        # 如果循环结束还没有得到结果，返回最后一个消息
        final_message = self.groupchat.messages[-1]["content"]
        print_colored("\n转换完成！", COLOR_SYSTEM)
        print_colored("="*50, COLOR_SYSTEM)
        return final_message
        
    if __name__ == "__main__":
    # 设置输入和输出目录
    input_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input")  # CAPL文件目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")  # Python-VBA文件输出目录
    
    print("初始化代码转换器...")
    converter = CodeConverter()
    
    # 处理整个目录
    converter.process_directory(input_dir, output_dir)
    
    print("\n所有文件处理完成！") 