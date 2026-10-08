import { $, api, day, el } from "./util.js";

const CATEGORIES = [["", "ALL"], ["Market Events", "MARKET EVENTS"], ["Guides", "GUIDES"], ["Weekly Wrap", "WEEKLY WRAP"]];
const catClass = (c) => `cat-${c.replace(/\s+/g, "")}`;
const state = { category: "", posts: [], issue: null };

/** Newsletter sign-up form; `compact` is the one-line footer version. */
export function signupForm({ compact = false } = {}) {
  let frequency = "WEEKLY";
  const input = el("input", { type: "email", required: true, placeholder: "you@example.com", "aria-label": "Email address", class: "field" });
  const msg = el("p", { class: "signup-msg", role: "status" });
  const freq = el("div", { class: "chips", role: "radiogroup", "aria-label": "How often" },
    [["WEEKLY", "WEEKLY"], ["EVENTS", "MARKET EVENTS ONLY"]].map(([v, label]) =>
      el("button", {
        type: "button", class: `chip ${v === frequency ? "selected" : ""}`, role: "radio", "aria-checked": String(v === frequency),
        onclick: (e) => {
          frequency = v;
          freq.querySelectorAll(".chip").forEach((c) => { c.classList.toggle("selected", c === e.currentTarget); c.setAttribute("aria-checked", String(c === e.currentTarget)); });
        },
      }, label)));
  const button = el("button", { type: "submit", class: "btn" }, "SUBSCRIBE");
  const form = el("form", { class: compact ? "signup compact" : "signup" },
    !compact && el("h3", {}, "The Smart Weekly"),
    !compact && el("p", { class: "sub" }, "Your week in markets, in five minutes: new calls, top picks, breadth and what to read. Free."),
    el("div", { class: "signup-row" }, input, button),
    !compact && freq,
    msg);
  form.onsubmit = async (e) => {
    e.preventDefault();
    button.disabled = true;
    msg.className = "signup-msg";
    try {
      const res = await fetch("/api/newsletter/subscribe", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: input.value, frequency }),
      });
      const body = await res.json();
      msg.textContent = res.ok ? body.message : (typeof body.detail === "string" ? body.detail : "Please enter a valid email address.");
      msg.classList.add(res.ok ? "ok" : "err");
      if (res.ok) input.value = "";
    } catch {
      msg.textContent = "Couldn't reach the server. Please try again.";
      msg.classList.add("err");
    } finally {
      button.disabled = false;
    }
  };
  return form;
}

function card(p, big = false) {
  return el("a", { class: `post-card ${big ? "featured" : ""}`, href: `#learn/${p.slug}`, onclick: (e) => { e.preventDefault(); openPost(p.slug); } },
    el("div", { class: `post-art ${catClass(p.category)}` },
      el("span", { class: "post-cat" }, p.category.toUpperCase()),
      big && el("span", { class: "post-art-title" }, p.title)),
    el("div", { class: "post-body" },
      big && el("span", { class: "badge setup" }, "FEATURED"),
      el("h3", {}, p.title),
      el("p", { class: "post-excerpt" }, p.excerpt),
      el("p", { class: "sub" }, `${day(p.date)} · ${p.read_min} min read`)));
}

function issuePreview(issue) {
  return el("div", { class: "email" },
    el("div", { class: "email-meta" },
      el("div", {}, el("span", { class: "sub" }, "Subject: "), el("strong", {}, issue.subject)),
      el("div", { class: "sub" }, issue.preheader)),
    el("div", { class: "email-body" },
      el("div", { class: "email-head" }, el("img", { src: "/tradesmart-logo.png", alt: "TradeSmart", height: "30" }),
        el("span", { class: "sub" }, `${issue.name} · ${day(issue.date)}`)),
      issue.sections.map((s) => el("section", {},
        el("h4", {}, s.title),
        s.slugs
          ? el("ul", {}, s.lines.map((line, i) => el("li", {}, el("a", { href: `#learn/${s.slugs[i]}`, onclick: (e) => { e.preventDefault(); openPost(s.slugs[i]); } }, line))))
          : el("ul", {}, s.lines.map((line) => el("li", {}, line))))),
      el("div", { class: "email-foot" }, issue.footer.map((f) => el("p", {}, f)))));
}

function renderList() {
  const posts = state.posts.filter((p) => !state.category || p.category === state.category);
  const featured = state.category ? null : state.posts.find((p) => p.featured);
  const rest = posts.filter((p) => p !== featured);
  $("view-learn").replaceChildren(
    el("div", { class: "intro" }, el("h2", {}, "Learn"),
      el("p", { class: "sub" }, "Market events explained, how our methods work, and a weekly wrap built from the app's own numbers. Sample content.")),
    el("div", { class: "learn-layout" },
      el("div", { class: "learn-main" },
        featured && card(featured, true),
        el("div", { class: "chips" }, CATEGORIES.map(([v, label]) =>
          el("button", { class: `chip ${state.category === v ? "selected" : ""}`, onclick: () => { state.category = v; renderList(); } }, label))),
        el("div", { class: "post-grid" }, rest.map((p) => card(p)))),
      el("aside", { class: "learn-side" }, el("div", { class: "panel" }, signupForm()))),
    state.issue && el("div", { class: "issue" },
      el("div", { class: "panel-head section-title" }, el("h3", {}, "Latest issue · preview"),
        el("span", { class: "sub" }, "Built automatically from this week's data. Sending is not switched on in this demo.")),
      issuePreview(state.issue)),
  );
}

function block(b) {
  if (b.type === "h") return el("h3", {}, b.content);
  if (b.type === "ul") return el("ul", {}, b.content.map((i) => el("li", {}, i)));
  if (b.type === "callout") return el("div", { class: "callout" }, b.content);
  return el("p", {}, b.content);
}

/** Make the Learn tab the visible one WITHOUT re-running its loader. (Clicking the tab here
 *  would call renderLearn, which re-opens the post from the URL — an endless reload loop.) */
function showLearnSection() {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === "learn"));
  document.querySelectorAll("main > section[id^='view-']").forEach((sec) => { sec.hidden = sec.id !== "view-learn"; });
}

export async function openPost(slug) {
  const p = await api(`/posts/${encodeURIComponent(slug)}`);
  if (location.hash !== `#learn/${slug}`) history.pushState(null, "", `#learn/${slug}`);
  showLearnSection();
  $("view-learn").replaceChildren(
    el("article", { class: "article" },
      el("a", { href: "#learn", class: "back", onclick: (e) => { e.preventDefault(); history.pushState(null, "", "#learn"); renderList(); } }, "← All posts"),
      el("div", { class: `article-art ${catClass(p.category)}` }, el("span", { class: "post-cat" }, p.category.toUpperCase())),
      el("h1", {}, p.title),
      el("p", { class: "sub" }, `${day(p.date)} · ${p.read_min} min read · TradeSmart Learn`),
      el("div", { class: "article-body" }, p.body.map(block)),
      el("div", { class: "plan" },
        el("div", {}, el("strong", {}, "Trade @ ₹15 per executed order."), el("p", { class: "sub" }, "Stocks, F&O, mutual funds and commodities.")),
        el("a", { class: "btn", href: "https://www.tradesmartonline.in", target: "_blank", rel: "noopener noreferrer" }, "OPEN AN ACCOUNT")),
      el("p", { class: "legal" }, "Disclaimer: The securities are quoted as an example and not as a recommendation. Sample content for demonstration."),
      el("div", { class: "panel" }, signupForm()),
      el("h3", { class: "section-title" }, "Related posts"),
      el("div", { class: "post-grid three" }, p.related.map((r) => card(r))),
    ));
  window.scrollTo({ top: 0 });
}

export async function renderLearn() {
  const [posts, issue] = await Promise.all([api("/posts"), api("/newsletter/latest")]);
  state.posts = posts.items;
  state.issue = issue;
  const m = location.hash.match(/^#learn\/(.+)$/);
  if (m) return openPost(decodeURIComponent(m[1]));
  renderList();
}
