#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawl-amap-poi.py
================================================================
高德地图 POI 采集 —— 抓全国母婴相关门店名单
================================================================

通过高德地图 Web 服务 API（官方合规接口）按「城市 + 关键词」搜索门店，
返回门店名称/地址/电话/经纬度/省市区，输出 amap_poi.json。

支持关键词（默认母婴相关业态，可改）：
  母婴店、婴儿游泳馆、母婴用品、月子中心、儿童摄影、早教中心、孕婴童

用法：
  python3 crawl-amap-poi.py --key 你的高德key --city 贵阳 --keyword 母婴店,婴儿游泳馆
  python3 crawl-amap-poi.py --key 你的高德key --city 贵阳,遵义,铜仁,惠水县

说明：
  - 高德个人开发者免费额度：每日数千次，足够抓取多城市母婴门店。
  - 单次请求最多返回 25 条，脚本自动翻页抓全（每关键词最多 100 页）。
  - 脚本已控制请求频率，请勿并发高频调用。
"""

import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

AMAP_SEARCH_URL = "https://restapi.amap.com/v3/place/text"

DEFAULT_KEYWORDS = "母婴店,婴儿游泳馆,母婴用品,月子中心,儿童摄影,早教中心"


def search_poi(key, keyword, city, page=1, offset=25):
    """调用高德 POI 关键字搜索，返回解析后的 dict。"""
    params = {
        "key": key,
        "keywords": keyword,
        "city": city,
        "offset": str(offset),
        "page": str(page),
        "extensions": "all",
    }
    url = AMAP_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="高德地图母婴门店采集")
    parser.add_argument("--key", required=True, help="高德 Web 服务 API key")
    parser.add_argument("--city", default="贵阳", help="城市（逗号分隔，支持区县），如 贵阳,遵义 或 惠水县")
    parser.add_argument("--keyword", default=DEFAULT_KEYWORDS, help="关键词（逗号分隔）")
    parser.add_argument("--out", default="amap_poi.json", help="输出文件")
    args = parser.parse_args()

    cities = [c.strip() for c in args.city.split(",") if c.strip()]
    keywords = [k.strip() for k in args.keyword.split(",") if k.strip()]

    print("=" * 60)
    print("高德地图 · 母婴门店采集")
    print("=" * 60)

    all_pois = []
    for city in cities:
        for kw in keywords:
            print(f"[{city}] 关键词「{kw}」")
            page = 1
            while page <= 100:
                try:
                    data = search_poi(args.key, kw, city, page)
                except Exception as e:
                    print(f"  网络错误：{e}")
                    break
                if data.get("status") != "1":
                    print(f"  API 错误：{data.get('info')}（请检查 key 是否正确）")
                    return
                pois = data.get("pois") or []
                count = int(data.get("count") or 0)
                if not pois:
                    break
                for p in pois:
                    all_pois.append({
                        "name": p.get("name"),
                        "type": p.get("type"),
                        "province": p.get("pname"),
                        "city": p.get("cityname"),
                        "district": p.get("adname"),
                        "address": p.get("address"),
                        "tel": (p.get("tel") or ""),
                        "location": p.get("location"),
                    })
                print(f"  第 {page} 页 {len(pois)} 条（该词共 {count} 条）")
                if page * 25 >= count:
                    break
                page += 1
                time.sleep(0.25)

    # 去重（同名称+地址）
    seen = set()
    unique = []
    for p in all_pois:
        k = (str(p["name"]), str(p["address"]))
        if k not in seen:
            seen.add(k)
            unique.append(p)

    tz = timezone(timedelta(hours=8))
    out = {
        "meta": {
            "generated_at": datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
            "source": "高德地图POI搜索API",
            "cities": cities,
            "keywords": keywords,
            "count": len(unique),
        },
        "pois": unique,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ 采集完成，共 {len(unique)} 条门店，输出 {args.out}")
    print("下一步：把 amap_poi.json 接入工作台，或继续抓其他城市。")


if __name__ == "__main__":
    main()
