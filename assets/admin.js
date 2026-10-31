/* Verwaltung ohne Code (/admin/): Uebersicht, Entitaeten bearbeiten, Datenbank, Schalter. Nur fuer Admins; alles laeuft ueber die bestehende Community-API.
   window.M365ADM = {api, base} */
(function () {
  var C = window.M365ADM || {}, API = C.api, BASE = C.base || "", root = document.getElementById("adm"); if (!root || !API) return;
  function h(t, a, kids) { var e = document.createElement(t); a = a || {}; for (var k in a) { if (k === "text") e.textContent = a[k]; else if (k === "class") e.className = a[k]; else if (k.slice(0, 2) === "on") e[k] = a[k]; else e.setAttribute(k, a[k]); } (kids || []).forEach(function (x) { if (x != null) e.appendChild(typeof x === "string" ? document.createTextNode(x) : x); }); return e; }
  function api(p, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(API + p, o).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; }); }); }
  var TYPES = { product: "Produkt", platform: "Plattform", concept: "Konzept", org: "Firma", person: "Person", cert: "Zertifikat", event: "Event", media: "Medium", category: "Kategorie" };
  var ERR = { bad_name: "Name zu kurz", bad_type: "Typ fehlt", too_short: "Kurzbeschreibung fehlt (mindestens 20 Zeichen in Englisch oder Deutsch)", too_long: "Kurzbeschreibung zu lang (höchstens 300 Zeichen)", bad_url: "Eine Adresse ist ungültig (nur https, Docs nur microsoft.com, azure.com oder github.com)", bad_qid: "Wikidata-ID muss wie Q12345 aussehen", bad_relation: "Eine Beziehung zeigt auf eine unbekannte Entität", unchanged: "Nichts geändert", rate_limit: "Zu viele Änderungen in kurzer Zeit, bitte später", login: "Bitte anmelden", forbidden: "Nur für Admins" };
  var tabs = [["ov", "Übersicht"], ["ent", "Entitäten"], ["db", "Datenbank"], ["sw", "Schalter"]], panes = {}, bar = h("div", { class: "adm-tabs", role: "tablist" });
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
      p.appendChild(h("p", { class: "mut" }, ["Freigeben und ablehnen geht im Admin-Bereich der ", h("a", { href: BASE + "/community/", text: "Community" }), "."]));
      p.appendChild(h("h2", { text: "Auf einen Blick" }));
      p.appendChild(h("div", { class: "adm-grid" }, [tile("Mitglieder", o.db.users), tile("Öffentliche Profile", o.db.profiles), tile("Blog-Beiträge live", o.db.blog_live), tile("Entitäten in der Datenbank", o.db.entities_db, "von " + (o.db.entities_file == null ? "?" : o.db.entities_file) + " in der Datei")]));
    }); },
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
      function sw(k, label, on) { var b = h("button", { type: "button", class: "btn" + (on ? " main" : ""), "aria-pressed": on ? "true" : "false", text: label + ": " + (on ? "an" : "aus"), onclick: function () { api("/api/admin/panel/flag", { method: "POST", body: { k: k, v: on ? "1" : "0" } }).then(function (r) { if (r.s === 200) LOAD.sw(); else msg(m, ERR[r.j.error] || "Fehler", true); }); } }); return b; }
      p.appendChild(h("p", {}, [sw("atr_off", "Neue Inhalte nach 24 Stunden übersetzen", f.atr_off !== "1"), " ", sw("tr_off", "Entitäten Englisch/Deutsch ergänzen", f.tr_off !== "1")]));
      var cap = h("input", { type: "number", min: "0", max: "2000", id: "adm-cap", value: f.atr_ent_cap || "300" });
      p.appendChild(h("p", {}, [h("label", { for: "adm-cap", text: "Tageslimit Entitäten-Übersetzungen " }), cap, " ", h("button", { type: "button", class: "btn", text: "Speichern", onclick: function () { api("/api/admin/panel/flag", { method: "POST", body: { k: "atr_ent_cap", v: String(Math.max(0, Math.min(2000, parseInt(cap.value, 10) || 0))) } }).then(function (r) { msg(m, r.s === 200 ? "Gespeichert." : (ERR[r.j.error] || "Fehler"), r.s !== 200); }); } })]));
      p.appendChild(m);
    }); },
    ent: function () { if (panes.ent.firstChild) return; entities(); }
  };

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
