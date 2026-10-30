/* Blog: eigene Beiträge schreiben, speichern, einreichen */
(function () {
  var M365L = window.M365L || function (de, k, a, b) { return de ? a : b; };
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-blog"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = M365L(de, "blog.Q", { h: "Blog", intro: "Schreibe Blogbeiträge für die Community. Beiträge neuer Mitglieder werden zuerst geprüft, vertrauenswürdige Mitglieder veröffentlichen sofort. Quellen fügst du als {{ref|Titel|https://url|Herausgeber|Datum}} ein – andere Links werden entfernt. Dein Profil muss öffentlich sein.", login: "Melde dich an, um Blogbeiträge zu schreiben.", newp: "Neuer Beitrag", title: "Titel", summary: "Kurzfassung (in Listen, max. 300 Zeichen)", lang: "Sprache", topics: "Themen", body: "Text", hint: "Auszeichnung: ## Überschrift, ### Zwischenüberschrift, **fett**, *kursiv*, - Liste, 1. Liste, > Zitat, [[entitaets-id|Text]] Link auf ein Thema, {{ref|Titel|https://url|Herausgeber|Datum}} Quelle.", draft: "Entwurf speichern", submit: "Veröffentlichen / zur Prüfung einreichen", del_: "Löschen", edit: "Bearbeiten", confirmdel: "Diesen Beitrag löschen?", saved: "Gespeichert.", st_draft: "Entwurf", st_pending: "In Prüfung", st_live: "Veröffentlicht", st_rejected: "Abgelehnt", votes: "Upvotes", e_title: "Der Titel braucht mindestens 5 Zeichen.", e_too_short: "Zum Veröffentlichen braucht der Text mindestens 300 Zeichen.", e_need_profile: "Mache zuerst dein Profil öffentlich (Reiter Profil).", e_bad_ref: "Eine Quelle braucht einen Titel und einen https://-Link (keine Kurzlinks, max. 25).", e_rate_limit: "Heute zu viele Beiträge – bitte später erneut versuchen.", e_generic: "Konnte nicht gespeichert werden.", viewp: "Ansehen", pubnow: "Veröffentlicht.", review: "Zur Prüfung eingereicht – du siehst es hier, sobald es freigegeben ist.", note: "Hinweis der Redaktion", none: "Noch keine Beiträge.", cancel: "Abbrechen" },
    { h: "Blog", intro: "Write blog posts for the community. New members' posts are reviewed first; trusted members publish immediately. Sources go in as {{ref|Title|https://url|Publisher|Date}} – other links are removed. Your profile must be public.", login: "Sign in to write blog posts.", newp: "New post", title: "Title", summary: "Short summary (shown in lists, max. 300 characters)", lang: "Language", topics: "Topics", body: "Text", hint: "Markup: ## heading, ### subheading, **bold**, *italic*, - list, 1. list, > quote, [[entity-id|text]] link to a topic, {{ref|Title|https://url|Publisher|Date}} source.", draft: "Save draft", submit: "Publish / submit for review", del_: "Delete", edit: "Edit", confirmdel: "Delete this post?", saved: "Saved.", st_draft: "Draft", st_pending: "In review", st_live: "Published", st_rejected: "Rejected", votes: "upvotes", e_title: "The title needs at least 5 characters.", e_too_short: "The text needs at least 300 characters to be published.", e_need_profile: "Make your profile public first (tab Profile).", e_bad_ref: "A source needs a title and an https:// link (no link shorteners, max. 25).", e_rate_limit: "Too many posts today – please try again later.", e_generic: "Could not save.", viewp: "View", pubnow: "Published.", review: "Sent for review – you will see it here once approved.", note: "Note from the editors", none: "No posts yet.", cancel: "Cancel" });
  var LANGS = [["en", "English"], ["de", "Deutsch"], ["fr", "Français"], ["es", "Español"], ["it", "Italiano"], ["nl", "Nederlands"], ["pt", "Português"], ["pl", "Polski"], ["id", "Bahasa Indonesia"], ["ru", "Русский"], ["uk", "Українська"], ["ar", "العربية"], ["he", "עברית"], ["hi", "हिन्दी"], ["ja", "日本語"], ["ko", "한국어"], ["ml", "മലയാളം"], ["pa", "ਪੰਜਾਬੀ"], ["ta", "தமிழ்"], ["te", "తెలుగు"]];
  var box = h("div", { class: "bl-box" }), msg = h("p", { role: "status", class: "mut" });
  function say(t) { msg.textContent = t || ""; }
  function pfx() { return X.lang && X.lang !== "en" ? "/" + X.lang : ""; }
  function form(p, state) {
    p = p || {}; var f = h("form", { class: "bl-form" });
    var ti = U.inp(p.title, 140), su = h("textarea", { maxlength: 300, rows: 2 }), bo = h("textarea", { maxlength: 12000, rows: 16 }), lg = U.sel(LANGS, p.lang || (X.lang || "en")), tp = U.topicsUI(p.topics || []);
    su.value = p.summary || ""; bo.value = p.body || "";
    f.appendChild(U.lab(Q.title, ti)); f.appendChild(U.lab(Q.summary, su)); f.appendChild(U.lab(Q.lang, lg));
    f.appendChild(h("div", {}, [h("b", { text: Q.topics }), tp])); f.appendChild(U.lab(Q.body, bo)); f.appendChild(h("p", { class: "mut", text: Q.hint }));
    function save(submit) {
      say(""); api("/api/blog/save", { method: "POST", body: { id: p.id, title: ti.value, summary: su.value, body: bo.value, lang: lg.value, topics: tp.get(), submit: submit } }).then(function (r) {
        var j = r.j || {}; if (j.ok) { say(submit ? (j.status === "live" ? Q.pubnow : Q.review) : Q.saved); load(); } else say(Q["e_" + j.error] || Q.e_generic);
      });
    }
    var row = h("p", {}, [h("button", { type: "button", class: "btn", text: Q.draft, onclick: function () { save(false); } }), " ", h("button", { type: "button", class: "btn main", text: Q.submit, onclick: function () { save(true); } }), " ", h("button", { type: "button", class: "btn", text: Q.cancel, onclick: function () { load(); } })]);
    f.appendChild(row); f.addEventListener("submit", function (e) { e.preventDefault(); }); return f;
  }
  function list(d) {
    box.textContent = ""; box.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.newp, onclick: function () { box.textContent = ""; box.appendChild(form(null)); } })]));
    if (!d.items.length) box.appendChild(h("p", { class: "mut", text: Q.none }));
    var ul = h("ul", { style: "padding:0;list-style:none" });
    d.items.forEach(function (p) {
      var li = h("li", { style: "padding:.6em 0;border-bottom:1px solid var(--bd)" });
      li.appendChild(h("b", { text: p.title })); li.appendChild(h("span", { class: "mut", text: " · " + (Q["st_" + p.status] || p.status) + (p.status === "live" ? " · " + p.votes + " " + Q.votes : "") }));
      if (p.note) li.appendChild(h("div", { class: "mut", text: Q.note + ": " + p.note }));
      var acts = h("div", {}, [h("button", { type: "button", class: "btn", text: Q.edit, onclick: function () { box.textContent = ""; box.appendChild(form(p)); } }), " "]);
      if (p.status === "live" && d.handle) acts.appendChild(h("a", { class: "btn", href: X.base + pfx() + "/community/u/" + d.handle + "/blog/" + p.slug + "/", text: Q.viewp }));
      acts.appendChild(document.createTextNode(" ")); acts.appendChild(h("button", { type: "button", class: "btn", text: Q.del_, onclick: function () { if (confirm(Q.confirmdel)) api("/api/blog/delete", { method: "POST", body: { id: p.id } }).then(load); } }));
      li.appendChild(acts); ul.appendChild(li);
    });
    box.appendChild(ul);
  }
  function load() { api("/api/blog/mine").then(function (r) { if (r.j && r.j.items) list(r.j); }); }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro })); root.appendChild(msg); root.appendChild(box);
  api("/api/me").then(function (r) { if (r.j && r.j.user) load(); else box.appendChild(h("p", { text: Q.login })); }).catch(function () { box.appendChild(h("p", { text: Q.login })); });
})();
