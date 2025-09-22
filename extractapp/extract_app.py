# extract_app.py

import os
import textwrap
import json
from dotenv import load_dotenv

# 导入 langextract 和 langextract-litellm
try:
    import langextract as lx
    # 导入 langextract-litellm 以自动注册 LiteLLM provider
    import langextract_litellm
    print("✅ langextract 和 langextract-litellm 加载成功")
    
except ImportError as e:
    print(f"错误：缺少必要的依赖库: {e}")
    print("请安装以下依赖：")
    print("pip install langextract langextract-litellm litellm python-dotenv")
    exit(1)

def main():
    """
    主函数，执行从加载配置到信息提取的全过程。
    """
    # --- 步骤 1: 加载环境变量 ---
    # 从项目根目录的 .env 文件中加载配置
    print("正在加载 .env 文件中的环境变量...")
    load_dotenv()

    # 从环境中获取API密钥
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not dashscope_api_key:
        print("错误：未找到 DASHSCOPE_API_KEY。")
        print("请在 .env 文件中配置阿里云 DashScope API 密钥")
        return
    
    print("使用阿里云 Qwen API 密钥")
    # LiteLLM 会自动使用 DASHSCOPE_API_KEY 环境变量
    
    # --- 步骤 2: 定义提取任务 ---
    print("正在定义信息提取任务...")
    # 定义提示，清晰地描述需要提取什么信息
    prompt_description = textwrap.dedent("""        Extract all characters, locations, and events from the text.
        - The extracted text must exactly match the original text.
        - Provide meaningful attributes for each entity to add context.
    """)

    # 提供高质量的示例（Few-shot Example）来指导模型
    examples = [
        lx.data.ExampleData(
            text="2024年，李明在北京的故宫博物院参观时，偶然发现了一本尘封已久的古籍。",
            extractions=[
                lx.data.Extraction(extraction_class='character', extraction_text='李明', attributes={'year': 2024}),
                lx.data.Extraction(extraction_class='location', extraction_text='北京', attributes={'specific_place': '故宫博物院'}),
                lx.data.Extraction(extraction_class='event', extraction_text='发现了一本尘封已久的古籍', attributes={'protagonist': '李明'}),
            ]
        )
    ]

    # --- 步骤 3: 准备模型和输入文本 ---
    model_config = lx.factory.ModelConfig(
        model_id="litellm/dashscope/qwen3-32b",
        provider="LiteLLMLanguageModel",
        provider_kwargs={
            "temperature": 0.1,
            "max_tokens": 2048,
            "stream": False,
            "extra_body": {"enable_thinking": False},
        },
    )
    model = lx.factory.create_model(model_config)
    input_text = "项目启动会议于上周在上海的环球金融中心举行，由项目经理王伟主持，确定了项目的关键里程碑。"

    # --- 步骤 4: 执行提取并处理结果 ---
    try:
        # 使用 langextract 进行信息提取
        print(f"开始使用 langextract 和 LiteLLM 进行信息提取...")
        
        # 使用 lx.extract 函数，通过 model_id 指定 LiteLLM 模型
        result = lx.extract(
            text_or_documents=input_text,
            prompt_description=prompt_description,
            examples=examples,
            model=model
        )
        
        print("\n✅ 提取成功！")
        
        # 打印提取到的实体
        print("\n提取到的实体:")
        if result and result.extractions:
            for extraction in result.extractions:
                print(f"- 类别: {extraction.extraction_class}, "
                      f"文本: '{extraction.extraction_text}', "
                      f"属性: {extraction.attributes}")
        else:
            print("- 无提取结果")

        # --- 步骤 5: 保存结果 ---
        # 定义输出目录和文件名
        output_dir = "outputs/extract_app"
        os.makedirs(output_dir, exist_ok=True)
        jsonl_path = os.path.join(output_dir, "results.jsonl") # 使用更具体的文件名

        # 将结果保存为 JSONL 文件
        docs = [result] if result else []
        lx.io.save_annotated_documents(docs, jsonl_path)
        print(f"\n结果已保存至: {jsonl_path}")

        # 生成可交互的 HTML 可视化文件
        html_path = os.path.join(output_dir, "visualization.html")
        html_content = lx.visualize(jsonl_path)
        with open(html_path, "w", encoding='utf-8') as f:
            f.write(getattr(html_content, "data", html_content))
        print(f"可视化文件已生成: {html_path}")
        print("\n请用浏览器打开 HTML 文件查看高亮标注的提取结果。")
        
    except Exception as e:
        print(f"\n❌ 提取过程中发生错误: {e}")
        print("请检查：\n1. DASHSCOPE_API_KEY 是否有效。\n2. 网络连接是否可以访问阿里云DashScope服务。\n3. 项目依赖是否已正确安装。")

if __name__ == "__main__":
    main()