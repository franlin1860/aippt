# aippt/parlant/run_system_tests.py
# -*- coding: utf-8 -*-
"""
批量系统测试脚本：
- 支持使用 --data-glob 灵活选择一批输入文件
- 为每个输入自动写出对应的 JSON 到 out/ 目录
- 对结果做同样的基本断言与统计
用法：
python3 aippt/parlant/run_system_tests.py --data-glob "aippt/parlant/data/*.txt"
"""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path

from aippt.parlant.journey import PageDesignJourney

def parse_args():
    ap = argparse.ArgumentParser(description="Batch system test for AIPPT Parlant")
    ap.add_argument("--data-glob", required=True, help='e.g. "aippt/parlant/data/*.txt"')
    ap.add_argument("--out-dir", default="aippt/parlant/out", help="output dir for json")
    ap.add_argument("--min-blocks", type=int, default=3)
    ap.add_argument("--max-blocks", type=int, default=6)
    return ap.parse_args()

async def run_one(j: PageDesignJourney, data_file: Path, out_dir: Path, min_blocks: int, max_blocks: int) -> dict:
    out_file = out_dir / (data_file.stem + ".json")
    res = await j.run(str(data_file), str(out_file))
    ok = res.get("ok") is True
    design = res.get("design", {})
    blocks = design.get("blocks", [])
    constraints_ok = ok and isinstance(blocks, list) and (min_blocks <= len(blocks) <= max_blocks) and all(len(b.get("content","").strip()) <= 50 for b in blocks)
    return {
        "file": str(data_file),
        "ok": ok,
        "blocks": len(blocks),
        "constraints_ok": constraints_ok,
        "out": str(out_file)
    }

async def main():
    args = parse_args()
    paths = sorted(Path().glob(args.data_glob))
    if not paths:
        print(f"[WARN] No files matched: {args.data_glob}")
        return

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    j = PageDesignJourney()
    results = []
    for p in paths:
        r = await run_one(j, p, out_dir, args.min_blocks, args.max_blocks)
        results.append(r)

    # 汇总打印
    total = len(results)
    ok_cnt = sum(1 for r in results if r["ok"])
    constr_cnt = sum(1 for r in results if r["constraints_ok"])
    print(json.dumps({
        "total": total,
        "ok": ok_cnt,
        "constraints_ok": constr_cnt,
        "items": results
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
