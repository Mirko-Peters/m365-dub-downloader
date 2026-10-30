/* Roadmap & Wunschliste: Wünsche einreichen, abstimmen; Admin übernimmt in die Roadmap und hakt ab */
(function () {
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-wish"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = de ? { h: "Roadmap & Wunschliste", intro: "Was wir als Nächstes bauen und was ihr euch wünscht. Sichtbar für alle Mitglieder mit Konto. Stimmt für Wünsche ab; Umgesetztes wird abgehakt und wandert ins Archiv.", login: "Melde dich an, um Roadmap und Wunschliste zu sehen.", newp: "Neuer Wunsch", title: "Titel", body: "Beschreibung (optional)", send: "Einreichen", sent: "Danke, dein Wunsch ist eingetragen.", s_open: "Wünsche", s_planned: "Roadmap – übernommen", s_done: "Umgesetzt (Archiv)", s_declined: "Abgelehnt", adopt: "In Roadmap übernehmen", done: "Abhaken (umgesetzt)", decline: "Ablehnen", reopen: "Zurück zu Wünschen", del_: "Löschen", note: "Notiz (optional)", e_title: "Der Titel braucht mindestens 5 Zeichen.", e_rate_limit: "Zu viele Wünsche – bitte später.", empty: "Noch nichts." }
    : { h: "Roadmap & wishlist", intro: "What we build next and what you wish for. Visible to all members with an account. Vote for wishes; finished ones are ticked off and move to the archive.", login: "Sign in to see the roadmap and wishlist.", newp: "New wish", title: "Title", body: "Description (optional)", send: "Submit", sent: "Thanks, your wish is listed.", s_open: "Wishes", s_planned: "Roadmap – adopted", s_done: "Done (archive)", s_declined: "Declined", adopt: "Adopt into roadmap", done: "Tick off (done)", decline: "Decline", reopen: "Back to wishes", del_: "Delete", note: "Note (optional)", e_title: "The title needs at least 5 characters.", e_rate_limit: "Too many wishes – please try later.", empty: "Nothing yet." };
  var box = h("div"), msg = h("p", { role: "status", class: "mut" });
  function post(p, b) { return api("/api/wish/" + p, { method: "POST", body: b }); }
  function item(w, admin) {
    var li = h("li", { style: "padding:.7em 0;border-bottom:1px solid var(--bd)" });
    var vb = h("button", { type: "button", class: "btn", "aria-pressed": w.voted ? "true" : "false", text: "▲ " + w.votes, onclick: function () { post("vote", { id: w.id }).then(load); } });
    li.appendChild(vb); li.appendChild(document.createTextNode(" ")); li.appendChild(h("b", { text: w.title })); li.appendChild(h("span", { class: "mut", text: " · " + (w.name || "") }));
    if (w.body) li.appendChild(h("div", { class: "mut", text: w.body })); if (w.note) li.appendChild(h("div", {}, [h("em", { text: w.note })]));
    var acts = h("div", { style: "margin-top:.4em" });
    function a(label, st) { acts.appendChild(h("button", { type: "button", class: "btn", text: label, onclick: function () { var n = st === "done" || st === "declined" ? (prompt(Q.note, w.note || "") || "") : (w.note || ""); post("status", { id: w.id, status: st, note: n }).then(load); } })); acts.appendChild(document.createTextNode(" ")); }
    if (admin) { if (w.status !== "planned") a(Q.adopt, "planned"); if (w.status !== "done") a(Q.done, "done"); if (w.status !== "declined") a(Q.decline, "declined"); if (w.status !== "open") a(Q.reopen, "open"); }
    if (w.mine || admin) acts.appendChild(h("button", { type: "button", class: "btn", text: Q.del_, onclick: function () { post("delete", { id: w.id }).then(load); } }));
    li.appendChild(acts); return li;
  }
  function draw(d) {
    box.textContent = "";
    var ti = U.inp("", 120), bo = h("textarea", { rows: 4, maxlength: 1500 }), det = h("details", { class: "wk-edit" }, [h("summary", { text: Q.newp })]), f = h("div", { class: "ed-form" });
    f.appendChild(U.lab(Q.title, ti)); f.appendChild(U.lab(Q.body, bo));
    f.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.send, onclick: function () { post("save", { title: ti.value, body: bo.value }).then(function (r) { var j = r.j || {}; if (j.ok) { msg.textContent = Q.sent; load(); } else msg.textContent = Q["e_" + j.error] || "Error"; }); } })]));
    det.appendChild(f); box.appendChild(det);
    [["planned", 0], ["open", 1], ["done", 2], ["declined", 3]].forEach(function (s) {
      var l = d.items.filter(function (w) { return w.status === s[0]; }); if (s[0] === "open") l.sort(function (a, b) { return b.votes - a.votes; }); if (s[0] === "declined" && !l.length) return;
      var sec = h("section", {}, [h("h3", { text: Q["s_" + s[0]] + " (" + l.length + ")" })]);
      if (!l.length) sec.appendChild(h("p", { class: "mut", text: Q.empty })); else { var ul = h("ul", { style: "padding:0;list-style:none" }); l.forEach(function (w) { ul.appendChild(item(w, d.admin)); }); sec.appendChild(ul); }
      box.appendChild(sec);
    });
  }
  function load() { api("/api/wish/list").then(function (r) { box.textContent = ""; if (r.j && r.j.items) draw(r.j); else box.appendChild(h("p", { text: Q.login })); }); }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro })); root.appendChild(msg); root.appendChild(box); load();
})();
