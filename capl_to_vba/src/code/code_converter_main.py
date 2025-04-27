import os
import re
from colorama import init, Fore, Style
from typing import Dict, List, Optional, Tuple
from autogen import UserProxyAgent, GroupChat, GroupChatManager, AssistantAgent
import json  # 添加 json 模块导入

from ..config.llm_config import OPENAI_CONFIG
from ..data.rule_loader import RuleLoader
from ..data.conversation_data import ConversationData
from ..agents.code_analyzer import CodeAnalyzerAgent
from ..agents.syntax_recognizer import SyntaxRecognizerAgent
from ..agents.import_converter import ImportConverterAgent
from ..agents.code_converter import CodeConverterAgent
from ..agents.syntax_checker import PythonSyntaxCheckerAgent
from ..agents.code_integrator import CodeIntegratorAgent
from ..agents.final_checker import FinalCheckerAgent

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

class CodeConverter:
    """代码转换器类"""
    def __init__(self):
        self.rule_loader = RuleLoader()
        self.rule_loader.load_rules()
        
        # 初始化对话数据
        self.conversation_data = ConversationData()
        
        # 初始化各个代理
        self.code_analyzer = CodeAnalyzerAgent(self.rule_loader)
        self.importer = ImportConverterAgent(self.rule_loader)
        self.syntax_recognizer = SyntaxRecognizerAgent(self.rule_loader)
        self.converter = CodeConverterAgent(self.rule_loader)
        self.integrator = CodeIntegratorAgent(self.rule_loader)
        self.syntax_checker = PythonSyntaxCheckerAgent(self.rule_loader)
        self.final_checker = FinalCheckerAgent(self.rule_loader)
        
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
        try:
            print(reply)
            # 尝试解析 JSON 响应
            analysis_result = json.loads(reply)

            # 检查是否完成分析
            if analysis_result.get("status") == "ANALYSIS_COMPLETE":
                # 设置预处理部分
                self.conversation_data.preprocess_section = analysis_result.get("preprocess", "").strip()

                # 处理代码片段
                code_snippets = []
                for snippet in analysis_result.get("code_snippets", []):
                    # 组合全局变量和函数定义
                    global_vars = snippet.get("global_variables", "").strip()
                    function_code = snippet.get("function", "").strip()

                    # 如果有全局变量，先添加全局变量，然后是函数代码
                    full_snippet = ""
                    if global_vars:
                        full_snippet += global_vars + "\n\n"
                    full_snippet += function_code

                    code_snippets.append(full_snippet.strip())

                self.conversation_data.code_snippets = code_snippets
                self.conversation_data.processing_queue = code_snippets.copy()

                # 打印提取结果
                print_colored("\n提取的预处理部分：", COLOR_SYSTEM)
                print_colored(
                    self.conversation_data.preprocess_section if self.conversation_data.preprocess_section else "空",
                    COLOR_DEBUG)

                print_colored("\n提取的代码片段：", COLOR_SYSTEM)
                for i, snippet in enumerate(self.conversation_data.code_snippets, 1):
                    print_colored(f"\n代码片{i}：", COLOR_SYSTEM)
                    print_colored(snippet, COLOR_DEBUG)

                # 确定下一阶段
                if self.conversation_data.preprocess_section:
                    return "imports", self.conversation_data.preprocess_section
                else:
                    if self.conversation_data.has_remaining_snippets():
                        return "syntax_recognize", self.conversation_data.get_snippet()
                    else:
                        return "integration", self.conversation_data.converted_snippets

            return "error", "Analysis not complete"
        except json.JSONDecodeError:
            return "error", "Invalid JSON response"
        except Exception as e:
            return "error", f"Error processing analysis: {str(e)}"

    def _process_imports_phase(self, reply: str) -> Tuple[str, str]:
        """处理导入阶段的结果"""
        if "IMPORTS_COMPLETE" in reply:
            if self.conversation_data.has_remaining_snippets():
                return "syntax_recognize", self.conversation_data.get_snippet()
            else:
                return "integration", self.conversation_data.converted_snippets
        return "error", "No IMPORTS_COMPLETE"

    def _process_syntax_recognize_phase(self, reply: str) -> Tuple[str, str]:
        """处理语法识别阶段的结果"""
        if "SYNTAX_RECOGNIZED" in reply:
            try:
                # 提取 JSON 部分
                json_start = reply.find('{')
                json_end = reply.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = reply[json_start:json_end]
                    # 解析 JSON
                    result = json.loads(json_str)
                    recognized_items = result.get("syntax_elements", [])
                    
                    # 生成映射
                    self.vba_rule_map = {}
                    self.current_mapping = {}
                    for capl_function in recognized_items:


                        # 获取CAPL函数对应的VBA映射列表
                        vba_mapping_list = self.rule_loader.get_capl_mapping(capl_function)
                        self.current_mapping[capl_function] = vba_mapping_list
                        if not vba_mapping_list:
                            continue

                        # 遍历VBA映射列表中的每个函数
                        for vba_func in vba_mapping_list:
                            vba_rule = self.rule_loader.get_vba_rule(vba_func)
                            if vba_rule:
                                self.vba_rule_map[vba_func] = vba_rule


                    

                    
                    return "conversion", ""
                else:
                    return "error", "未找到有效的JSON数据"
            except json.JSONDecodeError as e:
                return "error", f"JSON解析错误: {str(e)}"
            except Exception as e:
                return "error", f"处理语法识别结果时出错: {str(e)}"
        return "error", "No SYNTAX_RECOGNIZED"

    def _process_conversion_phase(self, reply: str) -> Tuple[str, str]:
        """处理转换阶段的结果"""
        if "CONVERSION_COMPLETE" in reply:
            try:
                # 提取最终代码部分
                start_marker = "最终代码："
                end_marker = "CONVERSION_COMPLETE"
                
                # 找到开始和结束位置
                start_idx = reply.find(start_marker)
                end_idx = reply.find(end_marker)
                
                if start_idx != -1 and end_idx != -1:
                    # 提取代码内容
                    code_content = reply[start_idx + len(start_marker):end_idx].strip()
                    return "syntax_check", code_content
                else:
                    return "error", "未找到有效的代码内容"
            except Exception as e:
                return "error", f"提取代码内容时出错: {str(e)}"
        return "error", "No CONVERSION_COMPLETE"

    def _process_syntax_check_phase(self, reply: str) -> Tuple[str, str]:
        """处理语法检查阶段的结果"""
        if "SYNTAX_CHECK_COMPLETE" in reply:
            if self.conversation_data.has_remaining_snippets():
                return "syntax_recognize", self.conversation_data.get_snippet()
            else:
                # 将converted_snippets转换为字符串
                converted_str = "\n".join([str(snippet) for snippet in self.conversation_data.converted_snippets])
                return "integration", converted_str
        return "error", "No SYNTAX_CHECK_COMPLETE"

    def _process_integration_phase(self, reply: str) -> str:
        """处理集成阶段的结果"""
        if "INTEGRATION_COMPLETE" in reply:
            return "final_check", reply
        return "error", "No INTEGRATION_COMPLETE"


    def _process_final_check_phase(self, reply: str) -> Tuple[str, str]:
        """处理最终检查阶段的结果"""
        if "FINAL_CHECK_COMPLETE" in reply:
            return "complete", None
        return "error", "No FINAL_CHECK_COMPLETE"

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
        return "error", "The non-existent stage: " + current_phase

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
        current_content = self.conversation_data.capl_code
        
        while round_count < 15:  # 设置最大对话轮数
            round_count += 1
            print_colored(f"\n第{round_count}轮对话开始...", COLOR_SYSTEM)
            
            # 根据当前阶段选择下一个发言者
            current_agent = self.code_analyzer if round_count == 1 else self._get_agent_from_phase(current_phase)
            if current_agent is None:
                print_colored(f"阶段异常: 无法找到{current_phase}阶段的代理", COLOR_ERROR)
                break
                
            print_colored(f"当前发言者: {current_agent.name}", COLOR_SYSTEM)
            
            print_colored("\n发送给大模型的消息内容：", COLOR_SYSTEM)
            print_colored("="*50, COLOR_SYSTEM)

            # 构建消息
            message = self._build_message(current_phase, current_content)
            if not message:
                break

            reply = current_agent.generate_reply(
                messages=[message],
                sender=self.user_proxy
            )
            # 生成回复
            print_colored("即将发送给大模型，等待生成回复...", COLOR_SYSTEM)

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
            "final_check": self.final_checker
        }
        return phase_to_agent.get(next_phase, None)  # 如果找不到对应的代理，返回None

    def _build_message(self, current_phase: str, content: str = None) -> Dict:
        """根据当前阶段构建消息"""
        print("\n" + "=" * 50)
        print(f"当前阶段: {current_phase}")
        print("构建的消息内容:")

        message = None
        if current_phase == "analysis":
            message = {
                "role": "user",
                "content": f"请分析以下CAPL代码：\n\n{content}"
            }
        elif current_phase == "imports":
            message = {
                "role": "user",
                "content": f"请转换以下预处理指令：\n\n{content}"
            }
        elif current_phase == "syntax_recognize":
            message = {
                "role": "user",
                "content": f"请识别以下代码片段的语法结构：\n\n{content}"
            }

        elif current_phase == "conversion":
            message = {
                "role": "user",
                "content": f"请将以下CAPL代码按照规则转换为VBA代码：\n\n代码：\n{self.conversation_data.current_snippet}\n\n 映射关系：\n{self.current_mapping}\n\nVBA规则：\n{self.vba_rule_map}"
            }
        elif current_phase == "syntax_check":
            message = {
                "role": "user",
                "content": f"请检查以下VBA代码的语法：\n\n{content}"
            }
        elif current_phase == "integration":
            message = {
                "role": "user",
                "content": f"请整合以下代码片段：\n\n{content}"
            }
        elif current_phase == "final_check":
            message = {
                "role": "user",
                "content": f"请对以下VBA代码进行最终检查：\n\n{content}"
            }

        if message:
            print("-" * 50)
            print(f"角色: {message['role']}")
            print(f"内容:\n{message['content']}")
            print("=" * 50)
        else:
            print("未能构建消息！")
            print("=" * 50)

        return message