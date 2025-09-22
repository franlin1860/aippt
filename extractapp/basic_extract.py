import os
import sys
import textwrap
from dotenv import load_dotenv

# LangExtract + LiteLLM (Qwen) — Basic Example
try:
    import langextract as lx
    import langextract_litellm  # ensure LiteLLM provider registers
except ImportError as e:
    print(f"缺少依赖: {e}\n请安装: pip install langextract langextract-litellm litellm python-dotenv")
    sys.exit(1)


def main():
    """
    Main function to run the basic extraction process.
    """
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
            "extra_body": {"enable_thinking": False},
        },
    )
    model = lx.factory.create_model(model_config)

    # 2. Prompt
    prompt = textwrap.dedent("""
        Extract characters from the text.
        Output a single JSON object wrapped in ```json ... ```.
    """)

    # 3. Examples
    examples = [
        lx.data.ExampleData(
            text="Harry meets Hermione.",
            extractions=[
                lx.data.Extraction(extraction_class='character', extraction_text='Harry'),
                lx.data.Extraction(extraction_class='character', extraction_text='Hermione'),
            ],
        ),
    ]

    # 4. Extraction
    text = "Alice meets Bob in Wonderland."
    result = lx.extract(
        text_or_documents=text,
        model=model,
        prompt_description=prompt,
        examples=examples,
        #suppress_parse_errors=True,
    )

    # 5. Save results
    if result and result.extractions:
        print("提取结果:")
        for extraction in result.extractions:
            print(f"- 类别: {extraction.extraction_class}, 文本: '{extraction.extraction_text}'")
    else:
        print("- 无提取结果")

    save_dir = "outputs/basic_extract"
    os.makedirs(save_dir, exist_ok=True)

    docs = [result] if result else []
    # lx.io.save_annotated_documents expects a directory
    lx.io.save_annotated_documents(docs, save_dir)
    jsonl_path = os.path.join(save_dir, "data.jsonl")

    html_path = os.path.join(save_dir, "visualization.html")
    html_content = lx.visualize(jsonl_path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(getattr(html_content, "data", html_content))

    print("\n✅ 已保存示例产物:")
    print(f"- {jsonl_path}")
    print(f"- {html_path}")


if __name__ == "__main__":
    main()



