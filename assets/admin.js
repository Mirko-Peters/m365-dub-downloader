/* Verwaltung ohne Code (/admin/): Uebersicht, Entitaeten bearbeiten, Datenbank, Schalter. Nur fuer Admins; alles laeuft ueber die bestehende Community-API.
   window.M365ADM = {api, base} */
(function () {
  var C = window.M365ADM || {}, API = C.api, BASE = C.base || "", root = document.getElementById("adm"); if (!root || !API) return;
  function h(t, a, kids) { var e = document.createElement(t); a = a || {}; for (var k in a) { if (k === "text") e.textContent = a[k]; else if (k === "class") e.className = a[k]; else if (k.slice(0, 2) === "on") e[k] = a[k]; else e.setAttribute(k, a[k]); } (kids || []).forEach(function (x) { if (x != null) e.appendChild(typeof x === "string" ? document.createTextNode(x) : x); }); return e; }
  function api(p, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(API + p, o).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; }); }); }
  var TYPES = { product: "Produkt", platform: "Plattform", concept: "Konzept", org: "Firma", person: "Person", cert: "Zertifikat", event: "Event", media: "Medium", category: "Kategorie" };
  var ERR = { bad_name: "Name zu kurz", bad_type: "Typ fehlt", too_short: "Kurzbeschreibung fehlt (mindestens 20 Zeichen in Englisch oder Deutsch)", too_long: "Kurzbeschreibung zu lang (höchstens 300 Zeichen)", bad_url: "Eine Adresse ist ungültig (nur https, Docs nur microsoft.com, azure.com oder github.com)", bad_qid: "Wikidata-ID muss wie Q12345 aussehen", bad_relation: "Eine Beziehung zeigt auf eine unbekannte Entität", unchanged: "Nichts geändert", rate_limit: "Zu viele Änderungen in kurzer Zeit, bitte später", login: "Bitte anmelden", forbidden: "Nur für Admins" };
  var tabs = [["ov", "Übersicht"], ["fr", "Freigaben"], ["tr", "Übersetzungen"], ["ent", "Entitäten"], ["db", "Datenbank"], ["sw", "Schalter"]], panes = {}, bar = h("div", { class: "adm-tabs", role: "tablist" });
  var LANGN = { de: "Deutsch", fr: "Französisch", es: "Spanisch", it: "Italienisch", nl: "Niederländisch", pt: "Portugiesisch", pl: "Polnisch", id: "Indonesisch", ru: "Russisch", uk: "Ukrainisch", ar: "Arabisch", he: "Hebräisch", ja: "Japanisch", ko: "Koreanisch", en: "Englisch" };
  var KINDN = { lblog: "Blog (früher)", blog: "Blog (Community)", podcast: "Podcast", video: "Video", notes: "Show Notes", entity: "Entität" };
  function ago(t) { if (!t) return "–"; var d = Math.round(Date.now() / 1000 - t); return d < 90 ? d + " s" : d < 5400 ? Math.round(d / 60) + " min" : d < 172800 ? Math.round(d / 3600) + " h" : Math.round(d / 86400) + " d"; }
  function show(k) { tabs.forEach(function (t) { panes[t[0]].hidden = t[0] !== k; bar.querySelector("[data-k=" + t[0] + "]").setAttribute("aria-selected", t[0] === k ? "true" : "false"); }); try { location.hash = k; } catch (e) {} if (LOAD[k]) LOAD[k](); }
  tabs.forEach(function (t) { bar.appendChild(h("button", { type: "button", role: "tab", "data-k": t[0], text: t[1], onclick: function () { show(t[0]); } })); panes[t[0]] = h("section", { class: "adm-pane", hidden: "" }); });
  function tile(label, v, hint) { return h("div", { class: "adm-tile" + (v ? " on" : "") }, [h("b", { text: v == null ? "–" : String(v) }), h("span", { text: label }), hint ? h("small", { text: hint }) : null]); }
  function msg(el, t, bad) { el.textContent = t; el.className = "adm-msg" + (bad ? " bad" : ""); }

  var OV = null;
  function overview(cb) { api("/api/admin/panel/overview").then(function (r) { if (r.s !== 200) { root.textContent = ""; root.appendChild(h("p", { class: "adm-msg bad", text: ERR[(r.j || {}).error] || "Kein Zugriff. Bitte als Admin anmelden." })); root.appendChild(h("p", {}, [h("a", { href: BASE + "/community/", text: "Zur Anmeldung in der Community" })])); return; } OV = r.j; cb && cb(OV); }); }
  var LOAD = {
    ov: function () { overview(function (o) { var p = panes.ov, q = o.queues; p.textContent = "";
      p.appendChild(h("h2", { text: "Wartet auf dich" }));
      p.appendChild(h("div", { class: "adm-grid" }, [tile("Blog-Beiträge", q.blog), tile("Podcast-Folgen", q.podcast), tile("Videos", q.video), tile("Wiki-Änderungen", q.wiki), tile("Entitäten-Vorschläge", q.entity), tile("Übernahme-Anfragen", q.claims), tile("Zertifikate", q.certs), tile("Meldungen", q.reports)]));
      p.appendChild(h("p", { class: "mut" }, ["Freigeben und ablehnen: ", h("a", { href: "#fr", text: "Reiter Freigaben", onclick: function (ev) { ev.preventDefault(); show("fr"); } }), "."]));
      p.appendChild(h("h2", { text: "Auf einen Blick" }));
      p.appendChild(h("div", { class: "adm-grid" }, [tile("Mitglieder", o.db.users), tile("Öffentliche Profile", o.db.profiles), tile("Blog-Beiträge live", o.db.blog_live), tile("Entitäten in der Datenbank", o.db.entities_db, "von " + (o.db.entities_file == null ? "?" : o.db.entities_file) + " in der Datei")]));
      var ops = h("div", {}); p.appendChild(h("h2", { text: "Betrieb" })); p.appendChild(ops); ops.appendChild(h("p", { class: "mut", text: "Lädt …" }));
      api("/api/admin/panel/ops").then(function (r) { ops.textContent = ""; if (r.s !== 200) { ops.appendChild(h("p", { class: "adm-msg bad", text: "Betriebsdaten nicht abrufbar" })); return; }
        var fails = {}; (r.j.fails || []).forEach(function (f) { fails[f.name] = f.n; });
        var tb = h("table", { class: "adm-tbl adm-ops" }, [h("thead", {}, [h("tr", {}, [h("th", { text: "Aufgabe" }), h("th", { text: "Letzter Lauf" }), h("th", { text: "Status" }), h("th", { text: "Fehler 24 h" }), h("th", { text: "Info" })])])]);
        var tbody = h("tbody"); (r.j.runs || []).forEach(function (x) { tbody.appendChild(h("tr", {}, [h("td", { text: x.name }), h("td", { text: "vor " + ago(x.started) }), h("td", { text: !x.finished ? "läuft" : x.ok ? "ok" : "Fehler" }), h("td", { text: String(fails[x.name] || 0) }), h("td", { text: (x.info || "").slice(0, 90) })])); });
        if (!(r.j.runs || []).length) tbody.appendChild(h("tr", {}, [h("td", { colspan: "5", class: "mut", text: "Noch keine Läufe protokolliert (ab dem nächsten Cron-Lauf nach dem Deploy)." })]));
        tb.appendChild(tbody); ops.appendChild(tb);
        ops.appendChild(h("h3", { text: "Protokoll der Verwaltung" }));
        var al = h("ul", { class: "adm-list" }); (r.j.audit || []).slice(0, 30).forEach(function (a) { al.appendChild(h("li", {}, [h("span", { class: "mut", text: "vor " + ago(a.created) + " · " }), h("b", { text: a.name || ("#" + a.user_id) }), " " + a.action + " " + (a.target || "") + (a.detail ? " · " + a.detail.slice(0, 80) : "")])); });
        if (!(r.j.audit || []).length) al.appendChild(h("li", { class: "mut", text: "Noch keine Einträge." })); ops.appendChild(al); });
    }); },
    tr: function () { if (panes.tr.firstChild) return; translations(); },
    fr: function () { approvals(); },
    db: function () { overview(function (o) { var p = panes.db, d = o.db, m = h("p", { class: "adm-msg" }); p.textContent = "";
      p.appendChild(h("h2", { text: "Umzug in die Datenbank" }));
      var miss = d.entities_file == null ? null : Math.max(0, d.entities_file - (d.entities_db || 0));
      p.appendChild(h("div", { class: "adm-grid" }, [tile("Entitäten in der Datenbank", d.entities_db, miss == null ? "" : miss + " noch nur in der Datei"), tile("Frühere Blog-Beiträge übernommen", d.blog_legacy, "Import-Stand " + d.blog_import_offset + " von 2307"), tile("Profil-Export", d.profiles_export_age == null ? "–" : Math.round(d.profiles_export_age / 60) + " min", "Alter des Zwischenspeichers"), tile("Übersetzungen (Inhalte)", d.item_tr), tile("Übersetzungen (Entitäten)", d.ent_tr)]));
      p.appendChild(h("p", {}, ["Entitäten: Bisher liegt die Grundlage in der Datei ", h("code", { text: "data/entities.json" }), ". Mit dem Knopf wird jede Entität, die noch keine Fassung in der Datenbank hat, einmal dorthin übernommen. Danach werden Änderungen nur noch hier und in der Datenbank gemacht. Es wird nichts überschrieben, was schon in der Datenbank steht."]));
      p.appendChild(h("button", { type: "button", class: "btn main", text: "Entitäten in die Datenbank übernehmen", onclick: function (ev) { ev.target.disabled = true; msg(m, "Läuft …"); api("/api/admin/panel/import-entities", { method: "POST", body: {} }).then(function (r) { ev.target.disabled = false; if (r.s === 200) { msg(m, r.j.imported + " übernommen, " + r.j.already + " waren schon da (" + r.j.total + " in der Datei)."); setTimeout(LOAD.db, 1500); } else msg(m, ERR[r.j.error] || "Fehler " + r.s, true); }); } }));
      p.appendChild(m);
    }); },
    sw: function () { overview(function (o) { var p = panes.sw, f = o.flags, m = h("p", { class: "adm-msg" }); p.textContent = "";
      p.appendChild(h("h2", { text: "Automatische Übersetzung (Haiku)" }));
      p.appendChild(h("p", { class: "mut", text: f.key ? "API-Schlüssel ist hinterlegt. Heute verbraucht: " + f.atr_today + " Übersetzungen für Inhalte, " + f.atr_ent_today + " für Entitäten." : "Kein API-Schlüssel hinterlegt: Die automatische Übersetzung läuft nicht." }));
      function sw(k, label, on) { var b = h("button", { type: "button", class: "btn" + (on ? " main" : ""), "aria-pressed": on ? "true" : "false", text: label + ": " + (on ? "an" : "aus"), onclick: function () { var nv = /_on$/.test(k) ? (on ? "0" : "1") : (on ? "1" : "0"); api("/api/admin/panel/flag", { method: "POST", body: { k: k, v: nv } }).then(function (r) { if (r.s === 200) LOAD.sw(); else msg(m, ERR[r.j.error] || "Fehler", true); }); } }); return b; }
      p.appendChild(h("p", {}, [sw("atr_off", "Neue Inhalte nach 24 Stunden übersetzen", f.atr_off !== "1"), " ", sw("tr_off", "Entitäten Englisch/Deutsch ergänzen", f.tr_off !== "1"), " ", sw("tr_queue_on", "Vormerkungen mit Haiku abarbeiten", f.tr_queue_on === "1")]));
      var src = f.entity_source === "db";
      p.appendChild(h("h2", { text: "Quelle der Entitäten" }));
      p.appendChild(h("p", {}, [h("button", { type: "button", class: "btn" + (src ? " main" : ""), "aria-pressed": src ? "true" : "false", text: "Entitäten nur aus der Datenbank: " + (src ? "an" : "aus"), onclick: function () { if (!src && !window.confirm("Ab jetzt liest die API Entitäten nur noch aus der Datenbank. Vorher prüfen: Datenbank-Reiter zeigt alle Entitäten der Datei als übernommen. Fortfahren?")) return; api("/api/admin/panel/flag", { method: "POST", body: { k: "entity_source", v: src ? "json" : "db" } }).then(function (r) { if (r.s === 200) LOAD.sw(); else msg(m, ERR[r.j.error] || "Fehler", true); }); } })]));
      p.appendChild(h("p", { class: "mut", text: src ? "Die Datenbank ist die einzige Quelle; entities.json wird vom Worker nicht mehr gelesen. Neue Einträge der Datei holt der Cron importEntitiesFromSite weiterhin in die Datenbank." : "Noch wie bisher: Datei plus Datenbank. Der Cron importEntitiesFromSite übernimmt neue Einträge der Datei automatisch; sobald alle übernommen sind, kann der Schalter auf Datenbank stehen (Rückweg jederzeit)." }));
      p.appendChild(h("p", { class: "mut", text: "Vormerkungen: Community-Inhalte und Entitäten übersetzt der Worker alle 30 Minuten (bis 6 je Lauf, Tageslimit 150), sobald der Schalter an ist. Frühere Blogbeiträge und Show Notes laufen über die GitHub-Workflows translate-blog (Eingabe queue=true) und translate-notes." }));
      var cap = h("input", { type: "number", min: "0", max: "2000", id: "adm-cap", value: f.atr_ent_cap || "300" });
      p.appendChild(h("p", {}, [h("label", { for: "adm-cap", text: "Tageslimit Entitäten-Übersetzungen " }), cap, " ", h("button", { type: "button", class: "btn", text: "Speichern", onclick: function () { api("/api/admin/panel/flag", { method: "POST", body: { k: "atr_ent_cap", v: String(Math.max(0, Math.min(2000, parseInt(cap.value, 10) || 0))) } }).then(function (r) { msg(m, r.s === 200 ? "Gespeichert." : (ERR[r.j.error] || "Fehler"), r.s !== 200); }); } })]));
      p.appendChild(m);
    }); },
    ent: function () { if (panes.ent.firstChild) return; entities(); }
  };

  // ---------- Freigaben: alles, was auf eine Entscheidung wartet, mit den bestehenden Admin-Routen ----------
  function approvals() {
    var p = panes.fr, m = h("p", { class: "adm-msg" }); p.textContent = ""; p.appendChild(h("h2", { text: "Wartet auf Freigabe" })); p.appendChild(m);
    var busy = 0; function done() { if (--busy <= 0 && !p.querySelector(".adm-list li")) p.appendChild(h("p", { class: "mut", text: "Nichts offen. Alles freigegeben." })); }
    function section(title, hint) { var s = h("section", {}, [h("h3", { text: title }), hint ? h("p", { class: "mut", text: hint }) : null, h("ul", { class: "adm-list" })]); p.appendChild(s); return s.querySelector("ul"); }
    function act(label, main, fn, after) { return h("button", { type: "button", class: "btn" + (main ? " main" : ""), text: label, onclick: function (ev) { ev.target.disabled = true; fn().then(function (r) { if (r.s === 200) { msg(m, "Erledigt."); after(); } else { ev.target.disabled = false; msg(m, ERR[(r.j || {}).error] || "Fehler " + r.s, true); } }); } }); }
    function row(ul, kids) { var li = h("li", {}, kids); ul.appendChild(li); return function () { li.remove(); if (!ul.children.length) ul.parentNode.remove(); }; }
    function note() { return window.prompt("Grund für die Ablehnung (optional):") || ""; }
    function when(t) { return t ? new Date(t * 1000).toLocaleDateString("de-DE") : ""; }
    busy = 8;
    api("/api/admin/blog").then(function (r) { var it = (r.j || {}).items || []; if (it.length) { var ul = section("Blog-Beiträge (" + it.length + ")"); it.forEach(function (x) { var rm = row(ul, [h("b", { text: x.title }), " ", h("span", { class: "mut", text: (x.name || "") + " · " + (x.lang || "") + " · " + when(x.created) }), h("p", { class: "mut", text: (x.summary || x.body || "").slice(0, 220) }), h("p", {}, [act("Freigeben", true, function () { return api("/api/admin/blog/decide", { method: "POST", body: { id: x.id, ok: true } }); }, function () { rm(); }), " ", act("Ablehnen", false, function () { return api("/api/admin/blog/decide", { method: "POST", body: { id: x.id, ok: false, note: note() } }); }, function () { rm(); })])]); }); } done(); });
    api("/api/admin/wiki/pending").then(function (r) { var it = (r.j || {}).pending || []; if (it.length) { var ul = section("Wiki-Änderungen (" + it.length + ")"); it.forEach(function (x) { var rm = row(ul, [h("b", { text: x.term + " (" + x.lang + ")" }), " ", h("span", { class: "mut", text: (x.name || "") + " · " + when(x.created) + (x.summary ? " · " + x.summary : "") }), h("p", { class: "mut", text: (x.body || "").slice(0, 260) }), h("p", {}, [act("Freigeben", true, function () { return api("/api/admin/wiki/approve/" + x.id, { method: "POST", body: {} }); }, function () { rm(); }), " ", act("Ablehnen", false, function () { return api("/api/admin/wiki/reject/" + x.id, { method: "POST", body: {} }); }, function () { rm(); })])]); }); } done(); });
    api("/api/admin/entity/pending").then(function (r) { var it = (r.j || {}).pending || []; if (it.length) { var ul = section("Entitäten-Vorschläge (" + it.length + ")"); it.forEach(function (x) { var d = x.data || {}; var rm = row(ul, [h("b", { text: (d.name || x.eid) }), " ", h("span", { class: "mut", text: x.eid + " · " + (x.name || "") + " · " + when(x.created) + (x.summary ? " · " + x.summary : "") }), h("p", { class: "mut", text: ((d.desc || {}).en || (d.desc || {}).de || "").slice(0, 220) }), h("p", {}, [act("Freigeben", true, function () { return api("/api/admin/entity/approve/" + x.id, { method: "POST", body: {} }); }, function () { rm(); }), " ", act("Ablehnen", false, function () { return api("/api/admin/entity/reject/" + x.id, { method: "POST", body: {} }); }, function () { rm(); }), " ", h("a", { href: BASE + "/entity/" + x.eid + "/", target: "_blank", rel: "noopener", text: "Seite" })])]); }); } done(); });
    api("/api/admin/entity/claims").then(function (r) { var it = (r.j || {}).claims || []; if (it.length) { var ul = section("Übernahme-Anfragen (" + it.length + ")", "Ein Mitglied möchte eine Entität (Firma, Produkt) als Inhaber betreuen."); it.forEach(function (x) { var rm = row(ul, [h("b", { text: x.eid }), " ", h("span", { class: "mut", text: (x.name || "") + (x.handle ? " (" + x.handle + ")" : "") }), h("p", {}, [act("Bestätigen", true, function () { return api("/api/admin/entity/claim", { method: "POST", body: { eid: x.eid, ok: true } }); }, function () { rm(); }), " ", act("Ablehnen", false, function () { return api("/api/admin/entity/claim", { method: "POST", body: { eid: x.eid, ok: false } }); }, function () { rm(); })])]); }); } done(); });
    api("/api/admin/cert-queue").then(function (r) { var it = (r.j || {}).items || []; if (it.length) { var ul = section("Zertifikate prüfen (" + it.length + ")"); it.forEach(function (x) { var rm = row(ul, [h("b", { text: x.e + (x.year ? " · " + x.year : "") }), " ", h("span", { class: "mut", text: (x.name || "") + (x.handle ? " (" + x.handle + ")" : "") }), x.url ? h("p", {}, [h("a", { href: x.url, target: "_blank", rel: "noopener nofollow", text: "Nachweis öffnen" })]) : null, h("p", {}, [act("Bestätigen", true, function () { return api("/api/admin/verify", { method: "POST", body: { owner: "u:" + x.handle, kind: "cert", key: x.e, value: 1 } }); }, function () { rm(); }), " ", act("Ablehnen", false, function () { return api("/api/admin/verify", { method: "POST", body: { owner: "u:" + x.handle, kind: "cert", key: x.e, value: 0 } }); }, function () { rm(); })])]); }); } done(); });
    api("/api/admin/reports").then(function (r) { var it = (r.j || {}).reports || []; if (it.length) { var ul = section("Gemeldete Kommentare (" + it.length + ")"); it.forEach(function (x) { var rm = row(ul, [h("b", { text: x.n + "× gemeldet" }), " ", h("span", { class: "mut", text: (x.lang || "") + " · " + (x.status || "") }), h("p", { class: "mut", text: (x.body || "").slice(0, 260) }), h("p", {}, [act("Ausblenden", true, function () { return api("/api/admin/hide/" + x.id, { method: "POST", body: {} }); }, function () { rm(); }), " ", act("Behalten", false, function () { return api("/api/admin/show/" + x.id, { method: "POST", body: {} }); }, function () { rm(); })])]); }); } done(); });
    api("/api/admin/podcast").then(function (r) { var it = (r.j || {}).items || []; if (it.length) { var ul = section("Podcast-Folgen (" + it.length + ")", "Freigabe läuft über die Abstimmung der Community (" + ((r.j || {}).threshold || 25) + " Punkte) und die Veröffentlichung bei Spreaker; hier nur ablehnen."); it.forEach(function (x) { var rm = row(ul, [h("b", { text: x.title }), " ", h("span", { class: "mut", text: (x.name || "") + " · " + x.status + " · " + (x.votes || 0) + " Stimmen · " + when(x.created) }), x.spreaker ? h("p", {}, [h("a", { href: x.spreaker, target: "_blank", rel: "noopener", text: "Bei Spreaker öffnen" })]) : null, h("p", {}, [act("Ablehnen", false, function () { return api("/api/admin/podcast/reject", { method: "POST", body: { id: x.id, note: note() } }); }, function () { rm(); })])]); }); } done(); });
    api("/api/admin/video").then(function (r) { var it = (r.j || {}).items || []; if (it.length) { var ul = section("Videos (" + it.length + ")", "Freigabe über die Abstimmung (" + ((r.j || {}).threshold || 25) + " Punkte) und die Veröffentlichung bei YouTube; hier nur ablehnen."); it.forEach(function (x) { var rm = row(ul, [h("b", { text: x.title }), " ", h("span", { class: "mut", text: (x.name || "") + " · " + x.status + " · " + (x.votes || 0) + " Stimmen · " + when(x.created) }), x.youtube ? h("p", {}, [h("a", { href: x.youtube, target: "_blank", rel: "noopener", text: "Im YouTube Studio öffnen" })]) : null, h("p", {}, [act("Ablehnen", false, function () { return api("/api/admin/video/reject", { method: "POST", body: { id: x.id, note: note() } }); }, function () { rm(); })])]); }); } done(); });
  }

  // ---------- Uebersetzungen: Uebersicht je Sprache, Filter, Vormerken ----------
  function translations() {
    var p = panes.tr, m = h("p", { class: "adm-msg" }), sum = h("div", { class: "adm-sum" }), kf = h("select", { "aria-label": "Art" }), lf = h("select", { "aria-label": "Sprache" }), sf = h("select", { "aria-label": "Status" }), q = h("input", { type: "search", placeholder: "Suchen im Titel", "aria-label": "Suchen" });
    var tbl = h("table", { class: "adm-tbl" }), tbody = h("tbody"), head = h("thead"), bulk = h("button", { type: "button", class: "btn", text: "Alle gefilterten vormerken" }), unbulk = h("button", { type: "button", class: "btn", text: "Vormerkung zurücknehmen" }), cnt = h("span", { class: "mut" });
    var D = null, Q = {};
    kf.appendChild(h("option", { value: "", text: "Alle Arten" })); Object.keys(KINDN).forEach(function (k) { kf.appendChild(h("option", { value: k, text: KINDN[k] })); });
    [["", "Alle Sprachen"]].concat(Object.keys(LANGN).filter(function (l) { return l !== "en"; }).map(function (l) { return [l, LANGN[l]]; })).forEach(function (x) { lf.appendChild(h("option", { value: x[0], text: x[1] })); });
    [["", "Alle"], ["missing", "fehlt"], ["done", "vorhanden"], ["queued", "vorgemerkt"], ["failed", "fehlgeschlagen"], ["none", "komplett ohne Übersetzung"]].forEach(function (x) { sf.appendChild(h("option", { value: x[0], text: x[1] })); });
    p.append(h("h2", { text: "Übersetzungen nach Sprache" }), h("p", { class: "mut", text: "Grün: vorhanden. Grau: fehlt, anklicken zum Vormerken. Blau: vorgemerkt (nochmal anklicken nimmt es zurück). Abgearbeitet wird, sobald unter Schalter „Vormerkungen mit Haiku abarbeiten“ an ist." }), sum, h("div", { class: "adm-row" }, [q, kf, lf, sf]), h("p", {}, [bulk, " ", unbulk, " ", cnt]), m, tbl);
    tbl.append(head, tbody); tbody.appendChild(h("tr", {}, [h("td", { class: "mut", text: "Lädt …" })]));
    function load() { api("/api/admin/panel/translations").then(function (r) { if (r.s !== 200) { msg(m, ERR[(r.j || {}).error] || "Übersicht nicht abrufbar", true); return; } D = r.j; Q = {}; (D.queue || []).forEach(function (x) { Q[x.kind + "|" + x.item_id + "|" + x.lang] = x; }); draw(); }); }
    function state(r, l) { if (r.lang === l) return "src"; if (r.langs.indexOf(l) > -1) return "done"; var x = Q[r.k + "|" + r.id + "|" + l]; return x ? (x.status === "failed" ? "failed" : x.status === "done" ? "done" : "queued") : "missing"; }
    function filtered() { var k = kf.value, l = lf.value, st = sf.value, s = q.value.trim().toLowerCase(), langs = D.langs; return (D.rows || []).filter(function (r) {
      if (k && r.k !== k) return false; if (s && r.t.toLowerCase().indexOf(s) < 0) return false;
      if (st === "none") return langs.every(function (x) { return state(r, x) === "missing" || state(r, x) === "src"; });
      if (!st) return true; var ls = l ? [l] : langs; return ls.some(function (x) { return state(r, x) === st; }); }); }
    function toggle(r, l, on) { api("/api/admin/panel/tr-queue", { method: "POST", body: { kind: r.k, id: r.id, lang: l, title: r.t, on: on } }).then(function (x) { if (x.s === 200) { if (on) Q[r.k + "|" + r.id + "|" + l] = { status: "open" }; else delete Q[r.k + "|" + r.id + "|" + l]; draw(); } else msg(m, ERR[(x.j || {}).error] || "Fehler", true); }); }
    function draw() {
      var langs = D.langs, rows = filtered(); sum.textContent = ""; head.textContent = ""; tbody.textContent = "";
      langs.forEach(function (l) { var d = 0, qd = 0, miss = 0; (D.rows || []).forEach(function (r) { var st = state(r, l); if (st === "done") d++; else if (st === "queued" || st === "failed") qd++; else if (st === "missing") miss++; }); sum.appendChild(h("div", {}, [h("b", { text: d + " / " + (d + miss + qd) }), LANGN[l] || l, h("br"), h("small", { text: miss + " fehlen" + (qd ? ", " + qd + " vorgemerkt" : "") })])); });
      head.appendChild(h("tr", {}, [h("th", { text: "Inhalt" }), h("th", { text: "Art" })].concat(langs.map(function (l) { return h("th", { text: l }); }))));
      rows.slice(0, 300).forEach(function (r) { tbody.appendChild(h("tr", {}, [h("td", { text: r.t }), h("td", { class: "mut", text: KINDN[r.k] || r.k })].concat(langs.map(function (l) { var st = state(r, l);
        if (st === "src") return h("td", { class: "mut", text: "Quelle" }); if (st === "done") return h("td", {}, [h("span", { class: "adm-chip ok", text: "✓" })]);
        var b = h("button", { type: "button", class: "adm-chip" + (st === "queued" ? " q" : st === "failed" ? " fail" : ""), text: st === "queued" ? "◷" : st === "failed" ? "!" : "+", title: st === "queued" ? "vorgemerkt – zurücknehmen" : st === "failed" ? "fehlgeschlagen – erneut vormerken" : "vormerken", onclick: function () { toggle(r, l, st !== "queued"); } }); return h("td", {}, [b]); })))); });
      cnt.textContent = rows.length + " Inhalte" + (rows.length > 300 ? " (300 angezeigt, bitte filtern)" : "");
      bulk.onclick = function () { var l = lf.value; if (!l) { msg(m, "Bitte zuerst eine Sprache wählen.", true); return; } var items = rows.filter(function (r) { return state(r, l) === "missing" || state(r, l) === "failed"; }).slice(0, 500).map(function (r) { return { kind: r.k, id: r.id, lang: l, title: r.t }; }); if (!items.length) { msg(m, "Nichts vorzumerken."); return; }
        api("/api/admin/panel/tr-queue", { method: "POST", body: { items: items, on: true } }).then(function (x) { if (x.s === 200) { msg(m, x.j.n + " vorgemerkt für " + LANGN[l] + "."); load(); } else msg(m, "Fehler", true); }); };
      unbulk.onclick = function () { var l = lf.value; if (!l) { msg(m, "Bitte zuerst eine Sprache wählen.", true); return; } var items = rows.filter(function (r) { return state(r, l) === "queued" || state(r, l) === "failed"; }).slice(0, 500).map(function (r) { return { kind: r.k, id: r.id, lang: l }; }); if (!items.length) { msg(m, "Nichts vorgemerkt."); return; }
        api("/api/admin/panel/tr-queue", { method: "POST", body: { items: items, on: false } }).then(function (x) { if (x.s === 200) { msg(m, x.j.n + " zurückgenommen."); load(); } else msg(m, "Fehler", true); }); };
    }
    [kf, lf, sf].forEach(function (e) { e.addEventListener("change", function () { if (D) draw(); }); }); q.addEventListener("input", function () { if (D) draw(); });
    load();
  }

  // ---------- Entitaeten ----------
  function entities() {
    var p = panes.ent, q = h("input", { type: "search", id: "adm-q", placeholder: "Suchen: Name, ID oder Alias", "aria-label": "Entitäten suchen" }), tf = h("select", { id: "adm-tf", "aria-label": "Typ" }), list = h("ul", { class: "adm-list" }), form = h("div", { class: "adm-form", hidden: "" }), all = [];
    tf.appendChild(h("option", { value: "", text: "Alle Typen" })); Object.keys(TYPES).forEach(function (k) { tf.appendChild(h("option", { value: k, text: TYPES[k] })); });
    p.append(h("div", { class: "adm-row" }, [q, tf]), list, form);
    list.appendChild(h("li", { class: "mut", text: "Lädt …" }));
    Promise.all([fetch(BASE + "/entities.json").then(function (r) { return r.json(); }).catch(function () { return { entities: [] }; }), api("/api/entity/export")]).then(function (res) {
      var by = {}; (res[0].entities || []).forEach(function (e) { by[e.id] = { e: e, db: false }; });
      ((res[1].j || {}).items || []).forEach(function (x) { by[x.id] = { e: Object.assign({ id: x.id }, x.data), db: true }; });
      all = Object.keys(by).map(function (k) { return by[k]; }).sort(function (a, b) { return String(a.e.name).localeCompare(String(b.e.name)); }); draw();
    });
    function draw() {
      var s = q.value.trim().toLowerCase(), t = tf.value, n = 0; list.textContent = "";
      all.forEach(function (x) { var e = x.e; if (t && e.type !== t) return; if (s && (e.name + " " + e.id + " " + (e.aliases || []).join(" ")).toLowerCase().indexOf(s) < 0) return; if (++n > 80) return;
        list.appendChild(h("li", {}, [h("button", { type: "button", class: "adm-item", onclick: function () { edit(e.id); } }, [h("b", { text: e.name }), " ", h("span", { class: "mut", text: (TYPES[e.type] || e.type) + " · " + e.id }), " ", h("span", { class: "adm-badge" + (x.db ? " on" : ""), text: x.db ? "Datenbank" : "nur Datei" })])])); });
      if (n > 80) list.appendChild(h("li", { class: "mut", text: (n - 80) + " weitere, bitte genauer suchen" }));
      if (!n) list.appendChild(h("li", { class: "mut", text: "Keine Treffer" }));
    }
    q.addEventListener("input", draw); tf.addEventListener("change", draw);
    function field(id, label, val, o) { o = o || {}; var inp = o.area ? h("textarea", { id: id, rows: o.rows || 3, maxlength: o.max || 600 }) : h("input", { type: "text", id: id, maxlength: o.max || 300 }); inp.value = val || ""; return h("p", { class: "adm-field" }, [h("label", { for: id, text: label }), inp, o.hint ? h("small", { class: "mut", text: o.hint }) : null]); }
    function edit(id) {
      form.hidden = false; form.textContent = "Lädt …"; form.scrollIntoView({ behavior: "smooth", block: "start" });
      api("/api/entity?id=" + encodeURIComponent(id)).then(function (r) {
        var base = (all.filter(function (x) { return x.e.id === id; })[0] || {}).e || {}, d = (r.j && r.j.live && r.j.live.data) || base, m = h("p", { class: "adm-msg" });
        form.textContent = ""; form.appendChild(h("h2", { text: d.name || id }));
        form.appendChild(h("p", { class: "mut" }, ["ID ", h("code", { text: id }), " · ", h("a", { href: BASE + "/entity/" + id + "/", target: "_blank", rel: "noopener", text: "Seite ansehen" })]));
        var typ = h("select", { id: "f-type" }); Object.keys(TYPES).forEach(function (k) { var o = h("option", { value: k, text: TYPES[k] }); if (k === d.type) o.selected = true; typ.appendChild(o); });
        var F = {
          name: field("f-name", "Name", d.name, { max: 80 }), aliases: field("f-al", "Andere Namen (mit Komma getrennt)", (d.aliases || []).join(", ")),
          den: field("f-den", "Kurzbeschreibung Englisch", (d.desc || {}).en, { area: 1, max: 300, hint: "20 bis 300 Zeichen, erscheint als Hover-Text" }), dde: field("f-dde", "Kurzbeschreibung Deutsch", (d.desc || {}).de, { area: 1, max: 300 }),
          len: field("f-len", "Lange Beschreibung Englisch", (d.long || {}).en, { area: 1, rows: 7, max: 3000, hint: "Bis 3000 Zeichen. Überschriften und Absätze wie im Editor." }), lde: field("f-lde", "Lange Beschreibung Deutsch", (d.long || {}).de, { area: 1, rows: 7, max: 3000 }),
          web: field("f-web", "Website (https)", d.web), docs: field("f-docs", "Dokumentation (microsoft.com, azure.com, github.com)", d.docs), wp: field("f-wp", "Wikipedia (https)", d.wikipedia), wd: field("f-wd", "Wikidata-ID (z. B. Q12345)", d.wikidata, { max: 12 }),
        };
        var old = h("input", { type: "checkbox", id: "f-old" }); old.checked = !!d.outdated;
        form.append(h("p", { class: "adm-field" }, [h("label", { for: "f-type", text: "Typ" }), typ]), F.name, F.aliases, F.den, F.dde, F.len, F.lde, F.web, F.docs, F.wp, F.wd, h("p", {}, [old, h("label", { for: "f-old", text: " Nicht mehr aktuell (Seite bleibt, wird ausgeblendet)" })]));
        form.appendChild(h("p", { class: "mut", text: "Beziehungen (" + (d.rel || []).length + ") bleiben erhalten; bearbeiten auf der Entitätsseite." }));
        var v = function (f) { return f.querySelector("input,textarea").value.trim(); };
        form.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: "Speichern", onclick: function (ev) {
          var data = Object.assign({}, d, { name: v(F.name), type: typ.value, aliases: v(F.aliases).split(",").map(function (s) { return s.trim(); }).filter(Boolean), desc: { en: v(F.den), de: v(F.dde) }, long: { en: v(F.len), de: v(F.lde) }, web: v(F.web), docs: v(F.docs), wikipedia: v(F.wp), wikidata: v(F.wd), outdated: old.checked, rel: d.rel || [] });
          ev.target.disabled = true; msg(m, "Speichert …");
          api("/api/entity", { method: "POST", body: { id: id, data: data, summary: "Verwaltung" } }).then(function (r) { ev.target.disabled = false;
            if (r.s === 200) { msg(m, r.j.status === "live" ? "Gespeichert. Auf der Seite sichtbar nach dem nächsten Seitenbau." : "Als Vorschlag gespeichert."); all.forEach(function (x) { if (x.e.id === id) { x.e = Object.assign({ id: id }, data); x.db = true; } }); draw(); }
            else msg(m, ERR[r.j.error] || "Fehler " + r.s, true); });
        } }), " ", h("button", { type: "button", class: "btn", text: "Schließen", onclick: function () { form.hidden = true; } })]));
        form.appendChild(m);
      });
    }
  }

  root.textContent = ""; root.append(bar); tabs.forEach(function (t) { root.appendChild(panes[t[0]]); });
  overview(function () { var k = (location.hash || "").slice(1); show(panes[k] ? k : "ov"); });
})();
