# 数智化全域数据工作台（优康宝贝）

优康宝贝母婴连锁的数字化运营数据看板，聚合全网真实数据，辅助经营决策。

## 功能模块

- **经营榜单**：商家榜 / 门店榜 / 商品榜 / 达人榜 / 搜索榜 / 内容榜
- **行业趋势**：抖音商品 / 店铺 / 品牌 / 达人 365 天投放榜单（蝉妈妈公开数据）
- **热点洞察**：抖音 + 快手实时热搜、母婴话题 TOP50
- **同行对比**：优康自有 727 门店 + 竞品 19782 门店（覆盖 8 省市 65 城）

## 数据底座

| 数据 | 来源 | 规模 |
|------|------|------|
| 抖音 / 快手热搜 | 免费公开接口 | 抖音 49 + 快手 50 |
| 365 天投放榜 | 蝉妈妈公开榜单 | 52427 条 |
| 门店分布 | 高德 POI + 自有门店表 | 20509 家 |
| 母婴话题 / 选品 | 内置词库 + 电商榜单 | 50 话题 + 100 商品 |

## 使用方法

1. 双击 `启动工作台.command`，或在目录下运行 `python3 -m http.server`
2. 浏览器打开 `http://localhost:8000`，自动加载数据
3. 也可直接双击 `youkang-mom-workbench.html`，再选择 / 拖入 `data.json`

## 目录结构

- `youkang-mom-workbench.html` — 单文件前端工作台（原生 JS/CSS，离线可用）
- `crawl-platforms.py` — 抖音 / 快手热搜采集
- `crawl-chanmama.js` — 蝉妈妈投放榜单采集（Node）
- `crawl-amap-poi.py` — 高德门店 POI 采集
- `crawl-mom-data.py` — 母婴话题 / 商品数据生成
- `*.json` — 各数据源产物

## 采集脚本（需重新拉数据时）

```bash
# 抖音/快手热搜
python3 crawl-platforms.py

# 蝉妈妈榜单（最近 N 天）
node crawl-chanmama.js --days 30

# 高德门店 POI
python3 crawl-amap-poi.py --key <高德key> --city <城市列表>
```
