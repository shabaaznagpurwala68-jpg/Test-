import { $, api, el } from "./util.js";

let filter = null;

function timeAgo(iso) {
  if (!iso) return "";
  const mins = Math.round((Date.now() - new Date(iso)) / 60000);
  if (mins < 60) return `${Math.max(mins, 1)} min ago`;
  if (mins < 1440) return `${Math.round(mins / 60)} hr ago`;
  return `${Math.round(mins / 1440)} d ago`;
}

export async function renderNews() {
  const { items } = await api(filter ? `/news?symbol=${encodeURIComponent(filter)}` : "/news");
  $("view-news").replaceChildren(
    filter
      ? el("div", { class: "filter-bar" }, `Showing news on ${filter} · `,
          el("button", { class: "btn-link", onclick: () => { filter = null; renderNews(); } }, "Show all"))
      : el("p", { class: "sub" }, "Headlines from Economic Times, Moneycontrol and Livemint. Tags show which covered stocks a headline mentions."),
    el("ul", { class: "news" },
      items.length ? items.map((n) =>
        el("li", {},
          el("div", { class: "meta" }, `${n.source.toUpperCase()} · ${timeAgo(n.published)}`),
          n.link ? el("a", { href: n.link, target: "_blank", rel: "noopener noreferrer" }, n.title) : el("span", {}, n.title),
          n.symbols.length > 0 && el("div", { class: "tags" }, n.symbols.map((s) =>
            el("button", { class: "tag", onclick: () => { filter = s; renderNews(); } }, s))),
        )) : el("li", { class: "sub" }, "No headlines."),
    ),
  );
}
