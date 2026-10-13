#!/usr/bin/env node
// crawl-chanmama.js —— 蝉妈妈「抖音投放排行榜」采集（多榜单类型，支持日榜/月榜）
// 榜单类型：product商品榜 / shop店铺榜 / brand品牌榜 / author达人榜
// 数据源：https://cy.chanmama.com/open/{type}Rank/{类目}/{granularity}/{日期}.html （SSR，__NUXT__）
// granularity：day 日榜(YYYY-MM-DD) / month 月榜(YYYY-MM)
//
// 用法：
//   node crawl-chanmama.js --cat 1,2 --days 365              # 抓最近365天日榜
//   node crawl-chanmama.js --cat 1,2 --granularity month --days 12   # 抓最近12个月月榜
//   类目 ID：1=母婴用品 2=本地生活(团购) 15=玩具乐器 17=食品饮料 ...

const fs = require("fs");
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36";

const TYPES = [
  { key: "product", label: "商品榜" },
  { key: "shop", label: "商家榜" },
  { key: "brand", label: "品牌榜" },
  { key: "author", label: "达人榜" },
];

function parseArgs(argv) {
  const a = { cat: "1,2", date: null, days: 0, granularity: "day", out: "chanmama_rank.json" };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--cat") a.cat = argv[++i];
    else if (argv[i] === "--date") a.date = argv[++i];
    else if (argv[i] === "--days") a.days = Number(argv[++i]);
    else if (argv[i] === "--granularity") a.granularity = argv[++i];
    else if (argv[i] === "--out") a.out = argv[++i];
  }
  return a;
}

function dayOffset(n) {
  const d = new Date(Date.now() - n * 86400000);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}

function monthOffset(n) {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - n);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;
}

async function fetchRank(type, catId, date, granularity) {
  const url = `https://cy.chanmama.com/open/${type}Rank/${catId}/${granularity}/${date}.html`;
  const resp = await fetch(url, { headers: { "User-Agent": UA } });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const html = await resp.text();
  const s = html.indexOf("window.__NUXT__=");
  if (s < 0) throw new Error("无 __NUXT__");
  const expr = html.slice(s + "window.__NUXT__=".length);
  const e = expr.indexOf("</script>");
  return eval(expr.slice(0, e).trim().replace(/;$/, "")).data[0];
}

// 各榜单类型的字段提取
const FIELDS = {
  product: (p) => ({ rank: p.rank, title: p.product_title, sub: p.shop_name, price: p.price, volume: p.volume, amount: p.amount }),
  shop:    (p) => ({ rank: p.rank, title: p.shop_title, sub: p.shop_type === 1 ? "自营" : "旗舰店", price: p.expr_score, volume: p.volume, amount: p.amount, extra: p.goods_ideas_count }),
  brand:   (p) => ({ rank: p.rank, title: p.brand_name, sub: p.label || "", price: null, volume: p.volume, amount: p.amount }),
  author:  (p) => ({ rank: p.rank, title: p.author_name, sub: p.shop_name || "", price: p.author_fans, volume: p.volume, amount: p.amount, extra: p.ideas_count }),
};

async function main() {
  const args = parseArgs(process.argv);
  const cats = args.cat.split(",").map((x) => x.trim()).filter(Boolean);
  const g = args.granularity === "month" ? "month" : "day";

  // 日期列表：--date 指定（逗号分隔），否则按 --days 抓最近 N 个周期
  let dates;
  if (args.date) {
    dates = args.date.split(",").map((x) => x.trim()).filter(Boolean);
  } else {
    const n = args.days > 0 ? args.days : 1;
    dates = [];
    for (let i = 0; i < n; i++) dates.push(g === "month" ? monthOffset(i + 1) : dayOffset(i + 1));
  }

  const out = { meta: { generated_at: new Date().toISOString(), source: "蝉妈妈·抖音投放排行榜", granularity: g, dates }, ranks: [] };

  for (const date of dates) {
    for (const t of TYPES) {
      for (const catId of cats) {
        try {
          const d = await fetchRank(t.key, catId, date, g);
          const items = (d.dataList || []).map(FIELDS[t.key]);
          out.ranks.push({ type: t.key, typeLabel: t.label, categoryId: Number(catId), category: d.categoryLabel, granularity: g, date: d.day || date, count: items.length, items });
          console.log(`✅ ${g} ${date} ${t.label}·${d.categoryLabel} ${items.length} 条`);
        } catch (e) {
          console.log(`❌ ${g} ${date} ${t.label}·类目${catId} 失败：${e.message}`);
        }
      }
    }
  }

  fs.writeFileSync(args.out, JSON.stringify(out), "utf-8");
  const total = out.ranks.reduce((s, r) => s + r.count, 0);
  console.log(`\n✅ 采集完成，共 ${total} 条，输出 ${args.out}`);
}
main().catch((e) => { console.error(e); process.exit(1); });
