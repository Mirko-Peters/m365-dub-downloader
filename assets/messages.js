/* Flüchtige Nachrichten: Postfach, Kontakt aufnehmen (Tageslimit), Nachrichten werden nach 7 Tagen gelöscht */
(function () {
  var X = window.M365X, root = document.getElementById("c-messages"); if (!X || !root) return;
  var de = X.lang === "de";
  var Q = de ? { h: "Nachrichten", intro: "Direkte Nachrichten sind flüchtig: Sie werden nach 7 Tagen automatisch gelöscht. Pro Tag kannst du eine begrenzte Zahl neuer Kontakte anschreiben – mit mehr Punkten werden es mehr.", login: "Zum Schreiben bitte oben anmelden.", none: "Noch keine Unterhaltungen.", open: "Ich bin für Kontaktanfragen offen", limit: "Neue Kontakte heute: {u} von {l}", send: "Senden", ph: "Deine Nachricht (ohne Links, max. 1000 Zeichen)", back: "← Zurück", block: "Blockieren", unblock: "Blockierung aufheben", del: "Unterhaltung löschen", exp: "Wird am {d} gelöscht", newmsg: "Neue Nachricht", to: "An (Profil-Adresse)", err: "Das hat nicht geklappt.", daily: "Tageslimit erreicht – mit mehr Punkten kannst du mehr Kontakte anschreiben.", closed: "Diese Person nimmt aktuell keine Anfragen an.", nf: "Person nicht gefunden.", sent: "✓ Gesendet.", ctxe: "Sponsoring-Anfrage zu: ", unread: "neu" }
    : { h: "Messages", intro: "Direct messages are ephemeral: they are deleted automatically after 7 days. You can contact a limited number of new people per day – more points unlock more.", login: "Please sign in above to write messages.", none: "No conversations yet.", open: "I am open to contact requests", limit: "New contacts today: {u} of {l}", send: "Send", ph: "Your message (no links, max. 1000 characters)", back: "← Back", block: "Block", unblock: "Unblock", del: "Delete conversation", exp: "Deleted on {d}", newmsg: "New message", to: "To (profile address)", err: "That did not work.", daily: "Daily limit reached – earn more points to contact more people.", closed: "This person is not accepting requests right now.", nf: "Person not found.", sent: "✓ Sent.", ctxe: "Sponsoring inquiry about: ", unread: "new" };
  function h(tag, a, kids) { var e = document.createElement(tag); for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }); return e; }
  function api(path, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(X.api + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  var timer = null;
  function dt(ts) { try { return new Date(ts * 1000).toLocaleDateString(X.lang); } catch (e) { return ""; } }
  function errMsg(r) { return r.j && r.j.error === "daily_limit" ? Q.daily : r.j && r.j.error === "closed" ? Q.closed : r.j && r.j.error === "not_found" ? Q.nf : Q.err; }

  function compose(sec, preTo, preEvent, back) {
    var f = h("div", { class: "wk-form" }), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    var to = h("input", { type: "text", maxlength: 30, "aria-label": Q.to }); to.value = preTo || ""; var ta = h("textarea", { rows: 5, maxlength: 1000, placeholder: Q.ph, "aria-label": Q.ph });
    if (preEvent) ta.value = Q.ctxe + preEvent + "\n";
    if (!preEvent) { f.appendChild(h("label", { text: Q.to })); f.appendChild(to); }
    f.appendChild(ta);
    f.appendChild(h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: Q.send, onclick: function () {
      api("/api/msg/start", { method: "POST", body: preEvent ? { event: preEvent, body: ta.value } : { to: to.value.trim().toLowerCase(), body: ta.value } }).then(function (r) { if (r.s === 200) { msg.textContent = Q.sent; ta.value = ""; setTimeout(back, 600); } else msg.textContent = errMsg(r); }); } }),
      h("button", { type: "button", class: "btn", text: Q.back, onclick: back }), msg]));
    sec.appendChild(f);
  }
  function thread(sec, t, back) {
    clearInterval(timer); sec.textContent = "";
    var list = h("div"), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" }), ta = h("textarea", { rows: 3, maxlength: 1000, placeholder: Q.ph, "aria-label": Q.ph }), bl = h("button", { type: "button", class: "btn" });
    sec.appendChild(h("div", { class: "btns" }, [h("button", { type: "button", class: "btn", text: Q.back, onclick: function () { clearInterval(timer); back(); } }), bl,
      h("button", { type: "button", class: "btn", text: Q.del, onclick: function () { api("/api/msg/thread/" + t.id, { method: "DELETE" }).then(function () { clearInterval(timer); back(); }); } })]));
    sec.appendChild(h("h3", { text: t.with.name })); sec.appendChild(list); sec.appendChild(ta);
    sec.appendChild(h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: Q.send, onclick: function () { api("/api/msg/thread/" + t.id, { method: "POST", body: { body: ta.value } }).then(function (r) { if (r.s === 200) { ta.value = ""; load(); } else msg.textContent = Q.err; }); } }), msg]));
    var isBlocked = false;
    bl.addEventListener("click", function () { api("/api/msg/block/" + t.id, { method: isBlocked ? "DELETE" : "POST" }).then(load); });
    function load() { api("/api/msg/thread/" + t.id).then(function (r) { if (r.s !== 200) return; isBlocked = !!r.j.blocked; bl.textContent = isBlocked ? Q.unblock : Q.block; list.textContent = "";
      r.j.messages.forEach(function (m) { list.appendChild(h("div", { class: "ev-s", style: "text-align:" + (m.mine ? "right" : "left") }, [h("p", { text: m.body, style: "white-space:pre-line;margin:0" }), h("span", { class: "cmut", text: dt(m.created) + " · " + Q.exp.replace("{d}", dt(m.expires)) })])); }); }); }
    load(); timer = setInterval(load, 20000);
  }
  function mount(me) {
    clearInterval(timer); root.textContent = "";
    var sec = h("section", { class: "ccard" }, [h("h2", { text: Q.h }), h("p", { class: "cmut", text: Q.intro })]); root.appendChild(sec);
    if (!me) { sec.appendChild(h("p", { text: Q.login })); return; }
    var pe = (/[?&]msg_event=([a-z0-9-]+)/.exec(location.search) || [])[1], pt = (/[?&]msg=([a-z0-9-]+)/.exec(location.search) || [])[1];
    var body = h("div"); function home() { history.replaceState(null, "", location.pathname + "#c-messages"); render(); }
    function render() { sec.textContent = ""; sec.appendChild(h("h2", { text: Q.h })); sec.appendChild(h("p", { class: "cmut", text: Q.intro })); sec.appendChild(body); body.textContent = "";
      api("/api/msg/prefs").then(function (r) { var p = r.j || {}; var cb = h("input", { type: "checkbox" }); cb.checked = p.open !== false; cb.addEventListener("change", function () { api("/api/msg/prefs", { method: "POST", body: { open: cb.checked } }); });
        body.appendChild(h("label", { style: "display:flex;align-items:center" }, [cb, " " + Q.open])); body.appendChild(h("p", { class: "cmut", text: Q.limit.replace("{u}", p.used || 0).replace("{l}", p.limit || 5) }));
        body.appendChild(h("button", { type: "button", class: "btn main", text: "+ " + Q.newmsg, onclick: function () { body.textContent = ""; compose(body, "", "", render); } }));
        api("/api/msg/threads").then(function (r2) { var l = (r2.j && r2.j.threads) || []; if (!l.length) body.appendChild(h("p", { class: "cmut", text: Q.none }));
          l.forEach(function (t) { body.appendChild(h("div", { class: "ev-s" }, [h("button", { type: "button", class: "wk-link", text: t.with.name + (t.unread ? " · " + Q.unread : ""), onclick: function () { thread(sec, t, render); } }), h("br"), h("span", { class: "cmut", text: (t.ctx ? "[" + t.ctx + "] " : "") + t.preview })])); }); }); }); }
    render();
    if (pe) { body.textContent = ""; compose(body, "", pe, home); } else if (pt) { body.textContent = ""; compose(body, pt, "", home); }
  }
  api("/api/me").then(function (r) { mount(r.j && r.j.user); }).catch(function () { mount(null); });
})();
