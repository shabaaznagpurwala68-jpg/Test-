import { callChart } from "./charts.js";
import { isSuited, getProfile } from "./risk.js";
import { $, STATUS, api, badge, day, el, inr, pct, tone, track } from "./util.js";

let chart = null;

export async function openDrawer(id) {
  const c = await api(`/recommendations/${id}`);
  const closed = c.status !== "OPEN";
  const kv = (k, v) => el("div", { class: "kv" }, el("span", {}, k), el("span", {}, v));
  const lvl = (label, v, cls = "") => el("div", {}, el("div", { class: "label" }, label), el("div", { class: `v ${cls}` }, v));
  const profile = getProfile();
  const chartBox = el("div", { class: "chart" });
  const explainBox = el("div", { class: "explain", hidden: true });
  const newsBox = el("div", { class: "drawer-news" }, el("div", { class: "sub" }, "Loading news…"));

  const explainBtn = el("button", {
    class: "btn-outline",
    onclick: async () => {
      if (explainBox.hidden && !explainBox.childElementCount) {
        const { paragraphs } = await api(`/recommendations/${id}/explain`);
        explainBox.append(
          ...paragraphs.map((p) => el("p", {}, p)),
          el("p", { class: "sub" }, "Auto-generated from this call's numbers. Not investment advice."),
        );
      }
      explainBox.hidden = !explainBox.hidden;
      explainBtn.textContent = explainBox.hidden ? "EXPLAIN THIS CALL SIMPLY" : "HIDE EXPLANATION";
    },
  }, "EXPLAIN THIS CALL SIMPLY");

  // Built with el() so conditional parts that evaluate to false are skipped, not printed.
  $("drawer-body").replaceChildren(el("div", {},
    el("div", { class: "badges" },
      badge(c.action, `call-${c.action}`),
      badge(`${c.risk_level.toUpperCase()} RISK`, `risk-${c.risk_level}`),
      closed && badge(STATUS[c.status], `st-${c.status}`),
      profile && !isSuited(c, profile) && badge("NOT SUITED TO YOUR PROFILE", "unsuited"),
    ),
    el("h2", {}, c.name),
    el("div", { class: "sub" }, `${c.symbol} · NSE · ${c.sector}`),
    el("div", { class: "price" }, inr(c.cmp)),
    el("div", { class: tone(c.change_pct) }, `${pct(c.change_pct)} today`),
    chartBox,
    closed
      ? el("div", { class: "levels" }, lvl("Entry", inr(c.entry)), lvl("Exit", inr(c.exit_price)),
          lvl("Result", pct(c.return_pct), tone(c.return_pct)))
      : el("div", { class: "levels" }, lvl("Entry", inr(c.entry)), lvl("Target", inr(c.target)), lvl("Stop loss", inr(c.stop_loss))),
    !closed && [track(c.progress), el("div", { class: "track-labels" }, el("span", {}, "Stop loss"), el("span", {}, "Target"))],
    el("div", { class: "kvs" },
      closed ? kv("Target / Stop loss", `${inr(c.target)} / ${inr(c.stop_loss)}`) : kv("Potential to target", pct(c.potential_pct)),
      kv("Status", STATUS[c.status]),
      kv("Horizon", c.horizon),
      kv("Issued on", day(c.issued_on)),
      closed && kv("Closed on", `${day(c.closed_on)} (${c.days_held} days)`),
      kv("Volatility", `${c.volatility}% a year`),
    ),
    el("div", { class: "rationale" }, el("strong", {}, "Rationale. "), c.rationale),
    explainBtn,
    explainBox,
    el("h3", {}, `News on ${c.symbol}`),
    newsBox,
    el("p", { class: "sub" }, "Disclaimer: The securities are quoted as an example and not as a recommendation."),
  ));

  $("drawer").classList.add("open");
  $("drawer").setAttribute("aria-hidden", "false");
  $("scrim").classList.add("open");
  $("drawer-close").focus();

  chart?.remove();
  const { bars } = await api(`/recommendations/${id}/candles`);
  chart = callChart(chartBox, c, bars);

  const { items } = await api(`/news?symbol=${encodeURIComponent(c.symbol)}`);
  newsBox.replaceChildren(
    items.length
      ? el("ul", { class: "mini-news" }, items.slice(0, 5).map((n) =>
          el("li", {}, n.link ? el("a", { href: n.link, target: "_blank", rel: "noopener noreferrer" }, n.title) : n.title,
            el("div", { class: "sub" }, n.source))))
      : el("div", { class: "sub" }, "No recent headlines mention this stock."),
  );
}

export function closeDrawer() {
  $("drawer").classList.remove("open");
  $("drawer").setAttribute("aria-hidden", "true");
  $("scrim").classList.remove("open");
}
