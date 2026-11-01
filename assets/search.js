/* T37 Seitensuche: /search/ und /<lang>/search/. Fragt /api/search der Community-API (alle Sprachen, tippfehlertolerant)
   und zeigt Treffer mit Facetten (Typ, Sprache, Thema, Jahr). Filter stehen in der Adresse (?q=&type=&lang=&entity=&year=),
   damit Suchen teilbar sind. Leicht fuer INP: Eingabe entprellt, Arbeit nur in den fetch-Rueckrufen. */
(function () {
  var box = document.getElementById("srch"); if (!box) return;
  var C = {}; try { C = JSON.parse(box.dataset.cfg || "{}"); } catch (e) { return; }
  var form = document.querySelector(".srch-f"), input = document.getElementById("srch-q");
  var fa = box.querySelector(".srch-fa"), out = box.querySelector(".srch-r");
  var KEYS = ["type", "lang", "entity", "year"], st = { q: "", page: 1, f: {} }, timer = 0, seq = 0, items = [];
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function label(k, v) {
    if (k === "type") return (C.types || {})[v] || v;
    if (k === "lang") return (C.langs || {})[v] || v;
    if (k === "entity") return v.replace(/-/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
    return v;
  }
  function readUrl() {
    var p = new URLSearchParams(location.search); st.q = (p.get("q") || "").trim(); st.f = {};
    KEYS.forEach(function (k) { var v = p.get(k); if (v) st.f[k] = v; });
  }
  function writeUrl() {
    var p = new URLSearchParams(); if (st.q) p.set("q", st.q);
    KEYS.forEach(function (k) { if (st.f[k]) p.set(k, st.f[k]); });
    history.replaceState(null, "", location.pathname + (p.toString() ? "?" + p : ""));
  }
  function run(more) {
    if (st.q.length < 2) { out.innerHTML = ""; fa.innerHTML = ""; return; }
    st.page = more ? st.page + 1 : 1; if (!more) items = [];
    var p = new URLSearchParams({ q: st.q, pref: C.lang || "en", page: String(st.page), size: "20" });
    KEYS.forEach(function (k) { if (st.f[k]) p.set(k, st.f[k]); });
    var my = ++seq;
    fetch(C.api + "/api/search?" + p, { credentials: "omit" }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (j) { if (my !== seq) return; items = items.concat(j.results || []); render(j); })
      .catch(function () { if (my !== seq) return; out.innerHTML = '<p class="srch-c">' + esc(C.err) + "</p>"; });
  }
  function render(j) {
    var total = j.total || 0;
    var h = '<p class="srch-c">' + esc((C.count || "{n}").replace("{n}", total.toLocaleString(C.lang))) + "</p>";
    if (!items.length) h += "<p>" + esc(C.none) + "</p>";
    else h += "<ol>" + items.map(function (r) {
      var meta = [label("type", r.type), label("lang", r.lang), r.date || ""].filter(Boolean).join(" · ");
      return '<li><a href="' + esc(r.url) + '"' + (r.lang && r.lang !== C.lang ? ' hreflang="' + esc(r.lang) + '"' : "") + ">" + esc(r.title) + '</a><div class="m">' + esc(meta) + "</div>" + (r.summary ? "<p>" + esc(r.summary) + "</p>" : "") + "</li>";
    }).join("") + "</ol>";
    if (items.length < total) h += '<p><button type="button" class="btn" data-more="1">' + esc(C.more) + "</button></p>";
    out.innerHTML = h;
    var fh = "", f = j.facets || {};
    KEYS.forEach(function (k) {
      var vals = Object.keys(f[k] || {}); if (!vals.length && !st.f[k]) return;
      vals.sort(function (a, b) { return k === "year" ? b.localeCompare(a) : (f[k][b] - f[k][a]); });
      fh += "<h2>" + esc((C.h || {})[k] || k) + "</h2>" + vals.slice(0, k === "entity" ? 15 : 20).map(function (v) {
        return '<button type="button" data-k="' + k + '" data-v="' + esc(v) + '" aria-pressed="' + (st.f[k] === v) + '">' + esc(label(k, v)) + "<span>" + f[k][v] + "</span></button>";
      }).join("");
    });
    if (Object.keys(st.f).length) fh += '<p><button type="button" data-clear="1">' + esc(C.clear) + "</button></p>";
    fa.innerHTML = fh;
  }
  fa.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    if (b.dataset.clear) st.f = {};
    else { var k = b.dataset.k, v = b.dataset.v; if (st.f[k] === v) delete st.f[k]; else st.f[k] = v; }
    writeUrl(); run(false);
  });
  out.addEventListener("click", function (e) { if (e.target.closest("[data-more]")) run(true); });
  form.addEventListener("submit", function (e) { e.preventDefault(); clearTimeout(timer); st.q = input.value.trim(); writeUrl(); run(false); });
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { st.q = input.value.trim(); writeUrl(); run(false); }, 350);
  });
  readUrl(); input.value = st.q; if (st.q) run(false);
})();
