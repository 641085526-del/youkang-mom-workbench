#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawl-platforms.py
================================================================
优康宝贝 · 全网热搜采集脚本  (v1.0)
================================================================

采集真实公开热搜榜数据（无需登录的公开榜单），输出 platforms.json：

  1. 抖音热榜   —— https://www.douyin.com/aweme/v1/web/hot/search/list/
                   返回 word（热搜词）+ hot_value（热度值）+ position（排名）
  2. 快手热榜   —— https://www.kuaishou.com/graphql  (GraphQL: visionHotRank)
                   返回 name（热搜词）+ hotValue（热度）+ rank（排名）

说明：
  - 仅抓取平台公开的热搜/热榜榜单，不涉及需登录的私有数据。
  - 请合理控制请求频率，遵守目标平台的使用条款与 robots.txt。
  - 淘宝/小红书/美团因需要登录或签名，免费公开接口无法获取，不在本脚本范围。

用法：
  python3 crawl-platforms.py                  # 输出 ./platforms.json
  python3 crawl-platforms.py --out platforms.json
  python3 crawl-platforms.py --keyword 母婴   # 按关键词过滤（可选）

依赖：仅标准库（urllib）。
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")


# ---------------------------------------------------------------------------
# HTTP 工具
# ---------------------------------------------------------------------------
def http_get_json(url, headers=None, timeout=10):
    headers = headers or {"User-Agent": UA}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url, payload, headers=None, timeout=10):
    headers = headers or {"User-Agent": UA}
    headers = dict(headers)
    headers.setdefault("Content-Type", "application/json")
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# 抖音热榜
# ---------------------------------------------------------------------------
def fetch_douyin_hot():
    url = ("https://www.douyin.com/aweme/v1/web/hot/search/list/"
           "?device_platform=webapp&aid=6383&channel=channel_pc_web")
    headers = {
        "User-Agent": UA,
        "Referer": "https://www.douyin.com/",
    }
    data = http_get_json(url, headers=headers)
    word_list = (data.get("data") or {}).get("word_list") or []
    items = []
    for w in word_list:
        word = (w.get("word") or "").strip()
        if not word:
            continue
        items.append({
            "rank": w.get("position"),
            "word": word,
            "hot_value": w.get("hot_value"),
            "sentence_id": w.get("sentence_id"),
        })
    return {
        "title": (data.get("data") or {}).get("trending_desc") or "抖音热榜",
        "active_time": (data.get("data") or {}).get("active_time"),
        "count": len(items),
        "items": items,
    }


# ---------------------------------------------------------------------------
# 快手热榜
# ---------------------------------------------------------------------------
def fetch_kuaishou_hot():
    url = "https://www.kuaishou.com/graphql"
    headers = {
        "User-Agent": UA,
        "Referer": "https://www.kuaishou.com/",
    }
    payload = {
        "operationName": "visionHotRank",
        "query": "query visionHotRank{visionHotRank{items{name hotValue rank}}}",
        "variables": {},
    }
    data = http_post_json(url, payload, headers=headers)
    items_raw = ((data.get("data") or {}).get("visionHotRank") or {}).get("items") or []
    items = []
    for it in items_raw:
        name = (it.get("name") or "").strip()
        if not name:
            continue
        items.append({
            "rank": it.get("rank"),
            "word": name,
            "hot_value": it.get("hotValue"),
        })
    return {
        "title": "快手热榜",
        "active_time": None,
        "count": len(items),
        "items": items,
    }


# ---------------------------------------------------------------------------
# 关键词过滤（可选）
# ---------------------------------------------------------------------------
def filter_keyword(items, kw):
    if not kw:
        return items
    return [it for it in items if kw in it.get("word", "")]


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="优康宝贝全网热搜采集")
    parser.add_argument("--out", default=None, help="输出 JSON 路径")
    parser.add_argument("--keyword", default=None, help="按关键词过滤热搜（可选）")
    args = parser.parse_args()

    out_path = args.out or "platforms.json"

    print("=" * 60)
    print("优康宝贝 · 全网热搜采集")
    print("=" * 60)

    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    result = {"meta": {"generated_at": now, "generator": "crawl-platforms.py v1.0"}}

    # 抖音
    try:
        print("[1/2] 采集抖音热榜 ...")
        dy = fetch_douyin_hot()
        dy["items"] = filter_keyword(dy["items"], args.keyword)
        dy["count"] = len(dy["items"])
        result["douyin"] = dy
        print(f"       ✅ 抖音热榜 {dy['count']} 条")
    except Exception as e:
        result["douyin"] = {"error": str(e), "count": 0, "items": []}
        print(f"       ❌ 抖音采集失败：{e}")

    # 快手
    try:
        print("[2/2] 采集快手热榜 ...")
        ks = fetch_kuaishou_hot()
        ks["items"] = filter_keyword(ks["items"], args.keyword)
        ks["count"] = len(ks["items"])
        result["kuaishou"] = ks
        print(f"       ✅ 快手热榜 {ks['count']} 条")
    except Exception as e:
        result["kuaishou"] = {"error": str(e), "count": 0, "items": []}
        print(f"       ❌ 快手采集失败：{e}")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total = result.get("douyin", {}).get("count", 0) + result.get("kuaishou", {}).get("count", 0)
    print()
    print(f"✅ 采集完成，共 {total} 条，输出 {out_path}")
    print("提示：淘宝/小红书/美团需登录或签名，免费接口无法获取，需走官方 API 或付费数据平台。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消。")
        sys.exit(130)
