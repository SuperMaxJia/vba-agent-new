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
COLOR_USER = Fore.GREEN
COLOR_ASSISTANT = Fore.BLUE
COLOR_SYSTEM = Fore.YELLOW
COLOR_ERROR = Fore.RED
COLOR_INFO = Fore.CYAN
COLOR_DEBUG = Fore.MAGENTA  # 添加调试颜色
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
print_colored(f"- 环境变量名称: OPENAI_API_KEY", COLOR_INFO)
print_colored(f"- 密钥长度: {len(OPENAI_CONFIG['config_list'][0]['api_key'])} 字符", COLOR_INFO)
print_colored(f"- 密钥前缀: {OPENAI_CONFIG['config_list'][0]['api_key'][:10]}", COLOR_INFO)
print_colored(f"- 密钥后缀: {OPENAI_CONFIG['config_list'][0]['api_key'][-10:]}", COLOR_INFO)

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

class CodeAnalyzerAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="code_analyzer",
            system_message="""你是一个CAPL代码分割专家，负责将CAPL脚本分割成预处理部分和代码片段列表。
            请专注于以下任务：
            1. 分割预处理部分
               - 只有下面的属于预处理指令 ：#include, #define
               - 保持原始格式和缩进
            
            2. 分割代码片段
               - 每个函数作为一个独立的代码片段
               - 对于每个函数，需要包含：
                 * 函数定义本身
                 * 函数内部使用的所有全局变量定义
                 * 如果函数内部使用了全局变量，必须在该代码片段中包含该全局变量的定义
               - 保持原始格式和缩进
            
            请按照以下格式输出分割结果：
            1. 预处理部分
               ```c
               预处理部分：
               [直接复制源代码中的预处理指令，保持原始格式]
               ```
            
            2. 代码片段列表
               ```c
               代码片段1：
               [直接复制源代码中的函数定义及其使用的全局变量定义，保持原始格式]
               
               代码片段2：
               [直接复制源代码中的函数定义及其使用的全局变量定义，保持原始格式]
               
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

class CodeConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="code_converter",
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
    """代码转换器类"""
    def __init__(self):
        self.rule_loader = RuleLoader()
        self.rule_loader.load_rules()
        
        # 初始化各个代理
        self.code_analyzer = CodeAnalyzerAgent()
        self.importer = ImportConverterAgent()
        self.syntax_recognizer = SyntaxRecognizerAgent()
        self.converter = CodeConverterAgent()
        self.integrator = CodeIntegratorAgent()
        self.syntax_checker = PythonSyntaxCheckerAgent()
        
        # 将规则添加到每个agent的system_message中
        for agent in [self.converter]:
            agent.update_system_message(agent.system_message + f"\n\n可用规则：\n{str(self.rule_loader.__dict__)}")
            
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
                    python_vba_code = self.convert_code(capl_code)
                    
                    # 保存转换后的代码
                    if self.save_python_vba_file(python_vba_code, output_file):
                        print(f"成功保存转换后的代码到: {output_file}")
                    else:
                        print(f"保存转换后的代码失败: {output_file}")
        
    def convert_code(self, capl_code: str) -> str:
        """转换CAPL代码为VBA代码"""
        # 初始化对话
        self.groupchat.messages = []
        print_colored("开始转换代码...", COLOR_SYSTEM)
        
        # 添加初始消息
        initial_message = {
            "role": "user",
            "content": f"请将以下CAPL代码转换为VBA代码：\n\n{capl_code}"
        }
        self.groupchat.messages.append(initial_message)
        print_colored("添加初始消息...", COLOR_SYSTEM)
        print_colored(f"初始消息内容：\n{initial_message['content']}", COLOR_INFO)
        
        # 开始对话
        last_speaker = self.user_proxy
        round_count = 0
        current_phase = "analysis"  # 当前处理阶段
        
        # 存储分析结果
        analyzed_sections = {
            "includes": [],  # 存储include部分
            "variables": [],  # 存储变量定义部分
            "functions": [],  # 存储函数定义部分
            "structs": []    # 存储结构体定义部分
        }
        
        # 存储当前正在处理的代码片段
        current_section = None
        current_section_type = None
        
        while len(self.groupchat.messages) < self.groupchat.max_round:
            round_count += 1
            print_colored(f"\n第{round_count}轮对话开始...", COLOR_SYSTEM)
            
            # 根据当前阶段选择下一个发言者
            if current_phase == "analysis":
                next_agent = self.code_analyzer
            elif current_phase == "imports":
                next_agent = self.importer
            elif current_phase == "syntax_recognize":
                next_agent = self.syntax_recognizer
            elif current_phase == "variables":
                next_agent = self.converter
            elif current_phase == "functions":
                next_agent = self.converter
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
                    # 提取各个部分
                    import re
                    
                    # 提取变量定义部分
                    var_pattern = r"```c\n// 变量定义：\n(.*?)\n```"
                    var_match = re.search(var_pattern, reply, re.DOTALL)
                    if var_match:
                        var_content = var_match.group(1)
                        # 提取变量定义
                        var_def_pattern = r"message\s+.*?;|msTimer\s+.*?;"
                        analyzed_sections["variables"] = re.findall(var_def_pattern, var_content)
                    
                    # 提取函数定义部分
                    func_pattern = r"```c\n// 函数定义：\n(.*?)\n```"
                    func_match = re.search(func_pattern, reply, re.DOTALL)
                    if func_match:
                        function_content = func_match.group(1)
                        # 提取函数定义
                        function_pattern = r"on\s+\w+\s*\([^)]*\)\s*{[^}]*}|on\s+\w+\s+\w+\s*{[^}]*}"
                        analyzed_sections["functions"] = re.findall(function_pattern, function_content, re.DOTALL)
                    
                    print_colored(f"分析完成：\n- {len(analyzed_sections['includes'])} 个include\n- {len(analyzed_sections['variables'])} 个变量\n- {len(analyzed_sections['functions'])} 个函数\n- {len(analyzed_sections['structs'])} 个结构体", COLOR_DEBUG)
                    
                    # 打印提取的内容
                    print_colored("\n提取的变量：", COLOR_DEBUG)
                    for var in analyzed_sections["variables"]:
                        print_colored(var, COLOR_DEBUG)
                    
                    print_colored("\n提取的函数：", COLOR_DEBUG)
                    for func in analyzed_sections["functions"]:
                        print_colored(func, COLOR_DEBUG)
                    
                    # 如果有include，先处理导入
                    if analyzed_sections["includes"]:
                        current_phase = "imports"
                        current_section = analyzed_sections["includes"]
                        current_section_type = "includes"
                    else:
                        # 初始化处理队列
                        self.processing_queue = {
                            "variables": analyzed_sections["variables"].copy(),
                            "functions": analyzed_sections["functions"].copy()
                        }
                        self.current_item = None
                        self.current_item_type = None
                        
                        # 开始处理第一个项目
                        if self.processing_queue["variables"]:
                            self.current_item = self.processing_queue["variables"].pop(0)
                            self.current_item_type = "variable"
                            current_phase = "syntax_recognize"
                            # 发送给 syntax_recognizer
                            self.groupchat.messages.append({
                                "role": "user",
                                "content": f"请识别以下CAPL代码中的语法：\n\n{self.current_item}"
                            })
                        elif self.processing_queue["functions"]:
                            self.current_item = self.processing_queue["functions"].pop(0)
                            self.current_item_type = "function"
                            current_phase = "syntax_recognize"
                            # 发送给 syntax_recognizer
                            self.groupchat.messages.append({
                                "role": "user",
                                "content": f"请识别以下CAPL代码中的语法：\n\n{self.current_item}"
                            })
                        else:
                            # 如果没有需要处理的项目，直接进入集成阶段
                            current_phase = "integration"
                
                # 处理导入转换结果
                elif current_phase == "imports" and "IMPORTS_COMPLETE" in reply:
                    current_phase = "syntax_recognize"
                
                # 处理语法识别结果
                elif current_phase == "syntax_recognize" and "SYNTAX_RECOGNIZED" in reply:
                    # 根据当前项目类型决定下一步
                    if self.current_item_type == "variable":
                        current_phase = "variables"
                        # 发送给 converter
                        self.groupchat.messages.append({
                            "role": "user",
                            "content": f"请转换以下CAPL变量定义：\n\n{self.current_item}"
                        })
                    elif self.current_item_type == "function":
                        current_phase = "functions"
                        # 发送给 converter
                        self.groupchat.messages.append({
                            "role": "user",
                            "content": f"请转换以下CAPL函数定义：\n\n{self.current_item}"
                        })
                
                # 处理变量转换结果
                elif current_phase == "variables" and "VARIABLES_COMPLETE" in reply:
                    # 检查是否还有待处理的变量
                    if self.processing_queue["variables"]:
                        self.current_item = self.processing_queue["variables"].pop(0)
                        self.current_item_type = "variable"
                        current_phase = "syntax_recognize"
                        # 发送给 syntax_recognizer
                        self.groupchat.messages.append({
                            "role": "user",
                            "content": f"请识别以下CAPL代码中的语法：\n\n{self.current_item}"
                        })
                    elif self.processing_queue["functions"]:
                        self.current_item = self.processing_queue["functions"].pop(0)
                        self.current_item_type = "function"
                        current_phase = "syntax_recognize"
                        # 发送给 syntax_recognizer
                        self.groupchat.messages.append({
                            "role": "user",
                            "content": f"请识别以下CAPL代码中的语法：\n\n{self.current_item}"
                        })
                    else:
                        # 所有项目都已处理完，进入集成阶段
                        current_phase = "integration"
                
                # 处理函数转换结果
                elif current_phase == "functions" and "FUNCTIONS_COMPLETE" in reply:
                    # 检查是否还有待处理的函数
                    if self.processing_queue["functions"]:
                        self.current_item = self.processing_queue["functions"].pop(0)
                        self.current_item_type = "function"
                        current_phase = "syntax_recognize"
                        # 发送给 syntax_recognizer
                        self.groupchat.messages.append({
                            "role": "user",
                            "content": f"请识别以下CAPL代码中的语法：\n\n{self.current_item}"
                        })
                    else:
                        # 所有项目都已处理完，进入集成阶段
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