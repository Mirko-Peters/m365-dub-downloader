/* Experten-Profil und Firmen-Konten bearbeiten (Community-Seite, nur eingeloggt). window.M365X = {api, base, lang}. Nur DOM-Knoten. */
(function () {
  var X = window.M365X, root = document.getElementById("c-expert"); if (!X || !root || /[?&]u=/.test(location.search)) return;
  var orgHost = document.createElement("div"); orgHost.id = "c-orgs"; root.parentNode.insertBefore(orgHost, root.nextSibling);
  (function tabs() {   // Reiter: Konto | Profil | Firmen | Events | Nachrichten
    var de0 = (X.lang || "en") === "de", T0 = [["c-page", de0 ? "Konto" : "Account"], ["c-expert", de0 ? "Profil" : "Profile"], ["c-orgs", de0 ? "Firmen" : "Companies"], ["c-events", "Events"], ["c-messages", de0 ? "Nachrichten" : "Messages"]];
    var bar = document.createElement("div"); bar.setAttribute("role", "tablist"); bar.className = "ctabs";
    function show(id) { T0.forEach(function (t) { var el = document.getElementById(t[0]); if (el) el.hidden = t[0] !== id; }); [].forEach.call(bar.children, function (b) { b.setAttribute("aria-selected", b.dataset.t === id ? "true" : "false"); }); try { history.replaceState(null, "", "#" + id); } catch (e) {} }
    T0.forEach(function (t) { var b = document.createElement("button"); b.type = "button"; b.className = "ctab"; b.setAttribute("role", "tab"); b.dataset.t = t[0]; b.textContent = t[1]; b.onclick = function () { show(t[0]); }; bar.appendChild(b); });
    var first = document.getElementById("c-page"); first.parentNode.insertBefore(bar, first);
    var h0 = (location.hash || "").slice(1); show(T0.some(function (t) { return t[0] === h0; }) ? h0 : "c-page");
    window.addEventListener("hashchange", function () { var x = location.hash.slice(1); if (T0.some(function (t) { return t[0] === x; })) show(x); });
  })();
  var de = X.lang === "de";
  var Q = de ? { bad_email: "Die E-Mail-Adresse ist ungültig.", h: "Öffentliches Experten-Profil", intro: "Freiwillig: Mit einem öffentlichen Profil erscheinst du im Mitgliederverzeichnis, bei deinen Themen und mit Verknüpfung zu den Schema.org-Entitäten. Programme und Expertise werden vom Redaktionsteam bestätigt oder von Mitgliedern gegengezeichnet.", pub: "Profil öffentlich anzeigen", handle: "Profil-Adresse (a-z, 0-9, -)", headline: "Kurzzeile (z. B. Power BI Berater, MVP)", about: "Über mich (Bio, ohne Links)", company: "Firma (Freitext)", job: "Position", country: "Land", showorg: "Firmenzugehörigkeit öffentlich zeigen", prog: "Microsoft-Programme", year: "Seit (Jahr)", proof: "Nachweis-Link (https)", exp: "Themen und Expertise", addexp: "Thema hinzufügen", lvl: ["Lerne", "Praxis", "Experte"], certs: "Zertifizierungen", addcert: "Zertifizierung hinzufügen", chan: "Kanäle und Links", addch: "Kanal hinzufügen", feedurl: "Feed-URL (RSS/Atom, optional)", save: "Profil speichern", saved: "Gespeichert.", err: "Etwas ist schiefgelaufen. Bitte prüfe deine Angaben.", rm: "Entfernen", pick: "Thema suchen…", url: "https://…", orgs: "Firmen", neworg: "Firma anlegen", orgname: "Firmenname", tagline: "Kurzbeschreibung", site: "Webseite", size: "Mitarbeitende", join: "Einer Firma beitreten", search: "Firma suchen…", req: "Beitritt anfragen", pending: "Offene Anfragen", team: "Team", approve: "Freigeben", remove: "Entfernen", pend_me: "Anfrage wartet auf Freigabe", leave: "Verlassen", edit: "Bearbeiten", open: "Öffentliche Seite", handle_taken: "Diese Adresse ist schon vergeben.", bad_handle: "Bitte eine Adresse mit 3–30 Zeichen (a-z, 0-9, -) angeben.", bad_channel: "Ein Kanal ist ungültig (https, passende Domain).", bad_expertise: "Ein Thema gibt es nicht.", bad_url: "Eine Adresse ist ungültig.", bad_cert: "Eine Zertifizierung ist ungültig.", rate_limit: "Zu viele Änderungen – bitte später erneut.", note: "Die öffentliche Seite erscheint nach dem nächsten Seitenbau (stündlich)." }
    : { bad_email: "The email address is invalid.", h: "Public expert profile", intro: "Optional: with a public profile you appear in the member directory, on your topics and linked to the Schema.org entities. Programs and expertise are confirmed by the editorial team or endorsed by members.", pub: "Show my profile publicly", handle: "Profile address (a-z, 0-9, -)", headline: "Headline (e.g. Power BI consultant, MVP)", about: "About me (bio, no links)", company: "Company (free text)", job: "Job title", country: "Country", showorg: "Show company membership publicly", prog: "Microsoft programs", year: "Since (year)", proof: "Proof link (https)", exp: "Topics and expertise", addexp: "Add topic", lvl: ["Learning", "Practitioner", "Expert"], certs: "Certifications", addcert: "Add certification", chan: "Channels and links", addch: "Add channel", feedurl: "Feed URL (RSS/Atom, optional)", save: "Save profile", saved: "Saved.", err: "Something went wrong. Please check your entries.", rm: "Remove", pick: "Search topic…", url: "https://…", orgs: "Companies", neworg: "Create a company", orgname: "Company name", tagline: "Tagline", site: "Website", size: "Employees", join: "Join a company", search: "Search company…", req: "Request to join", pending: "Open requests", team: "Team", approve: "Approve", remove: "Remove", pend_me: "Request awaiting approval", leave: "Leave", edit: "Edit", open: "Public page", handle_taken: "That address is already taken.", bad_handle: "Please use an address with 3–30 characters (a-z, 0-9, -).", bad_channel: "A channel is invalid (https, matching domain).", bad_expertise: "A topic does not exist.", bad_url: "An address is invalid.", bad_cert: "A certification is invalid.", rate_limit: "Too many changes – please try again later.", note: "The public page appears after the next site build (hourly)." };
  var PROG = [["mvp", "Microsoft MVP"], ["mct", "Microsoft Certified Trainer (MCT)"], ["rd", "Microsoft Regional Director"], ["msa", "Microsoft Student Ambassador"], ["ms_employee", de ? "Microsoft-Mitarbeiter:in" : "Microsoft employee"], ["partner", "Microsoft Partner"]];
  var KINDS = ["linkedin", "github", "youtube", "x", "mastodon", "bluesky", "twitch", "blog", "podcast", "newsletter", "website", "other"], KL = { linkedin: "LinkedIn", github: "GitHub", youtube: "YouTube", x: "X", mastodon: "Mastodon", bluesky: "Bluesky", twitch: "Twitch", blog: "Blog", podcast: "Podcast", newsletter: "Newsletter", website: "Website", other: "Link" };
  function h(tag, a, kids) { var e = document.createElement(tag); for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }); return e; }
  function api(path, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(X.api + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  var IQ = de ? { t: "Bild", up: "Bild hochladen", rm: "Entfernen", first: "Speichere zuerst dein Profil mit Profil-Adresse, dann kannst du ein Bild hochladen.", ok: "✓ Bild gespeichert.", bad: "Das Bild konnte nicht gespeichert werden (nur Bilddateien).", hint: "Wird auf 256×256 Pixel verkleinert und nur bei öffentlichem Profil angezeigt." } : { t: "Picture", up: "Upload picture", rm: "Remove", first: "Save your profile with a profile address first, then you can upload a picture.", ok: "✓ Picture saved.", bad: "The picture could not be saved (images only).", hint: "Resized to 256×256 pixels and shown only on public profiles." };
  function imgUI(kind, handle0, img0) {
    var w = h("div", { class: "pic" }), im = h("img", { alt: "", width: 96, height: 96, style: "border-radius:" + (kind === "u" ? "50%" : "12px") + ";object-fit:cover;background:var(--card);border:1px solid var(--bd)" }), msg = h("span", { class: "cmut", role: "status", "aria-live": "polite" });
    var f = h("input", { type: "file", accept: "image/png,image/jpeg,image/webp", "aria-label": IQ.up, style: "display:none" });
    function show(hd, v) { if (hd && v) { im.src = X.api + "/api/img/" + kind + "/" + hd + ".jpg?v=" + v; im.hidden = false; } else im.hidden = true; }
    show(handle0, img0);
    function resize(file) { return new Promise(function (res, rej) { var u = URL.createObjectURL(file), i = new Image(); i.onload = function () { var c = document.createElement("canvas"); c.width = c.height = 256; var g = c.getContext("2d"), m = Math.min(i.width, i.height), sx = (i.width - m) / 2, sy = (i.height - m) / 2; g.fillStyle = "#fff"; g.fillRect(0, 0, 256, 256); g.drawImage(i, sx, sy, m, m, 0, 0, 256, 256); URL.revokeObjectURL(u); var q = 0.88; (function t() { c.toBlob(function (b) { if (b && b.size > 140000 && q > 0.4) { q -= 0.15; t(); } else if (b) res(b); else rej(); }, "image/jpeg", q); })(); }; i.onerror = function () { rej(); }; i.src = u; }); }
    var up = h("button", { type: "button", class: "btn", text: IQ.up, onclick: function () { if (!w.handle()) { if (!w.ensure) { msg.textContent = IQ.first; return; } msg.textContent = "…"; w.ensure().then(function (ok) { if (ok) { msg.textContent = ""; f.click(); } else msg.textContent = IQ.first; }); return; } f.click(); } });
    var rm = h("button", { type: "button", class: "btn", text: IQ.rm, onclick: function () { api("/api/img/" + kind + "/" + w.handle(), { method: "DELETE" }).then(function () { show(null); msg.textContent = ""; }); } });
    f.addEventListener("change", function () {
      var file = f.files && f.files[0]; if (!file) return; msg.textContent = "…";
      resize(file).then(function (b) { return fetch(X.api + "/api/img/" + kind + "/" + w.handle(), { method: "POST", credentials: "include", headers: { "x-requested-with": "m365", "content-type": "image/jpeg" }, body: b }).then(function (r) { return r.json(); }); })
        .then(function (j) { if (j && j.ok) { show(w.handle(), j.img); msg.textContent = IQ.ok; } else msg.textContent = IQ.bad + (j && j.error ? " (" + j.error + ")" : ""); }).catch(function () { msg.textContent = IQ.bad; }); f.value = "";
    });
    w.handle = function () { return ""; };
    w.appendChild(h("label", { text: IQ.t, style: "display:block;margin-top:14px;font-weight:600" })); w.appendChild(h("div", { style: "display:flex;gap:12px;align-items:center;flex-wrap:wrap" }, [im, up, rm, f, msg])); w.appendChild(h("p", { class: "cmut", text: IQ.hint, style: "margin:4px 0 0;font-size:.85rem" }));
    return w;
  }
  var SQ = de ? { t: "Event-Sponsoring", d: "Nie öffentlich. Veranstalter, die Sponsoren suchen, sehen eure Kriterien – und ihr seht als potenzieller Sponsor, welche Events in Frage kommen, und könnt die Veranstalter direkt kontaktieren.", open: "Wir sind offen für Event-Sponsoring", topics: "Themen (z. B. Copilot, Security)", fmt: "Format", any: "egal", online: "Online", onsite: "Vor Ort", hybrid: "Hybrid", aud: "Mindestgröße Publikum", reg: "Regionen / Sprachen", bud: "Budgetrahmen (optional)", notes: "Weitere Kriterien", save: "Sponsoring speichern", saved: "✓ Gespeichert.", first: "Speichere die Firma zuerst, dann kannst du Sponsoring-Kriterien angeben." }
    : { t: "Event sponsoring", d: "Never public. Organizers who are looking for sponsors see your criteria – and as a potential sponsor you see which events qualify and can contact the organizers directly.", open: "We are open to sponsoring events", topics: "Topics (e.g. Copilot, security)", fmt: "Format", any: "any", online: "Online", onsite: "On site", hybrid: "Hybrid", aud: "Minimum audience size", reg: "Regions / languages", bud: "Budget range (optional)", notes: "Further criteria", save: "Save sponsoring", saved: "✓ Saved.", first: "Save the company first, then you can add sponsoring criteria." };
  function sponsorUI(getHandle) {
    var w = h("div", { class: "spons" }), msg = h("span", { class: "cmut", role: "status", "aria-live": "polite" });
    w.appendChild(h("h4", { text: SQ.t })); w.appendChild(h("p", { class: "cmut", text: SQ.d }));
    var on = h("input", { type: "checkbox" }), tp = inp(300), rg = inp(200), bd = inp(100), au = h("input", { type: "number", min: 0, max: 1000000 }), nt = h("textarea", { rows: 3, maxlength: 800 }), fm = h("select");
    [["", SQ.any], ["online", SQ.online], ["onsite", SQ.onsite], ["hybrid", SQ.hybrid]].forEach(function (x) { fm.appendChild(h("option", { value: x[0], text: x[1] })); });
    w.appendChild(h("label", { style: "display:block;margin:.4em 0" }, [on, " " + SQ.open]));
    [lab(SQ.topics, tp), lab(SQ.fmt, fm), lab(SQ.aud, au), lab(SQ.reg, rg), lab(SQ.bud, bd), lab(SQ.notes, nt)].forEach(function (x) { w.appendChild(x); });
    var loaded = "";
    function load() { var hd = getHandle(); if (!hd || hd === loaded) return; loaded = hd; api("/api/org/sponsor/" + hd).then(function (r) { if (r.s !== 200) return; on.checked = !!r.j.open; var c = r.j.criteria || {}; tp.value = c.topics || ""; fm.value = c.format || ""; au.value = c.min_audience || ""; rg.value = c.regions || ""; bd.value = c.budget || ""; nt.value = c.notes || ""; }); }
    load();
    w.appendChild(h("div", { class: "btns" }, [h("button", { type: "button", class: "btn", text: SQ.save, onclick: function () { var hd = getHandle(); if (!hd) { msg.textContent = SQ.first; return; } api("/api/org/sponsor/" + hd, { method: "POST", body: { open: on.checked, criteria: { topics: tp.value, format: fm.value, min_audience: +au.value || 0, regions: rg.value, budget: bd.value, notes: nt.value } } }).then(function (r) { msg.textContent = r.s === 200 ? SQ.saved : SQ.first; }); } }), msg]));
    return w;
  }
  var RIQ = de ? { t: "Empfehlungen für dich", none: "Noch keine Empfehlungen.", ok: "Freigeben", no: "Ablehnen", rm: "Entfernen", pend: "wartet auf Freigabe", live: "veröffentlicht" } : { t: "Recommendations for you", none: "No recommendations yet.", ok: "Approve", no: "Reject", rm: "Remove", pend: "awaiting approval", live: "published" };
  function recInbox() {
    var w = h("section", { class: "ccard" }, [h("h2", { text: RIQ.t })]);
    function load() { api("/api/recommend/inbox").then(function (r) { while (w.children.length > 1) w.removeChild(w.lastChild); var l = (r.j && r.j.items) || []; if (!l.length) w.appendChild(h("p", { class: "cmut", text: RIQ.none }));
      l.forEach(function (x) { var pend = x.status === "pending"; w.appendChild(h("div", { class: "ev-s" }, [h("b", { text: x.name }), h("span", { class: "cmut", text: " · " + x.relation + " · " + (pend ? RIQ.pend : RIQ.live) }), h("p", { text: x.body, style: "white-space:pre-line" }), h("div", { class: "btns" }, pend ? [
        h("button", { type: "button", class: "btn main", text: RIQ.ok, onclick: function () { api("/api/recommend/" + x.id, { method: "POST", body: { ok: true } }).then(load); } }),
        h("button", { type: "button", class: "btn", text: RIQ.no, onclick: function () { api("/api/recommend/" + x.id, { method: "POST", body: { ok: false } }).then(load); } })] : [
        h("button", { type: "button", class: "btn", text: RIQ.rm, onclick: function () { api("/api/recommend/" + x.id, { method: "DELETE" }).then(load); } })])])); }); }); }
    load(); return w;
  }
  var CQ = de ? { hint: "Deine Firma wählst du weiter unten bei „Firmen“: per Suche beitreten – gibt es sie noch nicht, legst du sie dort an. Firmen sind immer Entitäten, nie Freitext.", nf: "Keine Firma gefunden.", mk: "Firma anlegen", bad: "Die Firma konnte nicht angelegt werden – bitte den Namen prüfen." } : { hint: "You choose your company further down under “Companies”: join it via search – if it does not exist yet, create it there. Companies are always entities, never free text.", nf: "No company found.", mk: "Create company", bad: "The company could not be created – please check the name." };
  var uid = 0; function lab(text, el) { var id = "pe" + (++uid); el.id = id; return h("div", {}, [h("label", { for: id, text: text, style: "display:block;margin-top:.5em;font-weight:600" }), el]); }
  var inp = function (max, v) { var e = h("input", { type: "text", maxlength: max || 120 }); e.value = v || ""; return e; };
  var chk = function (text, v) { var c = h("input", { type: "checkbox" }); c.checked = !!v; return { c: c, w: h("label", { style: "display:block;margin:.4em 0" }, [c, " " + text]) }; };

  function programsUI(sel, orgSide) {
    var box = h("div", {}), rows = {};
    PROG.filter(function (p) { return orgSide ? p[0] === "partner" : true; }).forEach(function (p) {
      var cur = (sel || []).filter(function (x) { return x.p === p[0]; })[0] || {}, c = chk(p[1] + (cur.verified ? " ✔" : ""), !!cur.p), yr = h("input", { type: "number", min: 1990, max: 2100, "aria-label": Q.year, placeholder: Q.year, style: "width:7em" }), pr = h("input", { type: "text", maxlength: 300, placeholder: Q.proof, "aria-label": Q.proof });
      yr.value = cur.year || ""; pr.value = cur.url || ""; rows[p[0]] = { c: c.c, yr: yr, pr: pr };
      box.appendChild(h("div", { style: "margin:.5em 0" }, [c.w, h("div", { style: "display:flex;gap:.4em;flex-wrap:wrap" }, [yr, pr])]));
    });
    box.get = function () { return Object.keys(rows).filter(function (k) { return rows[k].c.checked; }).map(function (k) { return { p: k, year: +rows[k].yr.value || 0, url: rows[k].pr.value.trim() }; }); };
    return box;
  }
  function pickerRows(all, filter, initial, withYear, labelAdd, newType) {
    var wrap = h("div", {}), list = h("div"), dl = h("datalist", { id: "pdl" + (++uid) });
    all.filter(filter).forEach(function (x) { dl.appendChild(h("option", { value: x.name })); });
    var NQ = de ? { mk: "Gibt es noch nicht – als neue Entität anlegen", d: "Kurzbeschreibung (mind. 20 Zeichen, eigene Worte, ohne Links)", go: "Anlegen", live: "Angelegt und übernommen.", pend: "Danke! Der neue Eintrag erscheint nach der Prüfung; danach kannst du ihn auswählen.", err: "Konnte nicht angelegt werden: ", short: "Bitte mindestens 20 Zeichen." }
      : { mk: "Doesn't exist yet – create it as a new entity", d: "Short description (min. 20 characters, own words, no links)", go: "Create", live: "Created and selected.", pend: "Thank you! The new entry will appear after review; then you can select it.", err: "Could not be created: ", short: "Please enter at least 20 characters." };
    function slug(n) { return n.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48); }
    function add(it) {
      var name = h("input", { type: "text", list: dl.id, placeholder: Q.pick, "aria-label": Q.pick, maxlength: 80 }), lv = h("select", { "aria-label": Q.exp }), yr = h("input", { type: "number", min: 1990, max: 2100, "aria-label": Q.year, placeholder: Q.year, style: "width:6em" }), pr = h("input", { type: "text", maxlength: 300, placeholder: Q.proof, "aria-label": Q.proof });
      Q.lvl.forEach(function (l, i) { lv.appendChild(h("option", { value: i + 1, text: l })); }); lv.value = (it && it.level) || 2; yr.value = (it && it.year) || ""; pr.value = (it && it.url) || "";
      if (it && it.e) { var t = all.filter(function (x) { return x.id === it.e; })[0]; name.value = t ? t.name : it.e; }
      var stl = (withYear && it && it.e) ? h("span", { class: "cmut", text: it.verified ? (de ? "✔ geprüft" : "✔ verified") : (it.url ? (de ? "⏳ wird geprüft" : "⏳ under review") : (de ? "ohne Nachweis" : "no proof")) }) : null;
      var mkBox = h("div", { style: "flex-basis:100%", hidden: true }), mkBtn = h("button", { type: "button", class: "btn", hidden: true, text: NQ.mk });
      function matched() { var v = name.value.trim().toLowerCase(); return all.some(function (x) { return x.name.toLowerCase() === v; }); }
      function sync() { mkBtn.hidden = !name.value.trim() || matched(); if (mkBtn.hidden) mkBox.hidden = true; }
      name.addEventListener("input", sync);
      mkBtn.onclick = function () {
        mkBox.hidden = false; mkBox.textContent = "";
        var ta = h("textarea", { rows: 2, maxlength: 300, placeholder: NQ.d, "aria-label": NQ.d, style: "width:100%" }), go = h("button", { type: "button", class: "btn main", text: NQ.go }), ms = h("span", { class: "cmut" }), ty = h("select", { "aria-label": "Typ" });
        if (!newType) [["product", de ? "Produkt" : "Product"], ["platform", de ? "Plattform" : "Platform"], ["concept", de ? "Konzept / Thema" : "Concept / topic"], ["category", de ? "Kategorie" : "Category"]].forEach(function (o) { ty.appendChild(h("option", { value: o[0], text: o[1] })); });
        go.onclick = function () {
          var nm = name.value.trim(), dsc = ta.value.trim(); if (dsc.length < 20) { ms.textContent = NQ.short; return; }
          go.disabled = true;
          api("/api/entity", { method: "POST", body: { id: slug(nm), data: { name: nm, type: newType || ty.value, aliases: [], desc: de ? { en: "", de: dsc } : { en: dsc, de: "" }, rel: [] }, summary: "" } }).then(function (r) {
            go.disabled = false;
            if (r.s === 200 && r.j.status === "live") { var ne = { id: slug(nm), name: nm, type: newType || ty.value }; all.push(ne); dl.appendChild(h("option", { value: nm })); ms.textContent = NQ.live; mkBox.hidden = true; sync(); }
            else if (r.s === 200) { ms.textContent = NQ.pend; name.value = ""; sync(); }
            else ms.textContent = NQ.err + (r.j && r.j.error || "");
          }).catch(function () { go.disabled = false; ms.textContent = NQ.err; });
        };
        (newType ? [ta, go, ms] : [ty, ta, go, ms]).forEach(function (x) { mkBox.appendChild(x); });
      };
      var row = h("div", { style: "display:flex;gap:.4em;flex-wrap:wrap;margin:.3em 0" }, [name].concat(withYear ? [yr, pr] : [lv], stl ? [stl] : [], [h("button", { type: "button", class: "btn", text: Q.rm, onclick: function () { row.remove(); } }), mkBtn, mkBox]));
      row._get = function () { var v = name.value.trim().toLowerCase(), hit = all.filter(function (x) { return x.name.toLowerCase() === v; })[0]; if (!hit) return v ? null : false; return withYear ? { e: hit.id, year: +yr.value || 0, url: pr.value.trim() } : { e: hit.id, level: +lv.value }; };
      list.appendChild(row);
    }
    (initial || []).forEach(add);
    wrap.appendChild(dl); wrap.appendChild(list); wrap.appendChild(h("button", { type: "button", class: "btn", text: labelAdd, onclick: function () { add(null); } }));
    wrap.get = function () { var out = [], bad = false; [].slice.call(list.children).forEach(function (r) { var v = r._get(); if (v === null) bad = true; else if (v) out.push(v); }); return bad ? null : out; };
    return wrap;
  }
  function privateUI(pv) {
    pv = pv || {};
    var L = de ? { h: "Kontakt und Adresse (privat)", hint: "Diese Angaben sind standardmäßig nur für dich sichtbar und werden später für die Umkreissuche genutzt. Pro Feld bestimmst du, wer es sehen darf. „Kontakte“ wirkt, sobald es Kontakte gibt – bis dahin sieht es niemand außer dir.", city: "Stadt", zip: "Postleitzahl", street: "Straße und Hausnummer", email: "Kontakt-E-Mail", phone: "Mobilnummer", all: "Alle", contacts: "Nur Kontakte", none: "Niemand (nur ich)", vis: "Sichtbar für" }
      : { h: "Contact and address (private)", hint: "These details are visible only to you by default and will later be used for radius search. For each field you choose who may see it. “Contacts” takes effect once contacts exist – until then only you can see it.", city: "City", zip: "Postal code", street: "Street and number", email: "Contact email", phone: "Mobile number", all: "Everyone", contacts: "Contacts only", none: "Nobody (only me)", vis: "Visible to" };
    var F = ["city", "zip", "street", "email", "phone"], rows = {}, wrap = h("div", {}, [h("h3", { text: L.h }), h("p", { class: "cmut", text: L.hint })]);
    F.forEach(function (k) {
      var inp = h("input", { type: k === "email" ? "email" : "text", maxlength: k === "street" ? 120 : k === "email" ? 120 : k === "city" ? 80 : k === "zip" ? 10 : 30, autocomplete: "off" }), sel = h("select", { "aria-label": L.vis + ": " + L[k] });
      ["none", "contacts", "all"].forEach(function (v) { sel.appendChild(h("option", { value: v, text: L[v] })); });
      inp.value = pv[k] || ""; sel.value = pv["vis_" + k] || "none"; rows[k] = [inp, sel];
      wrap.appendChild(h("div", {}, [lab(L[k], inp), h("label", { class: "cmut", style: "display:block;margin:.2em 0 .6em" }, [document.createTextNode(L.vis + ": "), sel])]));
    });
    wrap.get = function () { var o = { vis: {} }; F.forEach(function (k) { o[k] = rows[k][0].value.trim(); o.vis[k] = rows[k][1].value; }); return o; };
    return wrap;
  }
  function channelsUI(initial) {
    var wrap = h("div"), list = h("div");
    function add(c) {
      var k = h("select", { "aria-label": Q.chan }); KINDS.forEach(function (x) { k.appendChild(h("option", { value: x, text: KL[x] })); }); k.value = (c && c.kind) || "linkedin";
      var u = h("input", { type: "text", maxlength: 300, placeholder: Q.url, "aria-label": Q.url }), f = h("input", { type: "text", maxlength: 300, placeholder: Q.feedurl, "aria-label": Q.feedurl });
      u.value = (c && c.url) || ""; f.value = (c && c.feed && !/youtube\.com\/feeds/.test(c.feed) ? c.feed : "") || "";
      var row = h("div", { style: "display:flex;gap:.4em;flex-wrap:wrap;margin:.3em 0" }, [k, u, f, h("button", { type: "button", class: "btn", text: Q.rm, onclick: function () { row.remove(); } })]);
      row._get = function () { return u.value.trim() ? { kind: k.value, url: u.value.trim(), feed: f.value.trim() } : null; }; list.appendChild(row);
    }
    (initial || []).forEach(add); wrap.appendChild(list); wrap.appendChild(h("button", { type: "button", class: "btn", text: Q.addch, onclick: function () { add(null); } }));
    wrap.get = function () { return [].slice.call(list.children).map(function (r) { return r._get(); }).filter(Boolean); }; return wrap;
  }
  function saveBtn(label, fn, msg) { var b = h("button", { type: "button", class: "btn main", text: label, onclick: function () { b.disabled = true; msg.textContent = ""; fn().then(function (r) { b.disabled = false; if (r) msg.textContent = r.s === 200 ? "✓ " + Q.saved : (Q[r.j.error] || Q.err); }).catch(function (e) { try { console.error(e); } catch (x) {} b.disabled = false; msg.textContent = Q.err; }); } }); return b; }

  function orgForm(all, org, onDone) {
    var o = org || {}, f = h("div", { class: "wk-form" }), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    var handle = inp(30, o.handle), name = inp(80, o.name), tag = inp(120, o.tagline), about = h("textarea", { rows: 4, maxlength: 1500 }), site = inp(250, o.website), country = inp(60, o.country), size = h("select");
    about.value = o.about || ""; ["", "1", "2-10", "11-50", "51-200", "201-1000", "1000+"].forEach(function (s) { size.appendChild(h("option", { value: s, text: s || "–" })); }); size.value = o.size || "";
    if (org) handle.disabled = true;
    var pub = chk(Q.pub, o.public), prog = programsUI(o.programs, true), ex = pickerRows(all, function (x) { return ["product", "platform", "concept", "category"].indexOf(x.type) > -1; }, (o.expertise || []).map(function (x) { return { e: x.e, level: x.level }; }), false, Q.addexp), ch = channelsUI(o.channels);
    var pic = imgUI("o", o.handle, o.img); pic.handle = function () { return o.handle || ""; }; pic.ensure = function () { if (!handle.value.trim() || !name.value.trim()) return Promise.resolve(false); mainSave.click(); return new Promise(function (res) { var n = 0, t = setInterval(function () { if (++n > 6) { clearInterval(t); res(true); } }, 500); }); };
    [pub.w, pic, lab(Q.handle, handle), lab(Q.orgname, name), lab(Q.tagline, tag), lab(de ? "Über uns (ohne Links)" : "About us (no links)", about), lab(Q.site, site), lab(Q.country, country), lab(Q.size, size), h("h4", { text: Q.prog }), prog, h("h4", { text: Q.exp }), ex, h("h4", { text: Q.chan }), ch, sponsorUI(function () { return o.handle || ""; })].forEach(function (x) { f.appendChild(x); });
    var mainSave = saveBtn(Q.save, function () {
      var e = ex.get(); if (e === null) { msg.textContent = Q.bad_expertise; return Promise.resolve(null); }
      o.handle = handle.value.trim().toLowerCase();
      return api("/api/org", { method: "POST", body: { handle: handle.value.trim().toLowerCase(), name: name.value, tagline: tag.value, about: about.value, website: site.value.trim(), country: country.value, size: size.value, public: pub.c.checked, programs: prog.get(), expertise: e, channels: ch.get() } }).then(function (r) { if (r.s === 200 && onDone) onDone(); return r; });
    }, msg); f.appendChild(h("div", { class: "btns" }, [mainSave])); f.appendChild(msg); return f;
  }

  Promise.all([api("/api/profile/me"), fetch(X.base + "/entities.json").then(function (r) { return r.json(); }), api("/api/org/mine")]).then(function (a) {
    if (a[0].s !== 200) return; var me = a[0].j, all = (a[1].entities || []), p = me.profile || {}, orgs = (a[2].j.orgs || []);
    var sec = h("section", { class: "ccard" }, [h("h2", { text: Q.h }), h("p", { class: "cmut", text: Q.intro })]), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    var pub = chk(Q.pub, p.public), handle = inp(30, p.handle || me.suggest), head = inp(100, p.headline), about = h("textarea", { rows: 6, maxlength: 1500 }), company = inp(80, p.company_eid ? ((all.filter(function (x) { return x.id === p.company_eid; })[0] || {}).name || p.company) : ""), job = inp(80, p.job), country = inp(60, p.country), so = chk(Q.showorg, p.show_org !== false);
    about.value = p.about || "";
    var prog = programsUI(p.programs, false), ex = pickerRows(all, function (x) { return ["cert", "person", "event", "media"].indexOf(x.type) < 0; }, (p.expertise || []).map(function (x) { return { e: x.e, level: x.level }; }), false, Q.addexp);
    var privUI = privateUI(p.private), cert = pickerRows(all, function (x) { return x.type === "cert"; }, (p.certs || []).map(function (x) { return { e: x.e, year: x.year, url: x.url, verified: x.verified }; }), true, Q.addcert, "cert"), ch = channelsUI(p.channels);
    var pic = imgUI("u", p.handle, p.img); pic.handle = function () { return p.handle || ""; }; pic.ensure = function () { if (!handle.value.trim()) return Promise.resolve(false); mainSave.click(); return new Promise(function (res) { var n = 0, t = setInterval(function () { if (p.handle || ++n > 30) { clearInterval(t); res(!!p.handle); } }, 200); }); };
    [pub.w, pic, lab(Q.handle, handle), lab(Q.headline, head), lab(Q.about, about), h("p", { class: "cmut", text: CQ.hint }), lab(Q.job, job), lab(Q.country, country), so.w, h("h3", { text: Q.prog }), prog, h("h3", { text: Q.exp }), ex, privUI, h("h3", { text: Q.certs }), h("p", { class: "cmut", text: de ? "Trage als Nachweis den Link zu deinem Credly-Abzeichen oder Microsoft-Learn-Zertifikat ein. Passen Zertifikat und dein Name, wird es automatisch geprüft; sonst prüft die Redaktion. Geprüfte Zertifikate berechtigen dich, verbundene Themen direkt zu bearbeiten und darüber abzustimmen. Andere Mitglieder können dein Zertifikat bestätigen; die meistbestätigten stehen zuerst." : "Add the link to your Credly badge or Microsoft Learn credential as proof. If certificate and your name match, it is verified automatically; otherwise the editorial team reviews it. Verified certificates let you edit and vote on linked topics directly. Other members can confirm your certificate; the most confirmed come first." }), cert, h("h3", { text: Q.chan }), ch].forEach(function (x) { sec.appendChild(x); });
    var mainSave = saveBtn(Q.save, function () {
      var e = ex.get(), c = cert.get(); if (e === null) { msg.textContent = Q.bad_expertise; return Promise.resolve(null); } if (c === null) { msg.textContent = Q.bad_cert; return Promise.resolve(null); }
      return Promise.resolve(true).then(function (okc) { return api("/api/profile/me", { method: "POST", body: { private: privUI.get(), public: pub.c.checked, handle: handle.value.trim().toLowerCase(), headline: head.value, about: about.value, company: company.value, job: job.value, country: country.value, show_org: so.c.checked, programs: prog.get(), expertise: e, certs: c, channels: ch.get() } }).then(function (r) {
        if (r.s === 200) { p.handle = handle.value.trim().toLowerCase(); msg.textContent = "✓ " + Q.saved + " " + Q.note; } return null; }); });
    }, msg); sec.appendChild(h("div", { class: "btns" }, [mainSave]));
    sec.appendChild(msg);
    if (p.public && p.handle) sec.appendChild(h("p", {}, [h("a", { href: X.base + (de ? "/de" : "") + "/community/u/" + p.handle + "/", text: Q.open })]));
    root.appendChild(sec); if (p.handle) root.appendChild(recInbox());
    // ---- Firmen ----
    var os = h("section", { class: "ccard" }, [h("h2", { text: Q.orgs })]);
    orgs.forEach(function (o) {
      var d = h("details", { class: "wk-edit" }, [h("summary", { text: o.name + " · " + o.role + (o.status === "pending" ? " · " + Q.pend_me : "") })]);
      if (o.status === "active") {
        d.appendChild(h("p", {}, [h("a", { href: X.base + (de ? "/de" : "") + "/community/c/" + o.handle + "/", text: Q.open })]));
        if (o.org && (o.role === "owner" || o.role === "admin")) {
          if ((o.pending || []).length) { d.appendChild(h("h4", { text: Q.pending })); o.pending.forEach(function (m) { d.appendChild(h("p", {}, [m.name + " ", h("button", { type: "button", class: "btn main", text: Q.approve, onclick: function () { api("/api/org/" + o.handle + "/member", { method: "POST", body: { user_id: m.user_id, action: "approve" } }).then(function () { location.reload(); }); } })])); }); }
          d.appendChild(h("h4", { text: Q.team })); (o.team || []).forEach(function (m) { d.appendChild(h("p", {}, [m.name + " · " + m.role + " ", m.role === "owner" ? null : h("button", { type: "button", class: "btn", text: Q.remove, onclick: function () { api("/api/org/" + o.handle + "/member", { method: "POST", body: { user_id: m.user_id, action: "remove" } }).then(function () { location.reload(); }); } })])); });
          d.appendChild(orgForm(all, o.org, null));
        }
      }
      d.appendChild(h("button", { type: "button", class: "btn", text: Q.leave, onclick: function () { api("/api/org/" + o.handle + "/leave", { method: "POST" }).then(function () { location.reload(); }); } }));
      os.appendChild(d);
    });
    var nd = h("details", { class: "wk-edit" }, [h("summary", { text: Q.neworg })]); nd.appendChild(orgForm(all, null, function () { setTimeout(function () { location.reload(); }, 600); })); os.appendChild(nd);
    var jd = h("details", { class: "wk-edit" }, [h("summary", { text: Q.join })]), q = inp(40, ""), res = h("ul"), jm = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    q.setAttribute("placeholder", Q.search); q.setAttribute("aria-label", Q.search); var t;
    q.addEventListener("input", function () { clearTimeout(t); t = setTimeout(function () { api("/api/orgs/search?q=" + encodeURIComponent(q.value)).then(function (r) { res.textContent = ""; if (!(r.j.items || []).length && q.value.trim().length > 1) res.appendChild(h("li", {}, [CQ.nf + " ", h("button", { type: "button", class: "btn main", text: CQ.mk + ": " + q.value.trim(), onclick: function () { nd.open = true; var ins = nd.querySelectorAll("input[type=text]"); if (ins[1]) { ins[1].value = q.value.trim(); } nd.scrollIntoView({ behavior: "smooth" }); } })])); (r.j.items || []).forEach(function (o) { res.appendChild(h("li", {}, [o.name + " ", h("button", { type: "button", class: "btn", text: Q.req, onclick: function () { api("/api/org/" + o.handle + "/join", { method: "POST" }).then(function (x) { jm.textContent = x.s === 200 ? "✓ " + Q.pend_me : Q.err; }); } })])); }); }); }, 300); });
    [q, res, jm].forEach(function (x) { jd.appendChild(x); }); os.appendChild(jd);
    (orgHost || root).appendChild(os);
  }).catch(function () {});
})();
