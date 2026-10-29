// Events (Veranstalter), Sessions mit Speakern, Sponsoren-Suche fuer Veranstalter
import { cleanText, rateLimit } from "./util.js";
import { baseIds } from "./entities.js";
import { cleanUrl } from "./profiles.js";

const HANDLE = /^[a-z0-9][a-z0-9-]{2,39}$/, PH = /^[a-z0-9][a-z0-9-]{2,29}$/;
const DATE = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?$/, MODES = ["online", "onsite", "hybrid"], LEVELS = ["", "100", "200", "300", "400"];
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const long = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();
const okDate = (s) => DATE.test(s) && !isNaN(Date.parse(s.length === 10 ? s + "T00:00:00Z" : s + ":00Z"));
const parse = (s, d) => { try { return JSON.parse(s); } catch { return d; } };

async function topics(env, list) {
  const known = await baseIds(env), out = [];
  for (const t of (Array.isArray(list) ? list : []).slice(0, 12)) { if (!known.has(t)) return null; if (!out.includes(t)) out.push(t); }
  return out;
}
// Darf der Nutzer das Event verwalten (Eigentuemer oder Admin/Inhaber der Veranstalter-Firma)?
async function canManage(db, user, ev) {
  if (!user || !ev) return false;
  if (ev.owner_id === user.id || user.admin) return true;
  if (!ev.org_id) return false;
  return !!(await db.prepare("SELECT 1 x FROM org_members WHERE org_id=? AND user_id=? AND status='active' AND role IN ('owner','admin')").bind(ev.org_id, user.id).first());
}
async function speakersCheck(db, list) {
  const out = [];
  for (const s of (Array.isArray(list) ? list : []).slice(0, 8)) {
    const n = txt(s?.n, 80), h = String(s?.h || "").toLowerCase().trim();
    if (h) {
      if (!PH.test(h)) return null;
      const p = await db.prepare("SELECT u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.handle=? AND p.public=1").bind(h).first();
      if (!p) return null; out.push({ h, n: n || p.name });
    } else if (n.length >= 2) out.push({ n });
  }
  return out;
}
const sessView = (r) => ({ id: r.id, title: r.title, abstract: r.abstract, start: r.start, end: r.end, room: r.room, track: r.track, level: r.level, lang: r.lang, topics: parse(r.topics, []), speakers: parse(r.speakers, []), recording_url: r.recording_url, status: r.status });
async function evView(db, ev, withPending) {
  const org = ev.org_id ? await db.prepare("SELECT handle,name,public FROM orgs WHERE id=?").bind(ev.org_id).first() : null;
  const ow = await db.prepare("SELECT u.name,p.handle FROM users u LEFT JOIN profiles p ON p.user_id=u.id AND p.public=1 WHERE u.id=?").bind(ev.owner_id).first();
  const rows = (await db.prepare("SELECT * FROM event_sessions WHERE event_id=? " + (withPending ? "" : "AND status='live' ") + "ORDER BY start,id").bind(ev.id).all()).results || [];
  return { handle: ev.handle, title: ev.title, summary: ev.summary, about: ev.about, start: ev.start, end: ev.end, mode: ev.mode, location: ev.location, country: ev.country, url: ev.url, tickets_url: ev.tickets_url,
    free: !!ev.free, lang: ev.lang, topics: parse(ev.topics, []), seeking_sponsor: !!ev.seeking_sponsor, public: !!ev.public,
    organizer: org ? { kind: "o", handle: org.public ? org.handle : "", name: org.name } : { kind: "u", handle: ow?.handle || "", name: ow?.name || "" }, sessions: rows.map(sessView) };
}

export async function handleEvents(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m;
  const need = () => (user ? null : J({ error: "login" }, 401));
  const body = async () => await request.json().catch(() => ({}));

  if (path === "/api/events/export" && method === "GET") {
    const evs = (await db.prepare("SELECT * FROM events WHERE public=1 ORDER BY start DESC LIMIT 300").all()).results || [];
    const out = []; for (const e of evs) out.push(await evView(db, e, false));
    return J({ events: out }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path === "/api/events/mine" && method === "GET") {
    if (need()) return need();
    const evs = (await db.prepare("SELECT e.* FROM events e WHERE e.owner_id=?1 OR e.org_id IN (SELECT org_id FROM org_members WHERE user_id=?1 AND status='active' AND role IN ('owner','admin')) ORDER BY e.start DESC").bind(user.id).all()).results || [];
    const out = []; for (const e of evs) out.push(await evView(db, e, true));
    const orgs = (await db.prepare("SELECT o.handle,o.name FROM org_members m JOIN orgs o ON o.id=m.org_id WHERE m.user_id=? AND m.status='active' AND m.role IN ('owner','admin')").bind(user.id).all()).results || [];
    return J({ events: out, orgs });
  }
  if (path === "/api/event" && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `event:${user.id}`, 30, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await body(), handle = String(b.handle || "").toLowerCase().trim();
    if (!HANDLE.test(handle)) return J({ error: "bad_handle" }, 400);
    const title = txt(b.title, 120); if (title.length < 3) return J({ error: "bad_title" }, 400);
    if (!okDate(String(b.start || ""))) return J({ error: "bad_date" }, 400);
    const end = String(b.end || ""); if (end && (!okDate(end) || end < b.start)) return J({ error: "bad_date" }, 400);
    const mode = MODES.includes(b.mode) ? b.mode : "online";
    const eu = cleanUrl(b.url, null), tu = cleanUrl(b.tickets_url, null); if (eu === null || tu === null) return J({ error: "bad_url" }, 400);
    const tp = await topics(env, b.topics); if (!tp) return J({ error: "bad_topic" }, 400);
    let orgId = null;
    if (b.org) {
      const o = await db.prepare("SELECT o.id FROM orgs o JOIN org_members m ON m.org_id=o.id WHERE o.handle=? AND m.user_id=? AND m.status='active' AND m.role IN ('owner','admin')").bind(String(b.org), user.id).first();
      if (!o) return J({ error: "forbidden" }, 403); orgId = o.id;
    }
    const ex = await db.prepare("SELECT * FROM events WHERE handle=?").bind(handle).first();
    if (ex && !(await canManage(db, user, ex))) return J({ error: "handle_taken" }, 409);
    const vals = [title, txt(b.summary, 200), long(b.about, 3000), b.start, end, mode, txt(b.location, 120), txt(b.country, 60), eu, tu, b.free === false ? 0 : 1, txt(b.lang, 10), JSON.stringify(tp), b.seeking_sponsor ? 1 : 0, b.public === false ? 0 : 1, now()];
    if (ex) await db.prepare("UPDATE events SET title=?,summary=?,about=?,start=?,end=?,mode=?,location=?,country=?,url=?,tickets_url=?,free=?,lang=?,topics=?,seeking_sponsor=?,public=?,updated=?,org_id=? WHERE id=?").bind(...vals, b.org === undefined ? ex.org_id : orgId, ex.id).run();
    else await db.prepare("INSERT INTO events(title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,updated,handle,owner_id,org_id,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(...vals, handle, user.id, orgId, now()).run();
    return J({ ok: true });
  }
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})$/)) && method === "DELETE") {
    if (need()) return need();
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first();
    if (!(await canManage(db, user, ev))) return J({ error: "forbidden" }, 403);
    await db.batch([db.prepare("DELETE FROM event_sessions WHERE event_id=?").bind(ev.id), db.prepare("DELETE FROM events WHERE id=?").bind(ev.id)]);
    return J({ ok: true });
  }
  // Session anlegen/aendern: Veranstalter -> sofort live; andere Mitglieder -> Vorschlag (pending)
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})\/session$/)) && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `sess:${user.id}`, 40, 3600))) return J({ error: "rate_limit" }, 429);
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first(); if (!ev) return J({ error: "not_found" }, 404);
    const mgr = await canManage(db, user, ev), b = await body();
    const title = txt(b.title, 140); if (title.length < 3) return J({ error: "bad_title" }, 400);
    const st = String(b.start || ""), en = String(b.end || "");
    if ((st && !okDate(st)) || (en && !okDate(en))) return J({ error: "bad_date" }, 400);
    const tp = await topics(env, b.topics); if (!tp) return J({ error: "bad_topic" }, 400);
    const sp = await speakersCheck(db, b.speakers); if (!sp) return J({ error: "bad_speaker" }, 400);
    const ru = cleanUrl(b.recording_url, null); if (ru === null) return J({ error: "bad_url" }, 400);
    const level = LEVELS.includes(String(b.level || "")) ? String(b.level || "") : "";
    const f = [title, long(b.abstract, 1500), st, en, txt(b.room, 60), txt(b.track, 60), level, txt(b.lang, 10), JSON.stringify(tp), JSON.stringify(sp), ru];
    if (b.id) {
      const s = await db.prepare("SELECT * FROM event_sessions WHERE id=? AND event_id=?").bind(+b.id, ev.id).first(); if (!s) return J({ error: "not_found" }, 404);
      if (!mgr && !(s.proposer_id === user.id && s.status === "pending")) return J({ error: "forbidden" }, 403);
      await db.prepare("UPDATE event_sessions SET title=?,abstract=?,start=?,end=?,room=?,track=?,level=?,lang=?,topics=?,speakers=?,recording_url=? WHERE id=?").bind(...f, s.id).run();
      return J({ ok: true });
    }
    if ((await db.prepare("SELECT COUNT(*) n FROM event_sessions WHERE event_id=?").bind(ev.id).first()).n >= 300) return J({ error: "limit" }, 400);
    await db.prepare("INSERT INTO event_sessions(title,abstract,start,end,room,track,level,lang,topics,speakers,recording_url,event_id,status,proposer_id,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(...f, ev.id, mgr ? "live" : "pending", user.id, now()).run();
    return J({ ok: true, status: mgr ? "live" : "pending" });
  }
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})\/session\/(\d+)(\/approve)?$/))) {
    if (need()) return need();
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first(); if (!ev) return J({ error: "not_found" }, 404);
    const s = await db.prepare("SELECT * FROM event_sessions WHERE id=? AND event_id=?").bind(+m[2], ev.id).first(); if (!s) return J({ error: "not_found" }, 404);
    const mgr = await canManage(db, user, ev);
    if (m[3] && method === "POST") {
      if (!mgr) return J({ error: "forbidden" }, 403);
      const b = await body();
      if (b.ok === false) await db.prepare("DELETE FROM event_sessions WHERE id=?").bind(s.id).run(); else await db.prepare("UPDATE event_sessions SET status='live' WHERE id=?").bind(s.id).run();
      return J({ ok: true });
    }
    if (!m[3] && method === "DELETE") {
      if (!mgr && s.proposer_id !== user.id) return J({ error: "forbidden" }, 403);
      await db.prepare("DELETE FROM event_sessions WHERE id=?").bind(s.id).run(); return J({ ok: true });
    }
  }
  // Veranstalter sehen Firmen, die Sponsoring angeboten haben (nur wer ein Event mit "sucht Sponsoren" hat)
  if (path === "/api/events/sponsors" && method === "GET") {
    if (need()) return need();
    const mine = await db.prepare("SELECT 1 x FROM events WHERE seeking_sponsor=1 AND (owner_id=?1 OR org_id IN (SELECT org_id FROM org_members WHERE user_id=?1 AND status='active' AND role IN ('owner','admin'))) LIMIT 1").bind(user.id).first();
    if (!mine && !user.admin) return J({ error: "forbidden" }, 403);
    const rows = (await db.prepare("SELECT o.handle,o.name,o.public,o.website,s.criteria FROM org_sponsor s JOIN orgs o ON o.id=s.org_id WHERE s.open=1 ORDER BY s.updated DESC LIMIT 100").all()).results || [];
    return J({ sponsors: rows.map((r) => ({ handle: r.public ? r.handle : "", name: r.name, website: r.website, criteria: parse(r.criteria, {}) })) });
  }
  return null;
}

export async function deleteUserEvents(db, uid) {
  const evs = (await db.prepare("SELECT id FROM events WHERE owner_id=? AND org_id IS NULL").bind(uid).all()).results || [];
  const ops = [];
  for (const e of evs) ops.push(db.prepare("DELETE FROM event_sessions WHERE event_id=?").bind(e.id), db.prepare("DELETE FROM events WHERE id=?").bind(e.id));
  ops.push(db.prepare("DELETE FROM event_sessions WHERE proposer_id=? AND status='pending'").bind(uid));
  if (ops.length) await db.batch(ops);
}
