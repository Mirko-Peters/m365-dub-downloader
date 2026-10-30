/* Events: anlegen, Sessions (Speaker), Vorschläge freigeben, Sponsoren-Ansicht für Veranstalter */
(function () {
  var X = window.M365X, root = document.getElementById("c-events"); if (!X || !root) return;
  var de = X.lang === "de";
  var Q = de ? { h: "Events", intro: "Als Veranstalter Events eintragen (Mitglieder, Firmen und Events sind getrennte Bereiche) und Sessions mit Speakern pflegen. Speaker können Sessions vorschlagen, der Veranstalter gibt sie frei.", login: "Zum Verwalten bitte oben anmelden.", mine: "Meine Events", newev: "Neues Event", title: "Titel", handle: "Adresse (a-z, 0-9, -)", summary: "Kurzbeschreibung", about: "Beschreibung (ohne Links)", start: "Beginn (JJJJ-MM-TT oder JJJJ-MM-TTTHH:MM)", end: "Ende (optional)", mode: "Format", online: "Online", onsite: "Vor Ort", hybrid: "Hybrid", loc: "Ort", country: "Land", url: "Webseite (https)", tickets: "Anmelde-/Ticket-Link (https)", free: "Kostenlos", lang: "Sprache (z. B. de)", topics: "Themen (aus der Entitätsdatenbank wählen)", seeking: "Wir suchen Sponsoren (nur für Veranstalter-Ansicht, Firmen sehen das nicht öffentlich)", org: "Veranstalter", me: "Ich selbst", save: "Event speichern", saved: "✓ Gespeichert.", del: "Event löschen", err: "Das hat nicht geklappt – bitte Eingaben prüfen.", sess: "Sessions", sadd: "Session hinzufügen", stitle: "Session-Titel", abstract: "Abstract (ohne Links)", sstart: "Beginn (optional)", room: "Raum", track: "Track", level: "Level", spk: "Speaker (Profil-Adresse oder Name, Komma getrennt)", rec: "Aufzeichnung (https, optional)", pending: "Vorschläge zur Freigabe", ok: "Freigeben", no: "Ablehnen", rm: "Löschen", propose: "Session vorschlagen", proposed: "✓ Vorschlag gesendet – der Veranstalter entscheidet.", sponsors: "Firmen, die Sponsoring anbieten", sp_none: "Noch keine Firma hat Sponsoring aktiviert.", pick: "Event wählen", ask: "Anfragen", askhint: "{f} Wunschfirmen pro Event sind frei, jede weitere kostet {c} Punkte.", asktxt: "Hallo, wir organisieren „{e}“ und suchen Sponsoren. Passt das zu euch?", asked: "angefragt", needpts: "Nicht genug Punkte.", askdone: "✓ Anfrage gesendet.", already: "Bereits angefragt.", forsp: "Events, die Sponsoren suchen", contact: "Kontakt aufnehmen", fmatch: "passt zu deinen Kriterien", spk_hint: "Format: Profil-Adresse, oder Name, oder Name|entitäten-id. Jeder Speaker muss die Teilnahme selbst bestätigen.", asked: "angefragt", declined: "abgelehnt", mail: "Per E-Mail", mailto: "E-Mail-Adresse des Speakers", mailok: "✓ E-Mail gesendet.", mailerr: "E-Mail konnte nicht gesendet werden – nimm den Link oder LinkedIn.", li: "Für LinkedIn kopieren", litxt: "Hallo {n}, ich würde dich gern als Speaker für „{e}“ einladen. Bitte bestätige hier deine Teilnahme: {u}", invlink: "Einladungslink kopieren", copied: "Link kopiert", req: "Anfragen als Speaker", req_none: "", conf: "Teilnahme bestätigen", decl: "Ablehnen", signin: "Anmelden mit", linkgo: "Profil anlegen und als Speaker verknüpfen", linkbusy: "Wird verknüpft …", linkdone: "✓ Fertig! Dein Profil ist jetzt mit der Session verknüpft.", linkview: "Zu deinem Profil", invt: "Einladung als Speaker", invtxt: "Du bist als Speaker für „{s}“ bei {e} eingetragen. Melde dich an, lege dein öffentliches Profil an und bestätige: Dann wird dein Profil mit dieser Session und deinem Speaker-Eintrag verknüpft, die Session erscheint auf deinem Profil und die Themen der Session werden als bestätigte Expertise übernommen.", needlogin: "Bitte melde dich oben an, um zu bestätigen.", needprof: "Lege zuerst ein öffentliches Profil an (unten), dann kannst du bestätigen.", thanks: "✓ Danke, deine Teilnahme ist bestätigt." }
    : { h: "Events", intro: "Add events as an organizer (members, companies and events are separate areas) and manage sessions with speakers. Speakers can propose sessions; the organizer approves them.", login: "Please sign in above to manage events.", mine: "My events", newev: "New event", title: "Title", handle: "Address (a-z, 0-9, -)", summary: "Short description", about: "Description (no links)", start: "Start (YYYY-MM-DD or YYYY-MM-DDTHH:MM)", end: "End (optional)", mode: "Format", online: "Online", onsite: "On site", hybrid: "Hybrid", loc: "Location", country: "Country", url: "Website (https)", tickets: "Registration / ticket link (https)", free: "Free", lang: "Language (e.g. en)", topics: "Topics (pick from the entity database)", seeking: "We are looking for sponsors (only shown to organizers, never public)", org: "Organizer", me: "Myself", save: "Save event", saved: "✓ Saved.", del: "Delete event", err: "That did not work – please check your input.", sess: "Sessions", sadd: "Add session", stitle: "Session title", abstract: "Abstract (no links)", sstart: "Start (optional)", room: "Room", track: "Track", level: "Level", spk: "Speakers (profile address or name, comma separated)", rec: "Recording (https, optional)", pending: "Proposals awaiting approval", ok: "Approve", no: "Reject", rm: "Delete", propose: "Propose a session", proposed: "✓ Proposal sent – the organizer decides.", sponsors: "Companies offering sponsorship", sp_none: "No company has enabled sponsoring yet.", pick: "Choose event", ask: "Ask", askhint: "{f} wish companies per event are free, every further one costs {c} points.", asktxt: "Hello, we are organizing “{e}” and are looking for sponsors. Would this fit you?", asked: "asked", needpts: "Not enough points.", askdone: "✓ Request sent.", already: "Already asked.", forsp: "Events looking for sponsors", contact: "Get in touch", fmatch: "fits your criteria", spk_hint: "Format: profile address, or name, or name|entity-id. Every speaker has to confirm participation themselves.", asked: "requested", declined: "declined", mail: "By email", mailto: "Speaker email address", mailok: "✓ Email sent.", mailerr: "Email could not be sent – use the link or LinkedIn.", li: "Copy for LinkedIn", litxt: "Hi {n}, I would love to invite you as a speaker for \"{e}\". Please confirm your participation here: {u}", invlink: "Copy invite link", copied: "Link copied", req: "Speaker requests", req_none: "", conf: "Confirm participation", decl: "Decline", signin: "Sign in with", linkgo: "Create my profile and link me as speaker", linkbusy: "Linking …", linkdone: "✓ Done! Your profile is now linked to the session.", linkview: "Go to your profile", invt: "Speaker invitation", invtxt: "You are listed as a speaker for “{s}” at {e}. Sign in, create your public profile and confirm: your profile is then linked to this session and your speaker entry, the session appears on your profile and the session topics are added as confirmed expertise.", needlogin: "Please sign in above to confirm.", needprof: "Create a public profile first (below), then you can confirm.", thanks: "✓ Thanks, your participation is confirmed." };
  function h(tag, a, kids) { var e = document.createElement(tag); for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }); return e; }
  function api(path, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(X.api + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  var uid = 0;
  function lab(text, el) { var id = "ev" + (++uid); el.id = id; return h("div", {}, [h("label", { for: id, text: text }), el]); }
  function inp(v, max, type) { var e = h("input", { type: type || "text", maxlength: max || 200 }); e.value = v || ""; return e; }
  function sel(opts, v) { var e = h("select"); opts.forEach(function (o) { e.appendChild(h("option", { value: o[0], text: o[1] })); }); e.value = v || opts[0][0]; return e; }
  var ENTS = null;
  function entList() { return ENTS ? Promise.resolve(ENTS) : fetch("/entities.json").then(function (r) { return r.json(); }).then(function (j) { ENTS = (j.entities || []).filter(function (x) { return ["product", "platform", "concept", "category", "cert"].indexOf(x.type) > -1; }); return ENTS; }).catch(function () { ENTS = []; return ENTS; }); }
  var TYPEL = { product: de ? "Produkt" : "Product", platform: de ? "Plattform" : "Platform", concept: de ? "Konzept" : "Concept", category: de ? "Kategorie" : "Category", cert: de ? "Zertifikat" : "Certification" };
  // Themen-Auswahl: Entitaeten (Produkt, Plattform, Konzept ...) per Suchfeld waehlen statt IDs tippen
  function topicsUI(initial) {
    var ids = (initial || []).slice(), chips = h("div", { style: "display:flex;gap:.4em;flex-wrap:wrap;margin:.3em 0" }), dl = h("datalist", { id: "tdl" + (++uid) }), box = h("input", { type: "text", list: dl.id, maxlength: 80, placeholder: de ? "Thema suchen (Produkt, Plattform, Konzept …)" : "Search a topic (product, platform, concept …)", "aria-label": de ? "Thema suchen" : "Search a topic" });
    var wrap = h("div", {}, [chips, box, dl]), byLabel = {};
    function name(id) { var e = (ENTS || []).filter(function (x) { return x.id === id; })[0]; return e ? e.name : id; }
    function draw() { chips.textContent = ""; ids.forEach(function (id) { chips.appendChild(h("button", { type: "button", class: "btn", title: de ? "Entfernen" : "Remove", text: name(id) + " ✕", onclick: function () { ids = ids.filter(function (x) { return x !== id; }); draw(); } })); }); }
    entList().then(function (list) { list.forEach(function (e) { var l = e.name + " · " + (TYPEL[e.type] || e.type); byLabel[l.toLowerCase()] = e.id; byLabel[e.name.toLowerCase()] = e.id; dl.appendChild(h("option", { value: l })); }); draw(); });
    function add() { var id = byLabel[box.value.trim().toLowerCase()]; if (id && ids.indexOf(id) < 0 && ids.length < 12) { ids.push(id); draw(); } if (id) box.value = ""; }
    box.addEventListener("change", add); box.addEventListener("input", function () { if (byLabel[box.value.trim().toLowerCase()]) add(); });
    draw(); wrap.get = function () { add(); return ids.slice(); }; return wrap;
  }
  function csv(s) { return String(s || "").split(",").map(function (x) { return x.trim(); }).filter(Boolean); }
  function spk(list) { return csv(list).map(function (x) { var p = x.split("|"), e = (p[1] || "").trim().toLowerCase(); if (/^[a-z0-9][a-z0-9-]{2,29}$/.test(p[0].trim()) && !e) return { h: p[0].trim() }; return e ? { n: p[0].trim(), e: e } : { n: p[0].trim() }; }); }
  function spkStr(l) { return (l || []).map(function (x) { return x.h || (x.n + (x.e ? "|" + x.e : "")); }).join(", "); }
  function spkLabel(l) { return (l || []).map(function (x) { return (x.n || x.h) + (x.s && x.s !== "confirmed" ? " (" + (x.s === "declined" ? Q.declined : Q.asked) + ")" : ""); }).join(", "); }
  function invLinks(l, st) { var out = []; (l || []).forEach(function (x) { if (x.t && (x.s !== "confirmed" || x.o)) { var url = location.origin + location.pathname + "?invite=" + x.t + "#c-events", note = h("span", { class: "cmut" }), em = h("input", { type: "email", maxlength: 120, placeholder: Q.mailto, "aria-label": Q.mailto });
    function cp(txt, el) { try { navigator.clipboard.writeText(txt); el.textContent = Q.copied; } catch (er) { window.prompt(Q.invlink, txt); } }
    out.push(h("div", { class: "cmut" }, [x.n + ": ",
      h("button", { type: "button", class: "btn", text: Q.invlink, onclick: function (e) { cp(url, e.target); } }), " ",
      h("button", { type: "button", class: "btn", text: Q.li, onclick: function (e) { cp(Q.litxt.replace("{n}", x.n).replace("{e}", (st && st.value) || "").replace("{u}", url), e.target); window.open("https://www.linkedin.com/messaging/", "_blank", "noopener"); } }), " ",
      em, " ", h("button", { type: "button", class: "btn", text: Q.mail, onclick: function () { api("/api/speaker/invite-send", { method: "POST", body: { token: x.t, email: em.value } }).then(function (r) { note.textContent = r.s === 200 ? Q.mailok : Q.mailerr; }); } }), " ", note])); } }); return out; }

  function sessionForm(ev, s, done, propose) {
    var f = h("div", { class: "wk-form" }), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    s = s || {};
    var t = inp(s.title, 140), ab = h("textarea", { rows: 3, maxlength: 1500 }), st = inp(s.start, 16), room = inp(s.room, 60), track = inp(s.track, 60), lv = sel([["", "–"], ["100", "100"], ["200", "200"], ["300", "300"], ["400", "400"]], s.level), sp = inp(spkStr(s.speakers), 300), tp = topicsUI(s.topics || []), rec = inp(s.recording_url, 300), lg = inp(s.lang, 10);
    ab.value = s.abstract || "";
    var inv = invLinks(s.speakers, t);
    [lab(Q.stitle, t), lab(Q.abstract, ab), lab(Q.spk, sp), h("p", { class: "cmut", text: Q.spk_hint }), lab(Q.sstart, st), lab(Q.room, room), lab(Q.track, track), lab(Q.level, lv), lab(Q.lang, lg), lab(Q.topics, tp), lab(Q.rec, rec)].concat(inv).forEach(function (x) { f.appendChild(x); });
    f.appendChild(h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: propose ? Q.propose : Q.save, onclick: function () {
      api("/api/event/" + ev.handle + "/session", { method: "POST", body: { id: s.id, title: t.value, abstract: ab.value, speakers: spk(sp.value), start: st.value.trim(), room: room.value, track: track.value, level: lv.value, lang: lg.value.trim(), topics: tp.get(), recording_url: rec.value.trim() } }).then(function (r) {
        if (r.s === 200) { msg.textContent = r.j.status === "pending" ? Q.proposed : Q.saved; if (done) done(); } else msg.textContent = Q.err; }); } }), msg]));
    return f;
  }
  function eventCard(ev, orgs, reload) {
    var d = h("details", { class: "wk-edit" }, [h("summary", { text: ev.title + " · " + ev.start })]), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    var f = h("div", { class: "wk-form" });
    var hd = inp(ev.handle, 40); hd.disabled = !!ev.handle;
    var t = inp(ev.title, 120), sm = inp(ev.summary, 200), ab = h("textarea", { rows: 5, maxlength: 3000 }), st = inp(ev.start, 16), en = inp(ev.end, 16), md = sel([["online", Q.online], ["onsite", Q.onsite], ["hybrid", Q.hybrid]], ev.mode), lc = inp(ev.location, 120), ct = inp(ev.country, 60), u = inp(ev.url, 300), tk = inp(ev.tickets_url, 300), lg = inp(ev.lang, 10), tp = topicsUI(ev.topics || []);
    ab.value = ev.about || "";
    var fr = h("input", { type: "checkbox" }); fr.checked = ev.handle ? !!ev.free : true; var sk = h("input", { type: "checkbox" }); sk.checked = !!ev.seeking_sponsor;
    var os = sel([["", Q.me]].concat((orgs || []).map(function (o) { return [o.handle, o.name]; })), ev.organizer && ev.organizer.kind === "o" ? ev.organizer.handle : "");
    [lab(Q.title, t), lab(Q.handle, hd), lab(Q.summary, sm), lab(Q.about, ab), lab(Q.start, st), lab(Q.end, en), lab(Q.mode, md), lab(Q.loc, lc), lab(Q.country, ct), lab(Q.url, u), lab(Q.tickets, tk), lab(Q.lang, lg), lab(Q.topics, tp), lab(Q.org, os)].forEach(function (x) { f.appendChild(x); });
    f.appendChild(h("label", {}, [fr, " " + Q.free])); f.appendChild(h("label", {}, [sk, " " + Q.seeking]));
    f.appendChild(h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: Q.save, onclick: function () {
      api("/api/event", { method: "POST", body: { handle: (ev.handle || hd.value).trim().toLowerCase(), title: t.value, summary: sm.value, about: ab.value, start: st.value.trim(), end: en.value.trim(), mode: md.value, location: lc.value, country: ct.value, url: u.value.trim(), tickets_url: tk.value.trim(), free: fr.checked, lang: lg.value.trim(), topics: tp.get(), seeking_sponsor: sk.checked, org: os.value || undefined } }).then(function (r) { msg.textContent = r.s === 200 ? Q.saved : Q.err; if (r.s === 200 && !ev.handle) reload(); }); } }),
      ev.handle ? h("button", { type: "button", class: "btn", text: Q.del, onclick: function () { if (confirm(Q.del + "?")) api("/api/event/" + ev.handle, { method: "DELETE" }).then(reload); } }) : null, msg]));
    d.appendChild(f);
    if (ev.handle) {
      d.appendChild(h("h4", { text: Q.sess }));
      var pend = (ev.sessions || []).filter(function (s) { return s.status === "pending"; }), live = (ev.sessions || []).filter(function (s) { return s.status !== "pending"; });
      if (pend.length) { d.appendChild(h("h4", { text: Q.pending })); pend.forEach(function (s) { d.appendChild(h("div", { class: "ev-s" }, [h("b", { text: s.title }), h("span", { class: "cmut", text: " · " + spkStr(s.speakers) }), h("div", { class: "btns" }, [
        h("button", { type: "button", class: "btn main", text: Q.ok, onclick: function () { api("/api/event/" + ev.handle + "/session/" + s.id + "/approve", { method: "POST", body: { ok: true } }).then(reload); } }),
        h("button", { type: "button", class: "btn", text: Q.no, onclick: function () { api("/api/event/" + ev.handle + "/session/" + s.id + "/approve", { method: "POST", body: { ok: false } }).then(reload); } })])])); }); }
      live.forEach(function (s) { var dd = h("details", {}, [h("summary", { text: s.title + (s.speakers.length ? " · " + spkLabel(s.speakers) : "") })]); dd.appendChild(sessionForm(ev, s, reload)); dd.appendChild(h("button", { type: "button", class: "btn", text: Q.rm, onclick: function () { api("/api/event/" + ev.handle + "/session/" + s.id, { method: "DELETE" }).then(reload); } })); d.appendChild(dd); });
      var add = h("details", {}, [h("summary", { text: Q.sadd })]); add.appendChild(sessionForm(ev, null, reload)); d.appendChild(add);
      d.appendChild(teamBox(ev));
    }
    return d;
  }
  var RL = de ? { organisator: "Organisator", "co-organisator": "Co-Organisator", "programm-manager": "Programm-Manager", "sponsor-manager": "Sponsoren-Manager", kommunikation: "Kommunikation", helfer: "Helfer" } : { organisator: "Organiser", "co-organisator": "Co-organiser", "programm-manager": "Programme manager", "sponsor-manager": "Sponsor manager", kommunikation: "Communications", helfer: "Helper" };
  var TQ = de ? { h: "Team und Rollen", hint: "Organisator: alles. Co-Organisator: Event, Programm, Sponsoring, Rollen. Programm-Manager: Sessions. Sponsoren-Manager: Sponsoren-Anfragen. Kommunikation: Texte und Links. Helfer: nur im Team genannt.", handle: "Profil-Adresse des Mitglieds", add: "Hinzufügen", rm: "Entfernen", err: "Hat nicht geklappt (Profil öffentlich? Recht vorhanden?)" } : { h: "Team and roles", hint: "Organiser: everything. Co-organiser: event, programme, sponsoring, roles. Programme manager: sessions. Sponsor manager: sponsor requests. Communications: texts and links. Helper: listed in the team only.", handle: "Member profile address", add: "Add", rm: "Remove", err: "That did not work (public profile? permission?)" };
  function teamBox(ev) {
    var box = h("div", { class: "ev-team" }, [h("h4", { text: TQ.h }), h("p", { class: "cmut", text: TQ.hint })]), list = h("ul", {});
    var hd = h("input", { type: "text", placeholder: TQ.handle }), rs = sel(Object.keys(RL).map(function (k) { return [k, RL[k]]; }), "helfer"), msg = h("span", { class: "cmut" });
    function load() { api("/api/event/" + ev.handle + "/team").then(function (r) { list.innerHTML = ""; (r.j.team || []).forEach(function (m) {
      var li = h("li", {}, [h("b", { text: m.name }), " · " + (RL[m.role] || m.role) + " "]);
      if (m.handle) li.appendChild(h("button", { type: "button", class: "btn", text: TQ.rm, onclick: function () { api("/api/event/" + ev.handle + "/team", { method: "DELETE", body: { handle: m.handle, role: m.role } }).then(load); } }));
      list.appendChild(li); }); }); }
    box.appendChild(list);
    box.appendChild(h("div", { class: "btns" }, [hd, rs, h("button", { type: "button", class: "btn main", text: TQ.add, onclick: function () { msg.textContent = ""; api("/api/event/" + ev.handle + "/team", { method: "POST", body: { handle: hd.value.trim().toLowerCase(), role: rs.value } }).then(function (r) { if (r.j && r.j.ok) { hd.value = ""; load(); } else msg.textContent = TQ.err; }); } }), msg]));
    load(); return box;
  }
  function proposeBox(want) {
    var sec = h("div", { class: "ccard" }, [h("h3", { text: Q.propose })]);
    fetch(X.api + "/api/events/export").then(function (r) { return r.json(); }).then(function (j) {
      var evs = j.events || [], s = sel([["", Q.pick]].concat(evs.map(function (e) { return [e.handle, e.title]; })), want || ""), slot = h("div");
      function draw() { slot.textContent = ""; var ev = evs.filter(function (e) { return e.handle === s.value; })[0]; if (ev) slot.appendChild(sessionForm(ev, null, null, true)); }
      s.addEventListener("change", draw); sec.appendChild(s); sec.appendChild(slot); draw();
    }).catch(function () {});
    return sec;
  }
  function mount(me) {
    var sec = h("section", { class: "ccard" }, [h("h2", { text: Q.h }), h("p", { class: "cmut", text: Q.intro })]); root.textContent = ""; root.appendChild(sec);
    var want = (/[?&]propose=([a-z0-9-]+)/.exec(location.search) || [])[1];
    var tok = (/[?&]invite=([a-f0-9]{36})/.exec(location.search) || [])[1];
    if (tok) fetch(X.api + "/api/speaker/invite/" + tok).then(function (r) { return r.json(); }).then(function (j) {
      if (!j.invite) return; var i = j.invite, box = h("div", { class: "ccard" }, [h("h3", { text: Q.invt }), h("p", { text: Q.invtxt.replace("{s}", i.title).replace("{e}", i.ev) })]), m2 = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
      if (!me) { var ret = encodeURIComponent(location.href.split("#")[0]), lg = h("div", { class: "btns" }); box.appendChild(h("p", { text: Q.needlogin })); box.appendChild(lg);
        fetch(X.api + "/api/providers").then(function (r) { return r.json(); }).catch(function () { return {}; }).then(function (pj) { var pv = (pj && pj.providers) || ["linkedin", "microsoft", "google"]; if (!Array.isArray(pv)) pv = Object.keys(pv);
          [["linkedin", "LinkedIn"], ["microsoft", "Microsoft"], ["google", "Google"]].forEach(function (x) { if (pv.indexOf(x[0]) >= 0) lg.appendChild(h("a", { class: "btn" + (x[0] === "linkedin" ? " main" : ""), href: X.api + "/auth/login/" + x[0] + "?return=" + ret, rel: "nofollow", text: Q.signin + " " + x[1] })); }); }); }
      else box.appendChild(h("div", { class: "btns" }, [
        h("button", { type: "button", class: "btn main", text: Q.linkgo, onclick: function (ev2) { var b = ev2.target; b.disabled = true; m2.textContent = Q.linkbusy;
          function confirmIt() { return api("/api/speaker/confirm", { method: "POST", body: { token: tok } }); }
          function done(r) { b.disabled = false; if (r.s === 200) { m2.textContent = Q.linkdone; if (r.j && r.j.handle) m2.appendChild(h("a", { href: (de ? "/de" : "") + "/community/u/" + r.j.handle + "/", text: " " + Q.linkview })); } else m2.textContent = Q.err; }
          confirmIt().then(function (r) { if (r.s !== 409) return done(r);
            api("/api/profile/me").then(function (pr) { var nm = i.name || "Speaker", base = nm.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 24) || (pr.j && pr.j.suggest) || "speaker";
              function mk(h2, n) { return api("/api/profile/me", { method: "POST", body: { handle: h2, public: true, headline: "Speaker", bio: nm + " – " + i.ev + ": " + i.title } }).then(function (r2) { if (r2.s === 200) return confirmIt().then(done); if (n < 3) return mk(base.slice(0, 22) + "-" + Math.floor(Math.random() * 900 + 100), n + 1); done(r2); }); }
              mk(base.length >= 3 ? base : "speaker-" + Math.floor(Math.random() * 9000 + 1000), 0); }); }); } }),
        h("button", { type: "button", class: "btn", text: Q.decl, onclick: function () { api("/api/speaker/confirm", { method: "POST", body: { token: tok, decline: true } }).then(function () { box.remove(); }); } }), m2]));
      sec.insertBefore(box, sec.children[2] || null);
    }).catch(function () {});
    if (!me) { sec.appendChild(h("p", { text: Q.login })); return; }
    api("/api/speaker/requests").then(function (r) { var l = (r.j && r.j.items) || []; if (!l.length) return; var box = h("div", { class: "ccard" }, [h("h3", { text: Q.req })]);
      l.forEach(function (x) { box.appendChild(h("div", { class: "ev-s" }, [h("b", { text: x.title }), h("span", { class: "cmut", text: " · " + x.event }), h("div", { class: "btns" }, [
        h("button", { type: "button", class: "btn main", text: Q.conf, onclick: function () { api("/api/speaker/respond", { method: "POST", body: { id: x.id, ok: true } }).then(function () { reload(); }); } }),
        h("button", { type: "button", class: "btn", text: Q.decl, onclick: function () { api("/api/speaker/respond", { method: "POST", body: { id: x.id, ok: false } }).then(function () { reload(); }); } })])])); });
      sec.insertBefore(box, sec.children[2] || null); });
    function reload() { mount(me); }
    api("/api/events/mine").then(function (r) {
      var j = r.j || {}; sec.appendChild(h("h3", { text: Q.mine }));
      (j.events || []).forEach(function (e) { sec.appendChild(eventCard(e, j.orgs, reload)); });
      var nw = h("details", { class: "wk-edit" }, [h("summary", { text: "+ " + Q.newev })]); nw.appendChild(eventCard({ title: "", start: "", sessions: [] }, j.orgs, reload).lastChild); sec.appendChild(nw);
      sec.appendChild(proposeBox(want));
      api("/api/events/for-sponsors").then(function (r3) { if (r3.s !== 200) return; var box = h("div", {}, [h("h3", { text: Q.forsp })]), l = r3.j.events || [];
        l.sort(function (a, b) { return (b.match ? 1 : 0) - (a.match ? 1 : 0); });
        l.forEach(function (e) { box.appendChild(h("div", { class: "ev-s" }, [h("b", { text: e.title }), h("span", { class: "cmut", text: " · " + e.start + " · " + e.mode + (e.match ? " · ✓ " + Q.fmatch : "") }), h("p", { class: "cmut", text: e.summary || "" }), h("a", { class: "btn", href: location.pathname + "?msg_event=" + e.handle + "#c-messages", text: Q.contact })])); });
        if (l.length) sec.appendChild(box); });
      if ((j.events || []).some(function (e) { return e.seeking_sponsor; })) api("/api/events/sponsors").then(function (r2) {
        if (r2.s !== 200) return; var box = h("div", {}, [h("h3", { text: Q.sponsors })]), l = r2.j.sponsors || [];
        if (!l.length) box.appendChild(h("p", { class: "cmut", text: Q.sp_none }));
        box.appendChild(h("p", { class: "cmut", text: Q.askhint.replace("{f}", r2.j.free_asks).replace("{c}", r2.j.ask_cost) }));
        var seek = (j.events || []).filter(function (e) { return e.seeking_sponsor; }), esel = sel(seek.map(function (e) { return [e.handle, e.title]; }), seek[0] && seek[0].handle);
        if (seek.length > 1) box.appendChild(esel);
        l.forEach(function (s) { var c = s.criteria || {}, am = h("span", { class: "cmut" }); box.appendChild(h("div", { class: "ev-s" }, [h("b", { text: s.name }), h("p", { class: "cmut", text: [c.topics, c.format, c.min_audience ? "≥ " + c.min_audience : "", c.regions, c.budget, c.notes].filter(Boolean).join(" · ") }), h("button", { type: "button", class: "btn", text: Q.ask, onclick: function () {
          var ev = seek.filter(function (e) { return e.handle === esel.value; })[0] || seek[0]; if (!ev) return;
          api("/api/events/ask-sponsor", { method: "POST", body: { event: ev.handle, org: s.handle, body: Q.asktxt.replace("{e}", ev.title) } }).then(function (r) { am.textContent = r.s === 200 ? Q.askdone : r.j.error === "need_points" ? Q.needpts : r.j.error === "already" ? Q.already : Q.err; }); } }), " ", am])); }); sec.appendChild(box);
      });
    });
  }
  api("/api/me").then(function (r) { mount(r.j && r.j.user); }).catch(function () { mount(null); });
})();
