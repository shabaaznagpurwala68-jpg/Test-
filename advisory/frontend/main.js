const $ = (id) => document.getElementById(id);
const inr = (n) => "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pct = (n) => (n > 0 ? "+" : "") + n.toFixed(2) + "%";
const tone = (n) => (n > 0 ? "gain" : n < 0 ? "loss" : "");
const STATUS = { OPEN: "OPEN", TARGET_HIT: "TARGET HIT", SL_HIT: "SL HIT" };

const state = { action: "", query: "", data: null };

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "style") node.style.cssText = v;
    else node.setAttribute(k, v);
  }
  for (const c of children) node.append(c ?? "");
  return node;
}

function track(progress) {
  return el("div", { class: "track", title: "Stop loss → Target" },
    el("span", { class: "marker", style: `left:${progress * 100}%` }));
}

async function loadRecs() {
  const qs = state.action ? `?action=${state.action}` : "";
  const res = await fetch(`/api/recommendations${qs}`);
  state.data = await res.json();
  renderSource(state.data.price_source, state.data.as_of);
  renderSummary(state.data.summary);
  renderRows();
}

function renderSource(source, asOf) {
  const label = { live: "LIVE PRICES", mixed: "PARTLY LIVE PRICES", dummy: "DUMMY PRICES" }[source];
  const time = new Date(asOf).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  $("source").replaceChildren(
    el("span", { class: `dot ${source === "live" ? "live" : ""}` }),
    label,
    el("span", { class: "as-of" }, ` · ${time}`),
  );
}

function renderSummary(s) {
  const card = (label, value, cls = "") =>
    el("div", { class: "card" }, el("div", { class: "label" }, label), el("div", { class: `value ${cls}` }, value));
  $("summary").replaceChildren(
    card("Open calls", String(s.open)),
    card("Target hit", String(s.target_hit), s.target_hit ? "gain" : ""),
    card("SL hit", String(s.sl_hit), s.sl_hit ? "loss" : ""),
    card("Avg potential (open)", pct(s.avg_potential_open), tone(s.avg_potential_open)),
  );
}

function renderRows() {
  const q = state.query.trim().toLowerCase();
  const items = state.data.items.filter(
    (i) => !q || [i.symbol, i.name, i.sector].some((f) => f.toLowerCase().includes(q)),
  );
  if (!items.length) {
    $("rows").replaceChildren(el("tr", {}, el("td", { class: "empty", colspan: "9" }, "No recommendations match.")));
    return;
  }
  $("rows").replaceChildren(
    ...items.map((i) => {
      const tr = el("tr", { tabindex: "0" },
        el("td", {}, el("div", { class: "sym" }, i.symbol), el("div", { class: "sub" }, `${i.name} · ${i.sector}`)),
        el("td", {}, el("span", { class: `badge call-${i.action}` }, i.action)),
        el("td", { class: "num" }, inr(i.entry)),
        el("td", { class: "num" }, inr(i.cmp), el("div", { class: `sub ${tone(i.change_pct)}` }, pct(i.change_pct))),
        el("td", { class: "num" }, inr(i.target)),
        el("td", { class: "num" }, inr(i.stop_loss)),
        el("td", { class: `num ${tone(i.potential_pct)}` }, pct(i.potential_pct)),
        el("td", {}, track(i.progress)),
        el("td", {}, el("span", { class: `badge st-${i.status}` }, STATUS[i.status])),
      );
      tr.onclick = () => openDrawer(i.id);
      tr.onkeydown = (e) => e.key === "Enter" && openDrawer(i.id);
      return tr;
    }),
  );
}

async function openDrawer(id) {
  const res = await fetch(`/api/recommendations/${id}`);
  if (!res.ok) return;
  const r = await res.json();
  const kv = (k, v) => el("div", { class: "kv" }, el("span", {}, k), el("span", {}, v));
  const lvl = (label, v) => el("div", {}, el("div", { class: "label" }, label), el("div", { class: "v" }, v));
  $("drawer-body").replaceChildren(
    el("span", { class: `badge call-${r.action}` }, r.action),
    el("h2", { style: "margin-top:8px" }, r.name),
    el("div", { class: "sub" }, `${r.symbol} · NSE · ${r.sector}`),
    el("div", { class: "price" }, inr(r.cmp)),
    el("div", { class: tone(r.change_pct) }, `${pct(r.change_pct)} today`),
    el("div", { class: "levels" }, lvl("Entry", inr(r.entry)), lvl("Target", inr(r.target)), lvl("Stop loss", inr(r.stop_loss))),
    track(r.progress),
    el("div", { class: "track-labels" }, el("span", {}, "Stop loss"), el("span", {}, "Target")),
    el("div", { style: "margin-top:16px" },
      kv("Potential to target", pct(r.potential_pct)),
      kv("Status", STATUS[r.status]),
      kv("Horizon", r.horizon),
      kv("Issued on", new Date(r.issued_on).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })),
    ),
    el("div", { class: "rationale" }, el("strong", {}, "Rationale. "), r.rationale),
    el("p", { class: "sub", style: "margin-top:16px" }, "Disclaimer: The securities are quoted as an example and not as a recommendation."),
  );
  $("drawer").classList.add("open");
  $("drawer").setAttribute("aria-hidden", "false");
  $("scrim").classList.add("open");
  $("drawer-close").focus();
}

function closeDrawer() {
  $("drawer").classList.remove("open");
  $("drawer").setAttribute("aria-hidden", "true");
  $("scrim").classList.remove("open");
}

function timeAgo(iso) {
  if (!iso) return "";
  const mins = Math.round((Date.now() - new Date(iso)) / 60000);
  if (mins < 60) return `${Math.max(mins, 1)} min ago`;
  if (mins < 1440) return `${Math.round(mins / 60)} hr ago`;
  return `${Math.round(mins / 1440)} d ago`;
}

async function loadNews() {
  const res = await fetch("/api/news");
  const { items } = await res.json();
  $("news").replaceChildren(
    ...items.map((n) =>
      el("li", {},
        el("div", { class: "meta" }, `${n.source.toUpperCase()} · ${timeAgo(n.published)}`),
        n.link ? el("a", { href: n.link, target: "_blank", rel: "noopener noreferrer" }, n.title) : el("span", {}, n.title),
      ),
    ),
  );
}

// Tabs
document.querySelectorAll(".tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
    const view = tab.dataset.view;
    $("view-recs").hidden = view !== "recs";
    $("view-news").hidden = view !== "news";
    if (view === "news") loadNews();
  };
});

// Filter chips (server-side filter) and search (client-side)
$("filters").onclick = (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("selected", c === chip));
  state.action = chip.dataset.action;
  loadRecs();
};
$("search").oninput = (e) => {
  state.query = e.target.value;
  if (state.data) renderRows();
};

$("drawer-close").onclick = closeDrawer;
$("scrim").onclick = closeDrawer;
document.addEventListener("keydown", (e) => e.key === "Escape" && closeDrawer());

loadRecs();
setInterval(loadRecs, 60000); // backend caches prices for 5 min, so this is cheap
