/* Live-Teil der oeffentlichen Profil-/Firmenseiten und Verzeichnisse: Upvotes, Bestaetigungen, Beitritt, Feed. window.M365P = {api, base} */
(function () {
  var P = window.M365P; if (!P) return;
  var de = /^\/de\//.test(location.pathname), T = de ? { confirm: "Bestätigen", confirmed: "Bestätigt ✓", join: "Der Firma beitreten", joined: "Anfrage gesendet", up: "Hochwählen", top: "Meist gelobt", neu: "Neueste", login: "Zum Anmelden" } : { confirm: "Confirm", confirmed: "Confirmed ✓", join: "Join this company", joined: "Request sent", up: "Upvote", top: "Most upvoted", neu: "Latest", login: "Sign in" };
  var home = P.base + (de ? "/de" : "") + "/community/";
  function h(tag, a, kids) { var e = document.createElement(tag); for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }); return e; }
  function api(path, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(P.api + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  function vote(btn, id) {
    btn.addEventListener("click", function () {
      api("/api/vote/" + id, { method: "POST" }).then(function (r) {
        if (r.s === 401) { location.href = home; return; }
        if (r.s === 200) { btn.setAttribute("aria-pressed", r.j.voted ? "true" : "false"); btn.querySelector(".n").textContent = r.j.votes; }
      });
    });
  }
  function wireVotes(items) {
    var by = {}; items.forEach(function (i) { by[i.id] = i; });
    [].slice.call(document.querySelectorAll(".pf-item[data-id]")).forEach(function (li) {
      var it = by[li.getAttribute("data-id")], b = li.querySelector(".vt"); if (!b) return;
      if (it) { b.querySelector(".n").textContent = it.votes; b.setAttribute("aria-pressed", it.voted ? "true" : "false"); }
      b.setAttribute("aria-label", T.up); vote(b, li.getAttribute("data-id"));
    });
  }
  var m = /\/community\/(u|c)\/([a-z0-9-]+)\/?$/.exec(location.pathname);
  if (m) {
    var kind = m[1], handle = m[2];
    api(kind === "u" ? "/api/profile/" + handle : "/api/org/" + handle).then(function (r) {
      if (r.s !== 200) return; var d = r.j.profile || r.j.org; wireVotes(d.items || []);
      if (kind === "u") {
        [].slice.call(document.querySelectorAll(".pf-endorse")).forEach(function (sp) {
          var ex = (d.expertise || []).filter(function (x) { return x.e === sp.getAttribute("data-e"); })[0]; if (!ex || d.mine) return;
          var b = h("button", { type: "button", class: "wk-link", text: ex.me ? T.confirmed : T.confirm, "aria-pressed": ex.me ? "true" : "false" });
          b.addEventListener("click", function () {
            var on = b.getAttribute("aria-pressed") === "true";
            api("/api/endorse", { method: on ? "DELETE" : "POST", body: { handle: handle, e: sp.getAttribute("data-e") } }).then(function (x) { if (x.s === 401) { location.href = home; return; } if (x.s === 200) { b.setAttribute("aria-pressed", on ? "false" : "true"); b.textContent = on ? T.confirm : T.confirmed; } });
          });
          sp.appendChild(document.createTextNode(" · ")); sp.appendChild(b);
        });

        [].slice.call(document.querySelectorAll(".pf-certend")).forEach(function (sp) {
          var ct = (d.certs || []).filter(function (x) { return x.e === sp.getAttribute("data-e"); })[0]; if (!ct || d.mine) return;
          var b = h("button", { type: "button", class: "wk-link", text: ct.me ? T.confirmed : T.confirm, "aria-pressed": ct.me ? "true" : "false" });
          b.addEventListener("click", function () {
            var on = b.getAttribute("aria-pressed") === "true";
            api("/api/cert-endorse", { method: on ? "DELETE" : "POST", body: { handle: handle, e: sp.getAttribute("data-e") } }).then(function (x) { if (x.s === 401) { location.href = home; return; } if (x.s === 200) { b.setAttribute("aria-pressed", on ? "false" : "true"); b.textContent = on ? T.confirm : T.confirmed; } });
          });
          sp.appendChild(document.createTextNode(" · ")); sp.appendChild(b);
        });

        if (!d.mine) {
          var RL = de ? { colleague: "Kollege/Kollegin", manager: "Führungskraft", report: "Mitarbeiter:in", client: "Kunde/Kundin", trainer: "Trainer:in", student: "Teilnehmer:in / Schüler:in", cospeaker: "Co-Speaker / Event", podcast: "Podcast-Gast oder -Host", community: "Community", mentor: "Mentor:in / Mentee", other: "Sonstiges" } : { colleague: "Colleague", manager: "Manager", report: "Direct report", client: "Client", trainer: "Trainer", student: "Student / participant", cospeaker: "Co-speaker / event", podcast: "Podcast guest or host", community: "Community", mentor: "Mentor / mentee", other: "Other" };
          var RT = de ? { open: "Empfehlung schreiben", rel: "In welcher Beziehung stehst du zu dieser Person?", body: "Deine Empfehlung (mind. 40 Zeichen, ohne Links)", send: "Absenden", sent: "✓ Danke! Die Empfehlung erscheint, sobald die Person sie freigibt.", err: "Das hat nicht geklappt – bitte Eingaben prüfen.", hint: "Empfehlungen werden mit deinem Anzeigenamen veröffentlicht, nachdem die empfohlene Person sie freigegeben hat." } : { open: "Write a recommendation", rel: "How do you know this person?", body: "Your recommendation (at least 40 characters, no links)", send: "Send", sent: "✓ Thanks! The recommendation appears once the person approves it.", err: "That did not work – please check your input.", hint: "Recommendations are published with your display name after the recommended person approves them." };
          var det = h("details", { class: "wk-edit" }, [h("summary", { text: RT.open })]), rsel = h("select", { "aria-label": RT.rel }), ta = h("textarea", { rows: 5, maxlength: 1200, "aria-label": RT.body, placeholder: RT.body }), rm = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
          Object.keys(RL).forEach(function (k) { rsel.appendChild(h("option", { value: k, text: RL[k] })); });
          det.appendChild(h("div", { class: "wk-form" }, [h("label", { text: RT.rel }), rsel, h("label", { text: RT.body }), ta, h("p", { class: "cmut", text: RT.hint }), h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: RT.send, onclick: function () {
            api("/api/recommend", { method: "POST", body: { handle: handle, relation: rsel.value, body: ta.value } }).then(function (x) { if (x.s === 401) { location.href = home; return; } rm.textContent = x.s === 200 ? RT.sent : RT.err; if (x.s === 200) ta.value = ""; }); } }), rm])]));
          var mn = document.querySelector("main"); if (mn) { mn.appendChild(h("p", {}, [h("a", { class: "btn", href: home + "?msg=" + handle + "#c-messages", text: de ? "Kontakt aufnehmen" : "Get in touch", rel: "nofollow" })])); mn.appendChild(det); }
        }
      } else {
        var host = document.querySelector("main h1"); if (host) {
          var jb = h("button", { type: "button", class: "btn", text: T.join }); jb.addEventListener("click", function () { api("/api/org/" + handle + "/join", { method: "POST" }).then(function (x) { if (x.s === 401) location.href = home; else if (x.s === 200) { jb.textContent = T.joined; jb.disabled = true; } }); });
          host.parentNode.insertBefore(h("p", {}, [jb]), host.nextSibling.nextSibling || null);
        }
      }
    });
  }
  var feed = document.getElementById("pf-feed");
  if (feed) {
    var mode = "new", box = h("div"), bar = h("div", { role: "group" });
    function load() {
      api("/api/feed?sort=" + (mode === "top" ? "top" : "new")).then(function (r) {
        box.textContent = ""; var ul = h("ul", { class: "pf-list" });
        (r.j.items || []).forEach(function (i) {
          var by = i.ref.split(":"), link = P.base + (de ? "/de" : "") + "/community/" + by[0] + "/" + by[1] + "/";
          var b = h("button", { type: "button", class: "vt", "aria-pressed": i.voted ? "true" : "false", "aria-label": T.up }, [h("span", { "aria-hidden": "true", text: "▲ " }), h("span", { class: "n", text: String(i.votes) })]); vote(b, i.id);
          ul.appendChild(h("li", { class: "pf-item" }, [b, h("div", {}, [h("a", { href: i.url, rel: "nofollow ugc noopener", target: "_blank", text: i.title }), h("br"), h("span", { class: "mut" }, [h("a", { href: link, text: i.by }), " · " + new Date(i.published * 1000).toLocaleDateString(de ? "de" : undefined)])])]));
        });
        box.appendChild(ul);
      });
    }
    [["new", feed.getAttribute("data-new") || T.neu], ["top", feed.getAttribute("data-top") || T.top]].forEach(function (x) {
      var b = h("button", { type: "button", class: "mb-f", "aria-pressed": x[0] === mode ? "true" : "false", text: x[1] });
      b.addEventListener("click", function () { mode = x[0]; [].slice.call(bar.children).forEach(function (c) { c.setAttribute("aria-pressed", c === b ? "true" : "false"); }); load(); }); bar.appendChild(b);
    });
    feed.appendChild(bar); feed.appendChild(box); load();
  }
})();
