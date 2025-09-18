# aippt/parlant/app.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .journey import PageDesignJourney, VERSION

api = FastAPI(title="AIPPT Parlant Page Designer", version=VERSION)

class GenerateReq(BaseModel):
    data_file: str = Field(..., description="aippt/parlant/data/xxxx.txt")
    design_file: str = Field(..., description="aippt/parlant/out/xxx.json")
    layout_hint: Optional[str] = Field(None, description="grid-2-2 等")

@api.get("/health")
async def health():
    return {"ok": True, "version": VERSION}

@api.post("/generate")
async def generate(req: GenerateReq):
    try:
        j = PageDesignJourney()
        res = await j.run(req.data_file, req.design_file, req.layout_hint)
        return res
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

# ---------- CLI ----------
def main_cli():
    import json
    parser = argparse.ArgumentParser(description="AIPPT Parlant Page Designer")
    parser.add_argument("--data-file", required=True, help="aippt/parlant/data/xxxx.txt")
    parser.add_argument("--design-file", required=True, help="aippt/parlant/out/xxx.json")
    parser.add_argument("--layout-hint", default=None, help="layout hint, e.g. grid-2-2")
    args = parser.parse_args()

    j = PageDesignJourney()
    res = asyncio.run(j.run(args.data_file, args.design_file, args.layout_hint))
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main_cli()
