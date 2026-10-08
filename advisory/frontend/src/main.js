import { closeDrawer } from "./drawer.js";
import { renderFundamental, rerenderFundamental } from "./fundamental.js";
import { renderLearn, signupForm } from "./learn.js";
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
  learn: renderLearn,
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

document.querySelectorAll(".tab").forEach((tab) => (tab.onclick = () => {
  // A tab click is a fresh start: LEARN opens the post list, and other tabs drop any post link.
  history.replaceState(null, "", tab.dataset.view === "learn" ? "#learn" : location.pathname);
  show(tab.dataset.view);
}));
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

$("footer-signup").append(signupForm({ compact: true }));
// A shared post link (#learn/<slug>) opens that post; otherwise start on Fundamental.
window.addEventListener("popstate", () => location.hash.startsWith("#learn") && show("learn"));
if (location.hash.startsWith("#learn")) show("learn");
else renderFundamental();
setInterval(() => !$("view-technical").hidden && loadTechnical(), 60000); // backend caches prices for 5 min
