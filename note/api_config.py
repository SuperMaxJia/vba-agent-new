#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
from typing import Dict

def save_to_shell_config(api_key: str) -> None:
    """将API密钥保存到shell配置文件中"""
    # 获取用户主目录
    home_dir = os.path.expanduser("~")
    
    # 根据不同的shell选择配置文件
    shell = os.getenv("SHELL", "")
    if "zsh" in shell:
        config_file = os.path.join(home_dir, ".zshrc")
    else:
        config_file = os.path.join(home_dir, ".bashrc")
    
    # 检查是否已经存在配置
    export_line = f'export OPENAI_API_KEY="{api_key}"\n'
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            content = f.read()
            if export_line in content:
                print(f"✅ API密钥已存在于 {config_file}")
                return
    
    # 添加配置到文件
    with open(config_file, "a") as f:
        f.write(f"\n# OpenAI API Key\n{export_line}")
    print(f"✅ API密钥已保存到 {config_file}")
    
    # 立即生效
    subprocess.run(["source", config_file], shell=True)

def configure_openai() -> Dict:
    """配置OpenAI API设置"""
    # 原始API密钥
    original_api_key = "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"
    
    # 设置前的环境变量值
    before_set = os.getenv("OPENAI_API_KEY")
    print(f"\n设置前的环境变量值: {before_set}")
    
    # 永久保存API密钥
    save_to_shell_config(original_api_key)
    
    # 设置当前进程的环境变量
    os.environ["OPENAI_API_KEY"] = original_api_key
    print(f"设置的新值: {original_api_key}")
    
    # 设置后的环境变量值
    after_set = os.getenv("OPENAI_API_KEY")
    print(f"设置后的环境变量值: {after_set}")
    
    # 详细验证
    print("\n验证结果：")
    if after_set == original_api_key:
        print("✅ API密钥设置成功")
        print("   - 设置的值与读取的值完全匹配")
    else:
        print("❌ API密钥设置失败")
        print("   - 设置的值与读取的值不匹配")
    
    # 返回配置字典
    return {
        "config_list": [
            {
                "model": "gpt-4-turbo-preview",
                "api_key": original_api_key
            }
        ],
        "temperature": 0.7,
        "timeout": 120,
        "cache_seed": None
    }

def main():
    """主函数"""
    print("开始设置OpenAI API配置...")
    config = configure_openai()
    print("\n配置信息：")
    print(f"模型: {config['config_list'][0]['model']}")
    print(f"温度: {config['temperature']}")
    print(f"超时: {config['timeout']}秒")
    print("\n设置完成！")
    print("\n注意：请重新打开终端或运行 'source ~/.zshrc' (或 'source ~/.bashrc') 使环境变量生效")

if __name__ == "__main__":
    main() 