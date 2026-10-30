/* Copilot-Bibliothek: Prompts, Anweisungen, KQL, DAX, Flows ... teilen */
(function () {
  var M365L = window.M365L || function (de, k, a, b) { return de ? a : b; };
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-library"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = M365L(de, "library.Q",
    { h: "Bibliothek", intro: "Teile Prompts, Agenten-Anweisungen, KQL, DAX, PowerShell, Flows und mehr. Einträge sind sofort sichtbar, bei Google erscheinen sie ab 10 Upvotes.", newp: "Neuer Eintrag", title: "Titel", summary: "Kurzbeschreibung", kind: "Art", lang: "Sprache", topics: "Themen (bis zu 10)", body: "Inhalt (Text oder Code)", save: "Speichern", edit: "Bearbeiten", del_: "Löschen", confirmdel: "Eintrag löschen?", none: "Noch keine Einträge.", saved: "Gespeichert.", viewp: "Ansehen", votes: "Upvotes", ver: "Version",
      e_title: "Titel zu kurz.", e_too_short: "Inhalt zu kurz.", e_need_profile: "Dafür brauchst du ein öffentliches Profil mit Handle.", e_bad_topic: "Unbekanntes Thema.", e_rate_limit: "Zu viele Einträge, bitte später wieder.", e_generic: "Das hat nicht geklappt.", login: "Bitte melde dich an.",
      k_prompt: "Prompt", k_instructions: "Custom Instructions", k_agent: "Agenten-Anweisung", k_skill: "Skill", k_plugin: "Plugin", k_manifest: "Agent-Manifest", k_copilotstudio: "Copilot-Studio-Thema", k_flow: "Power-Automate-Flow", k_powerapp: "Power-Apps-Vorlage", k_kql: "KQL", k_dax: "DAX", k_excel: "Excel-Formel", k_graph: "Graph-Abfrage", k_powershell: "PowerShell", k_adaptivecard: "Adaptive Card", k_other: "Sonstiges" },
    { h: "Library", intro: "Share prompts, agent instructions, KQL, DAX, PowerShell, flows and more. Entries are visible at once and appear on Google from 10 upvotes.", newp: "New entry", title: "Title", summary: "Short description", kind: "Type", lang: "Language", topics: "Topics (up to 10)", body: "Content (text or code)", save: "Save", edit: "Edit", del_: "Delete", confirmdel: "Delete this entry?", none: "No entries yet.", saved: "Saved.", viewp: "View", votes: "upvotes", ver: "Version",
      e_title: "Title too short.", e_too_short: "Content too short.", e_need_profile: "You need a public profile with a handle.", e_bad_topic: "Unknown topic.", e_rate_limit: "Too many entries, please try later.", e_generic: "That did not work.", login: "Please sign in.",
      k_prompt: "Prompt", k_instructions: "Custom instructions", k_agent: "Agent instructions", k_skill: "Skill", k_plugin: "Plugin", k_manifest: "Agent manifest", k_copilotstudio: "Copilot Studio topic", k_flow: "Power Automate flow", k_powerapp: "Power Apps template", k_kql: "KQL", k_dax: "DAX", k_excel: "Excel formula", k_graph: "Graph query", k_powershell: "PowerShell", k_adaptivecard: "Adaptive Card", k_other: "Other" });
  var KINDS = ["prompt", "instructions", "agent", "skill", "plugin", "manifest", "copilotstudio", "flow", "powerapp", "kql", "dax", "excel", "graph", "powershell", "adaptivecard", "other"];
  var LANGS = [["en", "English"], ["de", "Deutsch"], ["fr", "Français"], ["es", "Español"], ["it", "Italiano"], ["nl", "Nederlands"], ["pt", "Português"], ["pl", "Polski"]];
  var box = h("div", { class: "bl-box" }), msg = h("p", { role: "status", class: "mut" });
  function say(t) { msg.textContent = t || ""; }
  function pfx() { return X.lang && X.lang !== "en" ? "/" + X.lang : ""; }
  function form(p) {
    p = p || {}; var f = h("form", { class: "ed-form" });
    var ti = U.inp(p.title, 140), su = h("textarea", { maxlength: 300, rows: 2 }), bo = h("textarea", { maxlength: 20000, rows: 22 }), lg = U.sel(LANGS, p.lang || (X.lang || "en")), tp = U.topicsUI(p.topics || [], 10);
    var kd = U.sel(KINDS.map(function (k) { return [k, Q["k_" + k]]; }), p.kind || "prompt");
    su.value = p.summary || ""; bo.value = p.body || "";
    var lk = U.inp(p.link || "", 300), lkw = U.lab(de ? "Link (https) – bei Plugins Pflicht: Repository, Store oder Doku" : "Link (https) – required for plugins: repository, store or docs", lk);
    lk.placeholder = "https://"; function syncLk() { lk.required = kd.value === "plugin"; lkw.firstChild.textContent = (de ? "Link (https)" : "Link (https)") + (kd.value === "plugin" ? (de ? " – Pflicht bei Plugins" : " – required for plugins") : (de ? " – optional" : " – optional")); }
    kd.addEventListener("change", syncLk); syncLk();
    f.appendChild(U.lab(Q.title, ti)); f.appendChild(U.lab(Q.kind, kd)); f.appendChild(lkw); f.appendChild(U.lab(Q.summary, su)); f.appendChild(U.lab(Q.lang, lg));
    f.appendChild(h("div", {}, [h("b", { text: Q.topics }), tp])); f.appendChild(h("div", {}, [h("label", { text: Q.body }), U.editor ? U.editor(bo, 20000) : bo]));
    f.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.save, onclick: function () {
      say(""); api("/api/library/save", { method: "POST", body: { id: p.id, title: ti.value, summary: su.value, body: bo.value, link: lk.value, kind: kd.value, lang: lg.value, topics: tp.get() } }).then(function (r) {
        var j = r.j || {}; if (j.ok) { say(Q.saved); load(); } else say(j.error === "need_link" ? (de ? "Bei Plugins ist ein https-Link Pflicht." : "Plugins need an https link.") : j.error === "bad_link" ? (de ? "Der Link muss mit https:// beginnen (keine Kurzlinks)." : "The link must start with https:// (no shorteners).") : (Q["e_" + j.error] || Q.e_generic));
      });
    } })]));
    f.addEventListener("submit", function (e) { e.preventDefault(); }); return f;
  }
  function list(d) {
    box.textContent = ""; box.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.newp, onclick: function () { box.textContent = ""; box.appendChild(form(null)); } })]));
    if (!d.items.length) box.appendChild(h("p", { class: "mut", text: Q.none }));
    var ul = h("ul", { style: "padding:0;list-style:none" });
    d.items.forEach(function (p) {
      var li = h("li", { style: "padding:.6em 0;border-bottom:1px solid var(--bd)" });
      li.appendChild(h("b", { text: p.title })); li.appendChild(h("span", { class: "mut", text: " · " + (Q["k_" + p.kind] || p.kind) + " · " + Q.ver + " " + p.version + " · " + p.votes + " " + Q.votes }));
      var acts = h("div", {}, [h("button", { type: "button", class: "btn", text: Q.edit, onclick: function () { box.textContent = ""; box.appendChild(form(p)); } }), " "]);
      if (d.handle) acts.appendChild(h("a", { class: "btn", href: X.base + pfx() + "/community/library/" + d.handle + "-" + p.slug + "/", text: Q.viewp }));
      acts.appendChild(document.createTextNode(" ")); acts.appendChild(h("button", { type: "button", class: "btn", text: Q.del_, onclick: function () { if (confirm(Q.confirmdel)) api("/api/library/delete", { method: "POST", body: { id: p.id } }).then(load); } }));
      li.appendChild(acts); ul.appendChild(li);
    });
    box.appendChild(ul);
  }
  function load() { api("/api/library/mine").then(function (r) { if (r.j && r.j.items) list(r.j); else box.appendChild(h("p", { text: Q.login })); }); }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro })); root.appendChild(msg); root.appendChild(box);
  load();
})();
