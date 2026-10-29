/* Barrierefreiheits-Einstellungen: lokal gespeichert (localStorage), kein Tracking, keine externen Anfragen. window.M365A = {t} */
(function () {
  var A = window.M365A; if (!A) return;
  var T = A.t || {}, K = "m365-a11y", H = document.documentElement;
  var S = { s: 0, hc: 0, dk: 0, font: 0, sp: 0, ul: 0, nomo: 0 };
  try { var v = JSON.parse(localStorage.getItem(K) || "{}"); for (var k in S) if (typeof v[k] === "number") S[k] = v[k]; } catch (e) {}
  var CL = { hc: "a11y-hc", font: "a11y-font", sp: "a11y-sp", ul: "a11y-ul", nomo: "a11y-nomo" };
  function apply() {
    H.classList.remove("a11y-s1", "a11y-s2", "a11y-s3"); if (S.s) H.classList.add("a11y-s" + S.s);
    for (var k in CL) H.classList.toggle(CL[k], !!S[k]);
    if (S.dk) H.setAttribute("data-theme", "dark"); else if (H.getAttribute("data-theme") === "dark" && A.dk0 !== "dark") H.removeAttribute("data-theme");
    try { localStorage.setItem(K, JSON.stringify(S)); } catch (e) {}
  }
  A.dk0 = H.getAttribute("data-theme"); apply();
  function h(t, a, kids) { var e = document.createElement(t); for (var k in a || {}) { if (k === "text") e.textContent = a[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), a[k]); else e.setAttribute(k, a[k]); } (kids || []).forEach(function (c) { e.appendChild(c); }); return e; }
  function build() {
    var b = h("button", { type: "button", class: "a11yb", "aria-label": T.a11y, "aria-expanded": "false", "aria-controls": "a11yp", title: T.a11y, text: "♿" });
    var p = h("div", { class: "a11yp", id: "a11yp", role: "dialog", "aria-label": T.a11y, hidden: "" });
    var tg = [];
    function toggle(key, label) { var bt = h("button", { type: "button", "aria-pressed": S[key] ? "true" : "false", text: label, onclick: function () { S[key] = S[key] ? 0 : 1; apply(); sync(); } }); tg.push([key, bt]); return h("div", { class: "ar" }, [bt]); }
    function sync() { tg.forEach(function (x) { x[1].setAttribute("aria-pressed", S[x[0]] ? "true" : "false"); }); sz.textContent = (100 + [0, 15, 30, 50][S.s]) + "%"; }
    var sz = h("span", { "aria-live": "polite" });
    var close = h("button", { type: "button", class: "x", "aria-label": T.a_close, text: "✕", onclick: function () { show(false); b.focus(); } });
    p.appendChild(close); p.appendChild(h("h2", { text: T.a11y }));
    p.appendChild(h("div", { class: "sz" }, [h("button", { type: "button", "aria-label": T.a_smaller, text: "A−", onclick: function () { S.s = Math.max(0, S.s - 1); apply(); sync(); } }), sz, h("button", { type: "button", "aria-label": T.a_larger, text: "A+", onclick: function () { S.s = Math.min(3, S.s + 1); apply(); sync(); } })]));
    p.appendChild(toggle("hc", T.a_contrast)); p.appendChild(toggle("dk", T.a_dark)); p.appendChild(toggle("font", T.a_font)); p.appendChild(toggle("sp", T.a_spacing)); p.appendChild(toggle("ul", T.a_links)); p.appendChild(toggle("nomo", T.a_motion));
    p.appendChild(h("div", { class: "ar" }, [h("button", { type: "button", text: T.a_reset, onclick: function () { for (var k in S) S[k] = 0; apply(); sync(); } })]));
    p.appendChild(h("small", { text: T.a_note }));
    function show(o) { p.hidden = !o; b.setAttribute("aria-expanded", o ? "true" : "false"); if (o) { var f = p.querySelector("button"); f && f.focus(); } }
    b.addEventListener("click", function () { show(p.hidden); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !p.hidden) { show(false); b.focus(); } });
    var fs = document.querySelector(".fshare");
    if (fs) { b.classList.add("inbar"); p.classList.add("inbar"); fs.appendChild(b); } else document.body.appendChild(b);
    document.body.appendChild(p); sync();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build); else build();
})();
