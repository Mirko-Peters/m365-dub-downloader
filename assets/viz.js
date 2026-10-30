/* Interaktive Infografiken im Beitrag: {{viz|typ|Titel|Daten}} -> <figure class="viz">. Aus Text gebaut (kein HTML von Autoren), mit GSAP animiert, wenn vorhanden.
   Typen: bars (Balken), stats (Zahlen), steps (Schritte), timeline (Zeitleiste), compare (Vorher/Nachher). Ohne JS und bei reduzierter Bewegung bleibt die Liste bzw. eine statische Grafik. */
(function () {
  var D = document, RM = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches || D.documentElement.classList.contains("a11y-nomo");
  var CSS = ".viz{margin:1.6em 0;padding:1.1em 1.2em;border:1px solid var(--bd,#0002);border-radius:.7em;background:var(--card,transparent);overflow:hidden}.viz figcaption{font-weight:700;margin:0 0 .8em}" +
    ".viz-fb{margin:0;padding-inline-start:1.2em}.viz.on .viz-fb{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}" +
    ".vz-row{display:grid;grid-template-columns:minmax(5em,12em) 1fr 4.5em;gap:.7em;align-items:center;margin:.45em 0;cursor:pointer}.vz-row .t{height:.9em;border-radius:1em;background:var(--bd,#0002);overflow:hidden}.vz-row .f{display:block;height:100%;width:0;border-radius:1em;background:var(--ac,#b4233c);transition:width .8s cubic-bezier(.2,.7,.2,1),filter .2s}.vz-row .v{text-align:end;font-variant-numeric:tabular-nums}.vz-row:hover .f,.vz-row.sel .f{filter:brightness(1.25)}.vz-row.dim{opacity:.45}" +
    ".vz-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(8em,1fr));gap:.8em}.vz-stat{padding:.8em;border:1px solid var(--bd,#0002);border-radius:.6em;text-align:center;transition:transform .2s,border-color .2s}.vz-stat:hover{transform:translateY(-3px);border-color:var(--ac,#b4233c)}.vz-stat b{display:block;font-size:2rem;line-height:1.2;color:var(--ac,#b4233c);font-variant-numeric:tabular-nums}" +
    ".vz-steps{display:flex;gap:.5em;flex-wrap:wrap;position:relative}.vz-step{flex:1 1 7em;padding:.6em .7em;border:1px solid var(--bd,#0002);border-radius:.5em;background:transparent;color:inherit;font:inherit;text-align:start;cursor:pointer;transition:background .25s,border-color .25s,transform .25s}.vz-step i{display:block;font-style:normal;font-size:.75rem;color:var(--mut,#777)}.vz-step.on{border-color:var(--ac,#b4233c);background:color-mix(in srgb,var(--ac,#b4233c) 12%,transparent);transform:translateY(-2px)}" +
    ".vz-bar{height:3px;background:var(--bd,#0002);margin:.8em 0;border-radius:3px;overflow:hidden}.vz-bar i{display:block;height:100%;width:0;background:var(--ac,#b4233c)}.vz-detail{min-height:3.2em;margin:.3em 0 0}" +
    ".vz-tl{position:relative;margin:0;padding:0 0 0 1.6em;list-style:none}.vz-tl:before{content:'';position:absolute;left:.45em;top:.3em;bottom:.3em;width:2px;background:var(--bd,#0002)}.vz-tl .ln{position:absolute;left:.45em;top:.3em;width:2px;height:0;background:var(--ac,#b4233c)}.vz-tl li{position:relative;margin:0 0 .9em}.vz-tl li:before{content:'';position:absolute;left:-1.45em;top:.45em;width:.7em;height:.7em;border-radius:50%;background:var(--bg,#fff);border:2px solid var(--ac,#b4233c);transition:transform .3s,background .3s}.vz-tl li:hover:before,.vz-tl li.on:before{background:var(--ac,#b4233c);transform:scale(1.35)}.vz-tl b{color:var(--ac,#b4233c);margin-inline-end:.5em}" +
    ".vz-sw{display:inline-flex;border:1px solid var(--bd,#0002);border-radius:2em;overflow:hidden;margin:0 0 .8em}.vz-sw button{padding:.3em 1em;border:0;background:transparent;color:inherit;font:inherit;cursor:pointer}.vz-sw button.on{background:var(--ac,#b4233c);color:#fff}";
  function style() { if (D.getElementById("vz-css")) return; var s = D.createElement("style"); s.id = "vz-css"; s.textContent = CSS; D.head.appendChild(s); }
  function el(t, c, x) { var e = D.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function num(s) { var n = parseFloat(String(s).replace(",", ".")); return isFinite(n) ? n : 0; }
  function fmt(n) { return Math.abs(n) >= 1000 ? Math.round(n).toLocaleString() : String(Math.round(n * 10) / 10); }
  function whenSeen(node, fn) { if (!("IntersectionObserver" in window) || RM) return fn(); var o = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { o.disconnect(); fn(); } }, { threshold: 0.3 }); o.observe(node); }
  function tween(obj, to, dur, upd) { var g = window.gsap; if (g && !RM) g.to(obj, { v: to, duration: dur, ease: "power2.out", onUpdate: upd }); else { obj.v = to; upd(); } }

  var T = {
    bars: function (box, it) {
      var max = Math.max.apply(null, it.map(function (x) { return num(x.b); })) || 1, rows = it.map(function (x) {
        var r = el("div", "vz-row"), t = el("span", "t"), f = el("span", "f"), v = el("span", "v", fmt(num(x.b))); t.appendChild(f); r.append(el("span", "l", x.a), t, v); r.tabIndex = 0; box.appendChild(r); r._w = num(x.b) / max * 100; r._f = f; return r;
      });
      rows.forEach(function (r) { function pick() { var on = !r.classList.contains("sel"); rows.forEach(function (o) { o.classList.remove("sel"); o.classList.toggle("dim", on && o !== r); }); r.classList.toggle("sel", on); if (!on) rows.forEach(function (o) { o.classList.remove("dim"); }); } r.addEventListener("click", pick); r.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } }); });
      whenSeen(box, function () { rows.forEach(function (r, i) { setTimeout(function () { r._f.style.width = r._w + "%"; }, RM ? 0 : i * 90); }); });
    },
    stats: function (box, it) {
      var g = el("div", "vz-stats"); box.appendChild(g);
      var tiles = it.map(function (x) { var s = el("div", "vz-stat"), b = el("b", null, "0"); s.append(b, el("span", null, x.a)); g.appendChild(s); return [b, num(x.b)]; });
      whenSeen(box, function () { tiles.forEach(function (t) { var o = { v: 0 }; tween(o, t[1], 1.4, function () { t[0].textContent = fmt(o.v); }); }); });
    },
    steps: function (box, it) {
      var row = el("div", "vz-steps"), bar = el("div", "vz-bar"), fill = el("i"), det = el("p", "vz-detail"), cur = 0, auto = true, timer = 0;
      bar.appendChild(fill); det.setAttribute("aria-live", "polite"); box.append(row, bar, det);
      var bs = it.map(function (x, i) { var b = el("button", "vz-step"); b.type = "button"; b.append(el("i", null, String(i + 1)), D.createTextNode(x.a)); b.addEventListener("click", function () { auto = false; clearInterval(timer); go(i); }); row.appendChild(b); return b; });
      function go(i) { cur = i; bs.forEach(function (b, k) { b.classList.toggle("on", k === i); b.setAttribute("aria-pressed", k === i ? "true" : "false"); }); fill.style.width = ((i + 1) / it.length * 100) + "%"; fill.style.transition = "width .5s"; if (window.gsap && !RM) window.gsap.fromTo(det, { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.35 }); det.textContent = it[i].b || ""; }
      go(0); whenSeen(box, function () { if (RM) return; timer = setInterval(function () { if (!auto) return clearInterval(timer); go((cur + 1) % it.length); if (cur === it.length - 1) { auto = false; clearInterval(timer); } }, 2200); });
    },
    timeline: function (box, it) {
      var ul = el("ul", "vz-tl"), ln = el("i", "ln"); ul.appendChild(ln); box.appendChild(ul);
      var lis = it.map(function (x) { var li = el("li"); li.append(el("b", null, x.a), D.createTextNode(x.b || "")); li.style.opacity = RM ? 1 : 0.25; li.style.transition = "opacity .5s"; ul.appendChild(li); return li; });
      whenSeen(box, function () { var h = ul.offsetHeight; if (window.gsap && !RM) window.gsap.to(ln, { height: h - 8, duration: 1.2 + lis.length * 0.12, ease: "power1.inOut" }); else ln.style.height = (h - 8) + "px"; lis.forEach(function (li, i) { setTimeout(function () { li.style.opacity = 1; li.classList.add("on"); setTimeout(function () { li.classList.remove("on"); }, 500); }, RM ? 0 : 250 + i * 330); }); });
    },
    compare: function (box, it) {
      var lab = it[0] || { a: "A", b: "B" }, rows = it.slice(1), sw = el("div", "vz-sw"), bA = el("button", "on", lab.a), bB = el("button", "", lab.b), side = "b";
      bA.type = bB.type = "button"; sw.append(bA, bB); box.appendChild(sw);
      var max = Math.max.apply(null, rows.map(function (x) { return Math.max(num(x.b), num(x.c)); })) || 1;
      var rs = rows.map(function (x) { var r = el("div", "vz-row"), t = el("span", "t"), f = el("span", "f"), v = el("span", "v", ""); t.appendChild(f); r.append(el("span", "l", x.a), t, v); box.appendChild(r); return { f: f, v: v, x: x, cur: { v: 0 } }; });
      function show(s) { side = s; bA.classList.toggle("on", s === "b"); bB.classList.toggle("on", s === "c"); rs.forEach(function (r) { var to = num(r.x[s]); r.f.style.width = to / max * 100 + "%"; tween(r.cur, to, 0.7, function () { r.v.textContent = fmt(r.cur.v); }); }); }
      bA.addEventListener("click", function () { show("b"); }); bB.addEventListener("click", function () { show("c"); });
      whenSeen(box, function () { show("b"); });
    }
  };
  function init(fig) {
    var type = fig.getAttribute("data-viz"); if (!T[type]) return; var old = fig.querySelector(".vz-box"); if (old) old.remove(); fig.classList.remove("on"); style();
    var it = [].slice.call(fig.querySelectorAll(".viz-fb li")).map(function (li) { return { a: li.getAttribute("data-a") || "", b: li.getAttribute("data-b") || "", c: li.getAttribute("data-c") || "" }; });
    if (!it.length) return; var box = el("div", "vz-box"); box.setAttribute("aria-hidden", "true"); fig.appendChild(box); fig.classList.add("on");
    try { T[type](box, it); } catch (e) { fig.classList.remove("on"); box.remove(); }
  }
  window.m365Viz = init;
  function all() { [].forEach.call(D.querySelectorAll("figure.viz"), init); }
  if (D.readyState === "loading") D.addEventListener("DOMContentLoaded", all); else all();
})();
