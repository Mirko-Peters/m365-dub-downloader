/* Effekte im Technik-Look, ohne Bibliothek und ohne externe Anfragen:
   1) lebendiger Wissensgraph im Hintergrund (Knoten = Themen, Linien = Beziehungen, reagiert auf den Mauszeiger)
   2) Lesefortschritt oben, 3) Einblenden beim Scrollen, 4) Spotlight auf Karten, 5) Zaehler, 6) Lichtstreif auf der Hauptueberschrift.
   Aus bei reduzierter Bewegung, im Barrierefreiheits-Menue "Bewegung reduzieren" und (Hintergrund) auf Touch-Geraeten und schwachen Geraeten. */
(function () {
  try {
    var H = document.documentElement, mq = window.matchMedia;
    if (H.classList.contains("a11y-nomo") || (mq && mq("(prefers-reduced-motion: reduce)").matches)) return;
    H.classList.add("fx-on");
    var raf = window.requestAnimationFrame, coarse = mq && mq("(pointer: coarse)").matches;

    // --- 2) Lesefortschritt
    var bar = document.createElement("div"); bar.id = "fx-bar"; document.body.appendChild(bar);
    function prog() { var m = H.scrollHeight - innerHeight; bar.style.transform = "scaleX(" + (m > 0 ? Math.min(1, scrollY / m) : 0) + ")"; }
    addEventListener("scroll", prog, { passive: true }); prog();

    // --- 3) Einblenden beim Scrollen
    var sel = "main h2, main h3, .hub-card, .sb-card, .tile, .card, .thumbs a, article > p:first-of-type";
    var els = [].slice.call(document.querySelectorAll(sel)).filter(function (e) { return e.getBoundingClientRect().top > innerHeight * 0.9; });
    if ("IntersectionObserver" in window && els.length) {
      var io = new IntersectionObserver(function (es) { es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("fx-in"); io.unobserve(x.target); } }); }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
      els.forEach(function (e, i) { e.classList.add("fx-r"); e.style.setProperty("--fx-d", (i % 4) * 0.06 + "s"); io.observe(e); });
    }

    // --- 4) Spotlight
    [].forEach.call(document.querySelectorAll(".hub-card, .sb-card, .tile, .card"), function (c) {
      c.classList.add("fx-s");
      c.addEventListener("pointermove", function (ev) { var r = c.getBoundingClientRect(); c.style.setProperty("--mx", ev.clientX - r.left + "px"); c.style.setProperty("--my", ev.clientY - r.top + "px"); }, { passive: true });
    });

    // --- 5) Zaehler (nur reine Zahlen in .num)
    [].forEach.call(document.querySelectorAll(".num"), function (n) {
      var t = (n.textContent || "").trim(), m = /^(\d[\d.,]*)(\D*)$/.exec(t); if (!m) return;
      var v = parseInt(m[1].replace(/[.,]/g, ""), 10), sep = m[1].indexOf(".") > -1 ? "." : m[1].indexOf(",") > -1 ? "," : "";
      if (!(v > 0)) return;
      var o = new IntersectionObserver(function (es) {
        if (!es[0].isIntersecting) return; o.disconnect();
        var s = performance.now();
        (function f(now) { var k = Math.min(1, (now - s) / 1200), e = 1 - Math.pow(1 - k, 3), x = Math.round(v * e).toString();
          if (sep) x = x.replace(/\B(?=(\d{3})+(?!\d))/g, sep); n.textContent = x + m[2]; if (k < 1) raf(f); })(s);
      }); o.observe(n);
    });

    // --- 6) Lichtstreif auf der Hauptueberschrift (Text bleibt sofort sichtbar)
    var h1 = document.querySelector("main h1, h1"); if (h1) h1.classList.add("fx-h");

    // --- 1) Wissensgraph im Hintergrund
    if (coarse || (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) || (navigator.connection && navigator.connection.saveData)) return;
    var cv = document.createElement("canvas"); cv.id = "fx-graph"; cv.setAttribute("aria-hidden", "true"); document.body.insertBefore(cv, document.body.firstChild);
    var cx = cv.getContext("2d"), W = 0, Hh = 0, dpr = Math.min(devicePixelRatio || 1, 2), N = [], mouse = { x: -999, y: -999 }, col = [180, 35, 60], run = true;
    function colors() {
      var c = getComputedStyle(H).getPropertyValue("--ac").trim(), m = /^#([0-9a-f]{6})$/i.exec(c);
      col = m ? [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4, 6), 16)] : [90, 140, 255];
    }
    function size() {
      W = innerWidth; Hh = innerHeight; cv.width = W * dpr; cv.height = Hh * dpr; cx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.max(24, Math.min(90, Math.round(W * Hh / 16000)));
      while (N.length < n) N.push({ x: Math.random() * W, y: Math.random() * Hh, vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25, r: 1.2 + Math.random() * 1.8 });
      N.length = n;
    }
    addEventListener("resize", size); addEventListener("pointermove", function (e) { mouse.x = e.clientX; mouse.y = e.clientY; }, { passive: true });
    document.addEventListener("visibilitychange", function () { run = !document.hidden; if (run) raf(draw); });
    new MutationObserver(colors).observe(H, { attributes: true, attributeFilter: ["data-theme", "class"] });
    if (mq) { var dm = mq("(prefers-color-scheme: dark)"); (dm.addEventListener ? dm.addEventListener("change", colors) : 0); }
    function draw() {
      if (!run) return; if (H.classList.contains("a11y-nomo")) { cv.style.display = "none"; return; }
      cx.clearRect(0, 0, W, Hh);
      var L = 140, c = col[0] + "," + col[1] + "," + col[2];
      for (var i = 0; i < N.length; i++) {
        var a = N[i]; a.x += a.vx; a.y += a.vy;
        if (a.x < 0 || a.x > W) a.vx *= -1; if (a.y < 0 || a.y > Hh) a.vy *= -1;
        var dx = a.x - mouse.x, dy = a.y - mouse.y, d2 = dx * dx + dy * dy;
        if (d2 < 14000) { var f = (1 - d2 / 14000) * 0.6, d = Math.sqrt(d2) || 1; a.x += dx / d * f; a.y += dy / d * f; }
        for (var j = i + 1; j < N.length; j++) {
          var b = N[j], ex = a.x - b.x, ey = a.y - b.y, e2 = ex * ex + ey * ey;
          if (e2 < L * L) { cx.strokeStyle = "rgba(" + c + "," + (0.34 * (1 - Math.sqrt(e2) / L)).toFixed(3) + ")"; cx.lineWidth = 1; cx.beginPath(); cx.moveTo(a.x, a.y); cx.lineTo(b.x, b.y); cx.stroke(); }
        }
        var near = d2 < 28000, gl = near ? 1 - d2 / 28000 : 0;
        if (near) { cx.strokeStyle = "rgba(" + c + "," + (0.55 * gl).toFixed(3) + ")"; cx.lineWidth = 1.2; cx.beginPath(); cx.moveTo(a.x, a.y); cx.lineTo(mouse.x, mouse.y); cx.stroke(); }
        cx.shadowColor = "rgba(" + c + ",0.9)"; cx.shadowBlur = 6 + 14 * gl;
        cx.fillStyle = "rgba(" + c + "," + (0.55 + 0.45 * gl).toFixed(3) + ")"; cx.beginPath(); cx.arc(a.x, a.y, a.r + 1.2 * gl, 0, 6.283); cx.fill(); cx.shadowBlur = 0;
      }
      raf(draw);
    }
    colors(); size(); raf(draw);
  } catch (e) {}
})();
