export const $ = (id) => document.getElementById(id);

export const inr = (n) =>
  "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const inr0 = (n) => (n < 0 ? "−" : "") + "₹" + Math.abs(Math.round(n)).toLocaleString("en-IN");
export const pct = (n) => (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n).toFixed(2) + "%";
export const tone = (n) => (n > 0 ? "gain" : n < 0 ? "loss" : "");
export const day = (iso) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

export const STATUS = { OPEN: "OPEN", TARGET_HIT: "TARGET HIT", SL_HIT: "SL HIT", EXPIRED: "EXPIRED" };

export async function api(path, options) {
  const res = await fetch(`/api${path}`, options);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}

/** Tiny DOM builder. Text children are inserted as text, never as HTML. */
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k === "class") node.className = v;
    else if (k === "style") node.style.cssText = v;
    else if (k.startsWith("on")) node[k] = v;
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) if (c != null && c !== false && c !== "") node.append(c);
  return node;
}

export const badge = (text, cls) => el("span", { class: `badge ${cls}` }, text);
export const card = (label, value, cls = "", sub = null) =>
  el("div", { class: "card" }, el("div", { class: "label" }, label),
    el("div", { class: `value ${cls}` }, value), sub && el("div", { class: "sub" }, sub));

export function track(progress) {
  return el("div", { class: "track", title: "Stop loss → Target" },
    el("span", { class: "marker", style: `left:${progress * 100}%` }));
}

/** Reads a design token so canvas charts use the same colours as the CSS. */
export const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
export function alpha(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}

// Browser storage can be unavailable (private mode, blocked site data): never let that break the page.
export const store = {
  get(key) {
    try { return JSON.parse(localStorage.getItem(key)); } catch { return null; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* ignore */ }
  },
  remove(key) {
    try { localStorage.removeItem(key); } catch { /* ignore */ }
  },
};
