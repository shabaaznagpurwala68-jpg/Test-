import { openCall } from "./drawer.js";
import { getProfile, isSuited } from "./risk.js";
import { $, api, badge, card, day, el, inr, pct, tone, track } from "./util.js";

export const techState = { setup: "", query: "", suitedOnly: false, data: null, setups: null };

export async function loadTechnical() {
  const [data, setups] = await Promise.all([api("/calls"), techState.setups ? techState.setups : api("/setups")]);
  techState.data = data;
  techState.setups = setups;
  renderSource(data.price_source, data.as_of);
  renderSetupCards();
  renderTechnical();
}

export function renderSource(source, asOf) {
  const label = { live: "LIVE PRICES", mixed: "PARTLY LIVE PRICES", dummy: "DUMMY PRICES" }[source];
  const time = new Date(asOf).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  $("source").replaceChildren(el("span", { class: `dot ${source === "live" ? "live" : ""}` }), label,
    el("span", { class: "as-of" }, ` · ${time}`));
}

function selectSetup(key) {
  techState.setup = key;
  renderSetupCards();
  renderTechnical();
}

function renderSetupCards() {
  $("setup-cards").replaceChildren(...techState.setups.map((s) =>
    el("button", {
      class: `setup-card ${techState.setup === s.key ? "selected" : ""}`,
      "aria-pressed": techState.setup === s.key ? "true" : "false",
      onclick: () => selectSetup(techState.setup === s.key ? "" : s.key),
    },
      el("div", { class: "setup-head" }, el("h3", {}, s.name), badge(`${s.stats.open} OPEN`, "count")),
      el("p", { class: "setup-idea" }, s.idea),
      el("ul", { class: "rules" }, s.rules.map((r) => el("li", {}, r))),
      el("div", { class: "setup-levels" }, `SL: ${s.levels.stop_loss} · Target: 1:2 risk-reward · ${s.levels.horizon}`),
      el("div", { class: "setup-stats" },
        el("span", {}, el("strong", {}, String(s.stats.calls)), " calls in 12M"),
        el("span", {}, el("strong", {}, `${s.stats.win_rate}%`), " profitable"),
        el("span", { class: tone(s.stats.avg_return_pct) }, el("strong", {}, pct(s.stats.avg_return_pct)), " avg"),
      ),
      el("p", { class: "sub" }, s.risk_note),
    )));
  $("setup-filter").replaceChildren(
    ...[{ key: "", name: "ALL SETUPS" }, ...techState.setups].map((s) =>
      el("button", { class: `chip ${techState.setup === s.key ? "selected" : ""}`, onclick: () => selectSetup(s.key) },
        s.name.toUpperCase())));
}

export function renderTechnical() {
  if (!techState.data) return;
  const { summary } = techState.data;
  const profile = getProfile();
  const items = techState.data.items.filter((c) => !techState.setup || c.setup === techState.setup);
  const suitedCount = items.filter((c) => isSuited(c, profile)).length;

  $("suited-toggle").hidden = !profile;
  $("tech-summary").replaceChildren(
    card("Open calls", String(items.length), "", techState.setup ? "In this setup" : "Across all setups"),
    card("Avg potential (open)", pct(summary.avg_potential_open), tone(summary.avg_potential_open), "Distance to target"),
    card("12-month win rate", `${summary.win_rate}%`, "", `From ${summary.closed} closed calls`),
    profile
      ? card("Your profile", profile.profile, "", `${suitedCount} of ${items.length} open calls suit you`)
      : el("button", { class: "card card-cta", onclick: () => document.querySelector('.tab[data-view="risk"]').click() },
          el("div", { class: "label" }, "Your profile"), el("div", { class: "value cta" }, "Take the 1-min quiz →")),
  );

  const q = techState.query.trim().toLowerCase();
  const rows = items.filter((c) =>
    (!q || [c.symbol, c.name, c.sector].some((f) => f.toLowerCase().includes(q)))
    && (!techState.suitedOnly || isSuited(c, profile)));

  $("tech-rows").replaceChildren(
    ...(rows.length ? rows.map((c) => {
      const suited = isSuited(c, profile);
      return el("tr", { tabindex: "0", onclick: () => openCall(c.id), onkeydown: (e) => e.key === "Enter" && openCall(c.id) },
        el("td", {}, el("div", { class: "sym" }, c.symbol), el("div", { class: "sub" }, `${c.name} · ${c.sector}`)),
        el("td", {}, badge(c.setup_name.toUpperCase(), "setup")),
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
    }) : [el("tr", {}, el("td", { class: "empty", colspan: "10" },
      techState.setup ? "No open calls from this setup right now. New calls appear after a market close when every rule passes."
        : "No open calls match."))]),
  );
}
