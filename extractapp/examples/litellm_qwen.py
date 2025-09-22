import os
import litellm
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 清除LiteLLM配置缓存（避免使用旧的智谱AI配置）
if hasattr(litellm, '_config'):
    delattr(litellm, '_config')

# 1) 读取 API Key（阿里云 DashScope API Key）
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")

# 2) 读取 LiteLLM 配置（必须从环境变量中获取）
model = os.getenv("LITELLM_MODEL_NAME")
api_base = os.getenv("LITELLM_API_BASE")

if not model:
    raise ValueError("请设置 LITELLM_MODEL_NAME 环境变量")
if not api_base:
    raise ValueError("请设置 LITELLM_API_BASE 环境变量")

# 3) 准备消息负载
messages = [
    {"role": "system", "content": "你是一个乐于助人的人工智能助手。"},
    {"role": "user", "content": "你好！请用一句话介绍一下你自己。"},
]

print(f"使用模型: {model}")
print(f"API 基地址: {api_base}")

# 4) 调用 litellm.completion 并进行简单验证
try:
    response = litellm.completion(
        model=model,
        messages=messages,
        api_base=api_base,
        api_key=api_key,
        temperature=0.7,
        enable_thinking=False,  # 必须设置为False
    )

    content = response.choices[0].message.content

    print("\n--- 模型响应 ---")
    print(content)
    print("----------------\n")

    # 基于文档中的验证标准进行轻量校验
    lower = content.lower()
    if ("qwen" in lower or "通义" in lower or "人工智能" in lower or "助手" in lower):
        print("✅ 验证成功：响应内容表明Qwen模型正常工作。")
    else:
        print("⚠️ 验证警告：响应内容不符合预期，请检查配置或重试。")

except Exception as e:
    print(f"调用出错: {e}")