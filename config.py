import os

# 从环境变量读取 API 密钥，如果未设置则使用默认值（仅用于开发）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

if not DEEPSEEK_API_KEY:
    raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量，请在运行前设置")

BASE_URL = "https://api.deepseek.com/v1"

MODEL_NAME = "deepseek-chat"

# 安全警告
if DEEPSEEK_API_KEY.startswith("sk-") and "os.getenv" not in str(os.getenv("DEEPSEEK_API_KEY", "")):
    print("WARNING: 使用硬编码的 API 密钥，建议设置 DEEPSEEK_API_KEY 环境变量")
    print("    export DEEPSEEK_API_KEY=your_actual_key  # Linux/Mac")
    print("    set DEEPSEEK_API_KEY=your_actual_key     # Windows")
