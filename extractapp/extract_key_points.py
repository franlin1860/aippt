import os 
import sys 
import textwrap 
from dotenv import load_dotenv 
 
# 确保 langextract 和插件能被正确导入 
try:
    import langextract as lx
    import langextract_litellm
except ImportError as e:
    print(f"缺少依赖: {e}\n请安装: pip install langextract langextract-litellm litellm python-dotenv")
    sys.exit(1)
 
def main(): 
    """ 
    本示例演示如何使用 langextract 实现“抽取式摘要”。 
    目标：从给定的段落中，提取出最能代表核心思想的句子，作为PPT要点。 
    """ 
    # --- 1. 环境准备 --- 
    load_dotenv() 
    api_key = os.getenv("DASHSCOPE_API_KEY") 
    if not api_key: 
        print("错误：未找到 DASHSCOPE_API_KEY。请在 .env 文件中配置密钥。") 
        sys.exit(1) 
 
    print("环境配置加载完毕...") 
 
    # --- 2. 定义提取任务：提取关键句子 --- 
 
    # Prompt 指示模型去“提取”，而非“总结” 
    # 强调了提取目标是“独立的、表达完整思想的句子或核心短语” 
    prompt_description = textwrap.dedent(""" 
    你的任务是从提供的文本段落中，识别并提取出最能概括其核心成就、关键发现或主要观点的句子。 
     
    提取规则: 
    1.  提取的内容必须是原文中一字不差的、连续的文本片段。 
    2.  每个提取出的片段本身应该是一个能够独立表达完整思想的句子或核心短语。 
    3.  不要提取过于宽泛或缺乏具体信息的句子。 
    """) 
 
    # Few-shot 示例，向模型展示期望的提取结果 
    # 示例中，我们从一段话里精确地抽取出两个最关键的成果句子 
    examples = [ 
        lx.data.ExampleData( 
            text=( 
                "根据最新的市场分析报告，我们的旗舰产品'Phoenix'在第三季度的市场份额增长了5%。" 
                "这一增长主要归功于我们成功的社交媒体营销活动，该活动触达了超过一千万潜在用户。" 
                "同时，客户满意度调查显示，95%的用户对我们的售后服务表示满意。" 
            ), 
            extractions=[ 
                lx.data.Extraction( 
                    extraction_class="key_point", 
                    extraction_text="旗舰产品'Phoenix'在第三季度的市场份额增长了5%", 
                    attributes={"category": "Market Performance"} 
                ), 
                lx.data.Extraction( 
                    extraction_class="key_point", 
                    extraction_text="95%的用户对我们的售后服务表示满意", 
                    attributes={"category": "Customer Satisfaction"} 
                ), 
            ], 
        ) 
    ] 
 
    # --- 3. 准备输入内容 --- 
    # 模拟一个文档中的两个二级标题下的内容 
    document_sections = [ 
        { 
            "title": "一季度技术创新成果", 
            "content": ( 
                "在第一季度，我们的研发团队成功将用户留存率提升了15个百分点，这主要得益于" 
                "我们推出的全新个性化推荐系统。该系统通过先进的机器学习算法分析用户行为，" 
                "为每位用户提供量身定制的内容，从而显著增强了用户粘性。此外，我们也完成了" 
                "对后端架构的重构，将API平均响应时间减少了300毫秒，提升了产品稳定性。" 
            ) 
        }, 
        { 
            "title": "市场拓展与合作", 
            "content": ( 
                "市场方面，我们与欧洲领先的经销商'GlobalConnect'达成了独家战略合作协议。" 
                "此举预计将在未来一年内为我们带来超过500万欧元的新增收入。为了支持全球化战略，" 
                "我们的产品现已完成本地化，支持法语、德语和西班牙语。" 
            ) 
        } 
    ] 
     
    # 我们将所有段落内容合并，让 langextract 一次性处理 
    # （对于非常长的文档，langextract 会自动处理分块） 
    full_text = "\n\n".join([section["content"] for section in document_sections]) 
     
    print("准备从以下文本中提取要点:\n---") 
    print(full_text) 
    print("---\n") 
 
 
    # --- 4. 配置模型并运行提取 --- 
    model_config = lx.factory.ModelConfig( 
        model_id="litellm/dashscope/qwen3-32b", # 使用因为它在遵循长指令和理解上下文方面通常表现更好 
        provider="LiteLLMLanguageModel", 
        provider_kwargs={ 
            "temperature": 0.3, # 对于提取任务，使用0温度以获得最稳定、最可预测的结果 
            "max_tokens": 4096, 
            "stream": False,
            "extra_body": {"enable_thinking": False},
        }, 
    ) 
    model = lx.factory.create_model(model_config) 
 
    print("正在调用模型进行关键句提取...") 
    result = lx.extract( 
        text_or_documents=full_text, 
        prompt_description=prompt_description, 
        examples=examples, 
        model=model, 
    ) 
    print("模型处理完成！") 
 
    # --- 5. 展示与保存结果 --- 
    docs = result if isinstance(result, list) else [result] 
     
    # 在控制台打印提取出的PPT要点 
    print("\n====================") 
    print("提取出的PPT要点如下:") 
    print("====================") 
    for i, doc in enumerate(docs): 
        if not doc.extractions: 
            print("未从文本中提取出任何要点。") 
        for extraction in doc.extractions: 
            if extraction.extraction_class == "key_point": 
                # 格式化输出，使其看起来像PPT的点 
                print(f"  - {extraction.extraction_text}  (来源: {extraction.attributes.get('category', 'N/A')})") 
 
    # 保存JSONL和HTML可视化文件 
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "outputs", "key_points_extraction")) 
    os.makedirs(out_dir, exist_ok=True) 
 
    lx.io.save_annotated_documents(docs, out_dir)
    jsonl_path = os.path.join(out_dir, "data.jsonl")
 
    html_content = lx.visualize(jsonl_path) 
    html_path = os.path.join(out_dir, "visualization.html") 
    with open(html_path, "w", encoding="utf-8") as f: 
        f.write(getattr(html_content, "data", html_content)) 
 
    print("\n✅ 已保存详细产物:") 
    print(f"- 结构化数据: {jsonl_path}") 
    print(f"- 可视化报告: {html_path} (请用浏览器打开查看高亮原文)") 
 
 
if __name__ == "__main__": 
    main()