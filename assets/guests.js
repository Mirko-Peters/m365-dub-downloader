/* Gäste-Börse: Speaker finden Hosts (Podcast, YouTube, Events) und umgekehrt – über gemeinsame Themen */
(function () {
  var M365L = window.M365L || function (de, k, a, b) { return de ? a : b; };
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-guests"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = M365L(de, "guests.Q", { h: "Gäste-Börse", intro: "Podcaster, YouTuber und Veranstalter finden Gäste und Speaker – und umgekehrt. Zugeordnet wird über gemeinsame Themen (Entitäten), Sprache und Format. Kontakt läuft über die Nachrichten der Plattform. Dein Profil muss öffentlich sein.", login: "Melde dich an, um einen Eintrag anzulegen.", speaker: "Ich bin als Gast/Speaker verfügbar", host: "Meine Show/mein Kanal/mein Event sucht Gäste", title_h: "Name der Show, des Kanals oder Events", title_s: "Kurzthema (optional)", formats: "Formate", langs: "Sprachen", topics: "Themen", note: "Hinweis (max. 500 Zeichen)", link: "Link zur Show (https, optional)", active: "Aktiv (sichtbar)", save: "Speichern", del_: "Löschen", confirmdel: "Eintrag löschen?", edit: "Bearbeiten", mine: "Meine Einträge", matches: "Passende Treffer", none: "Noch nichts da.", nomatch: "Noch keine Treffer – mehr Themen helfen.", contact: "Nachricht senden", shared: "Gemeinsame Themen", saved: "Gespeichert.", f_podcast: "Podcast", f_youtube: "YouTube", f_event: "Event", f_webinar: "Webinar", f_article: "Artikel/Blog", st_speaker: "Speaker", st_host: "Host", e_need_profile: "Mache zuerst dein Profil öffentlich (Reiter Profil).", e_formats: "Wähle mindestens ein Format.", e_langs: "Wähle mindestens eine Sprache.", e_topics: "Wähle mindestens ein Thema.", e_title: "Der Name braucht mindestens 3 Zeichen.", e_limit: "Du hast die maximale Anzahl Einträge dieser Art erreicht.", e_bad_link: "Der Link muss mit https:// beginnen.", e_generic: "Das hat nicht geklappt.", paused: "pausiert" },
    { h: "Guest exchange", intro: "Podcasters, YouTubers and organizers find guests and speakers – and the other way round. Matching uses shared topics (entities), language and format. Contact goes through the platform messages. Your profile must be public.", login: "Sign in to add a listing.", speaker: "I am available as a guest/speaker", host: "My show/channel/event looks for guests", title_h: "Name of the show, channel or event", title_s: "Short topic (optional)", formats: "Formats", langs: "Languages", topics: "Topics", note: "Note (max. 500 characters)", link: "Link to the show (https, optional)", active: "Active (visible)", save: "Save", del_: "Delete", confirmdel: "Delete this listing?", edit: "Edit", mine: "My listings", matches: "Matches for you", none: "Nothing here yet.", nomatch: "No matches yet – more topics help.", contact: "Send message", shared: "Shared topics", saved: "Saved.", f_podcast: "Podcast", f_youtube: "YouTube", f_event: "Event", f_webinar: "Webinar", f_article: "Article/blog", st_speaker: "Speaker", st_host: "Host", e_need_profile: "Make your profile public first (tab Profile).", e_formats: "Choose at least one format.", e_langs: "Choose at least one language.", e_topics: "Choose at least one topic.", e_title: "The name needs at least 3 characters.", e_limit: "You reached the maximum number of listings of this kind.", e_bad_link: "The link must start with https://.", e_generic: "That did not work.", paused: "paused" });
  var FM = ["podcast", "youtube", "event", "webinar", "article"], LG = [["en", "English"], ["de", "Deutsch"], ["fr", "Français"], ["es", "Español"], ["it", "Italiano"], ["nl", "Nederlands"], ["pt", "Português"], ["pl", "Polski"], ["id", "Bahasa Indonesia"], ["ru", "Русский"], ["uk", "Українська"], ["ar", "العربية"], ["he", "עברית"], ["hi", "हिन्दी"], ["ja", "日本語"], ["ko", "한국어"], ["ml", "മലയാളം"], ["pa", "ਪੰਜਾਬੀ"], ["ta", "தமிழ்"], ["te", "తెలుగు"]];
  var msg = h("p", { role: "status", class: "mut" }), box = h("div"), list = h("div"), NAMES = {};
  function say(t) { msg.textContent = t || ""; }
  function pfx() { return X.lang && X.lang !== "en" ? "/" + X.lang : ""; }
  function checks(opts, sel, labelOf) {
    var wrap = h("div", { style: "display:flex;gap:.8em;flex-wrap:wrap" }), boxes = [];
    opts.forEach(function (o) { var c = h("input", { type: "checkbox", value: o[0] }); c.checked = sel.indexOf(o[0]) > -1; boxes.push(c); wrap.appendChild(h("label", {}, [c, " " + (labelOf ? labelOf(o) : o[1])])); });
    wrap.get = function () { return boxes.filter(function (c) { return c.checked; }).map(function (c) { return c.value; }); }; return wrap;
  }
  function form(kind, p) {
    p = p || {}; var f = h("form"), ti = U.inp(p.title, 120), no = h("textarea", { maxlength: 500, rows: 3 }), li = U.inp(p.link, 300), ac = h("input", { type: "checkbox" });
    no.value = p.note || ""; ac.checked = p.active !== 0 && p.active !== false;
    var fm = checks(FM.map(function (x) { return [x]; }), p.formats || [], function (o) { return Q["f_" + o[0]]; }), lg = checks(LG, p.langs || [X.lang || "en"]), tp = U.topicsUI(p.topics || [], 10);
    f.appendChild(h("h3", { text: kind === "host" ? Q.host : Q.speaker })); f.appendChild(U.lab(kind === "host" ? Q.title_h : Q.title_s, ti));
    f.appendChild(h("div", {}, [h("b", { text: Q.formats }), fm])); f.appendChild(h("div", {}, [h("b", { text: Q.langs }), lg])); f.appendChild(h("div", {}, [h("b", { text: Q.topics }), tp]));
    f.appendChild(U.lab(Q.note, no)); if (kind === "host") f.appendChild(U.lab(Q.link, li)); f.appendChild(h("p", {}, [h("label", {}, [ac, " " + Q.active])]));
    f.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.save, onclick: function () {
      api("/api/guests/save", { method: "POST", body: { id: p.id, kind: kind, title: ti.value, formats: fm.get(), langs: lg.get(), topics: tp.get(), note: no.value, link: li.value, active: ac.checked } }).then(function (r) { var j = r.j || {}; if (j.ok) { box.textContent = ""; say(Q.saved); load(); } else say(Q["e_" + j.error] || Q.e_generic); });
    } }), " ", h("button", { type: "button", class: "btn", text: "×", "aria-label": "Close", onclick: function () { box.textContent = ""; } })]));
    f.addEventListener("submit", function (e) { e.preventDefault(); }); return f;
  }
  function tname(id) { return NAMES[id] || id; }
  function load() {
    api("/api/guests/mine").then(function (r) {
      var d = r.j || {}; list.textContent = ""; if (!d.items) return;
      list.appendChild(h("h3", { text: Q.mine })); if (!d.items.length) list.appendChild(h("p", { class: "mut", text: Q.none }));
      d.items.forEach(function (p) {
        list.appendChild(h("p", {}, [h("b", { text: (p.title || Q["st_" + p.kind]) }), h("span", { class: "mut", text: " · " + Q["st_" + p.kind] + " · " + p.topics.map(tname).join(", ") + (p.active ? "" : " · " + Q.paused) }), " ",
          h("button", { type: "button", class: "btn", text: Q.edit, onclick: function () { box.textContent = ""; box.appendChild(form(p.kind, p)); } }), " ",
          h("button", { type: "button", class: "btn", text: Q.del_, onclick: function () { if (confirm(Q.confirmdel)) api("/api/guests/delete", { method: "POST", body: { id: p.id } }).then(load); } })]));
      });
      list.appendChild(h("h3", { text: Q.matches })); if (!d.matches.length) list.appendChild(h("p", { class: "mut", text: Q.nomatch }));
      d.matches.forEach(function (m) {
        list.appendChild(h("div", { style: "padding:.5em 0;border-bottom:1px solid var(--bd)" }, [h("b", { text: (m.title || m.name) }), h("span", { class: "mut", text: " · " + Q["st_" + m.kind] + " · " + m.name }), m.note ? h("p", { text: m.note }) : null,
          h("p", { class: "mut", text: Q.shared + ": " + m.shared.map(tname).join(", ") }),
          h("a", { class: "btn main", href: X.base + pfx() + "/community/?msg=" + m.handle + "#c-messages", text: Q.contact }), " ", m.link ? h("a", { class: "btn", href: m.link, rel: "nofollow ugc noopener", target: "_blank", text: "↗" }) : null]));
      });
    });
  }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro })); root.appendChild(msg);
  root.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.speaker, onclick: function () { box.textContent = ""; box.appendChild(form("speaker")); } }), " ", h("button", { type: "button", class: "btn main", text: Q.host, onclick: function () { box.textContent = ""; box.appendChild(form("host")); } })]));
  root.appendChild(box); root.appendChild(list);
  fetch("/entities.json").then(function (r) { return r.json(); }).then(function (j) { (j.entities || []).forEach(function (e) { NAMES[e.id] = e.name; }); }).catch(function () {}).then(function () {
    api("/api/me").then(function (r) { if (r.j && r.j.user) load(); else root.appendChild(h("p", { text: Q.login })); }).catch(function () { root.appendChild(h("p", { text: Q.login })); });
  });
})();
