import os
import sys
import textwrap
from dotenv import load_dotenv

# LangExtract + LiteLLM (Qwen) — Minimal Example
# Add local packages to path to avoid installation issues
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
litellm_provider_path = os.path.join(project_root, 'langextract_litellm-0.1.0')
sys.path.insert(0, litellm_provider_path)

import langextract as lx
import langextract_litellm  # ensure LiteLLM provider registers


def main():
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key:
        print("错误：未找到 DASHSCOPE_API_KEY/QWEN_API_KEY。请在项目根目录创建 .env 并配置密钥。")
        sys.exit(1)

    # 1) Prompt —- concise and structured instructions
    prompt = textwrap.dedent("""
    Your task is to extract characters, emotions, and relationships from the text in order of appearance.

    Follow these rules precisely:
    1.  Your entire output must be a single JSON object.
    2.  The JSON object must be enclosed in ```json and ``` markers.
    3.  Do not add any text, explanation, or conversation before or after the JSON block.
    4.  Use the exact text from the source for all extractions. Do not paraphrase.
    5.  Do not create overlapping entities.
    6.  For each extracted entity, provide meaningful attributes to add context.
    """)

    # 2) Few-shot example to steer the model
    examples = [
        lx.data.ExampleData(
            text=(
                "ROMEO. But soft! What light through yonder window breaks? It is "
                "the east, and Juliet is the sun."
            ),
            extractions=[
                lx.data.Extraction(
                    extraction_class="character",
                    extraction_text="ROMEO",
                    attributes={"emotional_state": "wonder"},
                ),
                lx.data.Extraction(
                    extraction_class="emotion",
                    extraction_text="But soft!",
                    attributes={"feeling": "gentle awe"},
                ),
                lx.data.Extraction(
                    extraction_class="relationship",
                    extraction_text="Juliet is the sun",
                    attributes={"type": "metaphor"},
                ),
            ],
        )
    ]

    # 3) Configure the model using ModelConfig for better structure
    model_config = lx.factory.ModelConfig(
        model_id="litellm/dashscope/qwen3-32b",
        provider="LiteLLMLanguageModel",
        provider_kwargs={
            "temperature": 0.1,
            "max_tokens": 4096,
            "stream": False,
            "extra_body": {"enable_thinking": False},
        },
    )
    model = lx.factory.create_model(model_config)

    # 4) Run extraction via LangExtract
    result = lx.extract(
        text_or_documents=(
            "Lady Juliet gazed longingly at the stars, her heart aching for Romeo"
        ),
        prompt_description=prompt,
        examples=examples,
        model=model,
    )

    # Normalize to list for IO helpers
    docs = result if isinstance(result, list) else [result]

    # 4) Save JSONL & HTML visualization
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
    os.makedirs(out_dir, exist_ok=True)

    # The save_annotated_documents function creates a directory at the specified path
    # and saves a file named 'data.jsonl' inside it, based on the logs.
    save_dir = os.path.join(out_dir, "examples_minimal_output")
    lx.io.save_annotated_documents(docs, save_dir)

    # Therefore, the actual path to the JSONL file is inside that directory.
    jsonl_path = os.path.join(save_dir, "data.jsonl")
    html_content = lx.visualize(jsonl_path)
    html_path = os.path.join(out_dir, "examples_minimal.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(getattr(html_content, "data", html_content))

    print("✅ 已保存示例产物:")
    print("-", jsonl_path)
    print("-", html_path)


if __name__ == "__main__":
    main()