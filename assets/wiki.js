/* Community-Wiki (Glossar + Entitaeten). Nutzt window.M365W = {api, term, lang, t, links:{id:[name,url]}}.
   Markup: ## / ### Ueberschrift, **fett**, *kursiv*, "- " und "1. " Listen, "> " Zitat, [[id|Text]] interne Links,
   {{ref|Titel|https://url|Herausgeber|Datum}} Quelle (Fussnote), {{cn}} = Beleg fehlt. Ausgabe nur ueber DOM-Knoten (kein innerHTML). */
(function () {
  var W = window.M365W; if (!W || !W.api) return;
  var T = W.t || {}, L = W.links || {}, root = document.getElementById("c-wiki"); if (!root) return;
  function h(tag, a, kids) { var e = document.createElement(tag); for (var k in (a || {})) { if (k === "class") e.className = a[k]; else if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }); return e; }
  function txt(s) { return document.createTextNode(s); }
  function api(path, o) { o = o || {}; o.credentials = "include"; o.headers = Object.assign({ "x-requested-with": "m365" }, o.headers || {}); if (o.body && typeof o.body !== "string") { o.body = JSON.stringify(o.body); o.headers["content-type"] = "application/json"; } return fetch(W.api + path, o).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); }); }
  function date(ts) { try { return new Date(ts * 1000).toLocaleDateString(W.lang === "en" ? undefined : W.lang); } catch (e) { return ""; } }

  /* ---------- Darstellung ---------- */
  var INL = /\{\{img\|([^{}|]*)\|([^{}]*)\}\}|\{\{ref\|([^{}]*)\}\}|\{\{cn\}\}|\[\[([a-z0-9-]{2,48})(?:\|([^\[\]]{1,80}))?\]\]|\*\*([^*]+?)\*\*|\*([^*\s][^*]*?)\*/;
  function host(u) { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return u; } }
  function inline(text, ctx, parent) {
    while (text) {
      var m = INL.exec(text);
      if (!m) { parent.appendChild(txt(text)); break; }
      if (m.index) parent.appendChild(txt(text.slice(0, m.index)));
      if (m[0].indexOf("{{img|") === 0) {
        var im = h("img", { src: m[1], alt: m[2], loading: "lazy", decoding: "async", referrerpolicy: "no-referrer" }); im.style.maxWidth = "100%"; im.style.height = "auto"; parent.appendChild(im);
      } else if (m[0].indexOf("{{ref|") === 0) {
        var p = m[3].split("|"), key = p[1] + "|" + p[0], n = ctx.keys[key];
        if (!n) { ctx.refs.push({ title: p[0], url: p[1], pub: p[2] || "", date: p[3] || "" }); n = ctx.keys[key] = ctx.refs.length; }
        var fa = h("a", { href: "#wkref-" + n, text: "[" + n + "]" }); if (!ctx.seen[n]) { fa.id = "wkfn-" + n; ctx.seen[n] = 1; }
        parent.appendChild(h("sup", { class: "wk-fn" }, [fa]));
      } else if (m[0] === "{{cn}}") {
        parent.appendChild(h("sup", { class: "wk-cn" }, [h("span", { text: "[" + T.cn + "]" })]));
      } else if (m[4]) {
        var t = L[m[4]];
        if (t) parent.appendChild(h("a", { href: t[1], text: m[5] || t[0] })); else parent.appendChild(txt(m[5] || m[4]));
      } else if (m[6] != null) { var b = h("strong"); inline(m[6], ctx, b); parent.appendChild(b); }
      else { var i = h("em"); inline(m[7], ctx, i); parent.appendChild(i); }
      text = text.slice(m.index + m[0].length);
    }
  }
  function renderWiki(body) {
    var ctx = { refs: [], keys: {}, seen: {} }, out = document.createDocumentFragment(), lines = body.split("\n"), para = [], list = null, heads = [], hn = 0;
    function flushP() { if (para.length) { var p = h("p"); inline(para.join(" "), ctx, p); out.appendChild(p); para = []; } }
    function flushL() { list = null; }
    lines.forEach(function (ln) {
      var m;
      if (!ln.trim()) { flushP(); flushL(); return; }
      if ((m = /^(#{2,3})\s+(.+)$/.exec(ln))) {
        flushP(); flushL(); var lv = m[1].length === 2 ? 3 : 4, id = "wk-h-" + (++hn), hd = h("h" + lv, { id: id }); inline(m[2], ctx, hd); out.appendChild(hd);
        if (lv === 3) heads.push([id, m[2].replace(/\*|\[\[[^\]|]*\|?|\]\]|\{\{[^}]*\}\}/g, "")]); return;
      }
      if ((m = /^(-|\d+\.)\s+(.+)$/.exec(ln))) {
        flushP(); var ord = m[1] !== "-";
        if (!list || list.ord !== ord) { list = { ord: ord, el: h(ord ? "ol" : "ul") }; out.appendChild(list.el); }
        var li = h("li"); inline(m[2], ctx, li); list.el.appendChild(li); return;
      }
      if ((m = /^>\s?(.+)$/.exec(ln))) { flushP(); flushL(); var q = h("blockquote"); var qp = h("p"); inline(m[1], ctx, qp); q.appendChild(qp); out.appendChild(q); return; }
      flushL(); para.push(ln.trim());
    });
    flushP();
    if (heads.length >= 3) {
      var nav = h("nav", { class: "wk-toc", "aria-label": T.toc }, [h("b", { text: T.toc })]), ol = h("ol");
      heads.forEach(function (x) { ol.appendChild(h("li", {}, [h("a", { href: "#" + x[0], text: x[1] })])); }); nav.appendChild(ol);
      out.insertBefore(nav, out.firstChild);
    }
    if (ctx.refs.length) {
      out.appendChild(h("h3", { class: "wk-refh", text: T.refs }));
      var rl = h("ol", { class: "wk-refs" });
      ctx.refs.forEach(function (r, i) {
        var li = h("li", { id: "wkref-" + (i + 1) }, [h("a", { href: "#wkfn-" + (i + 1), class: "wk-back", "aria-label": T.back, text: "↑" }), txt(" " + r.title + (r.pub ? " – " + r.pub : "") + (r.date ? " (" + r.date + ")" : "") + " · "),
          h("a", { href: r.url, rel: "nofollow ugc noopener", target: "_blank", text: host(r.url) })]);
        rl.appendChild(li);
      });
      out.appendChild(rl);
    }
    return out;
  }
  window.M365Wrender = renderWiki;

  /* ---------- Versionsvergleich (zeilenweise) ---------- */
  function diff(a, b) {
    var x = a.split("\n"), y = b.split("\n"), n = x.length, m = y.length, d = [], i, j;
    if (n * m > 90000) return [[0, "…"]];
    for (i = 0; i <= n; i++) { d.push(new Array(m + 1).fill(0)); }
    for (i = n - 1; i >= 0; i--) for (j = m - 1; j >= 0; j--) d[i][j] = x[i] === y[j] ? d[i + 1][j + 1] + 1 : Math.max(d[i + 1][j], d[i][j + 1]);
    var out = []; i = 0; j = 0;
    while (i < n && j < m) { if (x[i] === y[j]) { out.push([0, x[i]]); i++; j++; } else if (d[i + 1][j] >= d[i][j + 1]) { out.push([-1, x[i++]]); } else { out.push([1, y[j++]]); } }
    while (i < n) out.push([-1, x[i++]]); while (j < m) out.push([1, y[j++]]);
    return out;
  }

  var box = h("div", { class: "wk" }); root.appendChild(box);
  function pruneLogin(box){var P=window.__m365p=window.__m365p||fetch(W.api+"/api/providers").then(function(r){return r.json()}).catch(function(){return null});P.then(function(j){if(!j||!j.providers)return;[].slice.call(box.querySelectorAll("a[href*=\"/auth/login/\"]")).forEach(function(a){var m=/login\/(\w+)/.exec(a.href);if(m&&j.providers.indexOf(m[1])<0)a.remove()})})}
  function login() { var b = login0(); pruneLogin(b); return b; }
  function login0() { var ret = encodeURIComponent(location.href.split("#")[0]); return h("div", { class: "wk-login" }, [h("p", { text: T.login }), h("div", { class: "btns" }, [h("a", { class: "btn main", href: W.api + "/auth/login/google?return=" + ret, rel: "nofollow", text: "Google" }), h("a", { class: "btn", href: W.api + "/auth/login/microsoft?return=" + ret, rel: "nofollow", text: "Microsoft" }), h("a", { class: "btn", href: W.api + "/auth/login/linkedin?return=" + ret, rel: "nofollow", text: "LinkedIn" })])]); }

  /* ---------- Editor ---------- */
  function editor(d, cur) {
    var ed = h("div", { class: "wk-form" });
    var ta = h("textarea", { rows: 14, maxlength: 12000, id: "wk-ta", "aria-label": T.edit, spellcheck: "true" }); ta.value = (d.mine && d.mine.body) || (cur && cur.body) || "";
    var prev = h("div", { class: "wk-body wk-prev", hidden: "" }), panel = h("div", { class: "wk-panel", hidden: "" }), msg = h("p", { class: "wk-msg", role: "status", "aria-live": "polite" });
    function ins(before, after, ph) {
      var s = ta.selectionStart, e = ta.selectionEnd, sel = ta.value.slice(s, e) || ph || "";
      ta.setRangeText(before + sel + after, s, e, "end"); ta.focus();
    }
    function lineStart(prefix) { var s = ta.selectionStart, v = ta.value, ls = v.lastIndexOf("\n", s - 1) + 1; ta.setRangeText(prefix, ls, ls, "end"); ta.focus(); }
    function btn(label, title, fn) { return h("button", { type: "button", class: "wk-tb", title: title, "aria-label": title, text: label, onclick: fn }); }
    function openPanel(kind) {
      panel.textContent = ""; panel.hidden = false;
      if (kind === "link") {
        var dl = h("datalist", { id: "wk-dl" }); Object.keys(L).sort().forEach(function (id) { dl.appendChild(h("option", { value: L[id][0] })); });
        var inp = h("input", { type: "text", list: "wk-dl", placeholder: T.link_ph, "aria-label": T.link_ph, maxlength: 80 });
        panel.appendChild(dl); panel.appendChild(inp);
        panel.appendChild(h("button", { type: "button", class: "btn main", text: T.insert, onclick: function () {
          var v = inp.value.trim().toLowerCase(), id = null; Object.keys(L).forEach(function (k) { if (L[k][0].toLowerCase() === v || k === v) id = k; });
          if (!id) { inp.setAttribute("aria-invalid", "true"); return; } panel.hidden = true; ins("[[" + id + "|", "]]", L[id][0]);
        } }));
      } else {
        var f = {}; [["title", T.ref_title, 200], ["url", "https://…", 300], ["pub", T.ref_pub, 80], ["date", T.ref_date, 20]].forEach(function (x) {
          f[x[0]] = h("input", { type: "text", placeholder: x[1], "aria-label": x[1], maxlength: x[2] }); panel.appendChild(f[x[0]]);
        });
        panel.appendChild(h("button", { type: "button", class: "btn main", text: T.insert, onclick: function () {
          var u = f.url.value.trim(); if (!f.title.value.trim() || !/^https:\/\//i.test(u)) { f.url.setAttribute("aria-invalid", "true"); return; }
          panel.hidden = true; var c = function (s) { return s.replace(/[|{}\[\]]/g, " ").trim(); };
          ta.setRangeText("{{ref|" + c(f.title.value) + "|" + u + "|" + c(f.pub.value) + "|" + c(f.date.value) + "}}", ta.selectionEnd, ta.selectionEnd, "end"); ta.focus();
        } }));
      }
      panel.appendChild(h("button", { type: "button", class: "btn", text: T.cancel, onclick: function () { panel.hidden = true; ta.focus(); } }));
      var first = panel.querySelector("input"); if (first) first.focus();
    }
    var tb = h("div", { class: "wk-bar", role: "toolbar", "aria-label": T.toolbar }, [
      btn("H", T.tb_h, function () { lineStart("## "); }), btn("B", T.tb_b, function () { ins("**", "**", T.tb_b); }), btn("I", T.tb_i, function () { ins("*", "*", T.tb_i); }),
      btn("•", T.tb_ul, function () { lineStart("- "); }), btn("1.", T.tb_ol, function () { lineStart("1. "); }), btn("❝", T.tb_q, function () { lineStart("> "); }),
      btn("[[ ]]", T.tb_link, function () { openPanel("link"); }), btn("[1]", T.tb_ref, function () { openPanel("ref"); }), btn("[" + T.cn + "]", T.tb_cn, function () { ins("{{cn}}", "", ""); })]);
    var pv = h("button", { type: "button", class: "btn", text: T.preview, "aria-pressed": "false", onclick: function () {
      var on = prev.hidden; prev.hidden = !on; ta.hidden = on; tb.hidden = on; panel.hidden = true; pv.setAttribute("aria-pressed", on ? "true" : "false"); pv.textContent = on ? T.back_edit : T.preview;
      if (on) { prev.textContent = ""; prev.appendChild(renderWiki(ta.value)); }
    } });
    var sm = h("input", { type: "text", maxlength: 140, placeholder: T.summary, "aria-label": T.summary });
    var save = h("button", { type: "button", class: "btn main", text: T.save, onclick: function () {
      save.disabled = true; api("/api/wiki", { method: "POST", body: { term: W.term, lang: W.lang, body: ta.value, summary: sm.value } }).then(function (r) {
        save.disabled = false;
        if (r.s === 200) { msg.textContent = r.j.status === "live" ? T.saved_live : T.saved_pending; if (r.j.status === "live") load(); }
        else msg.textContent = ({ too_short: T.too_short, unchanged: T.unchanged, rate_limit: T.rate, bad_ref: T.bad_ref, too_many_refs: T.bad_ref })[r.j.error] || T.error;
      }).catch(function () { save.disabled = false; msg.textContent = T.error; }); } });
    ed.appendChild(h("p", { class: "cmut", text: T.rules })); if (d.mine) ed.appendChild(h("p", { class: "cmut", text: T.pending_own }));
    [tb, panel, ta, prev, sm, h("div", { class: "btns" }, [save, pv]), msg].forEach(function (x) { ed.appendChild(x); });
    return ed;
  }

  /* ---------- Seite ---------- */
  function render(d) {
    box.textContent = ""; var st = root.querySelector(".wk-static"); if (st) st.remove();
    var cur = d.live;
    if (cur) {
      var bd = h("div", { class: "wk-body" }); bd.appendChild(renderWiki(cur.body)); box.appendChild(bd);
      box.appendChild(h("p", { class: "wk-meta" }, [T.by.replace("{n}", cur.name || T.anon).replace("{d}", date(cur.created)), " ",
        d.loggedIn ? h("button", { type: "button", class: "wk-link", text: T.report, onclick: function (e) { api("/api/wiki/report/" + cur.id, { method: "POST" }).then(function (r) { e.target.textContent = r.s === 200 ? T.reported : T.error; e.target.disabled = true; }); } }) : null]));
    } else box.appendChild(h("p", { class: "wk-empty", text: T.empty }));
    var det = h("details", { class: "wk-edit" }, [h("summary", { text: cur ? T.edit : T.add })]);
    det.appendChild(d.loggedIn ? editor(d, cur) : login()); box.appendChild(det);
    var hist = d.history || [];
    if (hist.length > 1) {
      var hd = h("details", { class: "wk-hist" }, [h("summary", { text: T.history })]), ul = h("ul", { class: "wk-hl" });
      hist.forEach(function (x, i) {
        var prevRev = hist[i + 1], li = h("li", {}, [h("span", { text: date(x.created) + " · " + (x.name || T.anon) + (x.summary ? " – " + x.summary : "") + (i === 0 ? " (" + T.current + ")" : "") + " " })]);
        if (prevRev) {
          var dd = h("details", { class: "wk-diff" }, [h("summary", { text: T.changes })]), pre = h("div", { class: "wk-dl", role: "group", "aria-label": T.changes });
          diff(prevRev.body, x.body).forEach(function (r) { if (r[0] !== 0) pre.appendChild(h("div", { class: r[0] > 0 ? "wk-add" : "wk-del" }, [h("b", { "aria-hidden": "true", text: r[0] > 0 ? "+ " : "− " }), h("span", { class: "sr", text: r[0] > 0 ? T.added + ": " : T.removed + ": " }), txt(r[1])])); });
          dd.appendChild(pre); li.appendChild(dd);
        }
        if (d.admin && i > 0) li.appendChild(h("button", { type: "button", class: "wk-link", text: T.restore, onclick: function () { api("/api/admin/wiki/approve/" + x.id, { method: "POST" }).then(load); } }));
        ul.appendChild(li);
      });
      hd.appendChild(ul); box.appendChild(hd);
    }
    if (d.admin) adminQueue(); else voteQueue();
  }
  function voteQueue() {
    var de = (document.documentElement.lang || "en").slice(0, 2) === "de";
    api("/api/edits/pending?kind=wiki&key=" + encodeURIComponent(W.term) + "&lang=" + W.lang).then(function (r) {
      var l = (r.j.edits || []).filter(function (x) { return !x.own; }); if (r.s !== 200 || !l.length) return;
      var sec = h("div", { class: "wk-admin" }, [h("h3", { text: de ? "Offene Änderungen – die Community stimmt ab" : "Open edits – the community votes" })]);
      l.forEach(function (x) {
        var pb = h("div", { class: "wk-body" }); pb.appendChild(renderWiki(x.body)); var st = h("span", { class: "cmut", text: x.net + " / " + x.need });
        function vote(v) { api("/api/edits/vote", { method: "POST", body: { kind: "wiki", id: x.id, v: v } }).then(function (z) { if (z.s === 200) { st.textContent = z.j.net + " / " + z.j.need; if (z.j.status !== "pending") load(); } }); }
        sec.appendChild(h("div", { class: "wk-pend" }, [h("p", { class: "cmut", text: x.name + (x.summary ? " – " + x.summary : "") }), pb,
          r.j.can_vote ? h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: "👍", "aria-label": de ? "Zustimmen" : "Approve", onclick: function () { vote(1); } }), h("button", { type: "button", class: "btn", text: "👎", "aria-label": de ? "Ablehnen" : "Reject", onclick: function () { vote(-1); } }), " ", st]) : st]));
      });
      box.appendChild(sec);
    });
  }
  function adminQueue() {
    api("/api/admin/wiki/pending").then(function (r) {
      var list = (r.j.pending || []).filter(function (x) { return x.term === W.term && x.lang === W.lang; }); if (!list.length) return;
      var sec = h("div", { class: "wk-admin" }, [h("h3", { text: T.pending })]);
      list.forEach(function (x) {
        var pb = h("div", { class: "wk-body" }); pb.appendChild(renderWiki(x.body));
        sec.appendChild(h("div", { class: "wk-pend" }, [h("p", { class: "cmut", text: x.name + (x.summary ? " – " + x.summary : "") }), pb,
          h("div", { class: "btns" }, [h("button", { type: "button", class: "btn main", text: T.approve, onclick: function () { api("/api/admin/wiki/approve/" + x.id, { method: "POST" }).then(load); } }), h("button", { type: "button", class: "btn", text: T.reject, onclick: function () { api("/api/admin/wiki/reject/" + x.id, { method: "POST" }).then(load); } })])]));
      });
      box.appendChild(sec);
    });
  }
  function load() { return api("/api/wiki?term=" + encodeURIComponent(W.term) + "&lang=" + W.lang).then(function (r) { if (r.s === 200) render(r.j); else throw 0; }).catch(function () { if (!box.firstChild) box.appendChild(h("p", { class: "wk-empty", text: T.error })); }); }
  load();
})();
