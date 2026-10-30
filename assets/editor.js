/* Editor: Werkzeugleiste + Live-Vorschau (Schreiben | Vorschau nebeneinander) fuer Blog und Bibliothek */
(function () {
  var U = window.M365U; if (!U) return;
  var h = U.h, de = (window.M365X || {}).lang === "de";
  var T = de ? { h2: "Überschrift", h3: "Zwischenüberschrift", b: "Fett", i: "Kursiv", ul: "Liste", ol: "Nummerierte Liste", q: "Zitat", link: "Link auf ein Thema", ref: "Quelle einfügen", write: "Schreiben", prev: "Vorschau", empty: "Hier erscheint die Vorschau, sobald du schreibst.", chars: "Zeichen", refs: "Quellen", rtitle: "Titel der Quelle", rurl: "https://…", rpub: "Herausgeber", rdate: "Datum", add: "Einfügen", topic: "Thema-ID (z. B. power-bi)", ttext: "Linktext", bold: "fetter Text", ital: "kursiver Text", txt: "Text" }
    : { h2: "Heading", h3: "Subheading", b: "Bold", i: "Italic", ul: "List", ol: "Numbered list", q: "Quote", link: "Link to a topic", ref: "Insert source", write: "Write", prev: "Preview", empty: "The preview appears as soon as you start writing.", chars: "characters", refs: "Sources", rtitle: "Source title", rurl: "https://…", rpub: "Publisher", rdate: "Date", add: "Insert", topic: "Topic id (e.g. power-bi)", ttext: "Link text", bold: "bold text", ital: "italic text", txt: "text" };

  function inline(s, parent, ctx) {
    var re = /\{\{ref\|([^{}]*)\}\}|\{\{cn\}\}|\[\[([^\]|]+)\|?([^\]]*)\]\]|\*\*([^*]+)\*\*|\*([^*]+)\*/, m;
    while ((m = re.exec(s))) {
      if (m.index) parent.appendChild(document.createTextNode(s.slice(0, m.index)));
      if (m[1] != null) { var p = m[1].split("|"); ctx.refs.push(p); var sup = h("sup", { class: "ed-ref", text: "[" + ctx.refs.length + "]" }); parent.appendChild(sup); }
      else if (m[0] === "{{cn}}") parent.appendChild(h("sup", { class: "ed-cn", text: "[?]" }));
      else if (m[2] != null) parent.appendChild(h("span", { class: "ed-topic", text: m[3] || m[2] }));
      else if (m[4] != null) parent.appendChild(h("strong", { text: m[4] }));
      else parent.appendChild(h("em", { text: m[5] }));
      s = s.slice(m.index + m[0].length);
    }
    if (s) parent.appendChild(document.createTextNode(s));
  }
  function render(body, into) {
    into.textContent = ""; var ctx = { refs: [] }, para = [], list = null;
    function fp() { if (para.length) { var p = h("p"); inline(para.join(" "), p, ctx); into.appendChild(p); para = []; } }
    body.split("\n").forEach(function (ln) {
      var m; if (!ln.trim()) { fp(); list = null; return; }
      if ((m = /^(#{2,3})\s+(.+)$/.exec(ln))) { fp(); list = null; var hd = h(m[1].length === 2 ? "h3" : "h4"); inline(m[2], hd, ctx); into.appendChild(hd); return; }
      if ((m = /^(-|\d+\.)\s+(.+)$/.exec(ln))) { fp(); var ord = m[1] !== "-"; if (!list || list.o !== ord) { list = { o: ord, el: h(ord ? "ol" : "ul") }; into.appendChild(list.el); } var li = h("li"); inline(m[2], li, ctx); list.el.appendChild(li); return; }
      if ((m = /^>\s?(.+)$/.exec(ln))) { fp(); list = null; var q = h("blockquote"), qp = h("p"); inline(m[1], qp, ctx); q.appendChild(qp); into.appendChild(q); return; }
      list = null; para.push(ln.trim());
    });
    fp();
    if (ctx.refs.length) { into.appendChild(h("h4", { text: T.refs })); var ol = h("ol", { class: "ed-refs" }); ctx.refs.forEach(function (r) { ol.appendChild(h("li", { text: (r[0] || "") + (r[2] ? " – " + r[2] : "") + (r[3] ? " (" + r[3] + ")" : "") + (r[1] ? " · " + r[1].replace(/^https?:\/\//, "").split("/")[0] : "") })); }); into.appendChild(ol); }
    if (!body.trim()) into.appendChild(h("p", { class: "mut", text: T.empty }));
  }

  U.editor = function (ta, max) {
    ta.className = "ed-ta"; ta.setAttribute("spellcheck", "true");
    var pv = h("div", { class: "ed-pv wk-body", "aria-live": "polite" }), cnt = h("span", { class: "mut ed-cnt" }), panel = h("div", { class: "ed-panel", hidden: "" });
    function sel() { return [ta.selectionStart, ta.selectionEnd]; }
    function put(a, b, ph) { var s = sel(), v = ta.value, mid = v.slice(s[0], s[1]) || ph || ""; ta.value = v.slice(0, s[0]) + a + mid + b + v.slice(s[1]); ta.focus(); ta.setSelectionRange(s[0] + a.length, s[0] + a.length + mid.length); upd(); }
    function line(pre) { var s = sel()[0], v = ta.value, st = v.lastIndexOf("\n", s - 1) + 1; ta.value = v.slice(0, st) + pre + v.slice(st); ta.focus(); ta.setSelectionRange(s + pre.length, s + pre.length); upd(); }
    function fields(list, done) {
      panel.textContent = ""; panel.hidden = false; var els = list.map(function (f) { var e = h("input", { type: "text", maxlength: 300, placeholder: f[1], "aria-label": f[1] }); e.value = f[2] || ""; panel.appendChild(e); return e; });
      panel.appendChild(h("button", { type: "button", class: "btn main", text: T.add, onclick: function () { if (done(els.map(function (e) { return e.value.trim(); })) !== false) panel.hidden = true; } }));
      panel.appendChild(h("button", { type: "button", class: "btn", text: "✕", "aria-label": "Close", onclick: function () { panel.hidden = true; ta.focus(); } })); els[0].focus();
    }
    function btn(l, t, fn, cls) { return h("button", { type: "button", class: "ed-b " + (cls || ""), title: t, "aria-label": t, text: l, onclick: fn }); }
    var bar = h("div", { class: "ed-bar", role: "toolbar" }, [
      btn("H2", T.h2, function () { line("## "); }), btn("H3", T.h3, function () { line("### "); }), btn("B", T.b, function () { put("**", "**", T.bold); }, "ed-bold"), btn("I", T.i, function () { put("*", "*", T.ital); }, "ed-ital"),
      btn("•", T.ul, function () { line("- "); }), btn("1.", T.ol, function () { line("1. "); }), btn("❝", T.q, function () { line("> "); }),
      btn("[[ ]]", T.link, function () { var s = sel(); fields([["id", T.topic], ["t", T.ttext, ta.value.slice(s[0], s[1])]], function (v) { if (!v[0]) return false; put("[[" + v[0].toLowerCase().replace(/[^a-z0-9-]/g, "-") + "|" + (v[1] || v[0]) + "]]", "", ""); }); }),
      btn("[1] " + T.refs, T.ref, function () { fields([["t", T.rtitle], ["u", T.rurl], ["p", T.rpub], ["d", T.rdate]], function (v) { if (!v[0] || !/^https:\/\//.test(v[1])) return false; put("{{ref|" + v.join("|") + "}}", "", ""); }); }, "ed-wide")]);
    function upd() { render(ta.value, pv); cnt.textContent = ta.value.length + (max ? " / " + max : "") + " " + T.chars; }
    ta.addEventListener("input", upd); ta.addEventListener("keydown", function (e) { if ((e.ctrlKey || e.metaKey) && e.key === "b") { e.preventDefault(); put("**", "**", T.bold); } if ((e.ctrlKey || e.metaKey) && e.key === "i") { e.preventDefault(); put("*", "*", T.ital); } });
    var left = h("div", { class: "ed-left" }, [h("div", { class: "ed-cap", text: T.write }), bar, panel, ta, cnt]), right = h("div", { class: "ed-right" }, [h("div", { class: "ed-cap", text: T.prev }), pv]);
    var wrap = h("div", { class: "ed-wrap" }, [left, right]); upd(); wrap.refresh = upd; return wrap;
  };
})();
