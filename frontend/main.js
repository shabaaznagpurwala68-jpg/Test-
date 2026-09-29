const form = document.getElementById("add-form");
const rows = document.getElementById("rows");
const totalEl = document.getElementById("total");
const errorEl = document.getElementById("error");

const fmt = (n) => n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

async function refresh() {
  const [stocks, total] = await Promise.all([
    fetch("/api/stocks").then((r) => r.json()),
    fetch("/api/stocks/total").then((r) => r.json()),
  ]);

  rows.innerHTML = "";
  for (const s of stocks) {
    const tr = document.createElement("tr");
    for (const text of [s.symbol, s.quantity, fmt(s.buy_price), fmt(s.quantity * s.buy_price)]) {
      const td = document.createElement("td");
      td.textContent = text;
      tr.appendChild(td);
    }
    const btn = document.createElement("button");
    btn.textContent = "Delete";
    btn.onclick = async () => {
      await fetch(`/api/stocks/${s.id}`, { method: "DELETE" });
      refresh();
    };
    const td = document.createElement("td");
    td.appendChild(btn);
    tr.appendChild(td);
    rows.appendChild(tr);
  }
  totalEl.textContent = fmt(total.total_invested);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.textContent = "";
  const data = new FormData(form);
  const res = await fetch("/api/stocks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol: data.get("symbol"),
      quantity: Number(data.get("quantity")),
      buy_price: Number(data.get("buy_price")),
    }),
  });
  if (!res.ok) {
    const body = await res.json();
    errorEl.textContent = Array.isArray(body.detail)
      ? body.detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join("; ")
      : body.detail;
    return;
  }
  form.reset();
  refresh();
});

refresh();
