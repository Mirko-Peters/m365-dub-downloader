/* Bewertungen: Durchschnitt (Apple + Community), Sterne-Verteilung, Bewertung schreiben, "hilfreich", Moderation */
(function () {
  var root = document.getElementById("sh-reviews"); if (!root) return;
  var API = root.getAttribute("data-api") || "https://api-dub.m365.fm", SHOW = root.getAttribute("data-show") || "en";
  var xn = +root.getAttribute("data-ext-n") || 0, xs = +root.getAttribute("data-ext-sum") || 0, xd = (root.getAttribute("data-ext-dist") || "0,0,0,0,0").split(",").map(Number);
  var de = (document.documentElement.lang || "en").slice(0, 2) === "de";
  var T = de ? { w: "Bewertung schreiben", e: "Deine Bewertung bearbeiten", t: "Titel (optional)", b: "Deine Erfahrung mit dem Podcast (mind. 10 Zeichen, keine Links)", s: "Absenden", ok: "Danke! Deine Bewertung ist online.", err: { login: "Bitte melde dich an.", too_short: "Bitte etwas ausführlicher.", no_links: "Bitte ohne Links.", bad_rating: "Bitte Sterne wählen.", rate_limit: "Heute schon genug Bewertungen.", hidden: "Deine Bewertung wurde vom Team ausgeblendet." }, h: "Hilfreich", login: "Anmelden, um zu bewerten →", del: "Löschen", hide: "Ausblenden", c: "Bewertungen der Community", none: "Noch keine Community-Bewertungen. Sei der Erste!", of: "Bewertungen", own: "Deine Bewertung" }
    : { w: "Write a review", e: "Edit your review", t: "Title (optional)", b: "Your experience with the podcast (min. 10 characters, no links)", s: "Submit", ok: "Thanks! Your review is live.", err: { login: "Please sign in.", too_short: "Please write a bit more.", no_links: "No links, please.", bad_rating: "Please choose a star rating.", rate_limit: "Daily limit reached.", hidden: "Your review was hidden by the team." }, h: "Helpful", login: "Sign in to review →", del: "Delete", hide: "Hide", c: "Community reviews", none: "No community reviews yet. Be the first!", of: "ratings", own: "Your review" };
  function h(t, a, c) { var e = document.createElement(t); a = a || {}; for (var k in a) { if (k === "text") e.textContent = a[k]; else if (k === "onclick") e.onclick = a[k]; else e.setAttribute(k, a[k]); } (c || []).forEach(function (x) { e.appendChild(x); }); return e; }
  function api(p, o) { o = o || {}; var opt = { method: o.method || "GET", credentials: "include", headers: { "x-requested-with": "m365" } }; if (o.body) { opt.body = JSON.stringify(o.body); opt.headers["content-type"] = "application/json"; } return fetch(API + p, opt).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  function stars(n) { return "★★★★★".slice(0, n) + "☆☆☆☆☆".slice(0, 5 - n); }
  var sel = 0, box = h("div"); root.appendChild(box);
  function summary(d) {
    var n = xn + d.count, s = xs + d.sum, dist = xd.map(function (v, i) { return v + (d.dist[i] || 0); }), avg = n ? s / n : 0, mx = Math.max.apply(null, dist.concat(1));
    var bars = h("div", { class: "rv-bars" }); for (var i = 5; i >= 1; i--) bars.appendChild(h("div", { class: "rv-bar" }, [h("span", { text: i + "★" }), h("i", {}, [h("b", { style: "width:" + Math.round(dist[i - 1] / mx * 100) + "%" })]), h("span", { text: String(dist[i - 1]) })]));
    return h("div", { class: "rv-sum" }, [h("div", { class: "rv-big" }, [document.createTextNode(n ? avg.toFixed(1) : "–"), h("div", { class: "rv-stars", text: stars(Math.round(avg)) }), h("small", { text: n + " " + T.of })]), bars]);
  }
  function form(d) {
    var m = d.mine; sel = m ? m.rating : 0; var pick = h("div", { class: "rv-pick", role: "radiogroup", "aria-label": "Rating" }), msg = h("span", { class: "rv-msg", role: "status" });
    var ti = h("input", { type: "text", maxlength: 80, placeholder: T.t }), bo = h("textarea", { rows: 4, maxlength: 2000, placeholder: T.b }); if (m) { ti.value = m.title || ""; bo.value = m.body || ""; }
    function paint() { [].forEach.call(pick.children, function (b, i) { b.className = i < sel ? "on" : ""; b.setAttribute("aria-checked", i + 1 === sel ? "true" : "false"); }); }
    for (var i = 1; i <= 5; i++) (function (i) { pick.appendChild(h("button", { type: "button", role: "radio", "aria-label": i + " / 5", text: "★", onclick: function () { sel = i; paint(); } })); })(i); paint();
    var send = h("button", { type: "button", class: "btn main", text: T.s, onclick: function () { api("/api/reviews", { method: "POST", body: { show: SHOW, rating: sel, title: ti.value, body: bo.value } }).then(function (r) { if (r.j && r.j.ok) { msg.textContent = T.ok; load(); } else msg.textContent = (T.err[(r.j || {}).error] || "Error"); }); } });
    return h("div", { class: "rv-form" }, [h("h3", { text: m ? T.e : T.w }), pick, ti, bo, h("div", { class: "rv-act" }, [send, msg])]);
  }
  function item(r, mod) {
    var el = h("div", { class: "rv-item" }, [h("div", { class: "rv-stars", text: stars(r.rating) }), r.title ? h("h4", { text: r.title }) : h("span"), h("p", { text: r.body, style: "margin:.2rem 0;white-space:pre-wrap" })]);
    var by = r.handle ? h("a", { href: (root.getAttribute("data-login") || "").replace(/community\/?$/, "") + "community/u/" + r.handle + "/", text: r.name }) : document.createTextNode(r.name);
    el.appendChild(h("div", { class: "rv-meta" }, [by, document.createTextNode(" · " + new Date(r.created * 1000).toISOString().slice(0, 10) + (r.own ? " · " + T.own : ""))]));
    if (!r.own) el.appendChild(h("button", { type: "button", class: "rv-help", "aria-pressed": r.voted ? "true" : "false", text: "👍 " + T.h + " · " + r.helpful, onclick: function () { api("/api/reviews/helpful", { method: "POST", body: { id: r.id } }).then(function (x) { if (x.s === 401) location.href = root.getAttribute("data-login"); else load(); }); } }));
    if (r.own || mod) el.appendChild(h("button", { type: "button", class: "rv-help", text: r.own ? T.del : T.hide, onclick: function () { api("/api/reviews/delete", { method: "POST", body: { id: r.id } }).then(load); } }));
    return el;
  }
  function draw(d, authed) {
    box.textContent = ""; box.appendChild(summary(d));
    box.appendChild(authed ? form(d) : h("p", {}, [h("a", { class: "btn main", href: root.getAttribute("data-login") || "#", text: T.login })]));
    box.appendChild(h("h2", { text: T.c })); if (!d.items.length) box.appendChild(h("p", { class: "mut", text: T.none })); d.items.forEach(function (r) { box.appendChild(item(r, d.can_moderate)); });
  }
  function load() { api("/api/reviews?show=" + encodeURIComponent(SHOW)).then(function (r) { if (!r.j || r.j.error) { box.textContent = ""; return; } return api("/api/me").then(function (m) { draw(r.j, !!(m.j && m.j.user)); }); }).catch(function () { box.textContent = ""; }); }
  load();
})();
