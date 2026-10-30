// Gaeste-Boerse: Podcaster, YouTuber und Veranstalter finden Gaeste/Speaker und umgekehrt - Zuordnung ueber Entitaeten (Themen), Sprache und Format
import { cleanText, rateLimit, isLang } from "./util.js";
import { baseIds } from "./entities.js";
import { cleanUrl } from "./profiles.js";

const FORMATS = ["podcast", "youtube", "event", "webinar", "article"], MAX_LIST = 5;
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const parse = (s, d) => { try { return JSON.parse(s); } catch { return d; } };
const fix = (r) => ({ ...r, formats: parse(r.formats, []), langs: parse(r.langs, []), topics: parse(r.topics, []) });
const COLS = "g.id,g.user_id,g.kind,g.title,g.formats,g.langs,g.topics,g.note,g.link,g.updated,p.handle,u.name";
const JOIN = "FROM guest_listings g JOIN profiles p ON p.user_id=g.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=g.user_id AND u.banned=0";

export function score(a, b) {
  const t = a.topics.filter((x) => b.topics.includes(x)).length, l = a.langs.filter((x) => b.langs.includes(x)).length, f = a.formats.filter((x) => b.formats.includes(x)).length;
  return t ? t * 3 + l * 2 + f : 0;   // ohne gemeinsames Thema kein Treffer
}

export async function deleteUserGuests(db, uid) { await db.prepare("DELETE FROM guest_listings WHERE user_id=?").bind(uid).run(); }

export async function handleGuests(env, request, url, path, user, J) {
  const db = env.DB, method = request.method;
  const pub = (r) => { const { user_id, ...x } = fix(r); return x; };

  if ((path === "/api/guests/list" || path === "/api/guests/export") && method === "GET") {
    const kind = url.searchParams.get("kind"), topic = url.searchParams.get("topic");
    const rows = ((await db.prepare(`SELECT ${COLS} ${JOIN} WHERE g.active=1 ${kind === "speaker" || kind === "host" ? "AND g.kind=?" : ""} ORDER BY g.updated DESC LIMIT 500`).bind(...(kind === "speaker" || kind === "host" ? [kind] : [])).all()).results || []).map(pub);
    return J({ items: topic ? rows.filter((r) => r.topics.includes(topic)) : rows }, 200, { "cache-control": path.endsWith("export") ? "public, max-age=300" : "no-store" });
  }
  if (!user) return J({ error: "login" }, 401);

  if (path === "/api/guests/mine" && method === "GET") {
    const own = ((await db.prepare("SELECT * FROM guest_listings WHERE user_id=? ORDER BY updated DESC").bind(user.id).all()).results || []).map(fix);
    const others = ((await db.prepare(`SELECT ${COLS} ${JOIN} WHERE g.active=1 AND g.user_id<>? LIMIT 1000`).bind(user.id).all()).results || []).map(fix);
    const matches = [];
    for (const o of own.filter((x) => x.active)) for (const b of others) if (b.kind !== o.kind) { const s = score(o, b); if (s) matches.push({ mine: o.id, score: s, shared: o.topics.filter((x) => b.topics.includes(x)), ...(({ user_id, ...x }) => x)(b) }); }
    matches.sort((a, b) => b.score - a.score);
    return J({ items: own, matches: matches.slice(0, 40) });
  }

  if (path === "/api/guests/save" && method === "POST") {
    if (!(await rateLimit(db, `gl:${user.id}`, 30, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await request.json().catch(() => ({})), kind = b.kind === "host" ? "host" : b.kind === "speaker" ? "speaker" : null; if (!kind) return J({ error: "bad_kind" }, 400);
    const pr = await db.prepare("SELECT handle,public FROM profiles WHERE user_id=?").bind(user.id).first(); if (!(pr?.public && pr.handle)) return J({ error: "need_profile" }, 400);
    const formats = (Array.isArray(b.formats) ? b.formats : []).filter((x, i, a) => FORMATS.includes(x) && a.indexOf(x) === i);
    const langs = (Array.isArray(b.langs) ? b.langs : []).filter((x, i, a) => (x === "en" || isLang(x)) && a.indexOf(x) === i).slice(0, 8);
    if (!formats.length) return J({ error: "formats" }, 400); if (!langs.length) return J({ error: "langs" }, 400);
    const known = await baseIds(env), topics = [];
    for (const x of (Array.isArray(b.topics) ? b.topics : []).slice(0, 10)) { if (!known.has(x)) return J({ error: "bad_topic", topic: x }, 400); if (!topics.includes(x)) topics.push(x); }
    if (!topics.length) return J({ error: "topics" }, 400);
    const link = kind === "host" ? cleanUrl(b.link || "") : ""; if (link === null) return J({ error: "bad_link" }, 400);
    const title = txt(b.title || "", 120), note = txt(b.note || "", 500); if (kind === "host" && title.length < 3) return J({ error: "title" }, 400);
    const t = now(), active = b.active === false ? 0 : 1;
    if (b.id) {
      const cur = await db.prepare("SELECT id,kind FROM guest_listings WHERE id=? AND user_id=?").bind(+b.id, user.id).first(); if (!cur) return J({ error: "not_found" }, 404);
      await db.prepare("UPDATE guest_listings SET title=?,formats=?,langs=?,topics=?,note=?,link=?,active=?,updated=? WHERE id=?").bind(title, JSON.stringify(formats), JSON.stringify(langs), JSON.stringify(topics), note, link || "", active, t, cur.id).run();
      return J({ ok: true, id: cur.id });
    }
    const n = (await db.prepare("SELECT COUNT(*) n FROM guest_listings WHERE user_id=? AND kind=?").bind(user.id, kind).first()).n;
    if (n >= (kind === "speaker" ? 1 : MAX_LIST)) return J({ error: "limit" }, 400);
    const r = await db.prepare("INSERT INTO guest_listings(user_id,kind,title,formats,langs,topics,note,link,active,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?)").bind(user.id, kind, title, JSON.stringify(formats), JSON.stringify(langs), JSON.stringify(topics), note, link || "", active, t, t).run();
    return J({ ok: true, id: r.meta.last_row_id });
  }
  if (path === "/api/guests/delete" && method === "POST") {
    const b = await request.json().catch(() => ({}));
    await db.prepare("DELETE FROM guest_listings WHERE id=? AND (user_id=? OR ?=1)").bind(+b.id, user.id, user.admin ? 1 : 0).run();
    return J({ ok: true });
  }
  return null;
}
