import argparse
import json
from src.main import app

def main():
    parser = argparse.ArgumentParser(description="Generate PPT content from a text file.")
    parser.add_argument("input_file", type=str, help="The path to the input text file.")
    args = parser.parse_args()

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {args.input_file}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    final_result = app.invoke({"raw_text": input_text})

    print("\n===============================")
    print("✅ PPT页面内容生成完成！")
    print("===============================")
    print(f"页面标题: {final_result['title']}\n")
    print("核心要点:")
    for point in final_result['bullet_points']:
        print(f"  - {point}")
    print("===============================\n")

    # Output as JSON for downstream consumption
    # print(json.dumps(final_result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()