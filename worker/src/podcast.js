// Community-Podcast: Mitglieder reichen Episoden ein (Audio -> Entwurf bei Spreaker), die Community stimmt ab,
// ab der Schwelle prueft Mirko in Spreaker und veroeffentlicht dort; der Cron erkennt die Veroeffentlichung.
import { cleanText, rateLimit, isLang } from "./util.js";
import { baseIds } from "./entities.js";
import { sendPush } from "./push.js";
import { award } from "./badges.js";

const SHOWS = { en: 6704921, de: 7393187, es: 7393248, fr: 7393223, it: 7393231, pt: 7393243, nl: 7393222, pl: 7393242, id: 7393230, ru: 7393247, uk: 7393254, ar: 7393221, he: 7393227, hi: 7393228, ja: 7393232, ko: 7393236, ml: 7393238, pa: 7393244, ta: 7393250, te: 7393253 };
const THRESHOLD = 25, MAX_BYTES = 50 * 1024 * 1024, MIN_AGE = 86400, EXPIRE_DAYS = 30, API = "https://api.spreaker.com/v2";
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const long = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();
const parse = (s, d) => { try { return JSON.parse(s); } catch { return d; } };
const slugify = (t) => t.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50);
export const podSlug = (r) => `${r.id}-${slugify(r.title) || "episode"}`;
const sp = (env, path, init = {}) => fetch((env.SPREAKER_API || API) + path, { ...init, headers: { authorization: `Bearer ${env.SPREAKER_TOKEN}`, ...(init.headers || {}) } });
const PUB = "id,title,description,lang,topics,status,created,published,ep_url,note,ai";

async function notifyAdmins(env, ep) {
  const db = env.DB, adm = (env.ADMIN_SUBS || "").split(",").map((s) => s.trim());
  const users = (await db.prepare("SELECT id,provider,sub,role FROM users").all()).results || [];
  const ids = users.filter((u) => adm.includes(`${u.provider}:${u.sub}`) || u.role === "editor").map((u) => u.id);
  if (!ids.length || !env.VAPID_PRIVATE_JWK) return;
  const subs = (await db.prepare(`SELECT endpoint,p256dh,auth FROM push_subs WHERE user_id IN (${ids.map(() => "?").join(",")})`).bind(...ids).all()).results || [];
  for (const s of subs) { try { const r = await sendPush(env, s, { title: "Podcast-Pitch bereit zur Prüfung", body: ep.title, url: `${env.SITE}/community/` }); if (r.gone) await db.prepare("DELETE FROM push_subs WHERE endpoint=?").bind(s.endpoint).run(); } catch {} }
}

async function dropDraft(env, ep) { if (ep.spreaker_id && env.SPREAKER_TOKEN) await sp(env, `/episodes/${ep.spreaker_id}`, { method: "DELETE" }).catch(() => 0); }

// Cron: veroeffentlichte Episoden erkennen, Abgelaufene loeschen
export async function pollPodcast(env) {
  const db = env.DB, t = now();
  if (!env.SPREAKER_TOKEN) return { skip: true };
  const rows = (await db.prepare("SELECT * FROM pod_episodes WHERE status IN ('submitted','review') AND spreaker_id>0 ORDER BY updated LIMIT 20").all()).results || [];
  let pub = 0;
  for (const ep of rows) {
    const r = await sp(env, `/episodes/${ep.spreaker_id}`).catch(() => null); if (!r) continue;
    if (r.status === 404) { await db.prepare("UPDATE pod_episodes SET status='rejected',note=?,updated=? WHERE id=?").bind("Entwurf in Spreaker nicht mehr vorhanden", t, ep.id).run(); continue; }
    if (!r.ok) continue;
    const e = (await r.json().catch(() => ({}))).response?.episode;
    if (e && e.published_at && e.visibility === "PUBLIC" && e.type !== "DRAFT") {
      const url = e.site_url || `https://www.spreaker.com/episode/${ep.spreaker_id}`;
      await db.prepare("UPDATE pod_episodes SET status='published',published=?,ep_url=?,updated=? WHERE id=?").bind(t, url, t, ep.id).run(); pub++; await award(db, ep.user_id, "podcaster").catch(() => 0);
      const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(ep.user_id).first();
      if (pr?.handle) {   // Creator-Feed
        const curl = `${env.SITE}/community/u/${pr.handle}/podcast/`;
        await db.prepare("INSERT OR IGNORE INTO channels(owner_type,owner_id,kind,url,feed) VALUES('u',?,'podcast',?,'')").bind(ep.user_id, curl).run();
        const ch = await db.prepare("SELECT id FROM channels WHERE owner_type='u' AND owner_id=? AND url=?").bind(ep.user_id, curl).first();
        if (ch) await db.prepare("INSERT OR IGNORE INTO feed_items(channel_id,owner_type,owner_id,url,title,published) VALUES(?,?,?,?,?,?)").bind(ch.id, "u", ep.user_id, `${env.SITE}${ep.lang === "en" ? "" : "/" + ep.lang}/community/podcast/${podSlug(ep)}/`, ep.title, t).run();
      }
    }
  }
  const old = (await db.prepare("SELECT * FROM pod_episodes WHERE status='submitted' AND created<?").bind(t - EXPIRE_DAYS * 86400).all()).results || [];
  for (const ep of old) { await dropDraft(env, ep); await db.prepare("UPDATE pod_episodes SET status='expired',updated=? WHERE id=?").bind(t, ep.id).run(); }
  return { published: pub, expired: old.length };
}

export async function deleteUserPodcast(db, uid) {
  await db.batch([db.prepare("DELETE FROM pod_votes WHERE user_id=? OR ep_id IN (SELECT id FROM pod_episodes WHERE user_id=?)").bind(uid, uid), db.prepare("DELETE FROM pod_episodes WHERE user_id=?").bind(uid)]);
}

export async function handlePodcast(env, request, url, path, user, J) {
  const db = env.DB, method = request.method;

  if (path === "/api/podcast/list" && method === "GET") {   // oeffentlich: Pitches zum Abstimmen + veroeffentlichte Episoden
    const rows = (await db.prepare(
      `SELECT e.id,e.title,e.description,e.lang,e.topics,e.status,e.created,e.published,e.ep_url,p.handle,u.name,(SELECT COUNT(*) FROM pod_votes v WHERE v.ep_id=e.id) votes
       FROM pod_episodes e JOIN profiles p ON p.user_id=e.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=e.user_id AND u.banned=0
       WHERE e.status IN ('submitted','review','published') ORDER BY (e.status='published') DESC, e.created DESC LIMIT 300`).all()).results || [];
    const mine = user ? ((await db.prepare("SELECT ep_id FROM pod_votes WHERE user_id=?").bind(user.id).all()).results || []).map((x) => x.ep_id) : [];
    return J({ threshold: THRESHOLD, items: rows.map((r) => ({ ...r, topics: parse(r.topics, []), slug: podSlug(r), voted: mine.includes(r.id) })) }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/podcast/export" && method === "GET") {   // fuer den Seitenbau: nur veroeffentlichte
    const rows = (await db.prepare(
      `SELECT e.id,e.title,e.description,e.lang,e.topics,e.created,e.published,e.ep_url,e.spreaker_id,e.ai,p.handle,u.name
       FROM pod_episodes e JOIN profiles p ON p.user_id=e.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=e.user_id AND u.banned=0
       WHERE e.status='published' ORDER BY e.published DESC LIMIT 1000`).all()).results || [];
    return J({ items: rows.map((r) => ({ ...r, topics: parse(r.topics, []), slug: podSlug(r) })) }, 200, { "cache-control": "public, max-age=300" });
  }

  if (path.startsWith("/api/admin/podcast")) {
    if (!user || !(user.admin || user.editor)) return J({ error: "forbidden" }, 403);
    if (path === "/api/admin/podcast" && method === "GET") {
      const rows = (await db.prepare("SELECT e.id,e.title,e.description,e.lang,e.status,e.spreaker_id,e.ai,e.created,u.name,(SELECT COUNT(*) FROM pod_votes v WHERE v.ep_id=e.id) votes FROM pod_episodes e JOIN users u ON u.id=e.user_id WHERE e.status IN ('review','submitted') ORDER BY (e.status='review') DESC, e.created").all()).results || [];
      return J({ items: rows.map((r) => ({ ...r, spreaker: r.spreaker_id ? `https://www.spreaker.com/episode/${r.spreaker_id}` : "" })), threshold: THRESHOLD });
    }
    if (path === "/api/admin/podcast/reject" && method === "POST") {
      const b = await request.json().catch(() => ({})), ep = await db.prepare("SELECT * FROM pod_episodes WHERE id=?").bind(+b.id).first(); if (!ep) return J({ error: "not_found" }, 404);
      await dropDraft(env, ep);
      await db.prepare("UPDATE pod_episodes SET status='rejected',note=?,updated=? WHERE id=?").bind(txt(b.note || "", 300), now(), ep.id).run();
      return J({ ok: true });
    }
    if (path === "/api/admin/podcast/poll" && method === "POST") return J(await pollPodcast(env));
    return null;
  }

  if (!user) return J({ error: "login" }, 401);

  if (path === "/api/podcast/mine" && method === "GET") {
    const rows = (await db.prepare(`SELECT ${PUB},(SELECT COUNT(*) FROM pod_votes v WHERE v.ep_id=pod_episodes.id) votes FROM pod_episodes WHERE user_id=? ORDER BY created DESC LIMIT 50`).bind(user.id).all()).results || [];
    return J({ items: rows.map((r) => ({ ...r, topics: parse(r.topics, []), slug: podSlug(r) })), threshold: THRESHOLD, configured: !!env.SPREAKER_TOKEN });
  }

  if (path === "/api/podcast/submit" && method === "POST") {
    if (!env.SPREAKER_TOKEN) return J({ error: "not_configured" }, 503);
    const pr = await db.prepare("SELECT handle,public FROM profiles WHERE user_id=?").bind(user.id).first();
    if (!(pr?.public && pr.handle)) return J({ error: "need_profile" }, 400);
    if (!user.admin && !(await rateLimit(db, `pod:${user.id}`, 1, 7 * 86400))) return J({ error: "rate_limit" }, 429);
    let fd; try { fd = await request.formData(); } catch { return J({ error: "bad_request" }, 400); }
    const title = txt(fd.get("title") || "", 140), desc = long(fd.get("description") || "", 2000), lang = String(fd.get("lang") || "en"), file = fd.get("file");
    if (title.length < 5) return J({ error: "title" }, 400);
    if (desc.length < 30) return J({ error: "desc" }, 400);
    if (lang !== "en" && !isLang(lang)) return J({ error: "bad_lang" }, 400);
    if (fd.get("rights") !== "1") return J({ error: "rights" }, 400);
    if (!file || typeof file === "string" || !file.size) return J({ error: "file" }, 400);
    if (file.size > MAX_BYTES) return J({ error: "too_big" }, 413);
    const head = new Uint8Array(await file.slice(0, 3).arrayBuffer());
    if (!((head[0] === 0x49 && head[1] === 0x44 && head[2] === 0x33) || (head[0] === 0xff && (head[1] & 0xe0) === 0xe0))) return J({ error: "not_mp3" }, 400);
    let topics = []; try { topics = JSON.parse(String(fd.get("topics") || "[]")); } catch {}
    const known = await baseIds(env), tp = [];
    for (const x of (Array.isArray(topics) ? topics : []).slice(0, 10)) { if (!known.has(x)) return J({ error: "bad_topic", topic: x }, 400); if (!tp.includes(x)) tp.push(x); }
    const show = SHOWS[lang], ai = fd.get("ai") === "1" ? 1 : 0;
    const credit = `\n\nCommunity episode by ${user.name} – ${env.SITE}/community/u/${pr.handle}/${ai ? "\nAI use disclosed by the author." : ""}`;
    const f1 = new FormData(); f1.set("title", title); f1.set("show_id", String(show)); f1.set("description", desc + credit);
    const r1 = await sp(env, "/episodes/drafts", { method: "POST", body: f1 }); if (!r1.ok) return J({ error: "spreaker", status: r1.status }, 502);
    const sid = (await r1.json().catch(() => ({}))).response?.episode?.episode_id; if (!sid) return J({ error: "spreaker" }, 502);
    const f2 = new FormData(); f2.set("media_file", file, "episode.mp3");
    const r2 = await sp(env, `/episodes/${sid}`, { method: "POST", body: f2 });
    if (!r2.ok) { await sp(env, `/episodes/${sid}`, { method: "DELETE" }).catch(() => 0); return J({ error: "spreaker_upload", status: r2.status }, 502); }
    const t = now(), r = await db.prepare("INSERT INTO pod_episodes(user_id,title,description,lang,topics,status,spreaker_id,show_id,ai,created,updated) VALUES(?,?,?,?,?,'submitted',?,?,?,?,?)").bind(user.id, title, desc, lang, JSON.stringify(tp), sid, show, ai, t, t).run();
    return J({ ok: true, id: r.meta.last_row_id });
  }

  if (path === "/api/podcast/delete" && method === "POST") {
    const b = await request.json().catch(() => ({})), ep = await db.prepare("SELECT * FROM pod_episodes WHERE id=? AND (user_id=? OR ?=1)").bind(+b.id, user.id, user.admin ? 1 : 0).first(); if (!ep) return J({ error: "not_found" }, 404);
    if (ep.status === "published" && !user.admin) return J({ error: "published" }, 400);
    if (ep.status !== "published") await dropDraft(env, ep);
    await db.batch([db.prepare("DELETE FROM pod_votes WHERE ep_id=?").bind(ep.id), db.prepare("DELETE FROM pod_episodes WHERE id=?").bind(ep.id), db.prepare("DELETE FROM comments WHERE vid=?").bind("podcast" + ep.id)]);
    return J({ ok: true });
  }

  if (path === "/api/podcast/vote" && method === "POST") {
    if (!(await rateLimit(db, `podv:${user.id}`, 60, 3600))) return J({ error: "rate_limit" }, 429);
    if ((user.created || 0) > now() - MIN_AGE && !user.admin) return J({ error: "too_new" }, 400);
    const b = await request.json().catch(() => ({})), ep = await db.prepare("SELECT * FROM pod_episodes WHERE id=? AND status IN ('submitted','review')").bind(+b.id).first(); if (!ep) return J({ error: "not_found" }, 404);
    if (ep.user_id === user.id) return J({ error: "own" }, 400);
    const has = await db.prepare("SELECT 1 x FROM pod_votes WHERE ep_id=? AND user_id=?").bind(ep.id, user.id).first();
    if (has) await db.prepare("DELETE FROM pod_votes WHERE ep_id=? AND user_id=?").bind(ep.id, user.id).run();
    else await db.prepare("INSERT INTO pod_votes(ep_id,user_id,created) VALUES(?,?,?)").bind(ep.id, user.id, now()).run();
    const n = (await db.prepare("SELECT COUNT(*) n FROM pod_votes WHERE ep_id=?").bind(ep.id).first()).n;
    if (n >= THRESHOLD && ep.status === "submitted") { await db.prepare("UPDATE pod_episodes SET status='review',updated=? WHERE id=?").bind(now(), ep.id).run(); await notifyAdmins(env, ep).catch(() => 0); }
    return J({ ok: true, votes: n, voted: !has });
  }
  return null;
}
