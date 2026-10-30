/* Creator-Videos für den YouTube-Kanal m365 Show: einreichen (Upload direkt zu YouTube, zunächst privat), abstimmen, eigene Videos */
(function () {
  var M365L = window.M365L || function (de, k, a, b) { return de ? a : b; };
  var X = window.M365X, U = window.M365U, root = document.getElementById("c-video"); if (!X || !U || !root) return;
  var de = X.lang === "de", h = U.h, api = U.api;
  var Q = M365L(de, "video.Q", { h: "Videos", intro: "Reiche ein Video für den YouTube-Kanal m365 Show ein: Die Datei wird direkt zu YouTube hochgeladen und bleibt zunächst privat. Die Community stimmt über Titel und Beschreibung ab. Ab {n} Stimmen prüft die Redaktion das Video und schaltet es öffentlich. Dein Profil muss öffentlich sein, eine Einreichung pro Woche.", login: "Melde dich an, um Videos einzureichen oder abzustimmen.", newp: "Video einreichen", title: "Titel (max. 100 Zeichen)", desc: "Beschreibung (mindestens 30 Zeichen)", lang: "Sprache des Videos", topics: "Themen", file: "Videodatei", rights: "Die Rechte an Bild, Ton und Musik liegen bei mir.", ai: "Ich habe KI eingesetzt (wird offengelegt).", send: "Hochladen und einreichen", cancel: "Abbrechen", mine: "Meine Videos", pitches: "Videos zum Abstimmen", published: "Veröffentlicht", none: "Noch nichts da.", st_submitted: "Zur Abstimmung", st_review: "In Prüfung durch die Redaktion", st_published: "Veröffentlicht", st_rejected: "Abgelehnt", st_expired: "Abgelaufen", votes: "Stimmen", del_: "Löschen", confirmdel: "Dieses Video löschen?", preparing: "Upload wird vorbereitet …", uploading: "Wird hochgeladen: {p} %", finishing: "Wird abgeschlossen …", done: "Eingereicht. Das Video erscheint jetzt zur Abstimmung.", e_title: "Der Titel braucht mindestens 5 Zeichen.", e_desc: "Die Beschreibung braucht mindestens 30 Zeichen.", e_file: "Bitte eine Videodatei wählen.", e_too_big: "Die Datei ist größer als 2 GB.", e_rights: "Bitte bestätige die Rechte.", e_need_profile: "Mache zuerst dein Profil öffentlich (Reiter Profil).", e_rate_limit: "Nur eine Einreichung pro Woche.", e_not_configured: "Der Upload ist noch nicht eingerichtet.", e_youtube: "YouTube hat die Anfrage abgelehnt, bitte später erneut versuchen.", e_verify: "YouTube hat das Video nicht bestätigt, bitte erneut versuchen.", e_upload: "Der Upload ist fehlgeschlagen.", e_too_new: "Neue Konten (unter 24 Stunden) können noch nicht abstimmen.", e_own: "Für das eigene Video kannst du nicht abstimmen.", e_generic: "Das hat nicht geklappt.", mod: "Zu tun: Video prüfen und in YouTube Studio öffentlich schalten (Schwelle erreicht) · offene Pitches", studio: "In YouTube Studio öffnen", reject: "Ablehnen (Video löschen)", reason: "Grund (sichtbar für den Autor)", poll: "Jetzt Status abgleichen" },
    { h: "Videos", intro: "Submit a video for the m365 Show YouTube channel: the file is uploaded straight to YouTube and stays private at first. The community votes on title and description. At {n} votes the editors review the video and make it public. Your profile must be public, one submission per week.", login: "Sign in to submit videos or vote.", newp: "Submit a video", title: "Title (max. 100 characters)", desc: "Description (at least 30 characters)", lang: "Language of the video", topics: "Topics", file: "Video file", rights: "I own the rights to picture, sound and music.", ai: "I used AI (will be disclosed).", send: "Upload and submit", cancel: "Cancel", mine: "My videos", pitches: "Videos to vote on", published: "Published", none: "Nothing here yet.", st_submitted: "Open for votes", st_review: "Under editorial review", st_published: "Published", st_rejected: "Rejected", st_expired: "Expired", votes: "votes", del_: "Delete", confirmdel: "Delete this video?", preparing: "Preparing the upload …", uploading: "Uploading: {p} %", finishing: "Finishing …", done: "Submitted. The video is now open for votes.", e_title: "The title needs at least 5 characters.", e_desc: "The description needs at least 30 characters.", e_file: "Please choose a video file.", e_too_big: "The file is larger than 2 GB.", e_rights: "Please confirm the rights.", e_need_profile: "Make your profile public first (tab Profile).", e_rate_limit: "Only one submission per week.", e_not_configured: "Upload is not set up yet.", e_youtube: "YouTube rejected the request, please try again later.", e_verify: "YouTube did not confirm the video, please try again.", e_upload: "The upload failed.", e_too_new: "New accounts (under 24 hours) cannot vote yet.", e_own: "You cannot vote for your own video.", e_generic: "That did not work.", mod: "To do: check the video and set it public in YouTube Studio (threshold reached) · open pitches", studio: "Open in YouTube Studio", reject: "Reject (delete video)", reason: "Reason (visible to the author)", poll: "Sync status now" });
  var LANGS = [["en", "English"], ["de", "Deutsch"], ["fr", "Français"], ["es", "Español"], ["it", "Italiano"], ["nl", "Nederlands"], ["pt", "Português"], ["pl", "Polski"], ["id", "Bahasa Indonesia"], ["ru", "Русский"], ["uk", "Українська"], ["ar", "العربية"], ["he", "עברית"], ["hi", "हिन्दी"], ["ja", "日本語"], ["ko", "한국어"], ["ml", "മലയാളം"], ["pa", "ਪੰਜਾਬੀ"], ["ta", "தமிழ்"], ["te", "తెలుగు"]];
  var msg = h("p", { role: "status", class: "mut" }), box = h("div"), mineBox = h("div"), pitchBox = h("div"), modBox = h("div"), TH = 25;
  function say(t) { msg.textContent = t || ""; }
  function pfx(l) { return l && l !== "en" ? "/" + l : ""; }
  // Resumable Upload: ein PUT mit Fortschrittsanzeige (XMLHttpRequest), Antwort enthält die YouTube-Video-ID
  function put(url, file, onp) {
    return new Promise(function (ok, bad) {
      var x = new XMLHttpRequest(); x.open("PUT", url);
      x.upload.onprogress = function (e) { if (e.lengthComputable) onp(Math.round(e.loaded / e.total * 100)); };
      x.onload = function () { if (x.status >= 200 && x.status < 300) { try { ok(JSON.parse(x.responseText)); } catch (e) { bad(); } } else bad(); };
      x.onerror = bad; x.send(file);
    });
  }
  function form() {
    var f = h("form", { class: "ed-form" }), ti = U.inp("", 100), de_ = h("textarea", { maxlength: 4000, rows: 5 }), lg = U.sel(LANGS, X.lang || "en"), tp = U.topicsUI([], 10), fi = h("input", { type: "file", accept: "video/*" });
    var rt = h("input", { type: "checkbox" }), ai = h("input", { type: "checkbox" });
    f.appendChild(U.lab(Q.title, ti)); f.appendChild(U.lab(Q.desc, de_)); f.appendChild(U.lab(Q.lang, lg)); f.appendChild(h("div", {}, [h("b", { text: Q.topics }), tp])); f.appendChild(U.lab(Q.file, fi));
    f.appendChild(h("p", {}, [h("label", {}, [rt, " " + Q.rights])])); f.appendChild(h("p", {}, [h("label", {}, [ai, " " + Q.ai])]));
    var go = h("button", { type: "button", class: "btn main", text: Q.send, onclick: function () {
      var file = fi.files[0]; if (!file) return say(Q.e_file);
      go.disabled = true; say(Q.preparing);
      api("/api/video/init", { method: "POST", body: { title: ti.value, description: de_.value, lang: lg.value, topics: tp.get(), rights: rt.checked, ai: ai.checked, size: file.size, type: file.type || "video/mp4" } }).then(function (r) {
        var j = r.j || {}; if (!j.ok) { go.disabled = false; return say(Q["e_" + j.error] || Q.e_generic); }
        return put(j.upload_url, file, function (p) { say(Q.uploading.replace("{p}", p)); }).then(function (yt) {
          say(Q.finishing); return api("/api/video/confirm", { method: "POST", body: { id: j.id, video_id: yt.id } });
        }).then(function (r2) { go.disabled = false; var k = r2.j || {}; if (k.ok) { say(Q.done); box.textContent = ""; load(); } else say(Q["e_" + k.error] || Q.e_generic); },
          function () { go.disabled = false; say(Q.e_upload); });
      });
    } });
    f.appendChild(h("p", {}, [go, " ", h("button", { type: "button", class: "btn", text: Q.cancel, onclick: function () { box.textContent = ""; } })])); f.addEventListener("submit", function (e) { e.preventDefault(); }); return f;
  }
  function voteBtn(p) {
    var b = h("button", { type: "button", class: "btn", "aria-pressed": p.voted ? "true" : "false", onclick: function () { say(""); api("/api/video/vote", { method: "POST", body: { id: p.id } }).then(function (r) { var j = r.j || {}; if (j.ok) { p.voted = j.voted; p.votes = j.votes; b.setAttribute("aria-pressed", j.voted ? "true" : "false"); b.textContent = "▲ " + j.votes + " / " + TH; } else say(Q["e_" + j.error] || Q.e_generic); }); } });
    b.textContent = "▲ " + p.votes + " / " + TH; return b;
  }
  function load() {
    api("/api/video/mine").then(function (r) {
      mineBox.textContent = ""; var d = r.j || {}; if (!d.items) return; mineBox.appendChild(h("h3", { text: Q.mine }));
      if (!d.items.length) mineBox.appendChild(h("p", { class: "mut", text: Q.none }));
      d.items.forEach(function (p) {
        var li = h("p", {}, [h("b", { text: p.title }), h("span", { class: "mut", text: " · " + (Q["st_" + p.status] || p.status) + " · " + p.votes + " " + Q.votes })]);
        if (p.note) li.appendChild(h("span", { class: "mut", text: " · " + p.note }));
        if (p.status === "published") li.appendChild(h("a", { class: "btn", href: X.base + pfx(p.lang) + "/community/video/" + p.slug + "/", text: Q.published, style: "margin-inline-start:.5em" }));
        else li.appendChild(h("button", { type: "button", class: "btn", text: Q.del_, style: "margin-inline-start:.5em", onclick: function () { if (confirm(Q.confirmdel)) api("/api/video/delete", { method: "POST", body: { id: p.id } }).then(load); } }));
        mineBox.appendChild(li);
      });
    });
    api("/api/video/list").then(function (r) {
      pitchBox.textContent = ""; var d = r.j || {}; TH = d.threshold || 25; var it = (d.items || []).filter(function (p) { return p.status !== "published"; });
      pitchBox.appendChild(h("h3", { text: Q.pitches })); if (!it.length) pitchBox.appendChild(h("p", { class: "mut", text: Q.none }));
      it.forEach(function (p) { pitchBox.appendChild(h("div", { style: "padding:.5em 0;border-bottom:1px solid var(--bd)" }, [h("b", { text: p.title }), h("span", { class: "mut", text: " · " + p.name + " · " + p.lang + (p.status === "review" ? " · " + Q.st_review : "") }), h("p", { text: p.description }), voteBtn(p)])); });
    });
  }
  function moderation() {
    function draw() {
      api("/api/admin/video").then(function (r) {
        modBox.textContent = ""; modBox.appendChild(h("h3", { text: Q.mod })); var it = (r.j && r.j.items) || [];
        modBox.appendChild(h("p", {}, [h("button", { type: "button", class: "btn", text: Q.poll, onclick: function () { api("/api/admin/video/poll", { method: "POST" }).then(draw); } })]));
        if (!it.length) modBox.appendChild(h("p", { class: "mut", text: Q.none }));
        it.forEach(function (p) {
          var rs = h("input", { type: "text", maxlength: 300, placeholder: Q.reason, "aria-label": Q.reason });
          modBox.appendChild(h("div", { style: "padding:.5em 0;border-bottom:1px solid var(--bd)" }, [h("b", { text: p.title }), h("span", { class: "mut", text: " · " + p.name + " · " + p.lang + " · " + p.votes + " " + Q.votes + (p.status === "review" ? " ✔ 🎬" : "") + (p.ai ? " · AI" : "") }), h("p", { text: p.description }),
            p.youtube ? h("a", { class: "btn main", href: p.youtube, target: "_blank", rel: "noopener", text: Q.studio }) : null, " ", rs, " ", h("button", { type: "button", class: "btn", text: Q.reject, onclick: function () { api("/api/admin/video/reject", { method: "POST", body: { id: p.id, note: rs.value } }).then(draw); } })]));
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
