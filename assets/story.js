/* Scroll-Geschichten mit GSAP + ScrollTrigger, parallel zu Lenis (siehe smooth.js: m365LenisGsap). Lokal eingebunden, keine externen Anfragen.
   Je Seitentyp (body[data-story]) eine eigene Choreografie; Blogbeitraege bekommen ein Rezept (article[data-recipe], gewaehlt beim Seitenbau in site_story.py).
   Alles aus bei reduzierter Bewegung / "Bewegung reduzieren"; auf kleinen Bildschirmen leichter (kein Pinnen, weniger Parallaxe). Inhalte bleiben ohne JS sichtbar. */
(function () {
  try {
    var H = document.documentElement, mq = window.matchMedia;
    if (H.classList.contains("a11y-nomo") || (mq && mq("(prefers-reduced-motion: reduce)").matches) || (navigator.connection && navigator.connection.saveData)) return;
    var me = document.currentScript, base = me && me.src ? me.src.replace(/story\.js.*$/, "") : "/assets/";
    function load(u, cb) { var s = document.createElement("script"); s.src = base + u; s.onload = cb; s.onerror = function () {}; document.head.appendChild(s); }
    function boot() {
      if (!window.gsap || !window.ScrollTrigger) return;
      var gsap = window.gsap, ST = window.ScrollTrigger; gsap.registerPlugin(ST);
      if (window.m365LenisGsap) window.m365LenisGsap(gsap, ST);
      var kind = document.body.getAttribute("data-story") || "page", $ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };

      // --- Helfer
      function words(el) {   // Woerter in Masken, Screenreader lesen den Originaltext
        if (!el || el.getAttribute("data-split")) return [];
        var t = el.textContent.trim(); el.setAttribute("aria-label", t); el.setAttribute("data-split", "1"); el.textContent = "";
        return t.split(/\s+/).map(function (w, i, a) {
          var o = document.createElement("span"), n = document.createElement("span");
          o.style.cssText = "display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.12em"; n.style.cssText = "display:inline-block;will-change:transform"; n.setAttribute("aria-hidden", "true"); n.textContent = w;
          o.appendChild(n); el.appendChild(o); if (i < a.length - 1) el.appendChild(document.createTextNode(" ")); return n;
        });
      }
      function rise(list, d) { if (list.length) gsap.from(list, { yPercent: 115, duration: 0.9, ease: "power4.out", stagger: 0.05, delay: d || 0.1 }); }
      function reveal(sel, o) {
        var els = $(sel).filter(function (e) { return !e.closest(".fx-done"); }); if (!els.length) return;
        els.forEach(function (e) { e.classList.add("fx-done"); });
        ST.batch(els, { start: "top 88%", once: true, onEnter: function (b) { gsap.fromTo(b, { y: (o && o.y) || 36, opacity: 0, scale: (o && o.s) || 1 }, { y: 0, opacity: 1, scale: 1, duration: 0.8, ease: "power3.out", stagger: 0.09, overwrite: true }); } });
        gsap.set(els, { opacity: 0 });
      }
      function drift(sel, amt) { $(sel).forEach(function (i) { gsap.fromTo(i, { yPercent: -amt }, { yPercent: amt, ease: "none", scrollTrigger: { trigger: i, scrub: true, start: "top bottom", end: "bottom top" } }); }); }
      function bar(el, scaleProp) { return gsap.fromTo(el, { scaleY: 0 }, { scaleY: 1, ease: "none", transformOrigin: "50% 0" }); }

      var mm = gsap.matchMedia();
      mm.add({ desk: "(min-width: 900px)", mob: "(max-width: 899px)" }, function (ctx) {
        var desk = ctx.conditions.desk, h1 = document.querySelector("main h1, h1");
        if (h1 && kind !== "page") { h1.classList.remove("fx-h"); h1.style.cssText += ";-webkit-text-fill-color:currentColor;background:none"; rise(words(h1)); }

        if (kind === "home") {
          // Geschichte: Hauptueberschrift steigt auf, Kacheln und Karten folgen gestaffelt, Bilder driften leicht
          reveal("main h2", { y: 20 }); reveal(".hub-card, .tile, .card, .thumbs a, .sb-card", { y: 44, s: 0.96 }); drift("main img:not([width='16'])", desk ? 5 : 2);
        } else if (kind === "episode") {
          // Geschichte: Titel, dann wachsende Kernpunkte-Linie, FAQ klappt nacheinander auf, Cover mit Tiefe
          drift("main img:not([width='16']):not([height='16'])", desk ? 6 : 2);
          $(".kp").forEach(function (k) {
            var line = document.createElement("i"); line.setAttribute("aria-hidden", "true"); line.style.cssText = "position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--ac,#b4233c);transform-origin:50% 0;pointer-events:none";
            k.style.position = "relative"; k.appendChild(line);
            gsap.fromTo(line, { scaleY: 0 }, { scaleY: 1, ease: "none", scrollTrigger: { trigger: k, start: "top 80%", end: "bottom 45%", scrub: 0.6 } });
            gsap.from($("li", k), { x: -28, opacity: 0, duration: 0.6, ease: "power3.out", stagger: 0.12, scrollTrigger: { trigger: k, start: "top 78%", once: true } });
          });
          reveal(".faq details, .shownotes > h2, .shownotes > p, main h2", { y: 24 });
        } else if (kind === "entity") {
          // Geschichte: Karte zeichnet sich (Linien), Knoten ploppen auf, Zeitleiste und Themen folgen
          $("main svg").forEach(function (s) {
            var lines = $("line, path", s).filter(function (l) { return l.getTotalLength && l.getTotalLength() > 8; }), dots = $("circle, rect", s).filter(function (c) { return c.tagName === "circle"; });
            lines.forEach(function (l) { var L = l.getTotalLength(); gsap.set(l, { strokeDasharray: L, strokeDashoffset: L }); });
            var tl = gsap.timeline({ scrollTrigger: { trigger: s, start: "top 82%", once: true } });
            if (lines.length) tl.to(lines, { strokeDashoffset: 0, duration: 1, ease: "power2.inOut", stagger: 0.04 });
            if (dots.length) tl.from(dots, { scale: 0, transformOrigin: "50% 50%", duration: 0.5, ease: "back.out(2.4)", stagger: 0.03 }, lines.length ? "-=0.7" : 0);
          });
          reveal("main h2, .en-rel > *, .mb-tag, details, main li", { y: 26 }); drift("main > img, .wrap > img", desk ? 4 : 2);
        } else if (kind === "blog") { blog(); } else { reveal("main h2, .hub-card, .tile, .card, li", { y: 28 }); }
      });

      // --- Blog-Rezepte
      function blog() {
        var art = document.querySelector("article[data-recipe]"); if (!art) return; var r = art.getAttribute("data-recipe"), ps = $("p", art);
        var lead = ps.filter(function (p) { return p.textContent.length > 120; })[0];
        if (lead && r !== "focus") gsap.from(lead, { opacity: 0, y: 24, filter: "blur(8px)", duration: 1, ease: "power3.out", delay: 0.5 });
        if (r === "ink") {   // Ueberschriften wischen mit einer Linie ein
          $("h2, h3", art).forEach(function (h) { h.style.cssText += ";position:relative;display:block"; var u = document.createElement("i"); u.setAttribute("aria-hidden", "true"); u.style.cssText = "position:absolute;left:0;bottom:-.15em;height:2px;width:100%;background:var(--ac,#b4233c);transform-origin:0 50%"; h.appendChild(u);
            gsap.from(u, { scaleX: 0, duration: 0.9, ease: "power3.inOut", scrollTrigger: { trigger: h, start: "top 85%", once: true } });
            gsap.from(h, { clipPath: "inset(0 100% 0 0)", duration: 0.8, ease: "power3.out", scrollTrigger: { trigger: h, start: "top 85%", once: true } }); });
        } else if (r === "focus") {   // Leselicht: der Absatz in der Bildschirmmitte ist klar, die anderen treten zurueck
          ps.forEach(function (p) { ST.create({ trigger: p, start: "top 65%", end: "bottom 35%", onToggle: function (s) { gsap.to(p, { opacity: s.isActive ? 1 : 0.38, duration: 0.4, overwrite: true }); } }); gsap.set(p, { opacity: 0.38 }); });
          if (ps[0]) gsap.set(ps[0], { opacity: 1 });
        } else if (r === "marker") {   // Hervorhebungen werden beim Lesen mit Textmarker gezogen
          $("strong, b, mark", art).forEach(function (m) { m.style.cssText += ";background:linear-gradient(transparent 62%,color-mix(in srgb,var(--ac,#b4233c) 38%,transparent) 62%) no-repeat;background-size:0% 100%";
            gsap.to(m, { backgroundSize: "100% 100%", duration: 0.9, ease: "power2.out", scrollTrigger: { trigger: m, start: "top 80%", once: true } }); });
        } else if (r === "parallax") {   // Bilder driften, Absaetze folgen gestaffelt
          drift("article img, article figure", 6); reveal("article > p, article li", { y: 22 });
        } else if (r === "chapters") {   // Kapitelleiste: aktueller Abschnitt leuchtet, Fortschritt je Kapitel
          var hs = $("h2", art); if (hs.length > 1) {
            var nav = document.createElement("nav"); nav.setAttribute("aria-label", "Chapters"); nav.style.cssText = "position:fixed;right:14px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:10px;z-index:50";
            var dots = hs.map(function (h, i) { if (!h.id) h.id = "ch" + (i + 1); var a = document.createElement("a"); a.href = "#" + h.id; a.title = h.textContent; a.setAttribute("aria-label", h.textContent);
              a.style.cssText = "display:block;width:9px;height:9px;border-radius:50%;border:2px solid var(--ac,#b4233c);background:transparent;transition:background .3s,transform .3s"; nav.appendChild(a);
              ST.create({ trigger: h, start: "top 55%", end: i + 1 < hs.length ? "top+=0 " + "55%" : "bottom bottom", endTrigger: hs[i + 1] || art, onToggle: function (s) { if (s.isActive) dots.forEach(function (d, k) { d.style.background = k === i ? "var(--ac,#b4233c)" : "transparent"; d.style.transform = k === i ? "scale(1.5)" : "none"; }); } }); return a; });
            if (matchMedia("(min-width: 900px)").matches) document.body.appendChild(nav);
          }
          reveal("article h2", { y: 26 });
        } else {   // spark: Funken-Zeile am Absatzanfang, Zitate und Listen gleiten ein
          reveal("article blockquote, article ul > li, article ol > li, article h2", { y: 24 });
          $("h2", art).forEach(function (h) { var sp = document.createElement("span"); sp.setAttribute("aria-hidden", "true"); sp.textContent = "✦ "; sp.style.cssText = "color:var(--ac,#b4233c);display:inline-block"; h.insertBefore(sp, h.firstChild);
            gsap.from(sp, { rotate: -180, scale: 0, duration: 0.8, ease: "back.out(2)", scrollTrigger: { trigger: h, start: "top 85%", once: true } }); });
        }
      }
      addEventListener("load", function () { ST.refresh(); });
    }
    load("vendor/gsap.min.js", function () { load("vendor/ScrollTrigger.min.js", boot); });
  } catch (e) {}
})();
