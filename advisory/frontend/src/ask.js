import { $, el } from "./util.js";

const SUGGESTIONS = [
  "What is the current price of Infosys?",
  "How is the Nifty 50 doing today?",
  "Who are the top gainers in Nifty 50 today?",
  "Is HDFC Bank fundamentally strong?",
];
const TOOL_LABELS = {
  find_symbol: "Looking up symbol",
  get_quote: "Fetching price",
  get_index_quote: "Fetching index",
  get_market_movers: "Fetching top gainers and losers",
  get_fundamentals: "Reading fundamentals",
};

const history = []; // {role, content} pairs sent back for follow-up questions
let busy = false;
let built = false;

/** Renders the model's light Markdown (bold, bullet lists) as DOM. Text is never inserted as HTML. */
function rich(text) {
  const inline = (line) => line.split(/(\*\*[^*]+\*\*)/).map((part) =>
    part.startsWith("**") && part.endsWith("**") ? el("strong", {}, part.slice(2, -2)) : part);
  const out = [];
  let list = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[*-]\s+(.*)/);
    if (bullet) {
      if (!list) out.push((list = el("ul")));
      list.append(el("li", {}, inline(bullet[1])));
    } else {
      list = null;
      if (line) out.push(el("p", {}, inline(line.replace(/^#+\s*/, ""))));
    }
  }
  return out;
}

function addMessage(role, ...children) {
  const node = el("div", { class: `msg ${role}` }, ...children);
  $("ask-log").append(node);
  node.scrollIntoView({ block: "end", behavior: "smooth" });
  return node;
}

async function send(question) {
  if (busy || !question.trim()) return;
  busy = true;
  $("ask-input").value = "";
  $("ask-send").disabled = true;
  $("ask-suggestions").hidden = true;
  addMessage("user", question);

  const steps = el("ul", { class: "steps" });
  const body = el("div", { class: "answer" }, el("p", { class: "sub thinking" }, "Thinking…"));
  const meta = el("div", { class: "meta" });
  addMessage("bot", steps, body, meta);
  let draft = "";

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history: history.slice(-8) }),
    });
    if (res.status === 502 || res.status === 504) {
      throw new Error("the backend isn't running. Start it with: uv run uvicorn main:app --port 8001");
    }
    if (!res.ok) throw new Error(`the server answered ${res.status}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines.filter(Boolean)) {
        const e = JSON.parse(line);
        if (e.type === "tool") {
          draft = ""; // text before a tool call was the model thinking aloud, not the answer
          body.replaceChildren(el("p", { class: "sub thinking" }, "Thinking…"));
          const what = Object.values(e.args).join(", ");
          steps.append(el("li", { class: e.error ? "loss" : "" },
            `${TOOL_LABELS[e.name] || e.name}${what ? `: ${what}` : ""}`,
            e.source && el("span", { class: "src" }, ` · ${e.source}`),
            e.error && el("span", { class: "src" }, ` · ${e.error}`)));
        } else if (e.type === "delta") {
          draft += e.text;
          body.replaceChildren(...rich(draft));
        } else if (e.type === "answer") {
          body.replaceChildren(...rich(e.text));
          meta.replaceChildren(`${e.disclaimer} · answered in ${e.seconds}s`);
          history.push({ role: "user", content: question }, { role: "assistant", content: e.text });
        } else if (e.type === "error") {
          body.replaceChildren(el("p", { class: "loss" }, e.text));
        }
      }
    }
  } catch (err) {
    body.replaceChildren(el("p", { class: "loss" }, `Something went wrong: ${err.message}`));
  } finally {
    busy = false;
    $("ask-send").disabled = false;
    $("ask-input").focus();
  }
}

export function renderAsk() {
  if (built) return; // keep the conversation when switching tabs
  built = true;
  const input = el("input", {
    id: "ask-input", class: "search", type: "text", maxlength: "500", autocomplete: "off",
    placeholder: "Ask about a stock, an index or today's movers",
  });
  const form = el("form", {
    class: "ask-form",
    onsubmit: (e) => { e.preventDefault(); send(input.value); },
  }, input, el("button", { id: "ask-send", class: "btn", type: "submit" }, "ASK"));

  $("view-ask").replaceChildren(
    el("div", { class: "intro" },
      el("h2", {}, "Ask AI"),
      el("p", { class: "sub" },
        "An AI assistant that looks up live prices (TradeSmart API when connected, otherwise NSE's official " +
        "data feed) and this site's fundamental scorecard before it answers. Each answer lists the data it used. " +
        "It runs on a small local model, so an answer can take up to a minute.")),
    el("div", { class: "ask" },
      el("div", { id: "ask-log", class: "ask-log" }),
      el("div", { id: "ask-suggestions", class: "chips" },
        SUGGESTIONS.map((q) => el("button", { class: "chip", type: "button", onclick: () => send(q) }, q))),
      form),
  );
  input.focus();
}
