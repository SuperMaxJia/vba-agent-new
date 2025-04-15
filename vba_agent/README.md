# VBA 代码生成助手

这是一个基于 OpenAI API 的 VBA 代码生成工具，可以根据自然语言描述生成相应的 VBA 代码。

## 功能特点

- 根据描述生成 VBA 代码
- 自动添加代码注释
- 支持交互式使用

## 安装说明

1. 确保已安装 Python 3.7 或更高版本
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```
3. 设置环境变量：
   ```bash
   export OPENAI_API_KEY="你的API密钥"
   ```

## 使用方法

运行以下命令启动程序：
```bash
python vba_agent.py
```

然后按照提示输入您需要的 VBA 功能描述即可。

## 注意事项

- 使用前请确保已正确设置 OPENAI_API_KEY 环境变量
- 生成的代码仅供参考，建议在使用前进行测试和验证 