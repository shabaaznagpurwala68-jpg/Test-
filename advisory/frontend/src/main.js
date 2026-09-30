import { closeDrawer } from "./drawer.js";
import { renderFundamental, rerenderFundamental } from "./fundamental.js";
import { renderMarkets } from "./markets.js";
import { renderNews } from "./news.js";
import { onProfileChange, renderRisk } from "./risk.js";
import { loadTechnical, renderTechnical, techState } from "./technical.js";
import { renderTrack } from "./track.js";
import { $ } from "./util.js";

const views = {
  fundamental: renderFundamental,
  technical: loadTechnical,
  markets: renderMarkets,
  track: renderTrack,
  news: renderNews,
  risk: () => renderRisk(goToTechnical),
};

function show(view) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === view));
  for (const v of Object.keys(views)) $(`view-${v}`).hidden = v !== view;
  views[view]();
}

function goToTechnical(suitedOnly = false) {
  techState.suitedOnly = suitedOnly;
  $("suited-only").checked = suitedOnly;
  show("technical");
}

document.querySelectorAll(".tab").forEach((tab) => (tab.onclick = () => show(tab.dataset.view)));
$("search").oninput = (e) => {
  techState.query = e.target.value;
  renderTechnical();
};
$("suited-only").onchange = (e) => {
  techState.suitedOnly = e.target.checked;
  renderTechnical();
};
onProfileChange(() => {
  renderTechnical();
  rerenderFundamental();
});

$("drawer-close").onclick = closeDrawer;
$("scrim").onclick = closeDrawer;
document.addEventListener("keydown", (e) => e.key === "Escape" && closeDrawer());

renderFundamental();
setInterval(() => !$("view-technical").hidden && loadTechnical(), 60000); // backend caches prices for 5 min
