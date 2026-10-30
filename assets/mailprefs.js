/* Benachrichtigungen: E-Mail-Adresse bestätigen, Arten ein-/ausschalten */
(function () {
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-mail"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = de ? { h: "Benachrichtigungen", intro: "Wir schreiben dir nur, wenn etwas dich betrifft. Du bestätigst deine Adresse einmal und schaltest jede Art einzeln ein oder aus. In jeder Mail ist ein Abmeldelink.", email: "E-Mail-Adresse", save: "Bestätigungsmail senden", sent: "Bestätigungsmail ist unterwegs. Klicke den Link darin.", pending: "Noch nicht bestätigt – prüfe dein Postfach.", ok: "Bestätigt", remove: "Adresse entfernen", test: "Testmail senden", testok: "Testmail ist unterwegs.", off: "Der Mailversand ist auf dieser Plattform noch nicht aktiviert.", login: "Melde dich an, um Benachrichtigungen einzustellen.", kinds: { reply: "Antworten auf meine Kommentare", wish: "Status meiner Wünsche (Roadmap)", show: "Freigabe meiner Podcast-Shows", event: "Einladungen zu Events und Sessions" }, e_email: "Das ist keine gültige Adresse.", e_rate_limit: "Zu viele Versuche – bitte später.", e_mail_off: "Der Mailversand ist noch nicht aktiviert." }
    : { h: "Notifications", intro: "We only write when something concerns you. Confirm your address once and switch each kind on or off. Every mail has an unsubscribe link.", email: "E-mail address", save: "Send confirmation mail", sent: "Confirmation mail is on its way. Click the link inside.", pending: "Not confirmed yet – check your inbox.", ok: "Confirmed", remove: "Remove address", test: "Send test mail", testok: "Test mail is on its way.", off: "Mail sending is not enabled on this platform yet.", login: "Sign in to manage notifications.", kinds: { reply: "Replies to my comments", wish: "Status of my wishes (roadmap)", show: "Approval of my podcast shows", event: "Invitations to events and sessions" }, e_email: "That is not a valid address.", e_rate_limit: "Too many attempts – please try later.", e_mail_off: "Mail sending is not enabled yet." };
  var box = h("div"), msg = h("p", { role: "status", class: "mut" });
  function post(p, b) { return api("/api/mail/" + p, { method: "POST", body: b || {} }); }
  function draw(d) {
    box.textContent = ""; if (!d.configured) box.appendChild(h("p", { class: "mut", text: Q.off }));
    var ei = U.inp(d.email || "", 190), f = h("div", { class: "ed-form" });
    f.appendChild(U.lab(Q.email, ei));
    f.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.save, onclick: function () { post("set", { email: ei.value }).then(function (r) { var j = r.j || {}; msg.textContent = j.ok ? Q.sent : (Q["e_" + j.error] || "Error"); load(); }); } })]));
    box.appendChild(f);
    if (d.email) {
      box.appendChild(h("p", { class: "mut", text: d.email + " · " + (d.verified ? "✓ " + Q.ok : Q.pending) }));
      if (d.verified) {
        var ul = h("ul", { style: "list-style:none;padding:0" });
        Object.keys(Q.kinds).forEach(function (k) {
          var cb = h("input", { type: "checkbox", id: "mp-" + k }); cb.checked = !!d.prefs[k];
          cb.addEventListener("change", function () { post("prefs", { kind: k, on: cb.checked }); });
          ul.appendChild(h("li", { style: "margin:.5em 0" }, [cb, h("label", { for: "mp-" + k, style: "display:inline;font-weight:400;margin-left:.5em", text: Q.kinds[k] })]));
        });
        box.appendChild(ul);
        box.appendChild(h("p", {}, [h("button", { type: "button", class: "btn", text: Q.test, onclick: function () { post("test").then(function () { msg.textContent = Q.testok; }); } }), document.createTextNode(" "), h("button", { type: "button", class: "btn", text: Q.remove, onclick: function () { post("remove").then(load); } })]));
      }
    }
  }
  function load() { api("/api/mail/me").then(function (r) { box.textContent = ""; if (r.j && "configured" in r.j) draw(r.j); else box.appendChild(h("p", { text: Q.login })); }); }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro })); root.appendChild(msg); root.appendChild(box); load();
})();
