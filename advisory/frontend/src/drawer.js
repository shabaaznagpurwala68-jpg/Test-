import { indicatorChart, lineColors } from "./charts.js";
import { getProfile, isSuited } from "./risk.js";
import { $, STATUS, api, badge, day, el, inr, pct, tone, track } from "./util.js";

let chart = null;

function show(content) {
  // Built with el() so conditional parts that evaluate to false are skipped, not printed.
  $("drawer-body").replaceChildren(el("div", {}, ...content));
  $("drawer").classList.add("open");
  $("drawer").setAttribute("aria-hidden", "false");
  $("scrim").classList.add("open");
  $("drawer").scrollTop = 0;
  $("drawer-close").focus();
}

export function closeDrawer() {
  $("drawer").classList.remove("open");
  $("drawer").setAttribute("aria-hidden", "true");
  $("scrim").classList.remove("open");
}

function legend() {
  const c = lineColors();
  const item = (color, label) => el("span", { class: "legend-item" }, el("i", { style: `background:${color}` }), label);
  return el("div", { class: "legend" },
    item(c.sma20, "20-DMA"), item(c.sma50, "50-DMA"), item(c.sma200, "200-DMA"),
    el("span", { class: "sub" }, "· panes below: RSI(14) with 70/30 lines · MACD(12,26,9)"));
}

async function drawChart(box, path, call) {
  chart?.remove();
  chart = null;
  const data = await api(path);
  chart = indicatorChart(box, data, call);
}

async function newsFor(symbol, box) {
  const { items } = await api(`/news?symbol=${encodeURIComponent(symbol)}`);
  box.replaceChildren(
    items.length
      ? el("ul", { class: "mini-news" }, items.slice(0, 5).map((n) =>
          el("li", {}, n.link ? el("a", { href: n.link, target: "_blank", rel: "noopener noreferrer" }, n.title) : n.title,
            el("div", { class: "sub" }, n.source))))
      : el("div", { class: "sub" }, "No recent headlines mention this stock."),
  );
}

const kv = (k, v) => el("div", { class: "kv" }, el("span", {}, k), el("span", {}, v));
const lvl = (label, v, cls = "") => el("div", {}, el("div", { class: "label" }, label), el("div", { class: `v ${cls}` }, v));

export async function openCall(id) {
  const c = await api(`/calls/${id}`);
  const closed = c.status !== "OPEN";
  const v = c.signal.values;
  const profile = getProfile();
  const chartBox = el("div", { class: "chart chart-tall" });
  const explainBox = el("div", { class: "explain", hidden: true });
  const newsBox = el("div", {}, el("div", { class: "sub" }, "Loading news…"));

  const explainBtn = el("button", {
    class: "btn-outline",
    onclick: async () => {
      if (explainBox.hidden && !explainBox.childElementCount) {
        const { paragraphs } = await api(`/calls/${id}/explain`);
        explainBox.append(...paragraphs.map((p) => el("p", {}, p)),
          el("p", { class: "sub" }, "Auto-generated from this call's numbers. Not investment advice."));
      }
      explainBox.hidden = !explainBox.hidden;
      explainBtn.textContent = explainBox.hidden ? "EXPLAIN THIS CALL SIMPLY" : "HIDE EXPLANATION";
    },
  }, "EXPLAIN THIS CALL SIMPLY");

  show([
    el("div", { class: "badges" },
      badge(c.action, "call-BUY"),
      badge(c.setup_name.toUpperCase(), "setup"),
      badge(`${c.risk_level.toUpperCase()} RISK`, `risk-${c.risk_level}`),
      closed && badge(STATUS[c.status], `st-${c.status}`),
      profile && !isSuited(c, profile) && badge("NOT SUITED TO YOUR PROFILE", "unsuited"),
    ),
    el("h2", {}, c.name),
    el("div", { class: "sub" }, `${c.symbol} · NSE · ${c.sector}`),
    el("div", { class: "price" }, inr(c.cmp)),
    el("div", { class: tone(c.change_pct) }, `${pct(c.change_pct)} today`),
    legend(),
    chartBox,
    closed
      ? el("div", { class: "levels" }, lvl("Entry", inr(c.entry)), lvl("Exit", inr(c.exit_price)), lvl("Result", pct(c.return_pct), tone(c.return_pct)))
      : el("div", { class: "levels" }, lvl("Entry", inr(c.entry)), lvl("Target", inr(c.target)), lvl("Stop loss", inr(c.stop_loss))),
    !closed && [track(c.progress), el("div", { class: "track-labels" }, el("span", {}, "Stop loss"), el("span", {}, "Target"))],

    el("h3", {}, "Why this stock"),
    el("p", { class: "sub" }, `${c.setup_name} checklist on ${day(c.issued_on)} — every rule had to pass:`),
    el("div", { class: "checklist" }, c.signal.checks.map((ch) =>
      el("div", { class: `check ${ch.passed ? "pass" : "fail"}` },
        el("span", { class: "tick", "aria-label": ch.passed ? "passed" : "failed" }, ch.passed ? "✓" : "✕"),
        el("div", {}, el("div", { class: "check-label" }, ch.label), el("div", { class: "sub" }, `Needs: ${ch.requirement}`)),
        el("div", { class: "check-value" }, ch.value),
      ))),

    el("h3", {}, "How the levels were set"),
    el("div", { class: "formula" },
      el("div", {}, el("span", {}, "Entry"), el("span", {}, `Close on ${day(c.issued_on)}`), el("strong", {}, inr(c.entry))),
      el("div", {}, el("span", {}, "Stop loss"), el("span", {}, `${inr(c.entry)} − 2 × ATR ${inr(v.atr)}`), el("strong", {}, inr(c.stop_loss))),
      el("div", {}, el("span", {}, "Target"), el("span", {}, `${inr(c.entry)} + 2 × risk ${inr(c.entry - c.stop_loss)}`), el("strong", {}, inr(c.target))),
    ),
    el("div", { class: "kvs" },
      closed ? kv("Return", pct(c.return_pct)) : kv("Potential to target", pct(c.potential_pct)),
      kv("Status", STATUS[c.status]),
      kv("Time limit", c.horizon),
      closed && kv("Closed on", `${day(c.closed_on)} (${c.days_held} days)`),
      kv("Volatility", `${c.volatility}% a year → ${c.risk_level} risk`),
    ),
    explainBtn,
    explainBox,
    el("h3", {}, `News on ${c.symbol}`),
    newsBox,
    el("p", { class: "sub" }, "Disclaimer: The securities are quoted as an example and not as a recommendation."),
  ]);

  drawChart(chartBox, `/calls/${id}/chart`, c);
  newsFor(c.symbol, newsBox);
}

/** Any stock or index from the Markets tab: chart with indicators and its key numbers. */
export function openInstrument(row, extras = {}) {
  const chartBox = el("div", { class: "chart chart-tall" });
  const newsBox = el("div", {}, el("div", { class: "sub" }, "Loading news…"));
  const isStock = Boolean(row.symbol);
  show([
    el("div", { class: "badges" },
      row.trend && badge(row.trend.toUpperCase(), `trend-${row.trend}`),
      ...(extras.scanners || []).map((s) => badge(s.toUpperCase(), "setup"))),
    el("h2", {}, row.name),
    el("div", { class: "sub" }, isStock ? `${row.symbol} · NSE · ${row.sector}` : row.group),
    el("div", { class: "price" }, isStock ? inr(row.last) : row.last.toLocaleString("en-IN", { maximumFractionDigits: 2 })),
    el("div", { class: tone(row.chg_1d) }, `${pct(row.chg_1d)} today`),
    legend(),
    chartBox,
    el("div", { class: "kvs" },
      kv("1 week / 1 month / YTD", `${pct(row.chg_1w)} / ${pct(row.chg_1m)} / ${row.chg_ytd == null ? "–" : pct(row.chg_ytd)}`),
      kv("RSI(14)", row.rsi == null ? "–" : String(row.rsi)),
      kv("vs 50-DMA / 200-DMA", `${row.vs_sma50 == null ? "–" : pct(row.vs_sma50)} / ${row.vs_sma200 == null ? "–" : pct(row.vs_sma200)}`),
      kv("52-week range", `${row.low_52w.toLocaleString("en-IN")} – ${row.high_52w.toLocaleString("en-IN")}`),
      kv("From 52-week high", pct(row.from_high)),
      isStock && row.vol_ratio != null && kv("Volume vs 20-day average", `${row.vol_ratio}×`),
    ),
    isStock && el("h3", {}, `News on ${row.symbol}`),
    isStock && newsBox,
    el("p", { class: "sub" }, "Figures calculated from daily prices. Not a recommendation."),
  ]);
  drawChart(chartBox, `/chart/${encodeURIComponent(row.symbol || row.key)}?days=240`);
  if (isStock) newsFor(row.symbol, newsBox);
}

const PILLARS = ["Valuation", "Quality", "Growth", "Shareholder"];

/** A fundamental pick: pillar-by-pillar scorecard, fair value maths, peers and a price chart. */
export async function openFundamental(symbol) {
  const d = await api(`/fundamentals/${encodeURIComponent(symbol)}`);
  const profile = getProfile();
  const chartBox = el("div", { class: "chart chart-tall" });
  const newsBox = el("div", {}, el("div", { class: "sub" }, "Loading news…"));
  const capped = d.fair_value && d.fair_value_uncapped > d.fair_value + 0.01;
  const growth = Math.min(Math.max(d.eps_cagr3 ?? 0, 0), 15);
  const fwdEps = d.eps * (1 + growth / 100);
  const blended = d.pe != null ? (d.peer.median_pe + d.pe) / 2 : null;

  show([
    el("div", { class: "badges" },
      badge(d.verdict, `verdict-${d.verdict}`),
      badge(`SCORE ${d.score.toFixed(0)}/100`, "setup"),
      badge(`${d.risk_level.toUpperCase()} RISK`, `risk-${d.risk_level}`),
      profile && !isSuited(d, profile) && badge("NOT SUITED TO YOUR PROFILE", "unsuited")),
    el("h2", {}, d.name),
    el("div", { class: "sub" }, `${d.symbol} · NSE · ${d.sector} · peer group: ${d.peer_group}`),
    el("div", { class: "price" }, inr(d.cmp)),
    el("div", { class: tone(d.change_pct) }, `${pct(d.change_pct)} today`),
    el("div", { class: "levels" },
      lvl(d.verdict === "PICK" ? "Fair value (target)" : "Fair value", d.fair_value ? inr(d.fair_value) : "n/m"),
      lvl("Upside", d.upside_pct == null ? "–" : pct(d.upside_pct), tone(d.upside_pct)),
      // Trade levels only for picks: a stop loss on a stock we don't recommend would imply a trade.
      d.verdict === "PICK" ? lvl("Stop loss (−15%)", inr(d.stop_loss)) : lvl("Trade levels", "Picks only")),

    el("h3", {}, "Why this stock"),
    el("div", { class: "explain" }, d.narrative.map((p) => el("p", {}, p))),

    el("h3", {}, "Scorecard"),
    PILLARS.map((p, i) => el("div", { class: "pillar-block" },
      el("div", { class: "pillar-title" }, el("i", { class: `dot-seg seg-${i}` }), el("strong", {}, p),
        el("span", { class: "pillar-pts" }, `${d.pillars[p].toFixed(1)} / 25`)),
      el("div", { class: "checklist" }, d.factors.filter((f) => f.pillar === p).map((f) =>
        el("div", { class: "factor" },
          el("div", {}, el("div", { class: "check-label" }, f.label),
            el("div", { class: "sub" }, f.benchmark), f.note && el("div", { class: "sub note-inline" }, f.note)),
          el("div", { class: "check-value" }, f.value),
          el("div", { class: "factor-pts" },
            el("div", { class: "mini-bar" }, el("span", { style: `width:${(f.points / f.max) * 100}%` })),
            el("span", {}, `${(+f.points).toFixed(1)}/${f.max}`))))))),

    el("h3", {}, "How the fair value is calculated"),
    d.fair_value
      ? el("div", { class: "formula formula-wide" },
          el("div", {}, el("span", {}, "EPS (trailing)"), el("span", {}, "Sample"), el("strong", {}, inr(d.eps))),
          el("div", {}, el("span", {}, "Forward EPS"), el("span", {}, `${inr(d.eps)} × (1 + ${growth.toFixed(0)}% growth, max 15%)`), el("strong", {}, inr(fwdEps))),
          el("div", {}, el("span", {}, "Blended PE"), el("span", {}, `½ × peer median ${d.peer.median_pe}× + ½ × own ${d.pe}×`), el("strong", {}, `${blended.toFixed(1)}×`)),
          el("div", {}, el("span", {}, "Fair value"), el("span", {}, `${inr(fwdEps)} × ${blended.toFixed(1)}×${capped ? ` = ${inr(d.fair_value_uncapped)}, capped at +30%` : ""}`), el("strong", {}, inr(d.fair_value))))
      : el("p", { class: "sub" }, "Not meaningful: earnings are too small relative to the price (PE above 150×)."),

    el("h3", {}, `Peer group: ${d.peer_group}`),
    el("div", { class: "table-wrap" }, el("table", { class: "compact" },
      el("thead", {}, el("tr", {}, ["Stock", "PE", "PB", "ROE", "Score", "Verdict"].map((h, i) => el("th", { class: i && i < 5 ? "num" : "" }, h)))),
      el("tbody", {}, d.peers.map((p) => el("tr", { class: p.symbol === d.symbol ? "current" : "" },
        el("td", { class: "sym" }, p.symbol),
        el("td", { class: "num" }, p.pe == null ? "–" : `${p.pe}×`),
        el("td", { class: "num" }, `${p.pb}×`),
        el("td", { class: "num" }, `${p.roe}%`),
        el("td", { class: "num" }, p.score.toFixed(0)),
        el("td", {}, badge(p.verdict, `verdict-${p.verdict}`))))),
      el("tfoot", {}, el("tr", {}, el("td", {}, "Median"), el("td", { class: "num" }, `${d.peer.median_pe}×`),
        el("td", { class: "num" }, `${d.peer.median_pb}×`), el("td", { class: "num" }, `${d.peer.median_roe}%`), el("td", {}), el("td", {}))))),

    el("h3", {}, "Price chart"),
    legend(),
    chartBox,
    el("h3", {}, `News on ${d.symbol}`),
    newsBox,
    el("p", { class: "data-note" }, el("strong", {}, "Sample data. "), d.method.data_note),
    el("p", { class: "sub" }, "Disclaimer: The securities are quoted as an example and not as a recommendation."),
  ]);
  drawChart(chartBox, `/chart/${encodeURIComponent(symbol)}?days=365`);
  newsFor(symbol, newsBox);
}
