import { openDrawer } from "./drawer.js";
import { getProfile, isSuited } from "./risk.js";
import { $, api, badge, card, day, el, inr, pct, tone, track } from "./util.js";

export const recState = { action: "", query: "", suitedOnly: false, data: null };

export async function loadRecs() {
  const qs = recState.action ? `?action=${recState.action}` : "";
  recState.data = await api(`/recommendations${qs}`);
  renderSource(recState.data.price_source, recState.data.as_of);
  renderRecs();
}

function renderSource(source, asOf) {
  const label = { live: "LIVE PRICES", mixed: "PARTLY LIVE PRICES", dummy: "DUMMY PRICES" }[source];
  const time = new Date(asOf).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  $("source").replaceChildren(el("span", { class: `dot ${source === "live" ? "live" : ""}` }), label,
    el("span", { class: "as-of" }, ` · ${time}`));
}

export function renderRecs() {
  if (!recState.data) return;
  const { items, summary } = recState.data;
  const profile = getProfile();
  const suitedCount = items.filter((c) => isSuited(c, profile)).length;

  $("suited-toggle").hidden = !profile;
  $("rec-summary").replaceChildren(
    card("Open calls", String(summary.open)),
    card("Avg potential (open)", pct(summary.avg_potential_open), tone(summary.avg_potential_open)),
    card("Win rate", `${summary.win_rate}%`, "", `From ${summary.closed} closed calls`),
    profile
      ? card("Your profile", profile.profile, "", `${suitedCount} of ${items.length} calls suit you`)
      : el("button", { class: "card card-cta", onclick: () => document.querySelector('.tab[data-view="risk"]').click() },
          el("div", { class: "label" }, "Your profile"), el("div", { class: "value cta" }, "Take the 1-min quiz →")),
  );

  const q = recState.query.trim().toLowerCase();
  const rows = items.filter((c) =>
    (!q || [c.symbol, c.name, c.sector].some((f) => f.toLowerCase().includes(q)))
    && (!recState.suitedOnly || isSuited(c, profile)));

  $("rec-rows").replaceChildren(
    ...(rows.length ? rows.map((c) => {
      const suited = isSuited(c, profile);
      const tr = el("tr", { tabindex: "0", onclick: () => openDrawer(c.id), onkeydown: (e) => e.key === "Enter" && openDrawer(c.id) },
        el("td", {}, el("div", { class: "sym" }, c.symbol), el("div", { class: "sub" }, `${c.name} · ${c.sector}`)),
        el("td", {}, badge(c.action, `call-${c.action}`)),
        el("td", {}, badge(c.risk_level.toUpperCase(), `risk-${c.risk_level}`),
          profile && !suited && el("div", { class: "sub unsuited-text" }, "Not suited to you")),
        el("td", { class: "num" }, inr(c.entry)),
        el("td", { class: "num" }, inr(c.cmp), el("div", { class: `sub ${tone(c.change_pct)}` }, pct(c.change_pct))),
        el("td", { class: "num" }, inr(c.target)),
        el("td", { class: "num" }, inr(c.stop_loss)),
        el("td", { class: `num ${tone(c.potential_pct)}` }, pct(c.potential_pct)),
        el("td", {}, track(c.progress)),
        el("td", { class: "sub nowrap" }, day(c.issued_on)),
      );
      return tr;
    }) : [el("tr", {}, el("td", { class: "empty", colspan: "10" }, "No open calls match."))]),
  );
}
