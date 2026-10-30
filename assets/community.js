/* M365.FM Community: Kommentare, Abos, Kurator, Profil. Nutzt window.M365C = {api, lang, vid, t}. Texte nur per textContent. */
(function () {
  var C = window.M365C; if (!C || !C.api) return;
  var T = C.t || {}, API = C.api, LANG = C.lang, ICON = { editor: "✏️", wiki_author: "📖", author: "✍️", podcaster: "🎙️", videomaker: "🎬", newcomer: "🌱", first_comment: "💬", commentator: "🗣️", voice: "📣", helpful: "🤝", early_bird: "🐦", polyglot: "🌍", streak: "🔥", curator: "🏆", notified: "🔔", guardian: "🛡️", li_follower: "🔗", founder: "🏢", team_member: "👥", organizer: "📅", speaker: "🎤", recommender: "💌", recommended: "⭐", endorsed: "✅", endorser: "👍", connector: "💬", profile_pro: "🪪", entity_owner: "🧬", sponsor_open: "💼" };
  var BADGES = ["editor", "wiki_author", "author", "podcaster", "videomaker", "newcomer", "first_comment", "commentator", "voice", "helpful", "early_bird", "polyglot", "streak", "curator", "notified", "guardian", "li_follower", "founder", "team_member", "organizer", "speaker", "recommender", "recommended", "endorsed", "endorser", "connector", "profile_pro", "entity_owner", "sponsor_open"];
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

  function SPN(d, n, e) { return (document.documentElement.lang || "en").slice(0, 2) === "de" ? "Speaker " + d + " (" + n + " bestätigte Sessions)" : "Speaker " + (e || d) + " (" + n + " confirmed sessions)"; }
  var PGI = { speaker_bronze: "🥉", speaker_silver: "🥈", speaker_gold: "🥇", speaker_platinum: "💎", mvp: "🏆", mct: "🎓", rd: "🧭", msa: "🌟", ms_employee: "🪟", partner: "🤝" }, PGN = { speaker_bronze: SPN("Bronze", "1+"), speaker_silver: SPN("Silber", "3+", "Silver"), speaker_gold: SPN("Gold", "7+"), speaker_platinum: SPN("Platin", "15+", "Platinum"), mvp: "Microsoft MVP", mct: "Microsoft Certified Trainer", rd: "Microsoft Regional Director", msa: "Microsoft Student Ambassador", ms_employee: "Microsoft", partner: "Microsoft Partner" };
  function badgeEls(list, big) {
    return h("span", { class: "cbs" }, (list || []).map(function (b) { return h("span", { class: "cb" + (big ? " big" : ""), title: /^prog_/.test(b) ? PGN[b.slice(5)] : tt("b_" + b) + " – " + tt("b_" + b + "_d"), text: PGI[b.slice(5)] && /^prog_/.test(b) ? PGI[b.slice(5)] : (ICON[b] || "★") }); }));
  }
  function pruneLogin(box){var P=window.__m365p=window.__m365p||fetch(API+"/api/providers").then(function(r){return r.json()}).catch(function(){return null});P.then(function(j){if(!j||!j.providers)return;[].slice.call(box.querySelectorAll("a[href*=\"/auth/login/\"]")).forEach(function(a){var m=/login\/(\w+)/.exec(a.href);if(m&&j.providers.indexOf(m[1])<0)a.remove()})})}
  function loginBox() {
    var ret = encodeURIComponent(location.href.split("#")[0]);
    var lb = h("div", { class: "clogin" }, [
      h("p", { text: tt("login_to_comment") }),
      h("div", { class: "btns" }, [
        h("a", { class: "btn main", href: API + "/auth/login/google?return=" + ret, rel: "nofollow", text: tt("signin_google") }),
        h("a", { class: "btn", href: API + "/auth/login/microsoft?return=" + ret, rel: "nofollow", text: tt("signin_ms") }),
        h("a", { class: "btn", href: API + "/auth/login/linkedin?return=" + ret, rel: "nofollow", text: tt("signin_li") })]),
      h("small", {}, [tt("signin_note") + " ", h("a", { href: C.privacy, text: tt("privacy") })])]);
    pruneLogin(lb); return lb;
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
    var seedMsg = h("span", { class: "cmut" }), seedBtn = h("button", { type: "button", class: "btn", text: "M365Con 2027 als Event anlegen", onclick: function () { api("/api/events/seed-m365con", { method: "POST", body: {} }).then(function (r) { seedMsg.textContent = r.s === 200 ? (r.j.existed ? " bereits vorhanden" : " angelegt (nicht öffentlich) – Daten im Bereich Events pflegen") : " Fehler"; }); } });
    var cq = h("div"), cqh = h("h3", { text: "Zertifikat-Nachweise prüfen / Verify certificates" });
    api("/api/admin/cert-queue").then(function (r) {
      var items = (r.j && r.j.items) || []; if (r.s !== 200 || !items.length) { cqh.hidden = true; return; }
      items.forEach(function (it) {
        var row = h("p", {}, [h("b", { text: (it.name || it.handle || "?") + " · " + it.e.toUpperCase() + (it.year ? " (" + it.year + ")" : "") + " " })]);
        if (it.url) { var a = h("a", { href: it.url, target: "_blank", rel: "noopener nofollow", text: "Nachweis ↗ " }); row.appendChild(a); }
        function dec(v) { return function () { api("/api/admin/verify", { method: "POST", body: { owner: "u:" + it.handle, kind: "cert", key: it.e, value: v } }).then(function (x) { if (x.s === 200) row.remove(); }); }; }
        if (it.handle) { row.appendChild(h("button", { type: "button", class: "btn main", text: "Bestätigen", onclick: dec(true) })); row.appendChild(h("button", { type: "button", class: "btn", text: "Ablehnen", onclick: function () { row.remove(); } })); }
        cq.appendChild(row);
      });
    });
    return h("section", { class: "ccard" }, [h("h2", { text: "Team" }), h("p", {}, [seedBtn, seedMsg]), cqh, cq, h("p", { class: "cmut", text: "Editoren veröffentlichen Wiki-Beiträge direkt und prüfen fremde Beiträge. / Editors publish wiki notes directly and review others." }), h("label", {}, [q]), res]);
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
  var LI_URL = "https://www.linkedin.com/school/m365-show";
  function liCard(u, onDone, always) {
    var seen = false; try { seen = localStorage.getItem("m365li") === "1"; } catch (e) {}
    var has = u.badges.indexOf("li_follower") > -1;
    if (has || (!always && seen)) return null;
    var box = h("div", { class: "clogin" }), msg = h("span", { class: "cok" });
    box.appendChild(h("b", { text: tt("li_title") })); box.appendChild(h("p", { class: "cmut", text: tt("li_text") }));
    box.appendChild(h("div", { class: "btns" }, [
      h("a", { class: "btn main", href: LI_URL, target: "_blank", rel: "noopener", text: tt("li_open") }),
      h("button", { type: "button", class: "btn", text: tt("li_done"), onclick: function () { api("/api/me/li-follow", { method: "POST", body: {} }).then(function () { msg.textContent = tt("li_thanks"); try { localStorage.setItem("m365li", "1"); } catch (e) {} if (onDone) onDone(); }); } }),
      h("button", { type: "button", class: "btn", text: tt("li_later"), onclick: function () { try { localStorage.setItem("m365li", "1"); } catch (e) {} box.hidden = true; } }), msg]));
    return box;
  }
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
        var name = h("input", { type: "text", maxlength: 40, value: u.name, "aria-label": tt("your_name") }), mode = h("select", { "aria-label": tt("nm_label") }), opts = u.name_opts || {};
        [["short", "nm_short"], ["full", "nm_full"], ["first", "nm_first"], ["handle", "nm_handle"], ["custom", "nm_custom"]].forEach(function (x) { if (x[0] !== "custom" && !opts[x[0]]) return; mode.appendChild(h("option", { value: x[0], text: tt(x[1]) + (opts[x[0]] ? " – " + opts[x[0]] : "") })); });
        mode.value = u.name_mode || "short"; if (mode.value !== (u.name_mode || "short")) mode.value = "custom";
        function syncName() { var c = mode.value === "custom"; name.hidden = !c; nlab.hidden = !c; if (!c) name.value = opts[mode.value] || name.value; }
        var nlab = h("label", { text: tt("your_name") }); mode.addEventListener("change", syncName);
        var ok = h("span", { class: "cok" });
        var lic = liCard(u, function () { setTimeout(function () { location.reload(); }, 800); }, true) || (u.badges.indexOf("li_follower") < 0 ? null : h("a", { class: "btn", href: LI_URL, target: "_blank", rel: "noopener", text: tt("li_follow") }));
        if (lic) root.appendChild(lic);
        setTimeout(syncName, 0);
        root.appendChild(h("div", { class: "cprof" }, [
          h("h2", { text: tt("profile") }), h("p", { class: "cmut", text: u.points + " " + tt("points") + " · " + u.comments + " " + tt("comments_count") + " · " + u.likes + " " + tt("likes_count") }),
          h("label", { text: tt("nm_label") }), mode, nlab, name, h("p", { class: "cmut", text: tt("nm_hint") }),
          h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: tt("save"), onclick: function () { api("/api/me", { method: "POST", body: { name: name.value, name_mode: mode.value, lang: LANG } }).then(function (r) { ok.textContent = r.s === 200 ? "✓ " + tt("saved") : tt("error"); }); } }),
            h("button", { type: "button", class: "btn", text: tt("signout"), onclick: function () { api("/api/logout", { method: "POST" }).then(function () { location.reload(); }); } }), ok]),
          h("details", { class: "cdel" }, [h("summary", { text: tt("delete_account") }), h("p", { class: "cmut", text: tt("delete_account_d") }), h("button", { type: "button", class: "btn", text: tt("delete_account_btn"), onclick: function () { if (confirm(tt("delete_account_d"))) api("/api/me", { method: "DELETE" }).then(function () { location.reload(); }); } })])]));
      }
      var gotL = BADGES.filter(function (b) { return u && u.badges.indexOf(b) > -1; }), bd = h("div", { class: "cbadges" }, gotL.map(function (b) { return h("div", { class: "cbadge got" }, [h("span", { class: "cb big", text: ICON[b] }), h("div", {}, [h("b", { text: tt("b_" + b) }), h("span", { class: "cmut", text: tt("b_" + b + "_d") })])]); }));
      if (BADGES.length > gotL.length) bd.appendChild(h("div", { class: "cbadge" }, [h("span", { class: "cb big", text: "❔" }), h("div", {}, [h("b", { text: tt("hid").replace("{n}", BADGES.length - gotL.length) })])]));
      var ibox = h("div", { class: "ccard" }); root.appendChild(ibox);
      api("/api/edits/inbox").then(function (r) { if (r.s !== 200) return; var n = (r.j.entity || []).length + (r.j.wiki || []).length; if (!n) return;
        ibox.appendChild(h("h2", { text: "✏️ " + n + " offene Änderungsvorschläge" }));
        (r.j.entity || []).forEach(function (x) { ibox.appendChild(h("p", {}, [h("a", { href: "/entity/" + x.eid + "/", text: x.eid }), " – " + x.name + (x.summary ? ": " + x.summary : "")])); });
        (r.j.wiki || []).forEach(function (x) { ibox.appendChild(h("p", { class: "cmut", text: "Wiki: " + x.term + " (" + x.lang + ") – " + x.name })); }); });
      var ebox = h("div", { class: "ccard" }); root.appendChild(ebox);
      api("/api/events/mine").then(function (r) { var l = (r.j && r.j.events) || []; if (r.s !== 200 || !l.length) return; var de = (document.documentElement.lang || "en").slice(0, 2) === "de";
        ebox.appendChild(h("h2", { text: de ? "Meine Events" : "My events" }));
        l.forEach(function (e) { ebox.appendChild(h("p", {}, [h("b", { text: e.title }), " · " + e.start + (e.public ? "" : (de ? " · nicht öffentlich" : " · not public")) + " ", h("a", { class: "btn", href: "#c-events", text: de ? "Bearbeiten" : "Edit" }), " ", h("a", { href: (de ? "/de" : "") + "/community/events/" + e.handle + "/", text: de ? "Öffentliche Seite" : "Public page" })])); }); });
      var kbox = h("div", { class: "ccard" }); root.appendChild(kbox);
      (function aiTokens() { var de = (document.documentElement.lang || "en").slice(0, 2) === "de", msg = h("p", { class: "cok", role: "status", "aria-live": "polite" }), list = h("ul");
        kbox.appendChild(h("h2", { text: de ? "KI-Zugang (MCP)" : "AI access (MCP)" }));
        kbox.appendChild(h("p", { class: "cmut" }, [de ? "Verbinde Claude oder ChatGPT mit deinem Konto, damit deine KI dein Profil ausfüllt und Vorschläge macht. " : "Connect Claude or ChatGPT to your account so your AI can fill in your profile and make suggestions. ", h("a", { href: (de ? "/de" : "") + "/community/mcp/", text: de ? "Anleitung" : "How-to" })]));
        kbox.appendChild(h("p", { class: "cmut" }, [h("a", { href: "/m365-fm-skill/SKILL.md", download: "SKILL.md", text: de ? "Skill-Datei herunterladen (Anleitung für deine KI, was man hier anlegen kann)" : "Download skill file (guide for your AI on what can be created here)" })]));
        function load() { api("/api/ai-token").then(function (r) { list.textContent = ""; ((r.j && r.j.tokens) || []).forEach(function (t) { list.appendChild(h("li", {}, [t.label + " · " + new Date(t.created * 1000).toLocaleDateString() + (t.last_used ? " · " + (de ? "zuletzt genutzt " : "last used ") + new Date(t.last_used * 1000).toLocaleDateString() : "") + " ", h("button", { type: "button", class: "btn", text: de ? "Widerrufen" : "Revoke", onclick: function () { api("/api/ai-token/" + t.id, { method: "DELETE" }).then(load); } })])); }); }); }
        kbox.appendChild(list); kbox.appendChild(h("button", { type: "button", class: "btn main", text: de ? "Neuen Zugangstoken erzeugen" : "Create new access token", onclick: function () {
          api("/api/ai-token", { method: "POST", body: { label: "KI-Zugang" } }).then(function (r) { if (r.s !== 200) { msg.textContent = de ? "Nicht möglich (max. 5 Tokens)." : "Not possible (max. 5 tokens)."; return; } msg.textContent = ""; var box = h("p", {}, [h("code", { text: r.j.token }), " ", h("button", { type: "button", class: "btn", text: de ? "Kopieren" : "Copy", onclick: function (e) { try { navigator.clipboard.writeText(r.j.token); e.target.textContent = "✓"; } catch (x) {} } })]); kbox.appendChild(h("p", { class: "cmut", text: de ? "Wird nur einmal angezeigt. Wie ein Passwort behandeln." : "Shown only once. Treat it like a password." })); kbox.appendChild(box); load(); }); } }));
        kbox.appendChild(msg); load(); })();
      var pbox = h("div", { class: "ccard" }, [h("h2", { text: tt("points_t") })]); root.appendChild(pbox);
      api("/api/points").then(function (pr) { if (pr.s !== 200) return; var d = pr.j, msg = h("p", { class: "cok", role: "status", "aria-live": "polite" });
        pbox.appendChild(h("p", { text: tt("points_bal").replace("{b}", d.balance).replace("{e}", d.earned) }));
        d.catalog.forEach(function (it) { pbox.appendChild(h("div", { class: "btns" }, [h("span", { text: tt("it_" + it.id) + " – " + it.cost }), h("button", { type: "button", class: "btn", text: tt("redeem"), disabled: d.balance < it.cost ? "disabled" : null, onclick: function () {
          api("/api/points/redeem", { method: "POST", body: { item: it.id } }).then(function (r) { msg.textContent = r.s === 200 ? (r.j.status === "pending" ? tt("ok_pending") : tt("ok_done")) : tt("not_enough"); if (r.s === 200) setTimeout(function () { location.reload(); }, 1200); }); } })])); });
        pbox.appendChild(msg); });
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
