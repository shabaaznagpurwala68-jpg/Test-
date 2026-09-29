import { closeDrawer } from "./drawer.js";
import { renderNews } from "./news.js";
import { loadRecs, recState, renderRecs } from "./recs.js";
import { onProfileChange, renderRisk } from "./risk.js";
import { renderTrack } from "./track.js";
import { $ } from "./util.js";

const views = { recs: loadRecs, track: renderTrack, news: renderNews, risk: () => renderRisk(goToRecs) };

function show(view) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === view));
  for (const v of Object.keys(views)) $(`view-${v}`).hidden = v !== view;
  views[view]();
}

function goToRecs(suitedOnly = false) {
  recState.suitedOnly = suitedOnly;
  $("suited-only").checked = suitedOnly;
  show("recs");
}

document.querySelectorAll(".tab").forEach((tab) => (tab.onclick = () => show(tab.dataset.view)));

$("filters").onclick = (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  document.querySelectorAll("#filters .chip").forEach((c) => c.classList.toggle("selected", c === chip));
  recState.action = chip.dataset.action;
  loadRecs();
};
$("search").oninput = (e) => {
  recState.query = e.target.value;
  renderRecs();
};
$("suited-only").onchange = (e) => {
  recState.suitedOnly = e.target.checked;
  renderRecs();
};
onProfileChange(() => renderRecs());

$("drawer-close").onclick = closeDrawer;
$("scrim").onclick = closeDrawer;
document.addEventListener("keydown", (e) => e.key === "Escape" && closeDrawer());

loadRecs();
setInterval(() => !$("view-recs").hidden && loadRecs(), 60000); // backend caches prices for 5 min
