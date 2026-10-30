/* Entitaetsdatenbank: Eigenschaften bearbeiten / neues Thema anlegen. window.M365E = {api, lang, base, s}. Nur DOM-Knoten, kein innerHTML. */
(function () {
  var E = window.M365E; if (!E) return;
  var de = E.lang === "de";
  var X = de ? { edit: "Eigenschaften bearbeiten", create: "Neues Thema anlegen", name: "Name", type: "Typ", aliases: "Auch bekannt als (kommagetrennt)", den: "Kurzbeschreibung (Englisch) – Pflicht, erscheint beim Darüberfahren in Artikeln", dde: "Beschreibung (Deutsch)", web: "Webseite (https)", docs: "Dokumentation (learn.microsoft.com …)", wp: "Wikipedia-Link", wd: "Wikidata-ID (z. B. Q123)", rel: "Beziehungen", add: "Beziehung hinzufügen", pred: "Beziehung", target: "Ziel suchen…", rm: "Entfernen", sum: "Was hast du geändert? (optional)", save: "Speichern", login: "Melde dich an, um zu bearbeiten.", ok: "Veröffentlicht. Danke!", pend: "Danke! Die Änderung erscheint nach der Prüfung.", err: "Etwas ist schiefgelaufen. Bitte versuche es erneut.", rules: "Beschreibungen in eigenen Worten, ohne Links und Werbung. Beziehungen wählst du aus der Liste.", bad_relation: "Ein Beziehungsziel gibt es nicht. Bitte aus der Liste wählen.", bad_url: "Eine Adresse ist ungültig (nur https, Dokumentation nur Microsoft/GitHub, Wikipedia nur wikipedia.org).", bad_qid: "Die Wikidata-ID muss wie Q123 aussehen.", too_short: "Bitte beschreibe das Thema mit mindestens 20 Zeichen.", bad_name: "Bitte gib einen Namen an.", unchanged: "Keine Änderung gefunden.", rate_limit: "Zu viele Änderungen – bitte später erneut versuchen.", hint_new: "Nach der Prüfung entsteht eine eigene Seite mit Wiki, Beziehungen und Schema.org-Daten." }
    : { edit: "Edit properties", create: "Add a new topic", name: "Name", type: "Type", aliases: "Also known as (comma-separated)", den: "Short description (English) – required, shown on hover in articles", dde: "Description (German)", web: "Website (https)", docs: "Documentation (learn.microsoft.com …)", wp: "Wikipedia link", wd: "Wikidata ID (e.g. Q123)", rel: "Relationships", add: "Add relationship", pred: "Relationship", target: "Search target…", rm: "Remove", sum: "What did you change? (optional)", save: "Save", login: "Sign in to edit.", ok: "Published. Thank you!", pend: "Thank you! Your change will appear after review.", err: "Something went wrong. Please try again.", rules: "Describe in your own words, without links or advertising. Pick relationship targets from the list.", bad_relation: "A relationship target does not exist. Please pick from the list.", bad_url: "An address is invalid (https only; documentation only Microsoft/GitHub; Wikipedia only wikipedia.org).", bad_qid: "The Wikidata ID must look like Q123.", too_short: "Please describe the topic with at least 20 characters.", bad_name: "Please enter a name.", unchanged: "No changes found.", rate_limit: "Too many edits – please try again later.", hint_new: "After review it becomes its own page with wiki, relationships and Schema.org data." };
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
    var name = h("input", { type: "text", maxlength: 80 }), type = h("select"), al = h("input", { type: "text", maxlength: 700 }), den = h("textarea", { rows: 3, maxlength: 600 }), dde = h("textarea", { rows: 3, maxlength: 600 });
    var web = h("input", { type: "text", maxlength: 250 }), docs = h("input", { type: "text", maxlength: 250 }), wp = h("input", { type: "text", maxlength: 250 }), wd = h("input", { type: "text", maxlength: 12 }), sum = h("input", { type: "text", maxlength: 140, placeholder: X.sum, "aria-label": X.sum });
    Object.keys(TYPES).forEach(function (k) { type.appendChild(h("option", { value: k, text: TYPES[k][li] })); });
    name.value = e.name || ""; type.value = e.type || "product"; al.value = (e.aliases || []).join(", "); den.value = (e.desc || {}).en || ""; dde.value = (e.desc || {}).de || ""; web.value = e.web || ""; docs.value = e.docs || ""; wp.value = e.wikipedia || ""; wd.value = e.wikidata || "";
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
      var data = { name: name.value, type: type.value, aliases: al.value.split(",").map(function (x) { return x.trim(); }).filter(Boolean), desc: { en: den.value, de: dde.value }, web: web.value.trim(), docs: docs.value.trim(), wikipedia: wp.value.trim(), wikidata: wd.value.trim(), rel: rl };
      save.disabled = true;
      api("/api/entity", { method: "POST", body: { id: id, data: data, summary: sum.value } }).then(function (r) {
        save.disabled = false;
        if (r.s === 200) { msg.textContent = r.j.status === "live" ? X.ok : X.pend; return; }
        msg.textContent = X[r.j.error] || X.err;
      }).catch(function () { save.disabled = false; msg.textContent = X.err; });
    } });
    [h("p", { class: "cmut", text: X.rules + (isNew ? " " + X.hint_new : "") }), field(X.name, name)].forEach(function (x) { f.appendChild(x); });
    if (isNew) f.appendChild(field("ID (a-z, 0-9, -)", idInp));
    [field(X.type, type), field(X.aliases, al), field(X.den, den), field(X.dde, dde), field(X.web, web), field(X.docs, docs), field(X.wp, wp), field(X.wd, wd), h("h3", { text: X.rel }), dl, rels,
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
  var ed = document.getElementById("en-edit"); if (ed) { try { mount(ed, JSON.parse(ed.getAttribute("data-e")), false); } catch (e) {} }
  var nw = document.getElementById("en-new"); if (nw) mount(nw, {}, true);
})();
