/* Show Notes der Spreaker-Folgen bearbeiten (Redaktion/Admin): Liste aller Folgen aus dem taeglichen Spreaker-Abruf, Text bis 12000 Zeichen ohne Mindestumfang,
   Kernpunkte und FAQ als eigene Textfelder, Zuruecksetzen auf den Spreaker-Text. Gespeichert wird bei uns - Spreaker selbst bleibt unveraendert. */
(function () {
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-notes"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = de ? { h: "Show Notes", intro: "Die Show Notes aller Spreaker-Folgen werden täglich geholt. Hier bearbeitest du sie: der Text ist nicht auf 300 Zeichen beschränkt (bis 12.000 Zeichen, kein Mindestumfang), Kernpunkte und FAQ haben eigene Felder. Spreaker selbst bleibt unverändert; „Zurücksetzen“ stellt den Spreaker-Text wieder her.", only: "Nur für Redaktion und Admin.", lang: "Show", search: "Folge suchen …", go: "Suchen", more: "Mehr laden", none: "Keine Folgen gefunden. Die Show Notes werden beim nächsten Seitenbau (täglich) geholt.", edit: "Bearbeiten", edited: "bearbeitet", words: "Wörter", kp: "Kernpunkte", faq: "FAQ", body: "Show Notes (Text)", bodyh: "Auszeichnung: ## Überschrift, - Liste, **fett**, *kursiv*, {{link|https://url|Text}}, {{img|https://bild.jpg|Alt-Text}}. Kein Mindestumfang.", kpl: "Kernpunkte (ein Punkt pro Zeile, 3–6, je 10–200 Zeichen)", faql: "FAQ (Frage in einer Zeile, Antwort darunter; Einträge durch eine Leerzeile trennen, bis zu 10)", save: "Speichern", reset: "Auf Spreaker-Text zurücksetzen", saved: "Gespeichert – sichtbar nach dem nächsten Seitenbau.", resetok: "Zurückgesetzt.", cancel: "Schließen", orig: "Originaltext aus Spreaker", guests: "Gäste laut Feed", err: "Konnte nicht gespeichert werden.", e_bad_link: "Ein Link braucht eine https-Adresse (keine Kurzlinks).", e_too_many_links: "Höchstens 40 Links.", e_bad_image: "Ein Bild braucht eine https-Adresse auf .jpg, .png, .webp, .gif oder .avif.", e_bad_alt: "Jedes Bild braucht einen Alt-Text (mind. 5 Zeichen).", e_bad_keypoints: "Jeder Kernpunkt braucht mindestens 10 Zeichen.", e_too_many_keypoints: "Höchstens 8 Kernpunkte.", e_bad_faq: "Jede FAQ braucht Frage (ab 10) und Antwort (ab 20 Zeichen).", e_too_many_faq: "Höchstens 10 FAQ-Einträge.", e_forbidden: "Nur für Redaktion und Admin.", confirm: "Bearbeitung verwerfen und den Spreaker-Text wiederherstellen?" }
    : { h: "Show notes", intro: "The show notes of all Spreaker episodes are pulled daily. Edit them here: the text is not limited to 300 characters (up to 12,000, no minimum), key points and FAQ have their own fields. Spreaker itself stays unchanged; “Reset” restores the Spreaker text.", only: "Editors and admins only.", lang: "Show", search: "Find episode …", go: "Search", more: "Load more", none: "No episodes found. Show notes are pulled with the next site build (daily).", edit: "Edit", edited: "edited", words: "words", kp: "key points", faq: "FAQ", body: "Show notes (text)", bodyh: "Markup: ## heading, - list, **bold**, *italic*, {{link|https://url|text}}, {{img|https://image.jpg|alt text}}. No minimum length.", kpl: "Key points (one per line, 3–6, 10–200 characters each)", faql: "FAQ (question on one line, answer below; separate entries with a blank line, up to 10)", save: "Save", reset: "Reset to Spreaker text", saved: "Saved – visible after the next site build.", resetok: "Reset.", cancel: "Close", orig: "Original text from Spreaker", guests: "Guests per feed", err: "Could not be saved.", e_bad_link: "A link needs an https address (no short links).", e_too_many_links: "At most 40 links.", e_bad_image: "An image needs an https address ending in .jpg, .png, .webp, .gif or .avif.", e_bad_alt: "Every image needs alt text (min. 5 characters).", e_bad_keypoints: "Every key point needs at least 10 characters.", e_too_many_keypoints: "At most 8 key points.", e_bad_faq: "Every FAQ needs a question (10+) and an answer (20+ characters).", e_too_many_faq: "At most 10 FAQ entries.", e_forbidden: "Editors and admins only.", confirm: "Discard the edit and restore the Spreaker text?" };
  var LN = { en: "English", de: "Deutsch", es: "Español", fr: "Français", it: "Italiano", pt: "Português", nl: "Nederlands", pl: "Polski", id: "Bahasa Indonesia", ru: "Русский", uk: "Українська", ar: "العربية", he: "עברית", hi: "हिन्दी", ja: "日本語", ko: "한국어" };
  var sel = h("select", { "aria-label": Q.lang }, Object.keys(LN).map(function (k) { return h("option", { value: k, text: LN[k] }); })), q = h("input", { type: "search", maxlength: 80, placeholder: Q.search, "aria-label": Q.search });
  var list = h("div"), msg = h("p", { role: "status", class: "mut" }), form = h("div"), off = 0, shown = [];
  function faqText(l) { return (l || []).map(function (x) { return x.q + "\n" + x.a; }).join("\n\n"); }
  function open(it, li) {
    form.textContent = ""; msg.textContent = "";
    api("/api/notes/get?lang=" + sel.value + "&id=" + encodeURIComponent(it.id)).then(function (r) {
      var d = r.j || {}; if (!d.id) { msg.textContent = Q["e_" + d.error] || Q.err; return; }
      var bo = h("textarea", { rows: 20, maxlength: 12000 }), kp = h("textarea", { rows: 5, maxlength: 1800, "aria-label": Q.kpl }), fq = h("textarea", { rows: 9, maxlength: 8000, "aria-label": Q.faql });
      bo.dataset.links = "1"; bo.value = d.body || ""; kp.value = (d.keypoints || []).join("\n"); fq.value = faqText(d.faq);
      var f = h("div", { class: "ed-form", style: "border:1px solid var(--bd);border-radius:.5em;padding:.8em 1em;margin:1em 0" });
      f.appendChild(h("h3", { text: d.title })); f.appendChild(h("p", { class: "mut", text: (d.published || "") + (d.edited ? " · " + Q.edited : "") }));
      f.appendChild(h("div", {}, [h("label", { text: Q.body }), U.editor ? U.editor(bo, 12000) : bo])); f.appendChild(h("p", { class: "mut", text: Q.bodyh }));
      f.appendChild(U.lab(Q.kpl, kp)); f.appendChild(U.lab(Q.faql, fq));
      if ((d.persons || []).length) f.appendChild(h("p", { class: "mut", text: Q.guests + ": " + d.persons.map(function (p) { return p.name; }).join(", ") }));
      var det = h("details", {}, [h("summary", { class: "mut", text: Q.orig }), h("pre", { style: "white-space:pre-wrap", text: (d.spreaker && d.spreaker.body) || "" })]); f.appendChild(det);
      if (U.seo) f.appendChild(U.seo.box({ kind: "feed", draft: function () { return { title: d.title, summary: "", body: bo.value, keypoints: kp.value, faq: fq.value, topics: [], lang: sel.value }; } }));
      f.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.save, onclick: function () {
        api("/api/notes/save", { method: "POST", body: { lang: sel.value, id: d.id, body: bo.value, keypoints: kp.value.split("\n").map(function (x) { return x.trim(); }).filter(Boolean), faq: parseFaq(fq.value) } }).then(function (x) { var j = x.j || {}; msg.textContent = j.ok ? Q.saved : (Q["e_" + j.error] || Q.err); if (j.ok) load(true); });
      } }), " ", h("button", { type: "button", class: "btn", text: Q.reset, onclick: function () {
        if (!confirm(Q.confirm)) return; api("/api/notes/reset", { method: "POST", body: { lang: sel.value, id: d.id } }).then(function () { msg.textContent = Q.resetok; form.textContent = ""; load(true); });
      } }), " ", h("button", { type: "button", class: "btn", text: Q.cancel, onclick: function () { form.textContent = ""; } })]));
      form.appendChild(f); f.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
  function parseFaq(t) { return String(t || "").replace(/\r/g, "").split(/\n\s*\n/).map(function (b) { var ls = b.split("\n").map(function (l) { return l.trim(); }).filter(Boolean); return ls.length ? { q: ls[0], a: ls.slice(1).join(" ") } : null; }).filter(Boolean); }
  function row(it) {
    var li = h("li", { style: "padding:.5em 0;border-bottom:1px solid var(--bd)" }, [h("b", { text: it.title }), h("span", { class: "mut", text: " · " + (it.published || "") + " · " + it.words + " " + Q.words + " · " + it.keypoints + " " + Q.kp + " · " + it.faq + " " + Q.faq + (it.edited ? " · ✎ " + Q.edited : "") }), " ",
      h("button", { type: "button", class: "btn", text: Q.edit, onclick: function () { open(it, li); } })]);
    return li;
  }
  var ul = h("ul", { style: "list-style:none;padding:0" }), moreb = h("button", { type: "button", class: "btn", text: Q.more, onclick: function () { load(false); }, hidden: "" });
  function load(reset) {
    if (reset) { off = 0; ul.textContent = ""; }
    api("/api/notes/list?lang=" + sel.value + "&q=" + encodeURIComponent(q.value) + "&limit=30&offset=" + off).then(function (r) {
      var d = r.j || {}; if (d.error) { msg.textContent = Q["e_" + d.error] || Q.only; moreb.hidden = true; return; }
      if (!d.items.length && off === 0) { msg.textContent = Q.none; moreb.hidden = true; return; }
      msg.textContent = ""; d.items.forEach(function (it) { ul.appendChild(row(it)); }); off += d.items.length; moreb.hidden = off >= d.total;
    });
  }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro }));
  root.appendChild(h("p", {}, [sel, " ", q, " ", h("button", { type: "button", class: "btn", text: Q.go, onclick: function () { load(true); } })]));
  root.appendChild(msg); root.appendChild(form); ul.id = "notes-list"; root.appendChild(ul); root.appendChild(h("p", {}, [moreb]));
  sel.addEventListener("change", function () { form.textContent = ""; load(true); }); q.addEventListener("keydown", function (e) { if (e.key === "Enter") load(true); });
  api("/api/me").then(function (r) { var u = r.j && r.j.user; if (u && (u.admin || u.editor)) load(true); else root.appendChild(h("p", { class: "mut", text: Q.only })); });
})();
