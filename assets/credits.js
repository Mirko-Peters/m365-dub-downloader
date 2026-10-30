/* Gaeste bei eigenem Podcast/Video (wie Co-Autoren im Blog): Host traegt Profil-Adressen ein, Eingeladene bestaetigen selbst.
   M365U.credits.box(kind, item, reload) -> Element fuer einen eigenen Eintrag; M365U.credits.invites(into, reload) -> Einladungen an mich. */
(function () {
  var U = window.M365U; if (!U) return;
  var h = U.h, api = U.api, de = (window.M365X || {}).lang === "de";
  var T = de ? { lab: "Gäste (Profil-Adressen, kommagetrennt, max. 5)", save: "Gäste speichern", saved: "Gespeichert – Eingeladene bestätigen selbst.", hint: "Wie Co-Autoren im Blog: erst nach ihrer Bestätigung erscheinen Gäste auf der Seite und im Schema, ihre Themen zählen für ihre Expertise.", st_invited: "eingeladen", st_confirmed: "bestätigt", st_declined: "abgelehnt", bad: "Gast nicht gefunden (öffentliches Profil nötig, nicht du selbst): ", err: "Konnte nicht gespeichert werden.", inv: "Einladungen als Gast", invtxt: "{a} lädt dich als Gast ein:", yes: "Annehmen", no: "Ablehnen", done: "Erledigt.", needp: "Mache zuerst dein Profil öffentlich.", podcast: "Podcast", video: "Video" }
    : { lab: "Guests (profile handles, comma separated, max. 5)", save: "Save guests", saved: "Saved – invited members confirm themselves.", hint: "Like co-authors in the blog: guests appear on the page and in the schema only after they confirm, and their topics count towards their expertise.", st_invited: "invited", st_confirmed: "confirmed", st_declined: "declined", bad: "Guest not found (public profile required, not yourself): ", err: "Could not be saved.", inv: "Invitations as guest", invtxt: "{a} invites you as guest:", yes: "Accept", no: "Decline", done: "Done.", needp: "Make your profile public first.", podcast: "Podcast", video: "Video" };
  function csv(s) { return String(s || "").split(",").map(function (x) { return x.trim().toLowerCase(); }).filter(Boolean); }
  function box(kind, item, reload) {
    var inp = U.inp((item.guests || []).map(function (g) { return g.handle; }).join(", "), 160), msg = h("span", { class: "mut", role: "status" });
    var st = (item.guests || []).length ? " " + item.guests.map(function (g) { return g.name + ": " + (T["st_" + g.status] || g.status); }).join(" · ") : "";
    return h("div", { style: "margin:.4em 0" }, [U.lab(T.lab, inp), h("p", { class: "mut", text: T.hint + st }),
      h("button", { type: "button", class: "btn", text: T.save, onclick: function () {
        api("/api/credit/set", { method: "POST", body: { kind: kind, id: item.id, guests: csv(inp.value) } }).then(function (r) { var j = r.j || {}; if (j.ok) { msg.textContent = T.saved; if (reload) reload(); } else msg.textContent = j.error === "bad_guest" ? T.bad + (j.handle || "") : T.err; });
      } }), " ", msg]);
  }
  function invites(into, reload) {
    api("/api/credit/mine").then(function (r) {
      var d = r.j || {}; if (!(d.invites || []).length) return;
      into.appendChild(h("h3", { text: T.inv }));
      d.invites.forEach(function (iv) {
        function reply(ok) { api("/api/credit/respond", { method: "POST", body: { kind: iv.kind, id: iv.id, accept: ok } }).then(function (x) { var j = x.j || {}; p.appendChild(h("span", { class: "mut", text: " " + (j.ok ? T.done : (j.error === "need_profile" ? T.needp : T.err)) })); if (j.ok && reload) reload(); }); }
        var p = h("p", {}, [T.invtxt.replace("{a}", iv.host) + " ", h("b", { text: iv.title }), " (" + (T[iv.kind] || iv.kind) + ") ", h("button", { type: "button", class: "btn main", text: T.yes, onclick: function () { reply(true); } }), " ", h("button", { type: "button", class: "btn", text: T.no, onclick: function () { reply(false); } })]);
        into.appendChild(p);
      });
    });
  }
  U.credits = { box: box, invites: invites };
})();
