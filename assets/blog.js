/* Blog: eigene Beiträge schreiben, speichern, einreichen */
(function () {
  var M365L = window.M365L || function (de, k, a, b) { return de ? a : b; };
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-blog"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = M365L(de, "blog.Q", { h: "Blog", intro: "Schreibe Blogbeiträge für die Community. Jeder kann bloggen, Beiträge sind sofort sichtbar. Bei Google erscheint ein Beitrag erst ab 10 Upvotes. Quellen fügst du als {{ref|Titel|https://url|Herausgeber|Datum}} ein – andere Links werden entfernt. Dein Profil muss öffentlich sein.", login: "Melde dich an, um Blogbeiträge zu schreiben.", newp: "Neuer Beitrag", title: "Titel", summary: "Kurzfassung (in Listen, max. 300 Zeichen)", lang: "Sprache", topics: "Themen", body: "Text", hint: "Auszeichnung: ## Überschrift, ### Zwischenüberschrift, **fett**, *kursiv*, - Liste, 1. Liste, > Zitat, [[entitaets-id|Text]] Link auf ein Thema, {{ref|Titel|https://url|Herausgeber|Datum}} Quelle.", draft: "Entwurf speichern", submit: "Veröffentlichen", del_: "Löschen", edit: "Bearbeiten", confirmdel: "Diesen Beitrag löschen?", saved: "Gespeichert.", st_draft: "Entwurf", st_pending: "In Prüfung", st_live: "Veröffentlicht", st_rejected: "Abgelehnt", votes: "Upvotes", e_title: "Der Titel braucht mindestens 5 Zeichen.", e_too_short: "Zum Veröffentlichen braucht der Text mindestens 300 Zeichen.", e_need_profile: "Mache zuerst dein Profil öffentlich (Reiter Profil).", e_bad_ref: "Eine Quelle braucht einen Titel und einen https://-Link (keine Kurzlinks, max. 25).", e_rate_limit: "Heute zu viele Beiträge – bitte später erneut versuchen.", e_generic: "Konnte nicht gespeichert werden.", viewp: "Ansehen", pubnow: "Veröffentlicht.", review: "Zur Prüfung eingereicht – du siehst es hier, sobald es freigegeben ist.", note: "Hinweis der Redaktion", none: "Noch keine Beiträge.", cancel: "Abbrechen", mod: "Beiträge zur Prüfung", approve: "Freigeben", reject: "Ablehnen", reason: "Grund für die Ablehnung (sichtbar für den Autor)", nomod: "Keine Beiträge in Prüfung.", updNow: "Update-Check jetzt", updDone: "Update-Check erledigt, neue Meldungen:", demoOn: "Testinhalte anlegen", demoOff: "Testinhalte entfernen", demoDone: "Erledigt. Sichtbar nach dem nächsten Seitenbau (stündlich).", demoErr: "Fehler (öffentliches Profil mit Handle nötig)." },
    { h: "Blog", intro: "Write blog posts for the community. Anyone can blog and posts are visible immediately. A post appears on Google only after 10 upvotes. Sources go in as {{ref|Title|https://url|Publisher|Date}} – other links are removed. Your profile must be public.", login: "Sign in to write blog posts.", newp: "New post", title: "Title", summary: "Short summary (shown in lists, max. 300 characters)", lang: "Language", topics: "Topics", body: "Text", hint: "Markup: ## heading, ### subheading, **bold**, *italic*, - list, 1. list, > quote, [[entity-id|text]] link to a topic, {{ref|Title|https://url|Publisher|Date}} source.", draft: "Save draft", submit: "Publish", del_: "Delete", edit: "Edit", confirmdel: "Delete this post?", saved: "Saved.", st_draft: "Draft", st_pending: "In review", st_live: "Published", st_rejected: "Rejected", votes: "upvotes", e_title: "The title needs at least 5 characters.", e_too_short: "The text needs at least 300 characters to be published.", e_need_profile: "Make your profile public first (tab Profile).", e_bad_ref: "A source needs a title and an https:// link (no link shorteners, max. 25).", e_rate_limit: "Too many posts today – please try again later.", e_generic: "Could not save.", viewp: "View", pubnow: "Published.", review: "Sent for review – you will see it here once approved.", note: "Note from the editors", none: "No posts yet.", cancel: "Cancel", mod: "Posts awaiting review", approve: "Approve", reject: "Reject", reason: "Reason for rejection (visible to the author)", nomod: "No posts in review.", updNow: "Check updates now", updDone: "Update check done, new items:", demoOn: "Create test content", demoOff: "Remove test content", demoDone: "Done. Visible after the next site build (hourly).", demoErr: "Error (a public profile with a handle is required)." });
  var LANGS = [["en", "English"], ["de", "Deutsch"], ["fr", "Français"], ["es", "Español"], ["it", "Italiano"], ["nl", "Nederlands"], ["pt", "Português"], ["pl", "Polski"], ["id", "Bahasa Indonesia"], ["ru", "Русский"], ["uk", "Українська"], ["ar", "العربية"], ["he", "עברית"], ["hi", "हिन्दी"], ["ja", "日本語"], ["ko", "한국어"], ["ml", "മലയാളം"], ["pa", "ਪੰਜਾਬੀ"], ["ta", "தமிழ்"], ["te", "తెలుగు"]];
  var box = h("div", { class: "bl-box" }), msg = h("p", { role: "status", class: "mut" });
  function say(t) { msg.textContent = t || ""; }
  function pfx() { return X.lang && X.lang !== "en" ? "/" + X.lang : ""; }
Object.assign(Q, de ? { e_bad_image: "Ein Bild braucht eine https-Adresse auf .jpg, .png, .webp, .gif oder .avif (keine Kurzlinks).", e_bad_alt: "Jedes Bild braucht einen Alt-Text mit mindestens 5 Zeichen.", e_too_many_images: "Maximal 6 Bilder pro Text." } : { e_bad_image: "An image needs an https address ending in .jpg, .png, .webp, .gif or .avif (no short links).", e_bad_alt: "Every image needs alt text of at least 5 characters.", e_too_many_images: "At most 6 images per text." });
  var CO = de ? { lab: "Co-Autoren (Profil-Adressen, kommagetrennt, max. 3)", hint: "Wie Gäste bei Podcast und Video: Eingeladene bestätigen selbst, erst dann erscheinen sie als Autoren auf der Seite und die Themen zählen für ihre Expertise.", st_invited: "eingeladen", st_confirmed: "bestätigt", st_declined: "abgelehnt", inv: "Einladungen als Co-Autor", invtxt: "{a} lädt dich als Co-Autor ein:", yes: "Annehmen", no: "Ablehnen", done: "Erledigt.", e_bad_coauthor: "Co-Autor nicht gefunden (öffentliches Profil nötig, nicht du selbst): ", e_need_profile: "Mache zuerst dein Profil öffentlich." }
    : { lab: "Co-authors (profile handles, comma separated, max. 3)", hint: "Like guests on a podcast or video: invited members confirm themselves; only then do they appear as authors on the page and the topics count towards their expertise.", st_invited: "invited", st_confirmed: "confirmed", st_declined: "declined", inv: "Invitations to co-author", invtxt: "{a} invites you as co-author:", yes: "Accept", no: "Decline", done: "Done.", e_bad_coauthor: "Co-author not found (public profile required, not yourself): ", e_need_profile: "Make your profile public first." };
  function csv(s) { return String(s || "").split(",").map(function (x) { return x.trim().toLowerCase(); }).filter(Boolean); }
  function form(p, state) {
    p = p || {}; var f = h("form", { class: "ed-form" });
    var ti = U.inp(p.title, 140), su = h("textarea", { maxlength: 300, rows: 2 }), bo = h("textarea", { maxlength: 12000, rows: 22 }), lg = U.sel(LANGS, p.lang || (X.lang || "en")), tp = U.topicsUI(p.topics || [], 10);
    su.value = p.summary || ""; bo.value = p.body || "";
    f.appendChild(U.lab(Q.title, ti)); f.appendChild(U.lab(Q.summary, su)); f.appendChild(U.lab(Q.lang, lg));
    var co = U.inp((p.coauthors || []).map(function (c) { return c.handle; }).join(", "), 120);
    f.appendChild(U.lab(CO.lab, co)); f.appendChild(h("p", { class: "mut", text: CO.hint + ((p.coauthors || []).length ? " " + p.coauthors.map(function (c) { return c.name + ": " + (CO["st_" + c.status] || c.status); }).join(" · ") : "") }));
    f.appendChild(h("div", {}, [h("b", { text: Q.topics }), tp])); f.appendChild(h("div", {}, [h("label", { text: Q.body }), U.editor ? U.editor(bo, 12000) : bo])); f.appendChild(h("p", { class: "mut", text: Q.hint }));
    if (U.seo) f.appendChild(U.seo.box({ kind: "blog", draft: function () { return { title: ti.value, summary: su.value, body: bo.value, lang: lg.value, topics: tp.get() }; }, onAddTopic: tp.addId }));
    function save(submit) {
      say(""); api("/api/blog/save", { method: "POST", body: { id: p.id, title: ti.value, summary: su.value, body: bo.value, lang: lg.value, topics: tp.get(), coauthors: csv(co.value), submit: submit } }).then(function (r) {
        var j = r.j || {}; if (j.error === "bad_coauthor") { say(CO.e_bad_coauthor + (j.handle || "")); return; } if (j.ok) { say(submit ? (j.status === "live" ? Q.pubnow : Q.review) : Q.saved); load(); } else say(Q["e_" + j.error] || Q.e_generic);
      });
    }
    var row = h("p", {}, [h("button", { type: "button", class: "btn", text: Q.draft, onclick: function () { save(false); } }), " ", h("button", { type: "button", class: "btn main", text: Q.submit, onclick: function () { save(true); } }), " ", h("button", { type: "button", class: "btn", text: Q.cancel, onclick: function () { load(); } })]);
    f.appendChild(row); f.addEventListener("submit", function (e) { e.preventDefault(); }); return f;
  }
  var seoMap = {};
  function list(d) {
    box.textContent = ""; box.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.newp, onclick: function () { box.textContent = ""; box.appendChild(form(null)); } })]));
    if ((d.invites || []).length) {
      box.appendChild(h("h3", { text: CO.inv }));
      d.invites.forEach(function (iv) {
        function reply(ok) { api("/api/blog/coauthor", { method: "POST", body: { id: iv.post_id, accept: ok } }).then(function (r) { var j = r.j || {}; say(j.ok ? CO.done : (CO["e_" + j.error] || Q.e_generic)); load(); }); }
        box.appendChild(h("p", {}, [CO.invtxt.replace("{a}", iv.author) + " ", h("b", { text: iv.title }), " ", h("button", { type: "button", class: "btn main", text: CO.yes, onclick: function () { reply(true); } }), " ", h("button", { type: "button", class: "btn", text: CO.no, onclick: function () { reply(false); } })]));
      });
    }
    if (!d.items.length) box.appendChild(h("p", { class: "mut", text: Q.none }));
    var ul = h("ul", { style: "padding:0;list-style:none" });
    d.items.forEach(function (p) {
      var li = h("li", { style: "padding:.6em 0;border-bottom:1px solid var(--bd)" });
      li.appendChild(h("b", { text: p.title })); li.appendChild(h("span", { class: "mut", text: " · " + (Q["st_" + p.status] || p.status) + (p.status === "live" ? " · " + p.votes + " " + Q.votes : "") })); if (U.seo) li.appendChild(U.seo.badge(seoMap["blog:" + p.id]));
      if (p.note) li.appendChild(h("div", { class: "mut", text: Q.note + ": " + p.note }));
      var acts = h("div", {}, [h("button", { type: "button", class: "btn", text: Q.edit, onclick: function () { box.textContent = ""; box.appendChild(form(p)); } }), " "]);
      if (p.status === "live" && d.handle) acts.appendChild(h("a", { class: "btn", href: X.base + pfx() + "/community/u/" + d.handle + "/blog/" + p.slug + "/", text: Q.viewp }));
      acts.appendChild(document.createTextNode(" ")); acts.appendChild(h("button", { type: "button", class: "btn", text: Q.del_, onclick: function () { if (confirm(Q.confirmdel)) api("/api/blog/delete", { method: "POST", body: { id: p.id } }).then(load); } }));
      li.appendChild(acts); ul.appendChild(li);
    });
    box.appendChild(ul);
  }
  function load() { api("/api/blog/mine").then(function (r) { if (r.j && r.j.items) { if (U.seo) U.seo.scores(function (m) { seoMap = m; list(r.j); }); else list(r.j); } }); }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro })); root.appendChild(msg); root.appendChild(box);
  function demo() {
    var d = h("p", {}); root.appendChild(d);
    function go(on) { api("/api/admin/demo", { method: "POST", body: { on: on } }).then(function (r) { say(r.j && r.j.ok ? Q.demoDone : Q.demoErr); }); }
    d.appendChild(h("button", { type: "button", class: "btn", text: Q.demoOn, onclick: function () { go(true); } })); d.appendChild(document.createTextNode(" "));
    d.appendChild(h("button", { type: "button", class: "btn", text: Q.updNow, onclick: function () { api("/api/admin/updates/poll", { method: "POST", body: {} }).then(function (r) { say(r.j && r.j.ok ? Q.updDone + " " + r.j.added : Q.demoErr); }); } })); d.appendChild(document.createTextNode(" "));
    d.appendChild(h("button", { type: "button", class: "btn", text: Q.demoOff, onclick: function () { go(false); } }));
  }
  function moderation() {
    var mb = h("div", { class: "bl-mod" }); root.appendChild(mb);
    function draw() {
      api("/api/admin/blog").then(function (r) {
        mb.textContent = ""; mb.appendChild(h("h3", { text: Q.mod })); var it = (r.j && r.j.items) || [];
        if (!it.length) mb.appendChild(h("p", { class: "mut", text: Q.nomod }));
        it.forEach(function (p) {
          var rs = h("input", { type: "text", maxlength: 300, placeholder: Q.reason, "aria-label": Q.reason }), body = h("div", { style: "white-space:pre-wrap;max-height:16em;overflow:auto;border:1px solid var(--bd);padding:.5em;border-radius:.4em", text: p.body });
          mb.appendChild(h("div", { style: "padding:.6em 0;border-bottom:1px solid var(--bd)" }, [h("b", { text: p.title }), h("span", { class: "mut", text: " · " + p.name + " · " + p.lang }), h("p", { text: p.summary }), body, rs,
            h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.approve, onclick: function () { api("/api/admin/blog/decide", { method: "POST", body: { id: p.id, ok: true } }).then(draw); } }), " ",
              h("button", { type: "button", class: "btn", text: Q.reject, onclick: function () { api("/api/admin/blog/decide", { method: "POST", body: { id: p.id, ok: false, note: rs.value } }).then(draw); } })])]));
        });
      });
    }
    draw();
  }
  api("/api/me").then(function (r) { if (r.j && r.j.user && (r.j.user.admin || r.j.user.editor)) { moderation(); if (r.j.user.admin) demo(); } return r; }).then(function (r) { if (r.j && r.j.user) load(); else box.appendChild(h("p", { text: Q.login })); }).catch(function () { box.appendChild(h("p", { text: Q.login })); });
})();
