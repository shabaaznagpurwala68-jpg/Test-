import { openFundamental } from "./drawer.js";
import { getProfile, isSuited } from "./risk.js";
import { renderSource } from "./technical.js";
import { $, api, badge, card, el, inr, pct, tone } from "./util.js";

const state = { verdict: "PICK", query: "", data: null };
const VERDICTS = [["PICK", "PICKS"], ["WATCH", "WATCH"], ["", "ALL 50 STOCKS"]];
const PILLARS = ["Valuation", "Quality", "Growth", "Shareholder"];

/** Four stacked segments, one per pillar, each out of 25. */
export function scoreBar(item) {
  return el("div", { class: "scorebar-wrap", title: PILLARS.map((p) => `${p} ${item.pillars[p]}/25`).join(" · ") },
    el("strong", { class: "score-num" }, item.score.toFixed(0)),
    el("div", { class: "pillar-bar" }, PILLARS.map((p, i) =>
      el("span", { class: `seg seg-${i}`, style: `width:${item.pillars[p]}%` }))));
}

function methodPanel(m) {
  return el("details", { class: "panel method", open: true },
    el("summary", {}, el("h3", {}, "How we pick: a 100-point scorecard"), el("span", { class: "sub" }, "Show / hide")),
    el("div", { class: "pillar-grid" }, m.pillars.map((p, i) =>
      el("div", { class: "pillar" },
        el("div", { class: "pillar-head" }, el("i", { class: `dot-seg seg-${i}` }), el("strong", {}, p.name), el("span", { class: "sub" }, `${p.points} pts`)),
        el("ul", {}, p.factors.map((f) => el("li", {}, f)))))),
    el("div", { class: "method-rows" },
      el("div", {}, el("span", {}, "Fair value"), el("span", {}, m.fair_value)),
      el("div", {}, el("span", {}, "Verdicts"), el("span", {}, m.rules.join(" · "))),
      el("div", {}, el("span", {}, "Levels"), el("span", {}, `Target: ${m.levels.target}. Stop loss: ${m.levels.stop_loss}. Horizon: ${m.levels.horizon}.`)),
    ),
    el("p", { class: "data-note" }, el("strong", {}, "Sample data. "), m.data_note));
}

function render() {
  const d = state.data;
  const profile = getProfile();
  const picks = d.items.filter((i) => i.verdict === "PICK");
  const avgUp = picks.length ? picks.reduce((s, i) => s + i.upside_pct, 0) / picks.length : 0;
  const q = state.query.trim().toLowerCase();
  const rows = d.items.filter((i) => (!state.verdict || i.verdict === state.verdict)
    && (!q || [i.symbol, i.name, i.sector, i.peer_group].some((f) => f.toLowerCase().includes(q))));

  $("fund-summary").replaceChildren(
    card("Picks", String(picks.length), "", `Of ${d.items.length} stocks scored`),
    card("Avg upside (picks)", pct(avgUp), tone(avgUp), "To capped fair value"),
    card("Watch list", String(d.items.filter((i) => i.verdict === "WATCH").length), "", "Strong, but fairly priced"),
    card("Our 50 · aggregate PE", `${d.aggregate.pe}×`, "", `PB ${d.aggregate.pb}× · Yield ${d.aggregate.div_yield}%`),
  );
  $("fund-filter").replaceChildren(...VERDICTS.map(([v, label]) =>
    el("button", { class: `chip ${state.verdict === v ? "selected" : ""}`, onclick: () => { state.verdict = v; render(); } }, label)));

  $("fund-rows").replaceChildren(...(rows.length ? rows.map((i) => {
    const suited = isSuited(i, profile);
    return el("tr", { tabindex: "0", onclick: () => openFundamental(i.symbol), onkeydown: (e) => e.key === "Enter" && openFundamental(i.symbol) },
      el("td", {}, el("div", { class: "sym" }, i.symbol), el("div", { class: "sub" }, `${i.name} · ${i.peer_group}`)),
      el("td", {}, badge(i.verdict, `verdict-${i.verdict}`)),
      el("td", {}, scoreBar(i)),
      el("td", {}, badge(i.risk_level.toUpperCase(), `risk-${i.risk_level}`),
        profile && !suited && el("div", { class: "sub unsuited-text" }, "Not suited to you")),
      el("td", { class: "num" }, inr(i.cmp), el("div", { class: `sub ${tone(i.change_pct)}` }, pct(i.change_pct))),
      el("td", { class: "num" }, i.pe == null ? "–" : `${i.pe}×`),
      el("td", { class: "num" }, `${i.roe}%`),
      el("td", { class: "num" }, i.fair_value ? inr(i.fair_value) : "n/m"),
      el("td", { class: `num ${tone(i.upside_pct)}` }, i.upside_pct == null ? "–" : pct(i.upside_pct)),
    );
  }) : [el("tr", {}, el("td", { class: "empty", colspan: "9" }, "No stocks match."))]));
}

export async function renderFundamental() {
  const view = $("view-fundamental");
  if (!view.childElementCount) {
    view.append(
      el("div", { class: "intro" }, el("h2", {}, "Fundamental picks"),
        el("p", { class: "sub" }, "Long-term ideas (12 months). Every stock gets the same 100-point scorecard on valuation, "
          + "quality, growth and shareholder factors; a stock becomes a pick only when it scores high AND trades well below fair value.")),
      el("div", { id: "fund-method" }),
      el("div", { id: "fund-summary", class: "summary" }),
      el("div", { class: "controls" }, el("div", { class: "chips", id: "fund-filter" }),
        el("input", { class: "search", type: "search", placeholder: "Search stock, sector or peer group",
          oninput: (e) => { state.query = e.target.value; render(); } })),
      el("div", { class: "table-wrap" }, el("table", {},
        el("thead", {}, el("tr", {}, ["Stock", "Verdict", "Score", "Risk", "CMP", "PE", "ROE", "Fair value", "Upside"]
          .map((h, i) => el("th", { class: i >= 4 ? "num" : "" }, h)))),
        el("tbody", { id: "fund-rows" }))),
    );
  }
  state.data = await api("/fundamentals");
  renderSource(state.data.price_source, state.data.as_of);
  $("fund-method").replaceChildren(methodPanel(state.data.method));
  render();
}

export const rerenderFundamental = () => state.data && render();
