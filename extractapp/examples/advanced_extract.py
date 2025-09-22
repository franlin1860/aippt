import os
import sys
import json
import textwrap
from dotenv import load_dotenv

# LangExtract + LiteLLM (Qwen) — Advanced (fenced JSON, passes, diagnostics)
try:
    import langextract as lx
    import langextract_litellm  # ensure LiteLLM provider registers
except ImportError as e:
    print(f"缺少依赖: {e}\n请安装: pip install langextract langextract-litellm litellm python-dotenv")
    sys.exit(1)


def main():
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key:
        print("错误：未找到 DASHSCOPE_API_KEY/QWEN_API_KEY。请在项目根目录创建 .env 并配置密钥。")
        sys.exit(1)

    # 1. Model Configuration
    model_config = lx.factory.ModelConfig(
        model_id="litellm/dashscope/qwen3-32b",
        provider="LiteLLMLanguageModel",
        provider_kwargs={
            "temperature": 0.3,
            "max_tokens": 2048,
            "stream": False,
            # "response_format": {"type": "json_object"}, # Removed: Causes parsing issues
            "extra_body": {"enable_thinking": False},
        },
    )
    model = lx.factory.create_model(model_config)

    # 2. Prompt
    prompt = textwrap.dedent("""
        Extract characters and emotions in order of appearance.
        Use exact text for extractions. Do not paraphrase or overlap entities.
        Provide meaningful attributes for each entity to add context.
        Output a single JSON object wrapped in ```json ... ```.
        """)

    # 3. Examples (Required for reliable extraction)
    examples = [
        lx.data.ExampleData(
            text="Sarah was ecstatic about the news, but Mark felt a deep sadness.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="character",
                    extraction_text="Sarah",
                    attributes={"emotional_state": "ecstatic"}
                ),
                lx.data.Extraction(
                    extraction_class="emotion",
                    extraction_text="ecstatic",
                    attributes={"feeling": "joy"}
                ),
                lx.data.Extraction(
                    extraction_class="character",
                    extraction_text="Mark",
                    attributes={"emotional_state": "sad"}
                ),
                lx.data.Extraction(
                    extraction_class="emotion",
                    extraction_text="deep sadness",
                    attributes={"feeling": "sadness"}
                ),
            ]
        )
    ]

    # 4. Extraction
    text = "Alice met Bob at the cafe. She felt a sudden joy meeting him again."
    result = lx.extract(
        text,
        model=model,
        prompt_description=prompt,
        examples=examples,
        #suppress_parse_errors=True,
        extraction_passes=3, # Run multiple passes for more robust extraction
    )

    # 5. Save results and diagnostics
    # Create a dedicated directory for the output to avoid IsADirectoryError
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", "advanced_extract_output"))
    os.makedirs(save_dir, exist_ok=True)

    # save_annotated_documents creates a directory and saves `data.jsonl` inside it.
    lx.io.save_annotated_documents([result], save_dir)

    # The actual JSONL path is inside the directory created by the save function.
    jsonl_path = os.path.join(save_dir, "data.jsonl")

    html_path = os.path.join(save_dir, "visualization.html")
    html_content = lx.visualize(jsonl_path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(getattr(html_content, "data", html_content))

    print("✅ 已保存示例产物:")
    for p in (jsonl_path, html_path):
        print("-", p)


if __name__ == "__main__":
    main()