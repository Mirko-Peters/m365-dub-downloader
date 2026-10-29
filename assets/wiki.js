/* Community-Wiki fuer Glossarbegriffe. Nutzt window.M365W = {api, term, lang, t, privacy}. Texte nur per textContent. */
(function () {
  var W = window.M365W; if (!W || !W.api) return;
  var T = W.t || {}, root = document.getElementById("c-wiki"); if (!root) return;
  function h(tag, a, kids) { var e = document.createElement(tag); for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }); return e; }
  function api(path, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(W.api + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  function date(ts) { try { return new Date(ts * 1000).toLocaleDateString(W.lang === "en" ? undefined : W.lang); } catch (e) { return ""; } }
  var box = h("div", { class: "wk" }); root.appendChild(box);
  function login() { var ret = encodeURIComponent(location.href.split("#")[0]); return h("div", { class: "wk-login" }, [h("p", { text: T.login }), h("div", { class: "btns" }, [h("a", { class: "btn main", href: W.api + "/auth/login/google?return=" + ret, rel: "nofollow", text: "Google" }), h("a", { class: "btn", href: W.api + "/auth/login/microsoft?return=" + ret, rel: "nofollow", text: "Microsoft" })])]); }
  function render(d) {
    box.textContent = ""; var st = root.querySelector(".wk-static"); if (st) st.remove();
    var cur = d.live;
    if (cur) {
      box.appendChild(h("div", { class: "wk-body", text: cur.body }));
      box.appendChild(h("p", { class: "wk-meta" }, [T.by.replace("{n}", cur.name || T.anon).replace("{d}", date(cur.created)), " ",
        d.loggedIn ? h("button", { type: "button", class: "wk-link", text: T.report, onclick: function (e) { api("/api/wiki/report/" + cur.id, { method: "POST" }).then(function (r) { e.target.textContent = r.s === 200 ? T.reported : T.error; e.target.disabled = true; }); } }) : null]));
    } else box.appendChild(h("p", { class: "wk-empty", text: T.empty }));
    var ed = h("details", { class: "wk-edit" }, [h("summary", { text: cur ? T.edit : T.add })]);
    if (!d.loggedIn) ed.appendChild(login());
    else {
      var ta = h("textarea", { rows: 6, maxlength: 1500, "aria-label": T.edit }); ta.value = (d.mine && d.mine.body) || (cur && cur.body) || "";
      var sm = h("input", { type: "text", maxlength: 140, placeholder: T.summary, "aria-label": T.summary }), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
      var btn = h("button", { type: "button", class: "btn main", text: T.save, onclick: function () {
        btn.disabled = true; api("/api/wiki", { method: "POST", body: { term: W.term, lang: W.lang, body: ta.value, summary: sm.value } }).then(function (r) {
          btn.disabled = false;
          if (r.s === 200) { msg.textContent = r.j.status === "live" ? T.saved_live : T.saved_pending; if (r.j.status === "live") load(); }
          else msg.textContent = r.j.error === "too_short" ? T.too_short : r.j.error === "unchanged" ? T.unchanged : r.j.error === "rate_limit" ? T.rate : T.error;
        }).catch(function () { btn.disabled = false; msg.textContent = T.error; }); } });
      ed.appendChild(h("p", { class: "cmut", text: T.rules })); if (d.mine) ed.appendChild(h("p", { class: "cmut", text: T.pending_own }));
      [ta, sm, h("div", { class: "btns" }, [btn]), msg].forEach(function (x) { ed.appendChild(x); });
    }
    box.appendChild(ed);
    if (d.history && d.history.length > 1) {
      var hd = h("details", { class: "wk-hist" }, [h("summary", { text: T.history })]);
      hd.appendChild(h("ul", {}, d.history.map(function (x) { return h("li", { text: date(x.created) + " · " + (x.name || T.anon) + (x.summary ? " – " + x.summary : "") }); })));
      box.appendChild(hd);
    }
    if (d.admin) adminQueue();
  }
  function adminQueue() {
    api("/api/admin/wiki/pending").then(function (r) {
      var list = (r.j.pending || []).filter(function (x) { return x.term === W.term && x.lang === W.lang; }); if (!list.length) return;
      var sec = h("div", { class: "wk-admin" }, [h("h3", { text: T.pending })]);
      list.forEach(function (x) { var row = h("div", { class: "wk-pend" }, [h("p", { text: x.name + ": " + x.body }),
        h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: T.approve, onclick: function () { api("/api/admin/wiki/approve/" + x.id, { method: "POST" }).then(load); } }), h("button", { type: "button", class: "btn", text: T.reject, onclick: function () { api("/api/admin/wiki/reject/" + x.id, { method: "POST" }).then(load); } })])]); sec.appendChild(row); });
      box.appendChild(sec);
    });
  }
  function load() { return api("/api/wiki?term=" + encodeURIComponent(W.term) + "&lang=" + W.lang).then(function (r) { if (r.s === 200) render(r.j); else throw 0; }).catch(function () { if (!box.firstChild) box.appendChild(h("p", { class: "wk-empty", text: T.error })); }); }
  load();
})();
