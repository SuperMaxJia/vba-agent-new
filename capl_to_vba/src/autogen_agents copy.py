import os
from typing import Dict, List, Optional
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import openai

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


class CodeAnalyzerAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="code_analyzer",
            system_message="""你是一个代码分析专家，负责分析代码结构。
            请遵循以下规则：
            1. 分析代码的导入语句
            2. 识别类定义
            3. 识别函数定义
            4. 分析主程序结构

            请用自然语言描述代码结构，包括：
            - 代码中使用了哪些导入语句
            - 定义了哪些类，每个类包含哪些属性和方法
            - 定义了哪些函数，每个函数的参数和返回值
            - 主程序的主要逻辑流程

            请确保描述清晰、准确，便于其他agent理解代码结构。

            分析完成后，请添加"ANALYSIS_COMPLETE"标记。""",
            llm_config=OPENAI_CONFIG
        )


class ImportConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="import_converter",
            system_message="""你是一个代码转换专家，负责将VBA代码中的导入语句转换为Python代码。
            请遵循以下规则：
            1. 将VBA的导入语句转换为等效的Python导入
            2. 处理所有必要的依赖关系
            3. 保持代码结构清晰

            请只输出转换后的Python导入语句。
            转换完成后，请添加"IMPORTS_COMPLETE"标记。""",
            llm_config=OPENAI_CONFIG
        )


class ClassConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="class_converter",
            system_message="""你是一个代码转换专家，负责将VBA类定义转换为Python类。
            请遵循以下规则：
            1. 将VBA类成员转换为Python类属性
            2. 将VBA方法转换为Python方法
            3. 正确处理继承关系
            4. 保持代码结构和命名规范

            请只输出转换后的Python类定义。
            转换完成后，请添加"CLASSES_COMPLETE"标记。""",
            llm_config=OPENAI_CONFIG
        )


class FunctionConverterAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="function_converter",
            system_message="""你是一个代码转换专家，负责将VBA函数转换为Python函数。
            请遵循以下规则：
            1. 将VBA函数参数转换为Python参数
            2. 将VBA函数体转换为Python代码
            3. 保持函数的功能和逻辑不变
            4. 使用Python的最佳实践

            请只输出转换后的Python函数定义。
            转换完成后，请添加"FUNCTIONS_COMPLETE"标记。""",
            llm_config=OPENAI_CONFIG
        )


class PythonSyntaxCheckerAgent(AssistantAgent):
    def __init__(self):
        super().__init__(
            name="syntax_checker",
            system_message="""你是一个Python语法检查专家，负责检查生成的Python代码是否符合语法规则。
            请遵循以下规则：
            1. 检查代码的缩进是否正确
            2. 检查函数定义的位置是否正确（不能在if语句块内定义函数）
            3. 检查导入语句的位置是否正确
            4. 检查类定义的位置是否正确
            5. 检查主程序的位置是否正确

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
            system_message="""你是一个代码集成专家，负责将转换后的Python代码组件整合在一起。
            请遵循以下规则：
            1. 确保所有导入语句位于文件顶部
            2. 正确排序类定义和函数定义
            3. 放置主程序在适当位置
            4. 检查并解决任何依赖关系问题

            请按照以下格式输出：
            1. 首先输出完整的集成后的Python代码
            2. 在代码之后添加一个空行
            3. 最后添加"TERMINATE"标记

            示例输出格式：
            ```python
            # 导入语句
            import ...

            # 类定义
            class ...

            # 函数定义
            def ...

            # 主程序
            if __name__ == "__main__":
                ...
            ```

            TERMINATE

            注意：必须包含完整的代码，不能只输出TERMINATE。""",
            llm_config=OPENAI_CONFIG
        )


class CodeConverter:
    def __init__(self):
        """初始化代码转换器"""
        print("初始化代码转换器...")

        # 初始化各个agent
        self.analyzer = CodeAnalyzerAgent()
        self.importer = ImportConverterAgent()
        self.class_converter = ClassConverterAgent()
        self.function_converter = FunctionConverterAgent()
        self.syntax_checker = PythonSyntaxCheckerAgent()
        self.integrator = CodeIntegratorAgent()
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
                self.class_converter,
                self.function_converter,
                self.syntax_checker,
                self.integrator
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

    def convert_code(self, code: str, source_lang: str, target_lang: str) -> str:
        """转换代码的主方法"""
        print(f"\n开始转换代码：从{source_lang}到{target_lang}")
        print("=" * 50)

        # 初始化对话
        self.groupchat.messages = []
        print("初始化对话...")

        # 添加初始消息
        initial_message = {
            "role": "user",
            "content": f"请将以下{source_lang}代码转换为{target_lang}代码：\n\n{code}"
        }
        self.groupchat.messages.append(initial_message)
        print("添加初始消息...")
        print(f"初始消息内容：\n{initial_message['content']}")

        # 开始对话
        last_speaker = self.user_proxy
        round_count = 0
        current_phase = "analysis"  # 当前处理阶段

        while len(self.groupchat.messages) < self.groupchat.max_round:
            round_count += 1
            print(f"\n第{round_count}轮对话开始...")

            # 根据当前阶段选择下一个发言者
            if current_phase == "analysis":
                next_agent = self.analyzer
            elif current_phase == "imports":
                next_agent = self.importer
            elif current_phase == "classes":
                next_agent = self.class_converter
            elif current_phase == "functions":
                next_agent = self.function_converter
            elif current_phase == "syntax_check":
                next_agent = self.syntax_checker
            else:
                next_agent = self.integrator

            print(f"选择下一个发言者: {next_agent.name}")

            # 生成回复
            print("生成回复...")
            reply = next_agent.generate_reply(
                messages=self.groupchat.messages,
                sender=self.user_proxy
            )

            # 添加回复到消息历史
            if reply:
                print(f"收到回复，长度: {len(reply)} 字符")
                print(f"回复内容：\n{reply}")
                self.groupchat.messages.append({
                    "role": "assistant",
                    "content": reply
                })
                last_speaker = next_agent

                # 根据回复内容更新处理阶段
                if "ANALYSIS_COMPLETE" in reply:
                    current_phase = "imports"
                elif "IMPORTS_COMPLETE" in reply:
                    current_phase = "classes"
                elif "CLASSES_COMPLETE" in reply:
                    current_phase = "functions"
                elif "FUNCTIONS_COMPLETE" in reply:
                    current_phase = "syntax_check"
                elif "SYNTAX_CORRECT" in reply:
                    current_phase = "integration"

                # 检查是否应该终止对话
                if isinstance(next_agent, CodeIntegratorAgent) and reply.rstrip().endswith("TERMINATE"):
                    print("代码集成完成，结束对话")
                    # 提取代码部分（去掉TERMINATE标记）
                    final_code = reply[:reply.rfind("TERMINATE")].strip()
                    print("\n转换完成！")
                    print("=" * 50)
                    return final_code

        # 如果循环结束还没有得到结果，返回最后一个消息
        final_message = self.groupchat.messages[-1]["content"]
        print("\n转换完成！")
        print("=" * 50)
        return final_message


if __name__ == "__main__":
    # 测试代码
    test_code = """
    Sub Test()
        Dim x As Integer
        x = 10
        MsgBox "Hello, World!"
    End Sub
    """

    print("初始化代码转换器...")
    converter = CodeConverter()
    print("开始转换测试代码...")
    result = converter.convert_code(test_code, "VBA", "Python")
    print("\n转换结果：")
    print("=" * 50)
    print(result)
    print("=" * 50)