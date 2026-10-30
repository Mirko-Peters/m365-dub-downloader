/* Entitaetsdatenbank: Eigenschaften bearbeiten / neues Thema anlegen. window.M365E = {api, lang, base, s}. Nur DOM-Knoten, kein innerHTML. */
(function () {
  var E = window.M365E; if (!E) return;
  var de = E.lang === "de";
  var X = de ? { edit: "Eigenschaften bearbeiten", create: "Neues Thema anlegen", name: "Name", type: "Typ", aliases: "Auch bekannt als (kommagetrennt)", den: "Kurzbeschreibung (Englisch)", dde: "Kurzbeschreibung (Deutsch) – mindestens eine Sprache ist Pflicht, erscheint beim Darüberfahren in Artikeln; weitere Sprachen sind freiwillig", web: "Webseite (https)", docs: "Dokumentation (learn.microsoft.com …)", wp: "Wikipedia-Link", wd: "Wikidata-ID (z. B. Q123)", rel: "Beziehungen", add: "Beziehung hinzufügen", pred: "Beziehung", target: "Ziel suchen…", rm: "Entfernen", sum: "Was hast du geändert? (optional)", save: "Speichern", login: "Melde dich an, um zu bearbeiten.", ok: "Veröffentlicht. Danke!", pend: "Danke! Die Änderung erscheint nach der Prüfung.", err: "Etwas ist schiefgelaufen. Bitte versuche es erneut.", rules: "So geht's: 1) Name und Typ prüfen, 2) eine Kurzbeschreibung (20–300 Zeichen) in eigenen Worten schreiben – ohne Links und Werbung, 3) bei Bedarf Aliase, offizielle Links und Beziehungen aus der Liste ergänzen, 4) speichern. Vertrauenswürdige Mitglieder veröffentlichen direkt, alle anderen gehen in die Abstimmung. Auch deine KI kann das per MCP (siehe Community → KI-Anbindung).", owner_only: "Die lange Beschreibung dieses Eintrags darf nur der Eigentümer ändern.", bad_date: de ? "Datum bitte als JJJJ-MM-TT angeben." : "Please use YYYY-MM-DD.", bad_license: de ? "Ungültige Lizenz." : "Invalid licence.", bad_level: de ? "Ungültige Stufe." : "Invalid level.", bad_relation: "Ein Beziehungsziel gibt es nicht. Bitte aus der Liste wählen.", bad_url: "Eine Adresse ist ungültig (nur https, Dokumentation nur Microsoft/GitHub, Wikipedia nur wikipedia.org).", bad_qid: "Die Wikidata-ID muss wie Q123 aussehen.", too_short: "Bitte beschreibe das Thema mit mindestens 20 Zeichen.", bad_name: "Bitte gib einen Namen an.", unchanged: "Keine Änderung gefunden.", rate_limit: "Zu viele Änderungen – bitte später erneut versuchen.", hint_new: "Nach der Prüfung entsteht eine eigene Seite mit Wiki, Beziehungen und Schema.org-Daten." }
    : { edit: "Edit properties", create: "Add a new topic", name: "Name", type: "Type", aliases: "Also known as (comma-separated)", den: "Short description (English) – at least one language is required, shown on hover in articles; more languages are optional", dde: "Short description (German)", web: "Website (https)", docs: "Documentation (learn.microsoft.com …)", wp: "Wikipedia link", wd: "Wikidata ID (e.g. Q123)", rel: "Relationships", add: "Add relationship", pred: "Relationship", target: "Search target…", rm: "Remove", sum: "What did you change? (optional)", save: "Save", login: "Sign in to edit.", ok: "Published. Thank you!", pend: "Thank you! Your change will appear after review.", err: "Something went wrong. Please try again.", rules: "How it works: 1) check name and type, 2) write a short description (20-300 characters) in your own words – no links or advertising, 3) add aliases, official links and relationships from the list if needed, 4) save. Trusted members publish directly, everyone else goes to the vote. Your AI can do this too via MCP (see Community → AI connection).", owner_only: "Only the owner may change the long description of this entry.", bad_relation: "A relationship target does not exist. Please pick from the list.", bad_url: "An address is invalid (https only; documentation only Microsoft/GitHub; Wikipedia only wikipedia.org).", bad_qid: "The Wikidata ID must look like Q123.", too_short: "Please describe the topic with at least 20 characters.", bad_name: "Please enter a name.", unchanged: "No changes found.", rate_limit: "Too many edits – please try again later.", hint_new: "After review it becomes its own page with wiki, relationships and Schema.org data." };
  var TYPES = { product: ["Product", "Produkt"], platform: ["Platform", "Plattform"], concept: ["Concept", "Konzept"], org: ["Organization", "Organisation"], person: ["Person", "Person"], cert: ["Certification", "Zertifizierung"], event: ["Event", "Veranstaltung"], media: ["Media", "Medium"], category: ["Category", "Kategorie"] };
  var PRED = { instance_of: ["Is a", "Ist ein"], part_of: ["Part of", "Teil von"], developed_by: ["Developed by", "Entwickelt von"], related_to: ["Related to", "Verwandt mit"], requires: ["Requires", "Benötigt"], covers: ["Covers", "Behandelt"], created_by: ["Created by", "Erstellt von"], organized_by: ["Organized by", "Veranstaltet von"], similar_to: ["Similar to", "Ähnlich wie"] };
  var li = de ? 1 : 0;
  function h(tag, a, kids) { var e = document.createElement(tag); for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }); return e; }
  function api(path, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(E.api + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  function slug(s) { return s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48); }
  var ents = null;
  function list() { return ents ? Promise.resolve(ents) : fetch(E.base + "/entities.json").then(function (r) { return r.json(); }).then(function (j) { ents = j.entities || []; return ents; }); }
  function pruneLogin(box){var P=window.__m365p=window.__m365p||fetch(E.api+"/api/providers").then(function(r){return r.json()}).catch(function(){return null});P.then(function(j){if(!j||!j.providers)return;[].slice.call(box.querySelectorAll("a[href*=\"/auth/login/\"]")).forEach(function(a){var m=/login\/(\w+)/.exec(a.href);if(m&&j.providers.indexOf(m[1])<0)a.remove()})})}
  function login() { var b = login0(); pruneLogin(b); return b; }
  function login0() { var ret = encodeURIComponent(location.href.split("#")[0]); return h("div", {}, [h("p", { text: X.login }), h("a", { class: "btn main", href: E.api + "/auth/login/google?return=" + ret, rel: "nofollow", text: "Google" }), h("a", { class: "btn", href: E.api + "/auth/login/microsoft?return=" + ret, rel: "nofollow", text: "Microsoft" }), h("a", { class: "btn", href: E.api + "/auth/login/linkedin?return=" + ret, rel: "nofollow", text: "LinkedIn" })]); }

  function form(e, isNew, all) {
    var f = h("div", { class: "wk-form en-form" }), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    function field(label, el) { var id = "en-" + Math.random().toString(36).slice(2, 8); el.id = id; return h("div", {}, [h("label", { for: id, text: label, style: "display:block;margin-top:.5em;font-weight:600" }), el]); }
    var name = h("input", { type: "text", maxlength: 80 }), type = h("select"), al = h("input", { type: "text", maxlength: 700 }), den = h("textarea", { rows: 3, maxlength: 600 }), dde = h("textarea", { rows: 3, maxlength: 600 }), len = h("textarea", { rows: 8, maxlength: 3000 }), lde = h("textarea", { rows: 8, maxlength: 3000 });
    var web = h("input", { type: "text", maxlength: 250 }), docs = h("input", { type: "text", maxlength: 250 }), wp = h("input", { type: "text", maxlength: 250 }), wd = h("input", { type: "text", maxlength: 12 }), xl = h("input", { type: "text", maxlength: 250 }), xv = h("input", { type: "text", maxlength: 30 }), xr = h("input", { type: "text", maxlength: 10, placeholder: "2025-11-01" }), xe = h("input", { type: "text", maxlength: 20 }), xm = h("input", { type: "number", min: 0, max: 120 }), xs = h("select"), xk = h("select"), od = h("input", { type: "checkbox" }), rb = h("input", { type: "text", maxlength: 48 }), sum = h("input", { type: "text", maxlength: 140, placeholder: X.sum, "aria-label": X.sum });
    Object.keys(TYPES).forEach(function (k) { type.appendChild(h("option", { value: k, text: TYPES[k][li] })); });
    name.value = e.name || ""; type.value = e.type || "product"; al.value = (e.aliases || []).join(", "); den.value = (e.desc || {}).en || ""; len.value = (e.long || {}).en || ""; lde.value = (e.long || {}).de || ""; dde.value = (e.desc || {}).de || ""; web.value = e.web || ""; docs.value = e.docs || ""; wp.value = e.wikipedia || ""; wd.value = e.wikidata || "";
    [["", "–"], ["free", de ? "kostenlos" : "free"], ["included", de ? "in M365 enthalten" : "included in M365"], ["addon", "Add-on"], ["paid", de ? "kostenpflichtig" : "paid"]].forEach(function (o) { xs.appendChild(h("option", { value: o[0], text: o[1] })); });
    [["", "–"], ["fundamentals", "Fundamentals"], ["associate", "Associate"], ["expert", "Expert"], ["specialty", "Specialty"]].forEach(function (o) { xk.appendChild(h("option", { value: o[0], text: o[1] })); });
    xl.value = e.logo || ""; xv.value = e.version || ""; xr.value = e.released || ""; xe.value = e.exam || ""; xm.value = e.valid_months || ""; xs.value = e.license || ""; xk.value = e.level || ""; od.checked = !!e.outdated; rb.value = e.replaced_by || "";
    var idv = e.id || "", idInp = null;
    if (isNew) { idInp = h("input", { type: "text", maxlength: 48, pattern: "[a-z0-9-]{2,48}" }); }
    var dl = h("datalist", { id: "en-dl" }); all.forEach(function (x) { dl.appendChild(h("option", { value: x.name })); });
    var rels = h("div", { class: "en-rels" });
    function relRow(p, to) {
      var sel = h("select", { "aria-label": X.pred }); Object.keys(PRED).forEach(function (k) { sel.appendChild(h("option", { value: k, text: PRED[k][li] })); }); sel.value = p || "related_to";
      var inp = h("input", { type: "text", list: "en-dl", placeholder: X.target, "aria-label": X.target, maxlength: 80 });
      if (to) { var t = all.filter(function (x) { return x.id === to; })[0]; inp.value = t ? t.name : to; }
      var row = h("div", { class: "en-relrow", style: "display:flex;gap:.4em;flex-wrap:wrap;margin:.3em 0" }, [sel, inp, h("button", { type: "button", class: "btn", text: X.rm, onclick: function () { row.remove(); } })]);
      row._get = function () { var v = inp.value.trim().toLowerCase(), hit = all.filter(function (x) { return x.name.toLowerCase() === v || x.id === v; })[0]; return hit ? [sel.value, hit.id] : (v ? null : false); };
      rels.appendChild(row);
    }
    (e.rel || []).forEach(function (r) { relRow(r[0], r[1]); });
    var save = h("button", { type: "button", class: "btn main", text: X.save, onclick: function () {
      var rl = [], bad = false; [].slice.call(rels.children).forEach(function (r) { var v = r._get(); if (v === null) bad = true; else if (v) rl.push(v); });
      if (bad) { msg.textContent = X.bad_relation; return; }
      var id = isNew ? (idInp.value.trim() || slug(name.value)) : idv;
      var data = { name: name.value, type: type.value, aliases: al.value.split(",").map(function (x) { return x.trim(); }).filter(Boolean), desc: { en: den.value, de: dde.value }, long: { en: len.value, de: lde.value }, web: web.value.trim(), docs: docs.value.trim(), wikipedia: wp.value.trim(), wikidata: wd.value.trim(), rel: rl, outdated: od.checked, replaced_by: rb.value.trim().toLowerCase(), logo: xl.value.trim(), version: xv.value.trim(), released: xr.value.trim(), license: xs.value, level: xk.value, exam: xe.value.trim(), valid_months: +xm.value || 0, start: e.start, end: e.end };
      save.disabled = true;
      api("/api/entity", { method: "POST", body: { id: id, data: data, summary: sum.value } }).then(function (r) {
        save.disabled = false;
        if (r.s === 200) { msg.textContent = r.j.status === "live" ? X.ok : X.pend; return; }
        msg.textContent = X[r.j.error] || X.err;
      }).catch(function () { save.disabled = false; msg.textContent = X.err; });
    } });
    [h("p", { class: "cmut", text: X.rules + (isNew ? " " + X.hint_new : "") }), field(X.name, name)].forEach(function (x) { f.appendChild(x); });
    if (isNew) f.appendChild(field("ID (a-z, 0-9, -)", idInp));
    [field(X.type, type), field(X.aliases, al), field(X.den, den), field(X.dde, dde), h("p", { class: "cmut", text: de ? "Lange Beschreibung (optional, bis 3000 Zeichen, Absätze mit Leerzeile, keine Links). Bei Events, Profilen und Firmen darf nur der Eigentümer sie ändern; bei allen anderen Themen die Community." : "Long description (optional, up to 3000 characters, paragraphs separated by a blank line, no links). For events, profiles and companies only the owner may change it; for all other topics the community." }), field(de ? "Lange Beschreibung (Englisch)" : "Long description (English)", len), field(de ? "Lange Beschreibung (Deutsch)" : "Long description (German)", lde), field(X.web, web), field(X.docs, docs), field(X.wp, wp), field(X.wd, wd), field(de ? "Logo-URL (https, Bild)" : "Logo URL (https, image)", xl), field(de ? "Produkt: Version" : "Product: version", xv), field(de ? "Produkt: veröffentlicht (JJJJ-MM-TT)" : "Product: released (YYYY-MM-DD)", xr), field(de ? "Produkt: Lizenz" : "Product: licence", xs), field(de ? "Zertifikat: Stufe" : "Certification: level", xk), field(de ? "Zertifikat: Prüfungscode (z. B. AB-731)" : "Certification: exam code (e.g. AB-731)", xe), field(de ? "Zertifikat: gültig (Monate, 0 = unbegrenzt)" : "Certification: valid (months, 0 = unlimited)", xm), h("label", { class: "cmut" }, [od, document.createTextNode(" " + (de ? "Nicht mehr aktuell (Seite bleibt, wird aber standardmäßig ausgeblendet)" : "No longer current (page stays, hidden by default)"))]), field(de ? "Ersetzt durch (ID der neuen Entität, optional)" : "Replaced by (ID of the new entity, optional)", rb), h("h3", { text: X.rel }), dl, rels,
      h("button", { type: "button", class: "btn", text: X.add, onclick: function () { relRow("related_to", ""); } }), field(X.sum, sum), h("div", { class: "btns" }, [save]), msg].forEach(function (x) { f.appendChild(x); });
    return f;
  }
  function votes(host, entity) {
    if (!entity.id) return; var de = (document.documentElement.lang || "en").slice(0, 2) === "de";
    api("/api/edits/pending?kind=entity&key=" + encodeURIComponent(entity.id)).then(function (r) {
      var l = (r.j.edits || []).filter(function (x) { return !x.own; }); if (r.s !== 200 || !l.length) return;
      var sec = h("div", { class: "wk-admin" }, [h("h3", { text: de ? "Offene Änderungen – Abstimmung" : "Open edits – vote" })]);
      l.forEach(function (x) {
        var d = {}; try { d = JSON.parse(x.body); } catch (e) {} var st = h("span", { class: "cmut", text: x.net + " (" + x.votes + ")" });
        function vote(v) { api("/api/edits/vote", { method: "POST", body: { kind: "entity", id: x.id, v: v } }).then(function (z) { if (z.s === 200) { st.textContent = z.j.net + " (" + z.j.votes + ")"; if (z.j.status !== "pending") location.reload(); } }); }
        sec.appendChild(h("div", { class: "wk-pend" }, [h("p", { class: "cmut", text: x.name + (x.summary ? " – " + x.summary : "") }), h("p", { text: [d.name, d.description].filter(Boolean).join(" – ") }),
          r.j.can_vote ? h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: "👍", onclick: function () { vote(1); } }), h("button", { type: "button", class: "btn", text: "👎", onclick: function () { vote(-1); } }), " ", st]) : st]));
      });
      host.appendChild(sec);
    });
  }
  function mount(host, entity, isNew) {
    votes(host, entity);
    var det = h("details", { class: "wk-edit" }, [h("summary", { text: isNew ? X.create : X.edit })]); host.appendChild(det);
    det.addEventListener("toggle", function once() {
      if (!det.open || det._done) return; det._done = true;
      Promise.all([list(), api("/api/entity?id=" + encodeURIComponent(entity.id || "none"))]).then(function (a) {
        if (!a[1].j.loggedIn) { det.appendChild(login()); return; }
        var cur = a[1].j.mine ? a[1].j.mine.data : (a[1].j.live ? a[1].j.live.data : entity);
        var base = isNew ? {} : Object.assign({}, entity, cur, { id: entity.id });
        det.appendChild(form(base, isNew, a[0]));
      }).catch(function () { det.appendChild(h("p", { text: X.err })); });
    });
  }
  /* ---------- Fragen & Antworten ---------- */
  function mountQa(host) {
    var eid = host.getAttribute("data-eid"); if (!eid) return;
    var T = de ? { h: "Fragen und Antworten", ask: "Frage stellen", qph: "Deine Frage zu diesem Thema (10–200 Zeichen)", send: "Absenden", ans: "Antworten", aph: "Deine Antwort in eigenen Worten (20–600 Zeichen, keine Links)", up: "Hilfreich", acc: "In FAQ übernehmen", accd: "In der FAQ-Box", none: "Noch keine Fragen. Stell die erste!", login: "Zum Fragen und Antworten bitte anmelden.", err: "Das hat nicht geklappt – bitte Eingaben prüfen.", note: "Die beste Antwort erscheint in der FAQ-Box dieser Seite, sobald Eigentümer/Redaktion sie annehmen oder genug Mitglieder sie hilfreich finden.", del: "Löschen", noans: "Noch keine Antwort." }
      : { h: "Questions and answers", ask: "Ask a question", qph: "Your question about this topic (10–200 characters)", send: "Submit", ans: "Answer", aph: "Your answer in your own words (20–600 characters, no links)", up: "Helpful", acc: "Add to FAQ", accd: "In the FAQ box", none: "No questions yet. Ask the first one!", login: "Please sign in to ask or answer.", err: "That did not work – please check your input.", note: "The best answer appears in this page's FAQ box once the owner/editors accept it or enough members find it helpful.", del: "Delete", noans: "No answer yet." };
    var box = h("section", { class: "wk-qa" }), list = h("div"), msg = h("p", { class: "cmut", role: "status", "aria-live": "polite" });
    box.appendChild(h("h2", { text: T.h })); box.appendChild(h("p", { class: "cmut", text: T.note })); box.appendChild(list);
    function load() {
      api("/api/qa?eid=" + encodeURIComponent(eid)).then(function (r) {
        if (r.s !== 200) return; list.textContent = ""; var d = r.j;
        if (!d.questions.length) list.appendChild(h("p", { class: "cmut", text: T.none }));
        d.questions.forEach(function (q) {
          var item = h("div", { class: "wk-q" }, [h("h3", { text: q.q })]);
          if (!q.answers.length) item.appendChild(h("p", { class: "cmut", text: T.noans }));
          q.answers.forEach(function (a) {
            var row = h("div", { class: "wk-a" }, [h("p", { text: a.a }), h("p", { class: "cmut", text: (a.name || "") + (a.accepted ? " · ✔ " + T.accd : "") + " · " + a.votes + " 👍" })]);
            if (d.loggedIn && !a.own) row.appendChild(h("button", { type: "button", class: "wk-link", "aria-pressed": a.me ? "true" : "false", text: (a.me ? "✓ " : "") + T.up, onclick: function () { api("/api/qa/vote", { method: "POST", body: { aid: a.id } }).then(load); } }));
            if (d.canAccept) row.appendChild(h("button", { type: "button", class: "wk-link", text: a.accepted ? "✔ " + T.accd : T.acc, onclick: function () { api("/api/qa/accept", { method: "POST", body: { aid: a.id } }).then(load); } }));
            if (a.own) row.appendChild(h("button", { type: "button", class: "wk-link", text: T.del, onclick: function () { api("/api/qa/delete", { method: "POST", body: { kind: "a", id: a.id } }).then(load); } }));
            item.appendChild(row);
          });
          if (d.loggedIn) {
            var ta = h("textarea", { rows: 2, maxlength: 600, placeholder: T.aph, "aria-label": T.aph, style: "width:100%" });
            item.appendChild(h("details", { class: "wk-edit" }, [h("summary", { text: T.ans }), ta, h("button", { type: "button", class: "btn", text: T.send, onclick: function () { api("/api/qa/answer", { method: "POST", body: { qid: q.id, a: ta.value } }).then(function (x) { if (x.s === 200) load(); else msg.textContent = T.err; }); } })]));
          }
          if (q.own) item.appendChild(h("button", { type: "button", class: "wk-link", text: T.del, onclick: function () { api("/api/qa/delete", { method: "POST", body: { kind: "q", id: q.id } }).then(load); } }));
          list.appendChild(item);
        });
        if (d.loggedIn) {
          var qi = h("input", { type: "text", maxlength: 200, placeholder: T.qph, "aria-label": T.qph, style: "width:100%" });
          list.appendChild(h("details", { class: "wk-edit" }, [h("summary", { text: T.ask }), qi, h("button", { type: "button", class: "btn main", text: T.send, onclick: function () { api("/api/qa/ask", { method: "POST", body: { eid: eid, q: qi.value, lang: de ? "de" : "en" } }).then(function (x) { if (x.s === 200) load(); else msg.textContent = T.err; }); } })]));
        } else list.appendChild(h("p", { class: "cmut" }, [h("a", { href: E.base + (de ? "/de" : "") + "/community/", text: T.login })]));
        list.appendChild(msg);
      });
    }
    host.appendChild(box); load();
  }
  var qh = document.getElementById("en-qa"); if (qh) mountQa(qh);
  var ed = document.getElementById("en-edit"); if (ed) { try { mount(ed, JSON.parse(ed.getAttribute("data-e")), false); } catch (e) {} }
  var nw = document.getElementById("en-new"); if (nw) mount(nw, {}, true);
})();
