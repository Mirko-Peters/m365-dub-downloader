/* "I'm attending M365Con 2027": Countdown (Sidebar) + Popup nach 2 Minuten Inaktivitaet. */
(function () {
  var START = new Date("2027-01-11T00:00:00+01:00"), END = new Date("2027-01-23T00:00:00+01:00");
  var BASE = (document.currentScript && document.currentScript.src || "").replace(/\/assets\/attend\.js.*$/, "") || "https://www.m365.fm";
  var URL_ = "https://m365con.net/?utm_source=m365.fm&utm_medium=popup&utm_campaign=attending2027";
  var T = {
    en: { h: "I'm attending M365Con 2027 – join me!", p: "Free online event, January 11–22, 2027 · 120+ sessions · 120+ speakers · 10 topic days.", go: "Save your free seat →", no: "Not now", x: "Close", d: "days", hh: "hours", m: "min", live: "Live now", meta: "Free online event · Jan 11–22, 2027" },
    de: { h: "Ich bin bei der M365Con 2027 dabei – komm mit!", p: "Kostenloses Online-Event, 11.–22. Januar 2027 · 120+ Sessions · 120+ Speaker · 10 Themen-Tage.", go: "Kostenlosen Platz sichern →", no: "Nicht jetzt", x: "Schließen", d: "Tage", hh: "Std", m: "Min", live: "Läuft jetzt", meta: "Kostenloses Online-Event · 11.–22. Jan 2027" }
  };
  var lang = (document.documentElement.lang || "en").slice(0, 2), L = T[lang] || T.en;
  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  var now = function () { return new Date(); };
  if (now() >= END) return;
  // Countdown in der Sidebar
  function tick() {
    document.querySelectorAll("[data-m365con-countdown]").forEach(function (el) {
      var n = now(), diff = START - n;
      if (diff <= 0) { el.innerHTML = '<span class="sb-live">● ' + L.live + '</span><span class="sb-meta">' + L.meta + "</span>"; return; }
      var d = Math.floor(diff / 864e5), h = Math.floor(diff % 864e5 / 36e5), m = Math.floor(diff % 36e5 / 6e4);
      el.innerHTML = '<div class="sb-tiles"><div class="sb-tile"><b>' + d + "</b><small>" + L.d + '</small></div><div class="sb-tile"><b>' + h + "</b><small>" + L.hh + '</small></div><div class="sb-tile"><b>' + m + "</b><small>" + L.m + '</small></div></div><span class="sb-meta">' + L.meta + "</span>";
    });
  }
  tick(); setInterval(tick, 30000);
  // Popup
  if (/\/community\//.test(location.pathname)) return;
  var until = +ls("m365_attend_until") || 0; if (until > Date.now()) return;
  var timer, shown = false, last;
  function css() { if (document.querySelector('link[href*="sbar.css"]')) return; var l = document.createElement("link"); l.rel = "stylesheet"; l.href = BASE + "/assets/sbar.css"; document.head.appendChild(l); }
  function close(days) { var o = document.getElementById("att-ov"); if (o) o.remove(); ls("m365_attend_until", String(Date.now() + days * 864e5)); if (last && last.focus) try { last.focus(); } catch (e) {} document.removeEventListener("keydown", esc); }
  function esc(e) { if (e.key === "Escape") close(7); }
  function show() {
    if (shown || document.hidden) { arm(); return; }
    shown = true; css(); last = document.activeElement;
    var o = document.createElement("div"); o.id = "att-ov"; o.className = "att-ov";
    o.innerHTML = '<div class="att-box" role="dialog" aria-modal="true" aria-labelledby="att-h"><button class="att-x" type="button" aria-label="' + L.x + '">×</button>' +
      '<a href="' + URL_ + '" rel="noopener"><img src="' + BASE + '/assets/attending-m365con.webp" alt="I\'m attending M365Con International 2027" width="675" height="563"></a>' +
      '<h2 id="att-h">' + L.h + "</h2><p>" + L.p + '</p><div class="att-act"><a class="sb-btn" href="' + URL_ + '" rel="noopener">' + L.go + '</a><button class="att-no" type="button">' + L.no + "</button></div></div>";
    o.addEventListener("click", function (e) { if (e.target === o) close(7); });
    o.querySelector(".att-x").onclick = o.querySelector(".att-no").onclick = function () { close(7); };
    o.querySelector(".sb-btn").addEventListener("click", function () { ls("m365_attend_until", String(Date.now() + 30 * 864e5)); });
    document.body.appendChild(o); document.addEventListener("keydown", esc); o.querySelector(".att-x").focus();
  }
  function arm() { clearTimeout(timer); if (!shown) timer = setTimeout(show, 120000); }
  ["mousemove", "mousedown", "keydown", "scroll", "touchstart", "wheel"].forEach(function (ev) { window.addEventListener(ev, arm, { passive: true }); });
  arm();
})();
