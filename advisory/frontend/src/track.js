import { equityChart } from "./charts.js";
import { openDrawer } from "./drawer.js";
import { $, STATUS, api, badge, card, day, el, inr, inr0, pct, tone } from "./util.js";

let chart = null;

export async function renderTrack() {
  const d = await api("/performance");
  const s = d.stats;
  const chartBox = el("div", { class: "chart chart-lg" });

  const groupTable = (title, key, rows) =>
    el("div", { class: "table-wrap" },
      el("table", { class: "compact" },
        el("thead", {}, el("tr", {}, el("th", {}, title), el("th", { class: "num" }, "Calls"),
          el("th", { class: "num" }, "Win rate"), el("th", { class: "num" }, "Avg return"), el("th", { class: "num" }, "Net P&L"))),
        el("tbody", {}, rows.map((g) => el("tr", {},
          el("td", {}, g[key]), el("td", { class: "num" }, String(g.calls)), el("td", { class: "num" }, `${g.win_rate}%`),
          el("td", { class: `num ${tone(g.avg_return_pct)}` }, pct(g.avg_return_pct)),
          el("td", { class: `num ${tone(g.net_pnl)}` }, inr0(g.net_pnl))))),
      ));

  $("view-track").replaceChildren(
    el("div", { class: "summary summary-6" },
      card("Win rate", `${s.win_rate}%`, "", `${s.calls} closed calls`),
      card("Net P&L", inr0(s.net_pnl), tone(s.net_pnl), "₹1 lakh in every call"),
      card("Avg win / avg loss", `${pct(s.avg_win_pct)} / ${pct(s.avg_loss_pct)}`, "", s.win_loss_ratio ? `Ratio ${s.win_loss_ratio}×` : ""),
      card("Outcomes", `${s.target_hit} · ${s.sl_hit} · ${s.expired}`, "", "Target · SL · Expired"),
      card("Avg holding", `${s.avg_days_held} days`),
      card("Max drawdown", inr0(-s.max_drawdown), s.max_drawdown ? "loss" : "", "Largest fall from a peak"),
    ),
    el("div", { class: "panel" },
      el("div", { class: "panel-head" }, el("h3", {}, "Equity curve"),
        el("span", { class: "sub" }, "Cumulative net P&L, ₹1,00,000 per call")),
      chartBox),
    el("div", { class: "grid-2" }, groupTable("Call type", "action", d.by_action), groupTable("Sector", "sector", d.by_sector)),
    el("h3", { class: "section-title" }, "Closed calls"),
    el("div", { class: "table-wrap" },
      el("table", {},
        el("thead", {}, el("tr", {}, ["Stock", "Call", "Issued", "Closed", "Entry", "Exit", "Result", "Return", "Net P&L", "Days"]
          .map((h, i) => el("th", { class: i >= 4 && i !== 6 ? "num" : "" }, h)))),
        el("tbody", {}, d.closed_calls.map((c) => el("tr", { tabindex: "0", onclick: () => openDrawer(c.id), onkeydown: (e) => e.key === "Enter" && openDrawer(c.id) },
          el("td", {}, el("div", { class: "sym" }, c.symbol)),
          el("td", {}, badge(c.action, `call-${c.action}`)),
          el("td", { class: "sub nowrap" }, day(c.issued_on)),
          el("td", { class: "sub nowrap" }, day(c.closed_on)),
          el("td", { class: "num" }, inr(c.entry)),
          el("td", { class: "num" }, inr(c.exit_price)),
          el("td", {}, badge(STATUS[c.status], `st-${c.status}`)),
          el("td", { class: `num ${tone(c.return_pct)}` }, pct(c.return_pct)),
          el("td", { class: `num ${tone(c.net_pnl)}` }, inr0(c.net_pnl)),
          el("td", { class: "num" }, String(c.days_held)),
        ))),
      )),
    el("p", { class: "note" },
      "How this is calculated: sample calls replayed against actual daily prices. Each call exits on the first day its "
      + "target or stop loss is touched (if a day's range touches both, the stop loss is assumed); if a day opens beyond a "
      + "level, the exit is at the open. ₹1,00,000 per call in whole shares, after TradeSmart brokerage of ₹15 × 2 orders; "
      + "taxes and statutory charges excluded. SELL calls are measured as short positions. "
      + "Past performance is not indicative of future returns."),
  );

  chart?.remove();
  chart = equityChart(chartBox, d.equity_curve);
}
