// Creator-Videos fuer den YouTube-Kanal "m365 Show": Der Worker legt eine resumable Upload-Session an (privat), der Browser
// laedt direkt zu YouTube hoch. Abstimmung -> ab Schwelle Aufgabe fuer Mirko -> Freigabe (oeffentlich schalten) in YouTube Studio.
import { guestsOf, dropGuests } from "./credits.js";
import { cleanText, rateLimit, isLang } from "./util.js";
import { baseIds } from "./entities.js";
import { sendPush } from "./push.js";
import { award } from "./badges.js";

const THRESHOLD = 25, MIN_AGE = 86400, EXPIRE_DAYS = 30, MAX_BYTES = 2 * 1024 * 1024 * 1024;
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const long = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();
const parse = (s, d) => { try { return JSON.parse(s); } catch { return d; } };
const slugify = (t) => t.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50);
export const vidSlug = (r) => `${r.id}-${slugify(r.title) || "video"}`;
const api = (env) => env.YT_API || "https://www.googleapis.com";
const YTID = /^[A-Za-z0-9_-]{11}$/;
const PUB = "id,title,description,lang,topics,status,created,published,video_id,note,ai";

export async function token(env) {
  if (!env.YT_CLIENT_ID || !env.YT_CLIENT_SECRET || !env.YT_REFRESH_TOKEN) return null;
  const r = await fetch(env.YT_TOKEN_URL || "https://oauth2.googleapis.com/token", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: env.YT_CLIENT_ID, client_secret: env.YT_CLIENT_SECRET, refresh_token: env.YT_REFRESH_TOKEN, grant_type: "refresh_token" }) });
  if (!r.ok) return null;
  return (await r.json().catch(() => ({}))).access_token || null;
}

async function notifyAdmins(env, v) {
  const db = env.DB, adm = (env.ADMIN_SUBS || "").split(",").map((s) => s.trim());
  const users = (await db.prepare("SELECT id,provider,sub,role FROM users").all()).results || [];
  const ids = users.filter((u) => adm.includes(`${u.provider}:${u.sub}`) || u.role === "editor").map((u) => u.id);
  if (!ids.length || !env.VAPID_PRIVATE_JWK) return;
  const subs = (await db.prepare(`SELECT endpoint,p256dh,auth FROM push_subs WHERE user_id IN (${ids.map(() => "?").join(",")})`).bind(...ids).all()).results || [];
  for (const s of subs) { try { const r = await sendPush(env, s, { title: "Creator-Video: 25 Stimmen erreicht", body: "Video prüfen und in YouTube Studio freigeben: " + v.title, url: `${env.SITE}/community/` }); if (r.gone) await db.prepare("DELETE FROM push_subs WHERE endpoint=?").bind(s.endpoint).run(); } catch {} }
}

async function dropVideo(env, v) {
  if (!v.video_id) return;
  const t = await token(env); if (!t) return;
  await fetch(`${api(env)}/youtube/v3/videos?id=${encodeURIComponent(v.video_id)}`, { method: "DELETE", headers: { authorization: `Bearer ${t}` } }).catch(() => 0);
}

// Cron: veroeffentlichte Videos erkennen, Abgelaufene/Haengende aufraeumen
export async function pollVideos(env) {
  const db = env.DB, t = now(), at = await token(env);
  if (!at) return { skip: true };
  const rows = (await db.prepare("SELECT * FROM yt_videos WHERE status IN ('submitted','review') AND video_id<>'' ORDER BY updated LIMIT 50").all()).results || [];
  let pub = 0;
  if (rows.length) {
    const r = await fetch(`${api(env)}/youtube/v3/videos?part=status&id=${rows.map((x) => x.video_id).join(",")}`, { headers: { authorization: `Bearer ${at}` } }).catch(() => null);
    if (r && r.ok) {
      const st = new Map(((await r.json().catch(() => ({}))).items || []).map((i) => [i.id, i.status?.privacyStatus]));
      for (const v of rows) {
        if (!st.has(v.video_id)) { await db.prepare("UPDATE yt_videos SET status='rejected',note=?,updated=? WHERE id=?").bind("Video auf YouTube nicht mehr vorhanden", t, v.id).run(); continue; }
        if (st.get(v.video_id) === "public") {
          await db.prepare("UPDATE yt_videos SET status='published',published=?,updated=? WHERE id=?").bind(t, t, v.id).run(); pub++;
          await award(db, v.user_id, "videomaker").catch(() => 0);
          const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(v.user_id).first();
          if (pr?.handle) {   // Creator-Feed
            const curl = `${env.SITE}/community/u/${pr.handle}/videos/`;
            await db.prepare("INSERT OR IGNORE INTO channels(owner_type,owner_id,kind,url,feed) VALUES('u',?,'youtube',?,'')").bind(v.user_id, curl).run();
            const ch = await db.prepare("SELECT id FROM channels WHERE owner_type='u' AND owner_id=? AND url=?").bind(v.user_id, curl).first();
            if (ch) await db.prepare("INSERT OR IGNORE INTO feed_items(channel_id,owner_type,owner_id,url,title,published) VALUES(?,?,?,?,?,?)").bind(ch.id, "u", v.user_id, `${env.SITE}${v.lang === "en" ? "" : "/" + v.lang}/community/video/${vidSlug(v)}/`, v.title, t).run();
          }
        }
      }
    }
  }
  const old = (await db.prepare("SELECT * FROM yt_videos WHERE status='submitted' AND created<?").bind(t - EXPIRE_DAYS * 86400).all()).results || [];
  for (const v of old) { await dropVideo(env, v); await db.prepare("UPDATE yt_videos SET status='expired',updated=? WHERE id=?").bind(t, v.id).run(); }
  await db.prepare("DELETE FROM yt_videos WHERE status='uploading' AND created<?").bind(t - 2 * 86400).run();   // abgebrochene Uploads
  return { published: pub, expired: old.length };
}

export async function deleteUserVideos(db, uid) {
  await db.batch([db.prepare("DELETE FROM yt_votes WHERE user_id=? OR vid_id IN (SELECT id FROM yt_videos WHERE user_id=?)").bind(uid, uid), db.prepare("DELETE FROM yt_videos WHERE user_id=?").bind(uid)]);
}

export async function handleVideo(env, request, url, path, user, J) {
  const db = env.DB, method = request.method;

  if (path === "/api/video/list" && method === "GET") {
    const rows = (await db.prepare(
      `SELECT v.id,v.title,v.description,v.lang,v.topics,v.status,v.created,v.published,v.video_id,p.handle,u.name,(SELECT COUNT(*) FROM yt_votes x WHERE x.vid_id=v.id) votes
       FROM yt_videos v JOIN profiles p ON p.user_id=v.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=v.user_id AND u.banned=0
       WHERE v.status IN ('submitted','review','published') ORDER BY (v.status='published') DESC, v.created DESC LIMIT 300`).all()).results || [];
    const mine = user ? ((await db.prepare("SELECT vid_id FROM yt_votes WHERE user_id=?").bind(user.id).all()).results || []).map((x) => x.vid_id) : [];
    return J({ threshold: THRESHOLD, items: rows.map((r) => ({ ...r, video_id: r.status === "published" ? r.video_id : "", topics: parse(r.topics, []), slug: vidSlug(r), voted: mine.includes(r.id) })) }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/video/export" && method === "GET") {
    const rows = (await db.prepare(
      `SELECT v.id,v.title,v.description,v.lang,v.topics,v.created,v.published,v.video_id,v.ai,p.handle,u.name
       FROM yt_videos v JOIN profiles p ON p.user_id=v.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=v.user_id AND u.banned=0
       WHERE v.status='published' ORDER BY v.published DESC LIMIT 1000`).all()).results || [];
    const gs = await guestsOf(db, "video", rows.map((r) => r.id));
    return J({ items: rows.map((r) => ({ ...r, topics: parse(r.topics, []), slug: vidSlug(r), guests: gs[r.id] || [] })) }, 200, { "cache-control": "public, max-age=300" });
  }

  if (path.startsWith("/api/admin/video")) {
    if (!user || !(user.admin || user.editor)) return J({ error: "forbidden" }, 403);
    if (path === "/api/admin/video" && method === "GET") {
      const rows = (await db.prepare("SELECT v.id,v.title,v.description,v.lang,v.status,v.video_id,v.ai,v.created,u.name,(SELECT COUNT(*) FROM yt_votes x WHERE x.vid_id=v.id) votes FROM yt_videos v JOIN users u ON u.id=v.user_id WHERE v.status IN ('review','submitted') ORDER BY (v.status='review') DESC, v.created").all()).results || [];
      return J({ items: rows.map((r) => ({ ...r, youtube: r.video_id ? `https://studio.youtube.com/video/${r.video_id}/edit` : "" })), threshold: THRESHOLD });
    }
    if (path === "/api/admin/video/reject" && method === "POST") {
      const b = await request.json().catch(() => ({})), v = await db.prepare("SELECT * FROM yt_videos WHERE id=?").bind(+b.id).first(); if (!v) return J({ error: "not_found" }, 404);
      await dropVideo(env, v);
      await db.prepare("UPDATE yt_videos SET status='rejected',note=?,updated=? WHERE id=?").bind(txt(b.note || "", 300), now(), v.id).run();
      return J({ ok: true });
    }
    if (path === "/api/admin/video/poll" && method === "POST") return J(await pollVideos(env));
    return null;
  }

  if (!user) return J({ error: "login" }, 401);

  if (path === "/api/video/mine" && method === "GET") {
    const rows = (await db.prepare(`SELECT ${PUB},(SELECT COUNT(*) FROM yt_votes x WHERE x.vid_id=yt_videos.id) votes FROM yt_videos WHERE user_id=? AND status<>'uploading' ORDER BY created DESC LIMIT 50`).bind(user.id).all()).results || [];
    const gs = await guestsOf(db, "video", rows.map((r) => r.id), true);
    return J({ items: rows.map((r) => ({ ...r, video_id: r.status === "published" ? r.video_id : "", topics: parse(r.topics, []), slug: vidSlug(r), guests: gs[r.id] || [] })), threshold: THRESHOLD, configured: !!(env.YT_CLIENT_ID && env.YT_CLIENT_SECRET && env.YT_REFRESH_TOKEN) });
  }

  if (path === "/api/video/init" && method === "POST") {   // legt die resumable Upload-Session an; der Browser PUT die Datei direkt zu YouTube
    const at = await token(env); if (!at) return J({ error: "not_configured" }, 503);
    const pr = await db.prepare("SELECT handle,public FROM profiles WHERE user_id=?").bind(user.id).first();
    if (!(pr?.public && pr.handle)) return J({ error: "need_profile" }, 400);
    if (!user.admin && !(await rateLimit(db, `yt:${user.id}`, 1, 7 * 86400))) return J({ error: "rate_limit" }, 429);
    const b = await request.json().catch(() => ({}));
    const title = txt(b.title || "", 100), desc = long(b.description || "", 4000), lang = String(b.lang || "en"), size = +b.size || 0, ctype = String(b.type || "video/mp4");
    if (title.length < 5) return J({ error: "title" }, 400);
    if (desc.length < 30) return J({ error: "desc" }, 400);
    if (lang !== "en" && !isLang(lang)) return J({ error: "bad_lang" }, 400);
    if (b.rights !== true && b.rights !== 1 && b.rights !== "1") return J({ error: "rights" }, 400);
    if (!/^video\/[a-z0-9.+-]+$/i.test(ctype) || size < 1) return J({ error: "file" }, 400);
    if (size > MAX_BYTES) return J({ error: "too_big" }, 413);
    const known = await baseIds(env), tp = [];
    for (const x of (Array.isArray(b.topics) ? b.topics : []).slice(0, 10)) { if (!known.has(x)) return J({ error: "bad_topic", topic: x }, 400); if (!tp.includes(x)) tp.push(x); }
    const ai = b.ai ? 1 : 0;
    const credit = `\n\nCommunity video by ${user.name} – ${env.SITE}/community/u/${pr.handle}/${ai ? "\nAI use disclosed by the author." : ""}`;
    const meta = { snippet: { title, description: desc + credit, categoryId: "28", defaultLanguage: lang }, status: { privacyStatus: "private", selfDeclaredMadeForKids: false } };
    const r = await fetch(`${api(env)}/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status`, { method: "POST",
      headers: { authorization: `Bearer ${at}`, "content-type": "application/json; charset=UTF-8", "x-upload-content-type": ctype, "x-upload-content-length": String(size), origin: new URL(env.SITE).origin }, body: JSON.stringify(meta) });
    const loc = r.headers.get("location"); if (!r.ok || !loc) return J({ error: "youtube", status: r.status }, 502);
    const t = now(), ins = await db.prepare("INSERT INTO yt_videos(user_id,title,description,lang,topics,status,ai,created,updated) VALUES(?,?,?,?,?,'uploading',?,?,?)").bind(user.id, title, desc, lang, JSON.stringify(tp), ai, t, t).run();
    return J({ ok: true, id: ins.meta.last_row_id, upload_url: loc });
  }

  if (path === "/api/video/confirm" && method === "POST") {   // Browser meldet die YouTube-Video-ID nach dem Upload
    const b = await request.json().catch(() => ({})), vid = String(b.video_id || "");
    const v = await db.prepare("SELECT * FROM yt_videos WHERE id=? AND user_id=? AND status='uploading'").bind(+b.id, user.id).first(); if (!v) return J({ error: "not_found" }, 404);
    if (!YTID.test(vid)) return J({ error: "bad_video" }, 400);
    if (await db.prepare("SELECT 1 x FROM yt_videos WHERE video_id=?").bind(vid).first()) return J({ error: "duplicate" }, 400);
    const at = await token(env); if (!at) return J({ error: "not_configured" }, 503);
    const r = await fetch(`${api(env)}/youtube/v3/videos?part=status&id=${vid}`, { headers: { authorization: `Bearer ${at}` } });   // nur Videos des eigenen Kanals sind mit diesem Token sichtbar, wenn privat
    const it = r.ok ? ((await r.json().catch(() => ({}))).items || [])[0] : null;
    if (!it || it.status?.privacyStatus !== "private") return J({ error: "verify" }, 400);
    await db.prepare("UPDATE yt_videos SET status='submitted',video_id=?,updated=? WHERE id=?").bind(vid, now(), v.id).run();
    return J({ ok: true, id: v.id });
  }

  if (path === "/api/video/delete" && method === "POST") {
    const b = await request.json().catch(() => ({})), v = await db.prepare("SELECT * FROM yt_videos WHERE id=? AND (user_id=? OR ?=1)").bind(+b.id, user.id, user.admin ? 1 : 0).first(); if (!v) return J({ error: "not_found" }, 404);
    if (v.status === "published" && !user.admin) return J({ error: "published" }, 400);
    if (v.status !== "published") await dropVideo(env, v);
    await db.batch([db.prepare("DELETE FROM yt_votes WHERE vid_id=?").bind(v.id), db.prepare("DELETE FROM yt_videos WHERE id=?").bind(v.id), db.prepare("DELETE FROM comments WHERE vid=?").bind("video" + v.id), db.prepare("DELETE FROM item_guests WHERE kind='video' AND item_id=?").bind(v.id)]);
    return J({ ok: true });
  }

  if (path === "/api/video/vote" && method === "POST") {
    if (!(await rateLimit(db, `ytv:${user.id}`, 60, 3600))) return J({ error: "rate_limit" }, 429);
    if ((user.created || 0) > now() - MIN_AGE && !user.admin) return J({ error: "too_new" }, 400);
    const b = await request.json().catch(() => ({})), v = await db.prepare("SELECT * FROM yt_videos WHERE id=? AND status IN ('submitted','review')").bind(+b.id).first(); if (!v) return J({ error: "not_found" }, 404);
    if (v.user_id === user.id) return J({ error: "own" }, 400);
    const has = await db.prepare("SELECT 1 x FROM yt_votes WHERE vid_id=? AND user_id=?").bind(v.id, user.id).first();
    if (has) await db.prepare("DELETE FROM yt_votes WHERE vid_id=? AND user_id=?").bind(v.id, user.id).run();
    else await db.prepare("INSERT INTO yt_votes(vid_id,user_id,created) VALUES(?,?,?)").bind(v.id, user.id, now()).run();
    const n = (await db.prepare("SELECT COUNT(*) n FROM yt_votes WHERE vid_id=?").bind(v.id).first()).n;
    if (n >= THRESHOLD && v.status === "submitted") { await db.prepare("UPDATE yt_videos SET status='review',updated=? WHERE id=?").bind(now(), v.id).run(); await notifyAdmins(env, v).catch(() => 0); }
    return J({ ok: true, votes: n, voted: !has });
  }
  return null;
}
