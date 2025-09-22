import os
import sys
from dotenv import load_dotenv

# Add local packages to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
litellm_provider_path = os.path.join(project_root, 'langextract_litellm-0.1.0')
sys.path.insert(0, litellm_provider_path)

# Directly import litellm for a minimal test
import litellm

def debug_litellm():
    """A minimal script to debug the litellm completion call."""
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key:
        print("错误：未找到 DASHSCOPE_API_KEY/QWEN_API_KEY。")
        sys.exit(1)

    print("ℹ️ [Debug] API Key loaded.")
    
    model = "dashscope/qwen3-32b"
    messages = [{"content": "Hello, how are you?", "role": "user"}]

    print(f"ℹ️ [Debug] Calling litellm.completion() with model {model}...")
    
    try:
        # Set a timeout to prevent hanging indefinitely
        response = litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key, # Explicitly pass the key
            stream=False,
            temperature=0.3,
            max_tokens=2048,
            extra_body={"enable_thinking": False},
            timeout=120  # 120-second timeout
        )
        print("✅ [Debug] litellm.completion() completed.")
        print("ℹ️ [Debug] Response:")
        print(response)
    except Exception as e:
        print(f"❌ [Debug] An error occurred during litellm.completion(): {e}")

if __name__ == "__main__":
    debug_litellm()