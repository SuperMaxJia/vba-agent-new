from openai import OpenAI

class Translator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def translate(self, text: str, target_language: str = "中文") -> str:
        """
        将文本翻译成目标语言
        
        Args:
            text (str): 要翻译的文本
            target_language (str): 目标语言，默认为中文
            
        Returns:
            str: 翻译后的文本
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"你是一个专业的翻译助手。请将以下文本翻译成{target_language}，保持原文的语气和风格。"},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"翻译过程中出现错误: {str(e)}"

def main():
    # 直接设置API密钥
    api_key = "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"  # 在这里替换成你的实际API密钥
    translator = Translator(api_key)
    
    print("欢迎使用翻译助手！输入'q'退出。")
    while True:
        text = input("\n请输入要翻译的文本: ")
        if text.lower() == 'q':
            break
            
        target_lang = input("请输入目标语言（直接回车默认为中文）: ").strip()
        if not target_lang:
            target_lang = "中文"
            
        result = translator.translate(text, target_lang)
        print(f"\n翻译结果: {result}")

if __name__ == "__main__":
    main() 