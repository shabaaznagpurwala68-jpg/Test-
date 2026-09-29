import { $, api, el, store } from "./util.js";

const KEY = "ts-risk-profile";
const listeners = [];

export const getProfile = () => store.get(KEY);
export const onProfileChange = (fn) => listeners.push(fn);
export const isSuited = (call, profile = getProfile()) => !profile || profile.suited_levels.includes(call.risk_level);

function setProfile(p) {
  p ? store.set(KEY, p) : store.remove(KEY);
  listeners.forEach((fn) => fn(p));
}

export async function renderRisk(goToRecs) {
  const view = $("view-risk");
  const profile = getProfile();
  if (profile) {
    view.replaceChildren(resultCard(profile, goToRecs));
    return;
  }
  const questions = await api("/risk/questions");
  const answers = new Array(questions.length).fill(null);
  const submit = el("button", { class: "btn", disabled: true }, "SEE MY PROFILE");

  const form = el("form", { class: "quiz" },
    el("h2", {}, "Find your risk profile"),
    el("p", { class: "sub" }, "7 quick questions. We use your answers to show which calls suit you."),
    questions.map((q, qi) =>
      el("fieldset", {},
        el("legend", {}, `${qi + 1}. ${q.question}`),
        el("div", { class: "options" },
          q.options.map((opt, oi) =>
            el("label", { class: "option" },
              el("input", {
                type: "radio", name: `q${qi}`, value: oi,
                onchange: () => {
                  answers[qi] = oi;
                  submit.disabled = answers.includes(null);
                },
              }),
              el("span", {}, opt),
            ),
          ),
        ),
      ),
    ),
    submit,
  );
  form.onsubmit = async (e) => {
    e.preventDefault();
    const result = await api("/risk/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers }),
    });
    setProfile(result);
    renderRisk(goToRecs);
    window.scrollTo({ top: 0 });
  };
  view.replaceChildren(form);
}

function resultCard(p, goToRecs) {
  return el("div", { class: "profile-card" },
    el("div", { class: "label" }, "YOUR RISK PROFILE"),
    el("h2", {}, p.profile),
    el("p", {}, p.description),
    el("div", { class: "scorebar" }, el("span", { style: `width:${(p.score / p.max_score) * 100}%` })),
    el("div", { class: "sub" }, `Score ${p.score} of ${p.max_score}`),
    el("p", {}, "Calls suited to you: ", el("strong", {}, p.suited_levels.join(", ")), " risk."),
    el("p", { class: "sub" },
      "Risk levels come from each stock's measured volatility over the last 6 months: Low under 20% a year, "
      + "Medium 20–28%, High above 28%. SELL calls are at least Medium."),
    el("div", { class: "actions" },
      el("button", { class: "btn", onclick: () => goToRecs(true) }, "SEE CALLS SUITED TO ME"),
      el("button", { class: "btn-link", onclick: () => { setProfile(null); renderRisk(goToRecs); } }, "Retake quiz"),
    ),
    el("p", { class: "sub" }, "Saved in this browser only. A live product would record this against your KYC, as SEBI requires."),
  );
}
