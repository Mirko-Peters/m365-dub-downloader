/* Community-Podcast: Folge einreichen (mp3 -> Spreaker-Entwurf), abstimmen, eigene Folgen */
(function () {
  var M365L = window.M365L || function (de, k, a, b) { return de ? a : b; };
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-podcast"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = M365L(de, "podcast.Q", { h: "Podcast", intro: "Reiche eine Podcast-Folge ein: Die Audiodatei (mp3, max. 50 MB) landet als Entwurf in Spreaker, nur die Redaktion kann sie hören. Die Community stimmt über Titel und Beschreibung ab. Ab {n} Stimmen prüft die Redaktion die Folge und veröffentlicht sie. Dein Profil muss öffentlich sein, eine Einreichung pro Woche.", login: "Melde dich an, um Folgen einzureichen oder abzustimmen.", newp: "Folge einreichen", title: "Titel", desc: "Beschreibung (mindestens 30 Zeichen)", lang: "Sprache der Folge", topics: "Themen", file: "Audiodatei (mp3)", rights: "Die Rechte an Inhalt und Audio liegen bei mir.", ai: "Ich habe KI eingesetzt (wird offengelegt).", send: "Einreichen", cancel: "Abbrechen", mine: "Meine Folgen", pitches: "Pitches zum Abstimmen", published: "Veröffentlicht", none: "Noch nichts da.", st_submitted: "Zur Abstimmung", st_review: "In Prüfung durch die Redaktion", st_published: "Veröffentlicht", st_rejected: "Abgelehnt", st_expired: "Abgelaufen", votes: "Stimmen", vote: "Abstimmen", del_: "Löschen", confirmdel: "Diese Folge löschen?", uploading: "Wird hochgeladen …", done: "Eingereicht. Sie erscheint jetzt zur Abstimmung.", e_title: "Der Titel braucht mindestens 5 Zeichen.", e_desc: "Die Beschreibung braucht mindestens 30 Zeichen.", e_file: "Bitte eine mp3-Datei wählen.", e_not_mp3: "Das ist keine mp3-Datei.", e_too_big: "Die Datei ist größer als 50 MB.", e_rights: "Bitte bestätige die Rechte.", e_need_profile: "Mache zuerst dein Profil öffentlich (Reiter Profil).", e_rate_limit: "Nur eine Einreichung pro Woche.", e_not_configured: "Der Upload ist noch nicht eingerichtet.", e_spreaker: "Der Upload zu Spreaker hat nicht geklappt, bitte später erneut versuchen.", e_spreaker_upload: "Der Upload zu Spreaker hat nicht geklappt, bitte später erneut versuchen.", e_too_new: "Neue Konten (unter 24 Stunden) können noch nicht abstimmen.", e_own: "Für die eigene Folge kannst du nicht abstimmen.", e_generic: "Das hat nicht geklappt.", mod: "Zur Prüfung (Schwelle erreicht) und offene Pitches", spreaker: "In Spreaker öffnen", reject: "Ablehnen (Entwurf löschen)", reason: "Grund (sichtbar für den Autor)", poll: "Jetzt Status abgleichen" },
    { h: "Podcast", intro: "Submit a podcast episode: the audio file (mp3, max. 50 MB) is stored as a draft in Spreaker that only the editors can hear. The community votes on title and description. At {n} votes the editors review the episode and publish it. Your profile must be public, one submission per week.", login: "Sign in to submit episodes or vote.", newp: "Submit an episode", title: "Title", desc: "Description (at least 30 characters)", lang: "Language of the episode", topics: "Topics", file: "Audio file (mp3)", rights: "I own the rights to the content and audio.", ai: "I used AI (will be disclosed).", send: "Submit", cancel: "Cancel", mine: "My episodes", pitches: "Pitches to vote on", published: "Published", none: "Nothing here yet.", st_submitted: "Open for votes", st_review: "Under editorial review", st_published: "Published", st_rejected: "Rejected", st_expired: "Expired", votes: "votes", vote: "Vote", del_: "Delete", confirmdel: "Delete this episode?", uploading: "Uploading …", done: "Submitted. It is now open for votes.", e_title: "The title needs at least 5 characters.", e_desc: "The description needs at least 30 characters.", e_file: "Please choose an mp3 file.", e_not_mp3: "That is not an mp3 file.", e_too_big: "The file is larger than 50 MB.", e_rights: "Please confirm the rights.", e_need_profile: "Make your profile public first (tab Profile).", e_rate_limit: "Only one submission per week.", e_not_configured: "Upload is not set up yet.", e_spreaker: "The upload to Spreaker failed, please try again later.", e_spreaker_upload: "The upload to Spreaker failed, please try again later.", e_too_new: "New accounts (under 24 hours) cannot vote yet.", e_own: "You cannot vote for your own episode.", e_generic: "That did not work.", mod: "For review (threshold reached) and open pitches", spreaker: "Open in Spreaker", reject: "Reject (delete draft)", reason: "Reason (visible to the author)", poll: "Sync status now" });
  var LANGS = [["en", "English"], ["de", "Deutsch"], ["fr", "Français"], ["es", "Español"], ["it", "Italiano"], ["nl", "Nederlands"], ["pt", "Português"], ["pl", "Polski"], ["id", "Bahasa Indonesia"], ["ru", "Русский"], ["uk", "Українська"], ["ar", "العربية"], ["he", "עברית"], ["hi", "हिन्दी"], ["ja", "日本語"], ["ko", "한국어"], ["ml", "മലയാളം"], ["pa", "ਪੰਜਾਬੀ"], ["ta", "தமிழ்"], ["te", "తెలుగు"]];
  var msg = h("p", { role: "status", class: "mut" }), box = h("div"), mineBox = h("div"), pitchBox = h("div"), modBox = h("div"), TH = 25;
  function say(t) { msg.textContent = t || ""; }
  function pfx(l) { return l && l !== "en" ? "/" + l : ""; }
  function form() {
    var f = h("form"), ti = U.inp("", 140), de_ = h("textarea", { maxlength: 2000, rows: 5 }), lg = U.sel(LANGS, X.lang || "en"), tp = U.topicsUI([], 10), fi = h("input", { type: "file", accept: "audio/mpeg,.mp3" });
    var rt = h("input", { type: "checkbox" }), ai = h("input", { type: "checkbox" });
    f.appendChild(U.lab(Q.title, ti)); f.appendChild(U.lab(Q.desc, de_)); f.appendChild(U.lab(Q.lang, lg)); f.appendChild(h("div", {}, [h("b", { text: Q.topics }), tp])); f.appendChild(U.lab(Q.file, fi));
    f.appendChild(h("p", {}, [h("label", {}, [rt, " " + Q.rights])])); f.appendChild(h("p", {}, [h("label", {}, [ai, " " + Q.ai])]));
    var go = h("button", { type: "button", class: "btn main", text: Q.send, onclick: function () {
      if (!fi.files[0]) return say(Q.e_file);
      var fd = new FormData(); fd.set("title", ti.value); fd.set("description", de_.value); fd.set("lang", lg.value); fd.set("topics", JSON.stringify(tp.get())); fd.set("rights", rt.checked ? "1" : "0"); fd.set("ai", ai.checked ? "1" : "0"); fd.set("file", fi.files[0]);
      say(Q.uploading); go.disabled = true;
      fetch(X.api + "/api/podcast/submit", { method: "POST", body: fd, credentials: "include", headers: { "x-requested-with": "m365" } }).then(function (r) { return r.json(); }).then(function (j) {
        go.disabled = false; if (j.ok) { say(Q.done); box.textContent = ""; load(); } else say(Q["e_" + j.error] || Q.e_generic);
      }).catch(function () { go.disabled = false; say(Q.e_generic); });
    } });
    f.appendChild(h("p", {}, [go, " ", h("button", { type: "button", class: "btn", text: Q.cancel, onclick: function () { box.textContent = ""; } })])); f.addEventListener("submit", function (e) { e.preventDefault(); }); return f;
  }
  function voteBtn(p) {
    var b = h("button", { type: "button", class: "btn", "aria-pressed": p.voted ? "true" : "false", onclick: function () { say(""); api("/api/podcast/vote", { method: "POST", body: { id: p.id } }).then(function (r) { var j = r.j || {}; if (j.ok) { p.voted = j.voted; p.votes = j.votes; b.setAttribute("aria-pressed", j.voted ? "true" : "false"); b.textContent = "▲ " + j.votes + " / " + TH; } else say(Q["e_" + j.error] || Q.e_generic); }); } });
    b.textContent = "▲ " + p.votes + " / " + TH; return b;
  }
  function load() {
    api("/api/podcast/mine").then(function (r) {
      mineBox.textContent = ""; var d = r.j || {}; if (!d.items) return; mineBox.appendChild(h("h3", { text: Q.mine }));
      if (!d.items.length) mineBox.appendChild(h("p", { class: "mut", text: Q.none }));
      d.items.forEach(function (p) {
        var li = h("p", {}, [h("b", { text: p.title }), h("span", { class: "mut", text: " · " + (Q["st_" + p.status] || p.status) + " · " + p.votes + " " + Q.votes })]);
        if (p.note) li.appendChild(h("span", { class: "mut", text: " · " + p.note }));
        if (p.status === "published") li.appendChild(h("a", { class: "btn", href: X.base + pfx(p.lang) + "/community/podcast/" + p.slug + "/", text: Q.published, style: "margin-inline-start:.5em" }));
        else li.appendChild(h("button", { type: "button", class: "btn", text: Q.del_, style: "margin-inline-start:.5em", onclick: function () { if (confirm(Q.confirmdel)) api("/api/podcast/delete", { method: "POST", body: { id: p.id } }).then(load); } }));
        mineBox.appendChild(li);
      });
    });
    api("/api/podcast/list").then(function (r) {
      pitchBox.textContent = ""; var d = r.j || {}; TH = d.threshold || 25; var it = (d.items || []).filter(function (p) { return p.status !== "published"; });
      pitchBox.appendChild(h("h3", { text: Q.pitches })); if (!it.length) pitchBox.appendChild(h("p", { class: "mut", text: Q.none }));
      it.forEach(function (p) { pitchBox.appendChild(h("div", { style: "padding:.5em 0;border-bottom:1px solid var(--bd)" }, [h("b", { text: p.title }), h("span", { class: "mut", text: " · " + p.name + " · " + p.lang + (p.status === "review" ? " · " + Q.st_review : "") }), h("p", { text: p.description }), voteBtn(p)])); });
    });
  }
  function moderation() {
    function draw() {
      api("/api/admin/podcast").then(function (r) {
        modBox.textContent = ""; modBox.appendChild(h("h3", { text: Q.mod })); var it = (r.j && r.j.items) || [];
        modBox.appendChild(h("p", {}, [h("button", { type: "button", class: "btn", text: Q.poll, onclick: function () { api("/api/admin/podcast/poll", { method: "POST" }).then(draw); } })]));
        if (!it.length) modBox.appendChild(h("p", { class: "mut", text: Q.none }));
        it.forEach(function (p) {
          var rs = h("input", { type: "text", maxlength: 300, placeholder: Q.reason, "aria-label": Q.reason });
          modBox.appendChild(h("div", { style: "padding:.5em 0;border-bottom:1px solid var(--bd)" }, [h("b", { text: p.title }), h("span", { class: "mut", text: " · " + p.name + " · " + p.lang + " · " + p.votes + " " + Q.votes + (p.status === "review" ? " ✔" : "") + (p.ai ? " · AI" : "") }), h("p", { text: p.description }),
            p.spreaker ? h("a", { class: "btn main", href: p.spreaker, target: "_blank", rel: "noopener", text: Q.spreaker }) : null, " ", rs, " ", h("button", { type: "button", class: "btn", text: Q.reject, onclick: function () { api("/api/admin/podcast/reject", { method: "POST", body: { id: p.id, note: rs.value } }).then(draw); } })]));
        });
      });
    }
    root.appendChild(modBox); draw();
  }
  root.appendChild(h("h2", { text: Q.h })); root.appendChild(h("p", { class: "mut", text: Q.intro.replace("{n}", "25") })); root.appendChild(msg);
  root.appendChild(h("p", {}, [h("button", { type: "button", class: "btn main", text: Q.newp, onclick: function () { box.textContent = ""; box.appendChild(form()); } })]));
  root.appendChild(box); root.appendChild(mineBox); root.appendChild(pitchBox);
  api("/api/me").then(function (r) { var u = r.j && r.j.user; if (u && (u.admin || u.editor)) moderation(); if (u) load(); else root.appendChild(h("p", { text: Q.login })); }).catch(function () { root.appendChild(h("p", { text: Q.login })); });
})();
