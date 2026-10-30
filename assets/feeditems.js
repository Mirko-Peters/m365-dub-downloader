/* Meine gezogenen Inhalte: Videos/Beiträge aus den eigenen Kanälen. Optimieren hier im Editor oder per MCP (save_feed_item_text) */
(function () {
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-feed"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = de ? { h: "Meine Inhalte", intro: "Videos und Beiträge aus deinen Kanälen bekommen automatisch eine eigene Seite hier. Mit eigenem Text (nach Vorlage) werden sie für Google indexierbar. Optimiere sie hier im Editor oder lass es deinen KI-Assistenten per MCP erledigen.", login: "Melde dich an, um deine Inhalte zu sehen.", none: "Noch nichts gezogen. Trage in deinem Profil einen Kanal ein (YouTube, Blog, Podcast …).", has: "Text vorhanden", no: "Noch ohne Text", edit: "Hier optimieren", mcp: "Per MCP optimieren", copy: "Anweisung kopieren", copied: "Kopiert.", page: "Seite ansehen", summary: "Kurzfassung (max. 300 Zeichen)", topics: "Themen", body: "Text (mind. 300 Zeichen, in eigenen Worten)", save: "Speichern", saved: "Gespeichert.", e_too_short: "Der Text braucht mindestens 300 Zeichen.", e_bad_ref: "Quellen nur als {{ref|Titel|https://url|Herausgeber|Datum}}.", e_generic: "Konnte nicht gespeichert werden.", cancel: "Schließen", tpl: "## Worum es geht\n\n(2–3 Sätze, Antwort zuerst)\n\n## Die wichtigsten Punkte\n\n- \n- \n- \n\n## Einordnung\n\n(Produkte mit [[entitaets-id|Name]] verlinken)\n\n## Quellen\n\n", prompt: function (w) { return "Optimiere meinen Inhalt auf m365.fm per MCP: Rufe list_my_feed_items auf, nimm den Eintrag mit der id " + w.id + " („" + w.title + "“), lies die Anleitung (howto feed), schreibe nach der Vorlage einen Text in eigenen Worten (mind. 300 Zeichen) und speichere ihn mit save_feed_item_text (id " + w.id + ", body, summary, topics)."; } }
    : { h: "My content", intro: "Videos and posts from your channels automatically get their own page here. With your own text (following the template) they become indexable by Google. Optimise them here in the editor or let your AI assistant do it via MCP.", login: "Sign in to see your content.", none: "Nothing pulled yet. Add a channel to your profile (YouTube, blog, podcast …).", has: "Has text", no: "No text yet", edit: "Optimise here", mcp: "Optimise via MCP", copy: "Copy instruction", copied: "Copied.", page: "View page", summary: "Summary (max. 300 characters)", topics: "Topics", body: "Text (at least 300 characters, in your own words)", save: "Save", saved: "Saved.", e_too_short: "The text needs at least 300 characters.", e_bad_ref: "Sources only as {{ref|Title|https://url|Publisher|Date}}.", e_generic: "Could not save.", cancel: "Close", tpl: "## What it is about\n\n(2–3 sentences, answer first)\n\n## Key points\n\n- \n- \n- \n\n## Context\n\n(link products with [[entity-id|name]])\n\n## Sources\n\n", prompt: function (w) { return "Optimise my content on m365.fm via MCP: call list_my_feed_items, take the item with id " + w.id + " (\"" + w.title + "\"), read the guide (howto feed), write a text following the template in your own words (min. 300 characters) and save it with save_feed_item_text (id " + w.id + ", body, summary, topics)."; } };
  var box = h("div"), msg = h("p", { role: "status", class: "mut" });
  function slug(t) { return (t || "").toLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60).replace(/-+$/, "") || "inhalt"; }
  function editor(w, li) {
    var su = h("textarea", { rows: 2, maxlength: 300 }), bo = h("textarea", { maxlength: 12000, rows: 18 }), tp = U.topicsUI(w.topics || [], 10), f = h("div", { class: "ed-form" });
    su.value = w.summary || ""; bo.value = w.body || Q.tpl;
    f.appendChild(U.lab(Q.summary, su)); f.appendChild(h("div", {}, [h("b", { text: Q.topics }), tp])); f.appendChild(h("div", {}, [h("label", { text: Q.body }), U.editor ? U.editor(bo, 12000) : bo]));
    if (U.seo) f.appendChild(U.seo.box({ kind: "feed", draft: function () { return { title: w.title, summary: su.value, body: bo.value.trim() === Q.tpl.trim() ? "" : bo.value, topics: tp.get() }; }, onAddTopic: tp.addId }));
    f.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.save, onclick: function () {
      api("/api/feed/text", { method: "POST", body: { id: w.id, body: bo.value.trim() === Q.tpl.trim() ? "" : bo.value, summary: su.value, topics: tp.get() } }).then(function (r) { var j = r.j || {}; if (j.ok) { msg.textContent = Q.saved; load(); } else msg.textContent = Q["e_" + j.error] || Q.e_generic; });
    } }), " ", h("button", { type: "button", class: "btn", text: Q.cancel, onclick: function () { f.remove(); } })]));
    li.appendChild(f);
  }
  var seoMap = {};
  function draw(items) {
    box.textContent = ""; if (!items.length) { box.appendChild(h("p", { class: "mut", text: Q.none })); return; }
    var ul = h("ul", { style: "padding:0;list-style:none" });
    items.forEach(function (w) {
      var li = h("li", { style: "padding:.7em 0;border-bottom:1px solid var(--bd)" });
      li.appendChild(h("b", { text: w.title })); li.appendChild(h("span", { class: "mut", text: " · " + (w.has_text ? Q.has : Q.no) })); if (U.seo && w.has_text) li.appendChild(U.seo.badge(seoMap["feed:" + w.id]));
      if (w.summary) li.appendChild(h("div", { class: "mut", text: w.summary.slice(0, 200) }));
      var acts = h("div", { style: "margin-top:.4em" }, [h("button", { type: "button", class: "btn" + (w.has_text ? "" : " main"), text: Q.edit, onclick: function () { if (!li.querySelector(".ed-form")) { api("/api/feed/mine").then(function () { editor(w, li); }); } } }), " "]);
      var det = h("details", { style: "display:inline-block;vertical-align:top" }, [h("summary", { text: Q.mcp, class: "btn" })]);
      var pr = Q.prompt(w); det.appendChild(h("p", { class: "mut", text: pr })); det.appendChild(h("button", { type: "button", class: "btn", text: Q.copy, onclick: function () { try { navigator.clipboard.writeText(pr); msg.textContent = Q.copied; } catch (e) {} } }));
      acts.appendChild(det); acts.appendChild(document.createTextNode(" ")); acts.appendChild(h("a", { class: "btn", href: X.base + (de ? "/de" : "") + "/community/feed/" + w.id + "-" + slug(w.title) + "/", text: Q.page }));
      li.appendChild(acts); ul.appendChild(li);
    });
    box.appendChild(ul);
  }
  function load() { api("/api/feed/mine").then(function (r) { box.textContent = ""; if (r.j && r.j.items) { if (U.seo) U.seo.scores(function (m) { seoMap = m; draw(r.j.items); }); else draw(r.j.items); } else box.appendChild(h("p", { text: Q.login })); }); }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro })); root.appendChild(msg); root.appendChild(box); load();
})();
