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
