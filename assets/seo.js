/* SEO-Check im Profil: kompletter Score, was passt, was nicht, Vorschlaege fuer Entitaeten und ein Auftrag fuer die eigene KI (MCP).
   M365U.seo.box({ kind, id, draft: function () { return {title, summary, body, topics, lang}; }, onAddTopic: function (id) {} }) -> Element
   M365U.seo.scores(cb) -> cb({ "kind:id": score }) fuer Badges in Listen. Pruefregeln: worker/src/seo.js (gleiche wie im Seitenbau und im MCP). */
(function () {
  var U = window.M365U; if (!U) return;
  var h = U.h, api = U.api, de = (window.M365X || {}).lang === "de";
  var T = de ? { check: "SEO prüfen", busy: "Prüfe …", good: "Das passt", bad: "Das sollte besser werden", na: "Nicht prüfbar", score: "SEO-Score", sug: "Vorschläge zu Entitäten", add: "Thema ergänzen", links: "Beim ersten Vorkommen verlinken", create: "Fehlende Entitäten (erst suchen, dann anlegen)", self: "Selbst verbessern", ai: "Mit meiner KI verbessern (MCP)", aih: "Kopiere diesen Auftrag in Claude, ChatGPT oder Copilot (mit verbundenem MCP). Deine KI fragt dich vor dem Speichern.", copy: "Kopieren", copied: "Kopiert", ask: "Etwas fehlt – möchtest du es selbst verbessern oder von deiner KI über den MCP erledigen lassen?", err: "Der Check ist gerade nicht erreichbar.", login: "Bitte anmelden.", g: { green: "sehr gut", good: "gut", weak: "ausbaufähig", poor: "schwach" } }
    : { check: "Check SEO", busy: "Checking …", good: "What works", bad: "What should be better", na: "Not checkable", score: "SEO score", sug: "Entity suggestions", add: "Add topic", links: "Link at first mention", create: "Missing entities (search first, then create)", self: "Improve it myself", ai: "Improve with my AI (MCP)", aih: "Copy this task into Claude, ChatGPT or Copilot (with the MCP connected). Your AI asks you before saving.", copy: "Copy", copied: "Copied", ask: "Something is missing – do you want to improve it yourself or let your AI fix it through the MCP?", err: "The check is not reachable right now.", login: "Please sign in.", g: { green: "very good", good: "good", weak: "needs work", poor: "weak" } };
  var COL = { green: "#1a7f37", good: "#7a8a00", weak: "#b36b00", poor: "#c62828" }, MARK = { "true": "✓", warn: "⚠", "false": "✗" };
  function L(o) { return (o && (o[de ? "de" : "en"] || o.en)) || ""; }
  function render(into, r, o) {
    into.textContent = "";
    into.appendChild(h("p", { style: "margin:.2em 0" }, [h("b", { text: T.score + ": " }), h("b", { text: String(r.score), style: "font-size:1.7em;color:" + (COL[r.grade] || "inherit") }), h("span", { class: "mut", text: " / 100 · " + (T.g[r.grade] || "") + " · " + L(r.summary) })]));
    var good = r.checks.filter(function (c) { return c.ok === true; }), bad = r.checks.filter(function (c) { return c.ok === false || c.ok === "warn"; }), na = r.checks.filter(function (c) { return c.ok === null; });
    function sec(title, list, showFix) {
      if (!list.length) return; into.appendChild(h("h4", { text: title, style: "margin:.8em 0 .2em" }));
      var ul = h("ul", { style: "list-style:none;padding:0;margin:0" });
      list.forEach(function (c) { var li = h("li", { style: "margin:.25em 0" }, [h("b", { text: (MARK[String(c.ok)] || "–") + " " + L(c.label) }), h("div", { class: "mut", text: L(c.detail) })]); if (showFix && L(c.fix)) li.appendChild(h("div", { text: "→ " + L(c.fix) })); ul.appendChild(li); });
      into.appendChild(ul);
    }
    sec(T.bad, bad, true); sec(T.good, good, false); sec(T.na, na, false);
    var s = r.suggestions || {};
    if ((s.topics || []).length || (s.links || []).length || (s.create || []).length) {
      into.appendChild(h("h4", { text: T.sug, style: "margin:.8em 0 .2em" }));
      if ((s.topics || []).length) { var row = h("div", { style: "display:flex;gap:.4em;flex-wrap:wrap" }); s.topics.forEach(function (t) { row.appendChild(h("button", { type: "button", class: "btn", title: t.description || "", text: "+ " + t.name, onclick: function (e) { if (o.onAddTopic) { o.onAddTopic(t.id); e.target.disabled = true; e.target.textContent = "✓ " + t.name; } } })); }); into.appendChild(h("p", { class: "mut", text: T.add + ":" })); into.appendChild(row); }
      if ((s.links || []).length) { into.appendChild(h("p", { class: "mut", text: T.links + ":" })); into.appendChild(h("p", {}, s.links.slice(0, 8).map(function (l) { return h("code", { text: l.markup + " ", style: "margin-inline-end:.5em" }); }))); }
      if ((s.create || []).length) into.appendChild(h("p", {}, [h("span", { class: "mut", text: T.create + ": " }), document.createTextNode(s.create.map(function (c) { return c.name; }).join(", "))]));
    }
    if (bad.length || (s.topics || []).length) {
      into.appendChild(h("p", { class: "mut", style: "margin-top:1em", text: T.ask }));
      var pr = (r.ai_prompt && (de ? r.ai_prompt.de : r.ai_prompt.en)) || "", det = h("details", {}, [h("summary", { class: "btn", text: T.ai }), h("p", { class: "mut", text: T.aih }), h("textarea", { readonly: "readonly", rows: 8, style: "width:100%", "aria-label": T.ai })]);
      det.querySelector("textarea").value = pr;
      det.appendChild(h("button", { type: "button", class: "btn", text: T.copy, onclick: function (e) { try { navigator.clipboard.writeText(pr); e.target.textContent = T.copied; } catch (er) { det.querySelector("textarea").select(); } } }));
      into.appendChild(h("p", {}, [h("button", { type: "button", class: "btn", text: T.self, onclick: function () { into.hidden = true; if (o.onSelf) o.onSelf(); } }), " ", det]));
    }
  }
  function box(o) {
    var out = h("div", { class: "seo-box", style: "border:1px solid var(--bd);border-radius:.5em;padding:.6em .9em;margin:.8em 0" }), res = h("div"), btn;
    function run() {
      btn.disabled = true; btn.textContent = T.busy; res.hidden = false;
      var p = o.draft ? api("/api/seo/preview", { method: "POST", body: Object.assign({ kind: o.kind }, o.draft()) }) : api("/api/seo/check?kind=" + encodeURIComponent(o.kind) + "&id=" + encodeURIComponent(o.id));
      p.then(function (r) { btn.disabled = false; btn.textContent = T.check; var j = r.j || {}; if (j.error === "login") res.textContent = T.login; else if (j.score === undefined) res.textContent = T.err; else render(res, j, o); }, function () { btn.disabled = false; btn.textContent = T.check; res.textContent = T.err; });
    }
    btn = h("button", { type: "button", class: "btn", text: T.check, onclick: run });
    out.appendChild(btn); out.appendChild(res); return out;
  }
  var cache = null;
  function scores(cb) { api("/api/seo/mine").then(function (r) { var m = {}; ((r.j && r.j.items) || []).forEach(function (x) { m[x.kind + ":" + x.id] = x; }); cb(m); }, function () { cb({}); }); }
  function badge(x) { return x ? h("span", { class: "mut", style: "margin-inline-start:.4em;font-weight:700;color:" + (COL[x.grade] || "inherit"), text: "SEO " + x.score, title: T.g[x.grade] || "" }) : document.createTextNode(""); }
  U.seo = { box: box, scores: scores, badge: badge };
})();
