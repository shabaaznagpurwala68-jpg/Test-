import { sparkline } from "./charts.js";
import { openInstrument } from "./drawer.js";
import { renderSource } from "./technical.js";
import { $, api, badge, el, pct, tone } from "./util.js";

const num = (v) => v.toLocaleString("en-IN", { maximumFractionDigits: 2 });
const orDash = (v, f = pct) => (v == null ? "–" : f(v));
let sort = { key: "chg_1d", dir: -1 };
let query = "";
let data = null;

function indexCard(x) {
  return el("button", { class: "mkt-card", onclick: () => openInstrument(x) },
    el("div", { class: "mkt-head" }, el("span", { class: "mkt-name" }, x.name), x.trend && badge(x.trend.toUpperCase(), `trend-${x.trend}`)),
    el("div", { class: "mkt-row" },
      el("div", {}, el("div", { class: "mkt-last" }, num(x.last)), el("div", { class: `mkt-chg ${tone(x.chg_1d)}` }, pct(x.chg_1d))),
      sparkline(x.spark, x.spark[x.spark.length - 1] >= x.spark[0])),
    el("div", { class: "mkt-meta" },
      el("span", {}, "1M ", el("b", { class: tone(x.chg_1m) }, orDash(x.chg_1m))),
      el("span", {}, "YTD ", el("b", { class: tone(x.chg_ytd) }, orDash(x.chg_ytd))),
      el("span", {}, "RSI ", el("b", {}, orDash(x.rsi, String))),
    ));
}

function breadthPanel(b) {
  const meter = (label, value, hint) =>
    el("div", { class: "meter" },
      el("div", { class: "meter-head" }, el("span", {}, label), el("strong", {}, `${value}%`)),
      el("div", { class: "meter-bar" }, el("span", { style: `width:${value}%` })),
      el("div", { class: "sub" }, hint));
  const adv = (b.advances / b.total) * 100;
  return el("div", { class: "panel" },
    el("div", { class: "panel-head" }, el("h3", {}, "Market breadth"), el("span", { class: "sub" }, `Our ${b.total} stocks (≈ Nifty 50)`)),
    el("div", { class: "breadth" },
      el("div", {},
        el("div", { class: "meter-head" }, el("span", {}, "Advances vs declines"),
          el("strong", {}, el("span", { class: "gain" }, String(b.advances)), " / ", el("span", { class: "loss" }, String(b.declines)))),
        el("div", { class: "ad-bar", title: `${b.advances} up, ${b.declines} down, ${b.unchanged} unchanged` },
          el("span", { class: "ad-up", style: `width:${adv}%` }), el("span", { class: "ad-down", style: `width:${(b.declines / b.total) * 100}%` })),
        el("div", { class: "sub" }, `${b.unchanged} unchanged`)),
      meter("Above 50-DMA", b.above_sma50_pct, "Short-to-medium-term health"),
      meter("Above 200-DMA", b.above_sma200_pct, "Long-term health; below 50% is a weak market"),
      el("div", { class: "breadth-stats" },
        el("div", {}, el("strong", {}, String(b.new_highs)), el("span", { class: "sub" }, "New 52W highs")),
        el("div", {}, el("strong", {}, String(b.near_lows)), el("span", { class: "sub" }, "Near 52W lows")),
        el("div", {}, el("strong", {}, String(b.avg_rsi)), el("span", { class: "sub" }, "Average RSI"))),
    ));
}

function scannerCard(s) {
  const stockRow = (i) => data.stocks.find((r) => r.symbol === i.symbol);
  return el("div", { class: "scanner" },
    el("div", { class: "scanner-head" }, el("h3", {}, s.title), badge(String(s.items.length), s.items.length ? "count" : "count-zero")),
    el("p", { class: "sub" }, s.description),
    s.items.length
      ? el("ul", {}, s.items.map((i) => el("li", {},
          el("button", { class: "scan-item", onclick: () => openInstrument(stockRow(i), { scanners: scannersFor(i.symbol) }) },
            el("span", { class: "sym" }, i.symbol),
            el("span", { class: "sub" }, i.metric),
            el("span", { class: `num ${tone(i.chg_1d)}` }, pct(i.chg_1d))))))
      : el("p", { class: "sub empty-scan" }, "No stocks match today."));
}

const scannersFor = (symbol) => data.scanners.filter((s) => s.items.some((i) => i.symbol === symbol)).map((s) => s.title);

const COLUMNS = [
  ["symbol", "Stock"], ["last", "Last"], ["chg_1d", "1D"], ["chg_1m", "1M"], ["rsi", "RSI"],
  ["vs_sma50", "vs 50-DMA"], ["vs_sma200", "vs 200-DMA"], ["from_high", "From 52W high"], ["vol_ratio", "Vol ×"], ["trend", "Trend"],
];

function stockTable() {
  const q = query.trim().toLowerCase();
  const rows = data.stocks
    .filter((s) => !q || [s.symbol, s.name, s.sector].some((f) => f.toLowerCase().includes(q)))
    .sort((a, b) => {
      const x = a[sort.key], y = b[sort.key];
      if (x == null) return 1;
      if (y == null) return -1;
      return (typeof x === "string" ? x.localeCompare(y) : x - y) * sort.dir;
    });
  return el("table", {},
    el("thead", {}, el("tr", {}, COLUMNS.map(([k, label], idx) =>
      el("th", { class: idx ? "num" : "", "aria-sort": sort.key === k ? (sort.dir > 0 ? "ascending" : "descending") : "none" },
        el("button", {
          class: "th-sort", onclick: () => {
            sort = { key: k, dir: sort.key === k ? -sort.dir : k === "symbol" || k === "trend" ? 1 : -1 };
            $("stock-table").replaceChildren(stockTable());
          },
        }, label, sort.key === k ? (sort.dir > 0 ? " ▲" : " ▼") : ""))))),
    el("tbody", {}, rows.map((s) => el("tr", {
      tabindex: "0",
      onclick: () => openInstrument(s, { scanners: scannersFor(s.symbol) }),
      onkeydown: (e) => e.key === "Enter" && openInstrument(s, { scanners: scannersFor(s.symbol) }),
    },
      el("td", {}, el("div", { class: "sym" }, s.symbol), el("div", { class: "sub" }, s.sector)),
      el("td", { class: "num" }, num(s.last)),
      el("td", { class: `num ${tone(s.chg_1d)}` }, orDash(s.chg_1d)),
      el("td", { class: `num ${tone(s.chg_1m)}` }, orDash(s.chg_1m)),
      el("td", { class: "num" }, orDash(s.rsi, String)),
      el("td", { class: `num ${tone(s.vs_sma50)}` }, orDash(s.vs_sma50)),
      el("td", { class: `num ${tone(s.vs_sma200)}` }, orDash(s.vs_sma200)),
      el("td", { class: "num" }, orDash(s.from_high)),
      el("td", { class: "num" }, orDash(s.vol_ratio, (v) => `${v}×`)),
      el("td", { class: "num" }, s.trend ? badge(s.trend.toUpperCase(), `trend-${s.trend}`) : "–"),
    ))));
}

export async function renderMarkets() {
  data = await api("/markets");
  renderSource(data.price_source, data.as_of);
  const group = (g) => data.indices.filter((x) => x.group === g).map(indexCard);
  $("view-markets").replaceChildren(
    el("div", { class: "intro" },
      el("h2", {}, "Markets"),
      el("p", { class: "sub" }, "Indian and global indices, macro indicators, breadth and scanners — all calculated from daily prices. Click any card, scanner result or stock for its chart.")),
    el("h3", { class: "section-title" }, "Indian markets"), el("div", { class: "mkt-grid" }, group("India")),
    el("h3", { class: "section-title" }, "Global markets"), el("div", { class: "mkt-grid" }, group("Global")),
    el("h3", { class: "section-title" }, "Currency, commodities and yields"), el("div", { class: "mkt-grid" }, group("Macro")),
    breadthPanel(data.breadth),
    el("h3", { class: "section-title" }, "Scanners"),
    el("p", { class: "sub scanner-intro" }, "Each scanner checks all 50 stocks on the latest daily candle."),
    el("div", { class: "scanner-grid" }, data.scanners.map(scannerCard)),
    el("div", { class: "panel-head section-title" }, el("h3", {}, "Stock screener"),
      el("input", {
        class: "search", type: "search", placeholder: "Search stock or sector", value: query,
        oninput: (e) => { query = e.target.value; $("stock-table").replaceChildren(stockTable()); },
      })),
    el("div", { class: "table-wrap", id: "stock-table" }, stockTable()),
    el("p", { class: "note" }, "Trend: Uptrend = price above 50-DMA above 200-DMA; Downtrend = the reverse; otherwise Sideways. "
      + "Valuation ratios such as PE, PB and ROE arrive with the Fundamental section (Phase 2)."),
  );
}
