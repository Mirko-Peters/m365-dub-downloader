/* Editor: Werkzeugleiste + Live-Vorschau (Schreiben | Vorschau nebeneinander) fuer Blog und Bibliothek */
(function () {
  var U = window.M365U; if (!U) return;
  var h = U.h, de = (window.M365X || {}).lang === "de";
  var T = de ? { img: "Bild einfügen (https, .jpg/.png/.webp, Alt-Text Pflicht)", imgurl: "Bild-Adresse (https://…/bild.jpg)", imgalt: "Alt-Text (beschreibt das Bild, mind. 5 Zeichen)", h2: "Überschrift", h3: "Zwischenüberschrift", b: "Fett", i: "Kursiv", ul: "Liste", ol: "Nummerierte Liste", q: "Zitat", link: "Link auf ein Thema", ref: "Quelle einfügen", write: "Schreiben", prev: "Vorschau", empty: "Hier erscheint die Vorschau, sobald du schreibst.", chars: "Zeichen", refs: "Quellen", rtitle: "Titel der Quelle", rurl: "https://…", rpub: "Herausgeber", rdate: "Datum", add: "Einfügen", topic: "Thema-ID (z. B. power-bi)", ttext: "Linktext", bold: "fetter Text", ital: "kursiver Text", txt: "Text", vis: "Visuell", html: "HTML", md: "Markdown", htmlhint: "HTML einfügen oder bearbeiten – erlaubt sind Überschriften, Absätze, Listen, Zitate, fett und kursiv; alles andere wird beim Wechsel entfernt.", undo: "Rückgängig", redo: "Wiederholen", clear: "Formatierung entfernen", mdhint: "Markdown mit Live-Vorschau." }
    : { img: "Insert image (https, .jpg/.png/.webp, alt text required)", imgurl: "Image URL (https://…/image.jpg)", imgalt: "Alt text (describes the image, min. 5 characters)", h2: "Heading", h3: "Subheading", b: "Bold", i: "Italic", ul: "List", ol: "Numbered list", q: "Quote", link: "Link to a topic", ref: "Insert source", write: "Write", prev: "Preview", empty: "The preview appears as soon as you start writing.", chars: "characters", refs: "Sources", rtitle: "Source title", rurl: "https://…", rpub: "Publisher", rdate: "Date", add: "Insert", topic: "Topic id (e.g. power-bi)", ttext: "Link text", bold: "bold text", ital: "italic text", txt: "text", vis: "Visual", html: "HTML", md: "Markdown", htmlhint: "Paste or edit HTML – headings, paragraphs, lists, quotes, bold and italic are kept; everything else is removed when you switch.", undo: "Undo", redo: "Redo", clear: "Clear formatting", mdhint: "Markdown with live preview." };

  function inline(s, parent, ctx) {
    var ED = ctx.edit;
    var re = /\{\{img\|([^{}|]*)\|([^{}]*)\}\}|\{\{ref\|([^{}]*)\}\}|\{\{cn\}\}|\[\[([^\]|]+)\|?([^\]]*)\]\]|\*\*([^*]+)\*\*|\*([^*]+)\*/, m;
    while ((m = re.exec(s))) {
      if (m.index) parent.appendChild(document.createTextNode(s.slice(0, m.index)));
      if (m[0].indexOf("{{img|") === 0) { var im = h("img", { src: m[1], alt: m[2], loading: "lazy", referrerpolicy: "no-referrer" }); im.style.maxWidth = "100%"; im.style.height = "auto"; if (ED) { im.setAttribute("data-img", m[1] + "|" + m[2]); im.setAttribute("contenteditable", "false"); } parent.appendChild(im); }
      else if (m[3] != null) { var p = m[3].split("|"); ctx.refs.push(p); var sup = h("sup", { class: "ed-ref", text: "[" + ctx.refs.length + "]" }); if (ED) { sup.setAttribute("data-ref", m[3]); sup.setAttribute("contenteditable", "false"); } parent.appendChild(sup); }
      else if (m[0] === "{{cn}}") { var cn = h("sup", { class: "ed-cn", text: "[?]" }); if (ED) { cn.setAttribute("data-cn", "1"); cn.setAttribute("contenteditable", "false"); } parent.appendChild(cn); }
      else if (m[4] != null) { var tp = h("span", { class: "ed-topic", text: m[5] || m[4] }); if (ED) tp.setAttribute("data-topic", m[4]); parent.appendChild(tp); }
      else if (m[6] != null) parent.appendChild(h("strong", { text: m[6] }));
      else parent.appendChild(h("em", { text: m[7] }));
      s = s.slice(m.index + m[0].length);
    }
    if (s) parent.appendChild(document.createTextNode(s));
  }
  function render(body, into, edit) {
    into.textContent = ""; var ctx = { refs: [], edit: edit }, para = [], list = null;
    function fp() { if (para.length) { var p = h("p"); inline(para.join(" "), p, ctx); into.appendChild(p); para = []; } }
    body.split("\n").forEach(function (ln) {
      var m; if (!ln.trim()) { fp(); list = null; return; }
      if ((m = /^(#{2,3})\s+(.+)$/.exec(ln))) { fp(); list = null; var hd = h(edit ? (m[1].length === 2 ? "h2" : "h3") : (m[1].length === 2 ? "h3" : "h4")); inline(m[2], hd, ctx); into.appendChild(hd); return; }
      if ((m = /^(-|\d+\.)\s+(.+)$/.exec(ln))) { fp(); var ord = m[1] !== "-"; if (!list || list.o !== ord) { list = { o: ord, el: h(ord ? "ol" : "ul") }; into.appendChild(list.el); } var li = h("li"); inline(m[2], li, ctx); list.el.appendChild(li); return; }
      if ((m = /^>\s?(.+)$/.exec(ln))) { fp(); list = null; var q = h("blockquote"), qp = h("p"); inline(m[1], qp, ctx); q.appendChild(qp); into.appendChild(q); return; }
      list = null; para.push(ln.trim());
    });
    fp();
    if (edit) { if (!into.firstChild) into.appendChild(h("p", {}, [h("br")])); return; }
    if (ctx.refs.length) { into.appendChild(h("h4", { text: T.refs })); var ol = h("ol", { class: "ed-refs" }); ctx.refs.forEach(function (r) { ol.appendChild(h("li", { text: (r[0] || "") + (r[2] ? " – " + r[2] : "") + (r[3] ? " (" + r[3] + ")" : "") + (r[1] ? " · " + r[1].replace(/^https?:\/\//, "").split("/")[0] : "") })); }); into.appendChild(ol); }
    if (!body.trim()) into.appendChild(h("p", { class: "mut", text: T.empty }));
  }

  function ws(t) { return t.replace(/\s+/g, " "); }
  function inl(n) {
    var o = "";
    n.childNodes.forEach(function (c) {
      if (c.nodeType === 3) { o += ws(c.nodeValue); return; }
      if (c.nodeType !== 1) return;
      var t = c.tagName.toLowerCase(), x;
      if (t === "img") { var iu = c.getAttribute("data-img") || ((c.getAttribute("src") || "") + "|" + (c.getAttribute("alt") || "")); o += "{{img|" + iu.replace(/[{}]/g, "") + "}}"; }
      else if (t === "sup" && c.hasAttribute("data-ref")) o += "{{ref|" + c.getAttribute("data-ref") + "}}";
      else if (t === "sup" && c.hasAttribute("data-cn")) o += "{{cn}}";
      else if (c.hasAttribute("data-topic")) o += "[[" + c.getAttribute("data-topic") + "|" + ws(c.textContent).trim() + "]]";
      else if (t === "br") o += " ";
      else if (/^(script|style|iframe|object|embed|form)$/.test(t)) return;
      else if (t === "strong" || t === "b") { x = inl(c); o += x.trim() ? x.replace(/^(\s*)(.*?)(\s*)$/, "$1**$2**$3") : x; }
      else if (t === "em" || t === "i") { x = inl(c); o += x.trim() ? x.replace(/^(\s*)(.*?)(\s*)$/, "$1*$2*$3") : x; }
      else o += inl(c);
    });
    return o;
  }
  function domToMd(root) {
    var out = [], buf = "";
    function flush() { var t = buf.replace(/\s+/g, " ").trim(); if (t) out.push(t); buf = ""; }
    root.childNodes.forEach(function (c) {
      if (c.nodeType === 3) { buf += ws(c.nodeValue); return; }
      if (c.nodeType !== 1) return;
      var t = c.tagName.toLowerCase(), x;
      if (/^(h1|h2)$/.test(t)) { flush(); x = inl(c).trim(); if (x) out.push("## " + x); }
      else if (/^h[3-6]$/.test(t)) { flush(); x = inl(c).trim(); if (x) out.push("### " + x); }
      else if (t === "ul" || t === "ol") { flush(); var ls = []; c.querySelectorAll("li").forEach(function (li, k) { var y = inl(li).replace(/\s+/g, " ").trim(); if (y) ls.push((t === "ol" ? (k + 1) + ". " : "- ") + y); }); if (ls.length) out.push(ls.join("\n")); }
      else if (t === "blockquote") { flush(); x = inl(c).replace(/\s+/g, " ").trim(); if (x) out.push("> " + x); }
      else if (t === "p" || t === "div" || t === "pre" || t === "section" || t === "article") {
        if (c.querySelector("h1,h2,h3,h4,h5,h6,ul,ol,blockquote,p")) { flush(); var sub = domToMd(c); if (sub) out.push(sub); }
        else { flush(); x = inl(c).replace(/\s+/g, " ").trim(); if (x) out.push(x); }
      } else if (/^(script|style|iframe|object|embed|form|head)$/.test(t)) return;
      else { var w = document.createElement("div"); w.appendChild(c.cloneNode(true)); buf += inl(w); }
    });
    flush();
    return out.join("\n\n");
  }
  function htmlToMd(src) { var d = new DOMParser().parseFromString("<body>" + src + "</body>", "text/html"); return domToMd(d.body); }
  function mdToHtml(md) { var d = document.createElement("div"); render(md, d, true); return d.innerHTML; }

  U.editor = function (ta, max) {
    ta.className = "ed-ta"; ta.setAttribute("spellcheck", "true");
    var mode = "vis", saved = null;
    var pv = h("div", { class: "ed-pv wk-body", "aria-live": "polite" }), cnt = h("span", { class: "mut ed-cnt" }), panel = h("div", { class: "ed-panel", hidden: "" });
    var vis = h("div", { class: "ed-vis wk-body", contenteditable: "true", role: "textbox", "aria-multiline": "true", spellcheck: "true" });
    var hta = h("textarea", { class: "ed-ta ed-html", spellcheck: "false", "aria-label": "HTML" });
    var hint = h("p", { class: "mut ed-hint" });
    function count() { cnt.textContent = ta.value.length + (max ? " / " + max : "") + " " + T.chars; }
    function upd() { if (mode === "md") render(ta.value, pv); count(); }
    function fromVis() { ta.value = domToMd(vis); count(); }
    function toVis() { render(ta.value, vis, true); }
    function toHtml() { hta.value = vis.innerHTML || ""; }
    function setMode(m) {
      if (m === mode) return;
      if (mode === "vis") fromVis(); else if (mode === "html") ta.value = htmlToMd(hta.value);
      mode = m;
      if (m === "vis") toVis(); else if (m === "html") { toVis(); toHtml(); }
      else render(ta.value, pv);
      wrap.setAttribute("data-mode", m); tabs.forEach(function (b) { b.setAttribute("aria-selected", b.dataset.m === m ? "true" : "false"); });
      hint.textContent = m === "html" ? T.htmlhint : m === "md" ? T.mdhint : "";
      panel.hidden = true; count();
    }
    // Auswahl im visuellen Modus merken (fuer Dialoge)
    function keepSel() { var s = window.getSelection(); if (s.rangeCount && vis.contains(s.anchorNode)) saved = s.getRangeAt(0).cloneRange(); }
    document.addEventListener("selectionchange", function () { if (mode === "vis") keepSel(); });
    function restore() { vis.focus(); if (saved) { var s = window.getSelection(); s.removeAllRanges(); s.addRange(saved); } }
    function insertNode(node) {
      restore(); var s = window.getSelection(); if (!s.rangeCount) { vis.appendChild(node); } else { var r = s.getRangeAt(0); r.deleteContents(); r.insertNode(node); r.setStartAfter(node); r.collapse(true); s.removeAllRanges(); s.addRange(r); }
      fromVis();
    }
    function selText() { return mode === "vis" ? String(window.getSelection()).trim() : ta.value.slice(ta.selectionStart, ta.selectionEnd); }
    function mput(a, b, ph) { var s0 = ta.selectionStart, s1 = ta.selectionEnd, v = ta.value, mid = v.slice(s0, s1) || ph || ""; ta.value = v.slice(0, s0) + a + mid + b + v.slice(s1); ta.focus(); ta.setSelectionRange(s0 + a.length, s0 + a.length + mid.length); upd(); }
    function mline(pre) { var s = ta.selectionStart, v = ta.value, st = v.lastIndexOf("\n", s - 1) + 1; ta.value = v.slice(0, st) + pre + v.slice(st); ta.focus(); ta.setSelectionRange(s + pre.length, s + pre.length); upd(); }
    function ex(cmd, val) { restore(); document.execCommand(cmd, false, val || null); fromVis(); }
    function fields(list, done) {
      keepSel(); panel.textContent = ""; panel.hidden = false;
      var els = list.map(function (f) { var e = h("input", { type: "text", maxlength: 300, placeholder: f[1], "aria-label": f[1] }); e.value = f[2] || ""; panel.appendChild(e); return e; });
      panel.appendChild(h("button", { type: "button", class: "btn main", text: T.add, onclick: function () { if (done(els.map(function (e) { return e.value.trim(); })) !== false) panel.hidden = true; } }));
      panel.appendChild(h("button", { type: "button", class: "btn", text: "✕", "aria-label": "Close", onclick: function () { panel.hidden = true; if (mode === "vis") restore(); else ta.focus(); } })); els[0].focus();
    }
    function btn(l, t, fn, cls) { var b = h("button", { type: "button", class: "ed-b " + (cls || ""), title: t, "aria-label": t, text: l, onclick: fn }); b.addEventListener("mousedown", function (e) { e.preventDefault(); }); return b; }
    function act(v, m) { return function () { if (mode === "vis") v(); else m(); }; }
    var bar = h("div", { class: "ed-bar", role: "toolbar" }, [
      btn("H2", T.h2, act(function () { ex("formatBlock", "h2"); }, function () { mline("## "); })), btn("H3", T.h3, act(function () { ex("formatBlock", "h3"); }, function () { mline("### "); })),
      btn("¶", "Text", act(function () { ex("formatBlock", "p"); }, function () {})),
      btn("B", T.b, act(function () { ex("bold"); }, function () { mput("**", "**", T.bold); }), "ed-bold"), btn("I", T.i, act(function () { ex("italic"); }, function () { mput("*", "*", T.ital); }), "ed-ital"),
      btn("•", T.ul, act(function () { ex("insertUnorderedList"); }, function () { mline("- "); })), btn("1.", T.ol, act(function () { ex("insertOrderedList"); }, function () { mline("1. "); })), btn("❝", T.q, act(function () { ex("formatBlock", "blockquote"); }, function () { mline("> "); })),
      btn("↶", T.undo, act(function () { ex("undo"); }, function () { document.execCommand("undo"); }), "ed-vo"), btn("↷", T.redo, act(function () { ex("redo"); }, function () { document.execCommand("redo"); }), "ed-vo"),
      btn("[[ ]]", T.link, function () {
        var st = selText(); fields([["id", T.topic], ["t", T.ttext, st]], function (v) {
          if (!v[0]) return false; var id = v[0].toLowerCase().replace(/[^a-z0-9-]/g, "-"), tx = v[1] || v[0];
          if (mode === "vis") { var sp = h("span", { class: "ed-topic", text: tx }); sp.setAttribute("data-topic", id); insertNode(sp); } else mput("[[" + id + "|" + tx + "]]", "", "");
        });
      }),
      btn("🖼", T.img, function () {
        fields([["u", T.imgurl], ["a", T.imgalt, selText()]], function (v) {
          if (!/^https:\/\/\S+\.(jpe?g|png|webp|gif|avif)(\?\S*)?$/i.test(v[0]) || v[1].length < 5) return false;
          var val = v[0] + "|" + v[1].replace(/[{}|\[\]]/g, "");
          if (mode === "vis") { var im = h("img", { src: v[0], alt: v[1], referrerpolicy: "no-referrer" }); im.style.maxWidth = "100%"; im.style.height = "auto"; im.setAttribute("data-img", val); im.setAttribute("contenteditable", "false"); insertNode(im); } else mput("{{img|" + val + "}}", "", "");
        });
      }),
      btn("[1] " + T.refs, T.ref, function () {
        fields([["t", T.rtitle], ["u", T.rurl], ["p", T.rpub], ["d", T.rdate]], function (v) {
          if (!v[0] || !/^https:\/\//.test(v[1])) return false;
          if (mode === "vis") { var sp = h("sup", { class: "ed-ref", text: "[•]" }); sp.setAttribute("data-ref", v.join("|")); sp.setAttribute("contenteditable", "false"); insertNode(sp); } else mput("{{ref|" + v.join("|") + "}}", "", "");
        });
      }, "ed-wide")]);
    var tabs = [["vis", T.vis], ["html", T.html], ["md", T.md]].map(function (x) { var b = h("button", { type: "button", class: "ed-tab", text: x[1], role: "tab", onclick: function () { setMode(x[0]); } }); b.dataset.m = x[0]; b.setAttribute("aria-selected", x[0] === "vis" ? "true" : "false"); return b; });
    var tabbar = h("div", { class: "ed-tabs", role: "tablist" }, tabs);
    vis.addEventListener("input", fromVis);
    vis.addEventListener("keydown", function (e) { if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); bar.querySelector("button[title='" + T.link + "']").click(); } });
    vis.addEventListener("paste", function (e) {
      var cd = e.clipboardData; if (!cd) return; e.preventDefault();
      var hh = cd.getData("text/html"), tx = cd.getData("text/plain"), md = hh ? htmlToMd(hh) : tx;
      if (!hh && !/\n/.test(tx.trim())) { document.execCommand("insertText", false, tx); fromVis(); return; }
      var d = document.createElement("div"); render(md, d, true); document.execCommand("insertHTML", false, d.innerHTML); fromVis();
    });
    hta.addEventListener("input", function () { ta.value = htmlToMd(hta.value); count(); });
    ta.addEventListener("input", upd); ta.addEventListener("keydown", function (e) { if ((e.ctrlKey || e.metaKey) && e.key === "b") { e.preventDefault(); mput("**", "**", T.bold); } if ((e.ctrlKey || e.metaKey) && e.key === "i") { e.preventDefault(); mput("*", "*", T.ital); } });
    var left = h("div", { class: "ed-left" }, [tabbar, bar, panel, vis, hta, ta, hint, cnt]), right = h("div", { class: "ed-right" }, [h("div", { class: "ed-cap", text: T.prev }), pv]);
    var wrap = h("div", { class: "ed-wrap", "data-mode": "vis" }, [left, right]); toVis(); count();
    wrap.refresh = function () { if (mode === "vis") toVis(); else if (mode === "html") { toVis(); toHtml(); } upd(); count(); };
    return wrap;
  };
})();
