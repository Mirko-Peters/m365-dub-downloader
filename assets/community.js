/* M365.FM Community: Kommentare, Abos, Kurator, Profil. Nutzt window.M365C = {api, lang, vid, t}. Texte nur per textContent. */
(function () {
  var C = window.M365C; if (!C || !C.api) return;
  var T = C.t || {}, API = C.api, LANG = C.lang, ICON = { editor: "✏️", wiki_author: "📖", newcomer: "🌱", first_comment: "💬", commentator: "🗣️", voice: "📣", helpful: "🤝", early_bird: "🐦", polyglot: "🌍", streak: "🔥", curator: "🏆", notified: "🔔", guardian: "🛡️" };
  var BADGES = ["editor", "wiki_author", "newcomer", "first_comment", "commentator", "voice", "helpful", "early_bird", "polyglot", "streak", "curator", "notified", "guardian"];
  var tt = function (k) { return T[k] || k; };
  function h(tag, a, kids) {
    var e = document.createElement(tag);
    for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); }
    (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function api(path, o) {
    o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {});
    if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; }
    return fetch(API + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); });
  }
  var mePromise = null;
  function me(force) { if (!mePromise || force) mePromise = api("/api/me").then(function (r) { return r.j.user || null; }); return mePromise; }
  function hideAll(sel) { document.querySelectorAll(sel).forEach(function (e) { e.hidden = true; }); }
  function date(ts) { try { return new Date(ts * 1000).toLocaleDateString(LANG); } catch (e) { return ""; } }

  function badgeEls(list, big) {
    return h("span", { class: "cbs" }, (list || []).map(function (b) { return h("span", { class: "cb" + (big ? " big" : ""), title: tt("b_" + b) + " – " + tt("b_" + b + "_d"), text: (ICON[b] || "★") }); }));
  }
  function loginBox() {
    var ret = encodeURIComponent(location.href.split("#")[0]);
    return h("div", { class: "clogin" }, [
      h("p", { text: tt("login_to_comment") }),
      h("div", { class: "btns" }, [
        h("a", { class: "btn main", href: API + "/auth/login/google?return=" + ret, rel: "nofollow", text: tt("signin_google") }),
        h("a", { class: "btn", href: API + "/auth/login/microsoft?return=" + ret, rel: "nofollow", text: tt("signin_ms") })]),
      h("small", {}, [tt("signin_note") + " ", h("a", { href: C.privacy, text: tt("privacy") })])]);
  }


  /* ---------- Team (nur Admin): Editoren ernennen ---------- */
  function teamPanel() {
    var res = h("ul", { class: "cteam-list" }), q = h("input", { type: "text", placeholder: "Name", "aria-label": "Name", maxlength: 40 });
    function load() {
      api("/api/admin/users?q=" + encodeURIComponent(q.value)).then(function (r) {
        res.textContent = "";
        (r.j.users || []).forEach(function (x) {
          var ed = x.role === "editor";
          res.appendChild(h("li", {}, [h("span", { text: "#" + x.id + " " + x.name + (ed ? " ✏️" : "") + " " }),
            h("button", { type: "button", class: "btn", text: ed ? "Editor entfernen / Remove editor" : "Zum Editor machen / Make editor", onclick: function () { api("/api/admin/role/" + x.id, { method: "POST", body: { role: ed ? "user" : "editor" } }).then(load); } })]));
        });
      });
    }
    q.addEventListener("input", function () { clearTimeout(q._t); q._t = setTimeout(load, 300); });
    load();
    return h("section", { class: "ccard" }, [h("h2", { text: "Team" }), h("p", { class: "cmut", text: "Editoren veröffentlichen Wiki-Beiträge direkt und prüfen fremde Beiträge. / Editors publish wiki notes directly and review others." }), h("label", {}, [q]), res]);
  }

  /* ---------- Kommentare ---------- */
  function mountComments(root) {
    var list = h("div", { class: "clist" }), form = h("div", { class: "cform" });
    root.appendChild(h("h2", { text: tt("comments") })); root.appendChild(list); root.appendChild(form);
    var user = null, replyTo = null;
    function load() {
      return api("/api/comments?vid=" + encodeURIComponent(C.vid) + "&lang=" + LANG).then(function (r) {
        if (r.s !== 200) throw 0;
        list.textContent = "";
        var cs = r.j.comments, top = cs.filter(function (c) { return !c.parent; });
        if (!top.length) list.appendChild(h("p", { class: "cmut", text: tt("no_comments") }));
        top.forEach(function (c) { list.appendChild(item(c, false)); cs.filter(function (x) { return x.parent === c.id; }).forEach(function (x) { list.appendChild(item(x, true)); }); });
      });
    }
    function item(c, isReply) {
      var u = h("a", { href: C.communityUrl + "?u=" + c.user.id, text: c.user.name, class: "cuser" });
      var act = h("div", { class: "cact" });
      if (!c.hidden) {
        if (user && !c.mine) act.appendChild(h("button", { type: "button", class: "cbtn" + (c.liked ? " on" : ""), text: "👍 " + tt("like") + (c.likes ? " (" + c.likes + ")" : ""), onclick: function () { act1("/api/comments/" + c.id + "/like"); } }));
        else if (c.likes) act.appendChild(h("span", { class: "cmut", text: "👍 " + c.likes }));
        if (user && !isReply) act.appendChild(h("button", { type: "button", class: "cbtn", text: tt("reply"), onclick: function () { replyTo = c.id; box.focus(); box.placeholder = "↪ " + c.user.name; } }));
        if (user && !c.mine) act.appendChild(h("button", { type: "button", class: "cbtn", text: tt("report"), onclick: function () { act1("/api/comments/" + c.id + "/report", tt("reported")); } }));
        if (c.canDelete) act.appendChild(h("button", { type: "button", class: "cbtn", text: tt("delete"), onclick: function () { api("/api/comments/" + c.id, { method: "DELETE" }).then(load); } }));
      }
      return h("article", { class: "citem" + (isReply ? " reply" : "") }, [
        h("header", {}, [u, badgeEls(c.user.badges), h("time", { class: "cmut", text: date(c.created) })]),
        h("p", { class: "cbody", text: c.hidden ? "—" : c.body }), act]);
    }
    function act1(p, msg) { api(p, { method: "POST" }).then(function (r) { if (msg) note(msg); load(); }); }
    var box = h("textarea", { rows: 4, maxlength: 1500, placeholder: tt("comment_ph"), "aria-label": tt("comment_ph") }), msg = h("p", { class: "cmsg", role: "status" });
    function note(t) { msg.textContent = t; }
    var btn = h("button", { type: "button", class: "btn main", text: tt("post"), onclick: function () {
      btn.disabled = true;
      api("/api/comments", { method: "POST", body: { vid: C.vid, lang: LANG, body: box.value, parent: replyTo } }).then(function (r) {
        btn.disabled = false;
        if (r.s === 200) { box.value = ""; replyTo = null; box.placeholder = tt("comment_ph"); note(""); (r.j.earned || []).forEach(function (b) { note((ICON[b] || "★") + " " + tt("b_" + b) + "!"); }); load(); }
        else note(r.s === 429 ? tt("rate_limit") : r.j.error === "bad_request" ? tt("too_short") : tt("error"));
      }).catch(function () { btn.disabled = false; note(tt("error")); });
    } });
    me().then(function (u) { user = u; form.appendChild(u ? h("div", {}, [box, h("div", { class: "btns" }, [btn]), msg]) : loginBox()); return load(); })
      .catch(function () { root.hidden = true; });
  }

  /* ---------- Abo (Push + E-Mail) ---------- */
  var pushOK = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  function b64(s) { s = (s + "====".slice(s.length % 4 || 4)).replace(/-/g, "+").replace(/_/g, "/"); var r = atob(s), o = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) o[i] = r.charCodeAt(i); return o; }
  function mountSub(root) {
    var st = h("p", { class: "cmsg", role: "status" }), push = h("div", { class: "csub" }), mail = h("form", { class: "csub" });
    function setPush() {
      push.textContent = "";
      if (!pushOK) { push.appendChild(h("p", { class: "cmut", text: tt("push_unsupported") })); return; }
      navigator.serviceWorker.getRegistration("/").then(function (reg) { return reg ? reg.pushManager.getSubscription() : null; }).then(function (sub) {
        if (sub) {
          push.appendChild(h("span", { class: "cok", text: "✓ " + tt("push_on") + " " }));
          push.appendChild(h("button", { type: "button", class: "btn", text: tt("push_off"), onclick: function () { sub.unsubscribe().then(function () { return api("/api/push/unsubscribe", { method: "POST", body: { endpoint: sub.endpoint } }); }).then(setPush); } }));
        } else push.appendChild(h("button", { type: "button", class: "btn main", text: "🔔 " + tt("push_btn"), onclick: enable }));
      });
    }
    function enable() {
      if (Notification.permission === "denied") { st.textContent = tt("push_denied"); return; }
      Notification.requestPermission().then(function (p) {
        if (p !== "granted") { st.textContent = tt("push_denied"); return; }
        return navigator.serviceWorker.register("/sw.js").then(function () { return navigator.serviceWorker.ready; }).then(function (reg) {
          return api("/api/push/key").then(function (k) { return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64(k.j.key) }); });
        }).then(function (sub) { var j = sub.toJSON(); return api("/api/push/subscribe", { method: "POST", body: { endpoint: j.endpoint, keys: j.keys, lang: LANG } }); }).then(setPush);
      }).catch(function () { st.textContent = tt("error"); });
    }
    var em = h("input", { type: "email", required: "required", placeholder: tt("email_ph"), "aria-label": tt("email_ph"), autocomplete: "email" });
    mail.appendChild(em); mail.appendChild(h("button", { type: "submit", class: "btn", text: "✉ " + tt("email_btn") }));
    mail.addEventListener("submit", function (e) { e.preventDefault(); api("/api/email/subscribe", { method: "POST", body: { email: em.value, lang: LANG } }).then(function (r) { st.textContent = r.s === 200 ? tt("email_sent") : r.s === 429 ? tt("rate_limit") : tt("error"); if (r.s === 200) em.value = ""; }); });
    root.appendChild(h("h2", { text: tt("sub_title") })); root.appendChild(h("p", { class: "cmut", text: tt("sub_text") }));
    root.appendChild(push); root.appendChild(mail); root.appendChild(st); setPush();
    api("/api/push/key").catch(function () { root.hidden = true; });
  }

  /* ---------- Kurator / Bestenliste ---------- */
  function memberRow(u, i) {
    return h("li", {}, [h("span", { class: "cr", text: String(i + 1) }), h("a", { href: C.communityUrl + "?u=" + u.id, text: u.name }), badgeEls(u.badges), h("span", { class: "cmut", text: u.points + " " + tt("points") })]);
  }
  function mountCurator(root, full) {
    api("/api/curator?lang=" + LANG).then(function (r) {
      if (r.s !== 200) throw 0;
      root.appendChild(h("h2", { text: "🏆 " + tt(full ? "leaderboard" : "curator_title") }));
      var j = r.j;
      if (j.last) root.appendChild(h("p", { class: "ccur" }, ["🏆 " + j.last.month + ": ", h("a", { href: C.communityUrl + "?u=" + j.last.id, text: j.last.name }), " – " + j.last.points + " " + tt("points")]));
      if (!j.top.length) root.appendChild(h("p", { class: "cmut", text: tt("curator_none") }));
      else root.appendChild(h("ol", { class: "clb" }, j.top.map(memberRow)));
      if (!full) root.appendChild(h("p", {}, [h("a", { href: C.communityUrl, text: tt("community") + " →" })]));
    }).catch(function () { root.hidden = true; });
  }

  /* ---------- Community-Seite: Konto, Profil, Abzeichen ---------- */
  function mountPage(root) {
    var uid = new URLSearchParams(location.search).get("u");
    if (uid) {
      api("/api/u/" + encodeURIComponent(uid)).then(function (r) {
        if (r.s !== 200) { root.appendChild(h("p", { text: tt("error") })); return; }
        var j = r.j;
        var H=document.getElementById("c-h1");if(H)H.textContent=j.user.name;
        root.appendChild(badgeEls(j.badges, true));
        if (j.user.bio) root.appendChild(h("p", { text: j.user.bio }));
        root.appendChild(h("p", { class: "cmut", text: j.points + " " + tt("points") + " · " + j.comments + " " + tt("comments_count") + " · " + j.likes + " " + tt("likes_count") + " · " + tt("members_since") + " " + date(j.user.created) }));
        (j.curator || []).forEach(function (c) { root.appendChild(h("p", { text: "🏆 " + tt("curator_title") + ": " + c.month + " (" + c.lang + ")" })); });
      }).catch(function () { root.hidden = true; });
      return;
    }
    me().then(function (u) {
      if (!u) root.appendChild(loginBox());
      else {
        var name = h("input", { type: "text", maxlength: 40, value: u.name, "aria-label": tt("your_name") }), bio = h("textarea", { rows: 3, maxlength: 280, placeholder: tt("bio_ph"), "aria-label": tt("bio_ph") });
        bio.value = u.bio || "";
        var ok = h("span", { class: "cok" });
        root.appendChild(h("div", { class: "cprof" }, [
          h("h2", { text: tt("profile") }), h("p", { class: "cmut", text: u.points + " " + tt("points") + " · " + u.comments + " " + tt("comments_count") + " · " + u.likes + " " + tt("likes_count") }),
          h("label", { text: tt("your_name") }), name, bio,
          h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: tt("save"), onclick: function () { api("/api/me", { method: "POST", body: { name: name.value, bio: bio.value, lang: LANG } }).then(function (r) { ok.textContent = r.s === 200 ? "✓ " + tt("saved") : tt("error"); }); } }),
            h("button", { type: "button", class: "btn", text: tt("signout"), onclick: function () { api("/api/logout", { method: "POST" }).then(function () { location.reload(); }); } }), ok]),
          h("details", { class: "cdel" }, [h("summary", { text: tt("delete_account") }), h("p", { class: "cmut", text: tt("delete_account_d") }), h("button", { type: "button", class: "btn", text: tt("delete_account_btn"), onclick: function () { if (confirm(tt("delete_account_d"))) api("/api/me", { method: "DELETE" }).then(function () { location.reload(); }); } })])]));
      }
      var bd = h("div", { class: "cbadges" }, BADGES.map(function (b) { var got = u && u.badges.indexOf(b) > -1; return h("div", { class: "cbadge" + (got ? " got" : "") }, [h("span", { class: "cb big", text: ICON[b] }), h("div", {}, [h("b", { text: tt("b_" + b) }), h("span", { class: "cmut", text: tt("b_" + b + "_d") })])]); }));
      root.appendChild(h("h2", { text: tt("badges") })); root.appendChild(bd);
      if (u && u.admin) root.appendChild(teamPanel());
      var cur = h("section", { class: "ccard" }), sub = h("section", { class: "ccard" });
      root.appendChild(cur); root.appendChild(sub); mountCurator(cur, true); mountSub(sub);
    }).catch(function () { root.hidden = false; root.appendChild(h("p", { class: "cmut", role: "status", text: tt("error") })); });
  }

  function init() {
    var el;
    if ((el = document.getElementById("c-comments"))) mountComments(el);
    if ((el = document.getElementById("c-sub"))) mountSub(el);
    if ((el = document.getElementById("c-curator"))) mountCurator(el, false);
    if ((el = document.getElementById("c-page"))) mountPage(el);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
