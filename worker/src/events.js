// Events (Veranstalter), Sessions mit Speakern, Sponsoren-Suche fuer Veranstalter
import { ownedEntity } from "./profiles.js";
import { cleanText, rateLimit } from "./util.js";
import { baseIds } from "./entities.js";
import { cleanUrl } from "./profiles.js";
import { stats } from "./badges.js";

const FREE_ASKS = 2, ASK_COST = 1000;
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
const EID = /^[a-z0-9-]{2,48}$/;
const rndToken = () => [...crypto.getRandomValues(new Uint8Array(18))].map((b) => b.toString(16).padStart(2, "0")).join("");
// Speaker pruefen. Jede Person muss die Teilnahme selbst bestaetigen (s: invited|confirmed). Bestehende Stati/Tokens bleiben erhalten.
async function speakersCheck(db, list, prev, selfHandle) {
  const out = [], old = new Map((prev || []).map((x) => [x.h || x.n, x]));
  for (const s of (Array.isArray(list) ? list : []).slice(0, 8)) {
    const n = txt(s?.n, 80), h = String(s?.h || "").toLowerCase().trim(), e = String(s?.e || "").toLowerCase().trim();
    if (e && !EID.test(e)) return null;
    const keep = old.get(h || n);
    if (h) {
      if (!PH.test(h)) return null;
      const p = await db.prepare("SELECT u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.handle=? AND p.public=1").bind(h).first();
      if (!p) return null;
      out.push({ h, n: keep?.n || n || p.name, ...(e ? { e } : keep?.e ? { e: keep.e } : {}), s: keep?.s === "confirmed" || h === selfHandle ? "confirmed" : keep?.s === "declined" ? "declined" : "invited" });
    } else if (n.length >= 2) out.push({ n, ...(e ? { e } : keep?.e ? { e: keep.e } : {}), s: keep?.s === "confirmed" ? "confirmed" : "invited", ...(keep?.t ? { t: keep.t } : { t: rndToken() }) });
  }
  return out;
}
async function saveInvites(db, evId, sid, sp) {
  const ops = [db.prepare("DELETE FROM speaker_invites WHERE session_id=? AND token NOT IN (SELECT value FROM json_each(?))").bind(sid, JSON.stringify(sp.filter((x) => x.t).map((x) => x.t)))];
  for (const x of sp) if (x.t && x.s !== "confirmed") ops.push(db.prepare("INSERT OR IGNORE INTO speaker_invites(token,event_id,session_id,name,eid,created) VALUES(?,?,?,?,?,?)").bind(x.t, evId, sid, x.n, x.e || "", now()));
  await db.batch(ops);
}
async function claimEntity(db, eid, uid, via) {
  const c = await db.prepare("SELECT user_id FROM entity_claims WHERE eid=?").bind(eid).first();
  if (c && c.user_id !== uid) return false;
  await db.prepare("INSERT INTO entity_claims(eid,user_id,status,via,created) VALUES(?,?,?,?,?) ON CONFLICT(eid) DO UPDATE SET status=CASE WHEN excluded.status='verified' THEN 'verified' ELSE entity_claims.status END").bind(eid, uid, via === "invite" ? "verified" : "pending", via, now()).run();
  return true;
}
const sessView = (r, mgr) => ({ id: r.id, title: r.title, abstract: r.abstract, start: r.start, end: r.end, room: r.room, track: r.track, level: r.level, lang: r.lang, topics: parse(r.topics, []), speakers: mgr ? parse(r.speakers, []) : parse(r.speakers, []).filter((x) => x.s === "confirmed").map((x) => ({ h: x.h, n: x.n, e: x.e })), speakers_open: parse(r.speakers, []).filter((x) => x.s !== "confirmed").length, recording_url: r.recording_url, status: r.status });
async function evView(db, ev, withPending) {
  const org = ev.org_id ? await db.prepare("SELECT handle,name,public FROM orgs WHERE id=?").bind(ev.org_id).first() : null;
  const ow = await db.prepare("SELECT u.name,p.handle FROM users u LEFT JOIN profiles p ON p.user_id=u.id AND p.public=1 WHERE u.id=?").bind(ev.owner_id).first();
  const rows = (await db.prepare("SELECT * FROM event_sessions WHERE event_id=? " + (withPending ? "" : "AND status='live' ") + "ORDER BY start,id").bind(ev.id).all()).results || [];
  return { handle: ev.handle, title: ev.title, summary: ev.summary, about: ev.about, start: ev.start, end: ev.end, mode: ev.mode, location: ev.location, country: ev.country, url: ev.url, tickets_url: ev.tickets_url,
    free: !!ev.free, lang: ev.lang, topics: parse(ev.topics, []), seeking_sponsor: !!ev.seeking_sponsor, public: !!ev.public,
    asked: withPending ? ((await db.prepare("SELECT o.handle FROM sponsor_asks a JOIN orgs o ON o.id=a.org_id WHERE a.event_id=?").bind(ev.id).all()).results || []).map((x) => x.handle) : undefined,
    organizer: org ? { kind: "o", handle: org.public ? org.handle : "", name: org.name } : { kind: "u", handle: ow?.handle || "", name: ow?.name || "" }, sessions: rows.map((r) => sessView(r, withPending)) };
}

export async function ensureM365Con(env) {   // M365Con 2027 ist ein Event und gehoert dem Admin als Veranstalter
  const db = env.DB, subs = (env.ADMIN_SUBS || "").split(",").map((x) => x.trim()).filter(Boolean);
  let owner = null;
  for (const a of subs) { const [pr, ...rest] = a.split(":"); owner = await db.prepare("SELECT id FROM users WHERE provider=? AND sub=?").bind(pr, rest.join(":")).first(); if (owner) break; }
  if (!owner) return;
  const t = Math.floor(Date.now() / 1000), ex = await db.prepare("SELECT id,owner_id FROM events WHERE handle='m365con-2027'").first();
  for (const [h, nm, tg, web, eid] of [["m365fm", "M365.FM", "Podcast and community about Microsoft 365, Copilot and AI", "https://www.m365.fm", "m365fm"], ["m365con", "M365Con", "Free online convention for the Microsoft 365 community", "https://m365con.net", "m365con"]]) {
    let o = await db.prepare("SELECT id FROM orgs WHERE handle=?").bind(h).first();
    if (!o) { const r = await db.prepare("INSERT INTO orgs(handle,name,tagline,about,website,country,size,public,created) VALUES(?,?,?,?,?,'Germany','2-10',1,?)").bind(h, nm, tg, "", web, t).run(); o = { id: r.meta.last_row_id }; }
    await db.prepare("INSERT OR IGNORE INTO org_members(org_id,user_id,role,status,created) VALUES(?,?,'owner','active',?)").bind(o.id, owner.id, t).run();
    await db.prepare("INSERT OR IGNORE INTO org_entity(org_id,eid) VALUES(?,?)").bind(o.id, eid).run();
  }
  for (const eid of ["m365con", "m365fm", "mirko-peters"]) await db.prepare("INSERT INTO entity_claims(eid,user_id,status,via,created) VALUES(?,?,'verified','admin',?) ON CONFLICT(eid) DO NOTHING").bind(eid, owner.id, t).run();
  if (!ex) await db.prepare("INSERT INTO events(handle,owner_id,title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,created,updated) VALUES('m365con-2027',?,?,?,?,?,?,'online','Online','','https://m365con.net','https://m365con.net',1,'en','[\"m365con\"]',1,1,?,?)")
    .bind(owner.id, "M365Con 2027", "Free online convention: 10 days, 120+ sessions, 120+ speakers, a daily focus topic.", "M365Con 2027 is a free online convention about Microsoft 365, Copilot and AI with 10 days of sessions, a daily focus topic and 120+ speakers.", "2027-01-11T08:00", "2027-01-22", t, t).run();
  else if (ex.owner_id !== owner.id) await db.prepare("UPDATE events SET owner_id=? WHERE id=?").bind(owner.id, ex.id).run();
}

export async function handleEvents(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m;
  const need = () => (user ? null : J({ error: "login" }, 401));
  const body = async () => await request.json().catch(() => ({}));

  if (path === "/api/events/seed-m365con" && method === "POST") {   // Admin: M365Con 2027 als Event anlegen (zunaechst nicht oeffentlich, Daten spaeter im Organizer-Bereich pflegen)
    if (!user?.admin) return J({ error: "forbidden" }, 403);
    const ex = await db.prepare("SELECT id FROM events WHERE handle='m365con-2027'").first();
    if (ex) { await db.prepare("UPDATE events SET owner_id=?, public=1 WHERE id=?").bind(user.id, ex.id).run(); return J({ ok: true, existed: true, handle: "m365con-2027" }); }
    const b = await body(), t = Math.floor(Date.now() / 1000);
    await db.prepare("INSERT INTO events(handle,owner_id,title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,created,updated) VALUES('m365con-2027',?,?,?,?,?,?,'online','Online','',?,?,1,'en','[\"m365con\"]',1,1,?,?)")
      .bind(user.id, "M365Con 2027", "Free online convention: 10 days, 120+ sessions, 120+ speakers, a daily focus topic.", "M365Con 2027 is a free online convention about Microsoft 365, Copilot and AI with 10 days of sessions, a daily focus topic and 120+ speakers.", String(b.start || "2027-01-11T08:00").slice(0, 16), String(b.end || "2027-01-22").slice(0, 16), "https://m365con.net", "https://m365con.net", t, t).run();
    return J({ ok: true, handle: "m365con-2027", public: false });
  }
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
    if (b.public !== false) await ownedEntity(env, user, { eid: handle, type: "event", name: title, en: `${title} is an event in the Microsoft community, starting ${b.start}.`, de: `${title} ist eine Veranstaltung der Microsoft-Community, Beginn ${b.start}.`, web: String(b.url || "").startsWith("https://") ? b.url : "" });
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
    const myH = (await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(user.id).first())?.handle || "";
    let prevSp = []; if (b.id) { const ps = await db.prepare("SELECT speakers FROM event_sessions WHERE id=? AND event_id=?").bind(+b.id, ev.id).first(); prevSp = parse(ps?.speakers, []); }
    const sp = await speakersCheck(db, b.speakers, prevSp, myH); if (!sp) return J({ error: "bad_speaker" }, 400);
    const ru = cleanUrl(b.recording_url, null); if (ru === null) return J({ error: "bad_url" }, 400);
    const level = LEVELS.includes(String(b.level || "")) ? String(b.level || "") : "";
    const f = [title, long(b.abstract, 1500), st, en, txt(b.room, 60), txt(b.track, 60), level, txt(b.lang, 10), JSON.stringify(tp), JSON.stringify(sp), ru];
    if (b.id) {
      const s = await db.prepare("SELECT * FROM event_sessions WHERE id=? AND event_id=?").bind(+b.id, ev.id).first(); if (!s) return J({ error: "not_found" }, 404);
      if (!mgr && !(s.proposer_id === user.id && s.status === "pending")) return J({ error: "forbidden" }, 403);
      await db.prepare("UPDATE event_sessions SET title=?,abstract=?,start=?,end=?,room=?,track=?,level=?,lang=?,topics=?,speakers=?,recording_url=? WHERE id=?").bind(...f, s.id).run();
      await saveInvites(db, ev.id, s.id, sp);
      return J({ ok: true });
    }
    if ((await db.prepare("SELECT COUNT(*) n FROM event_sessions WHERE event_id=?").bind(ev.id).first()).n >= 300) return J({ error: "limit" }, 400);
    await db.prepare("INSERT INTO event_sessions(title,abstract,start,end,room,track,level,lang,topics,speakers,recording_url,event_id,status,proposer_id,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(...f, ev.id, mgr ? "live" : "pending", user.id, now()).run();
    const nid = (await db.prepare("SELECT last_insert_rowid() id").first()).id; await saveInvites(db, ev.id, nid, sp);
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
  // ---- Speaker: Einladung ansehen/bestaetigen, Anfragen an bestehende Mitglieder ----
  if ((m = path.match(/^\/api\/speaker\/invite\/([a-f0-9]{36})$/)) && method === "GET") {
    const i = await db.prepare("SELECT i.name,i.eid,s.title,e.title ev,e.handle FROM speaker_invites i JOIN event_sessions s ON s.id=i.session_id JOIN events e ON e.id=i.event_id WHERE i.token=?").bind(m[1]).first();
    return i ? J({ invite: i }) : J({ error: "not_found" }, 404);
  }
  if (path === "/api/speaker/confirm" && method === "POST") {
    if (need()) return need();
    const b = await body(), tok = String(b.token || "");
    const i = await db.prepare("SELECT * FROM speaker_invites WHERE token=?").bind(tok).first(); if (!i) return J({ error: "not_found" }, 404);
    const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(user.id).first();
    const se = await db.prepare("SELECT id,speakers FROM event_sessions WHERE id=?").bind(i.session_id).first();
    let sp = parse(se?.speakers, []);
    if (b.decline) { sp = sp.map((x) => (x.t === tok ? { ...x, s: "declined" } : x)); await db.batch([db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), se.id), db.prepare("DELETE FROM speaker_invites WHERE token=?").bind(tok)]); return J({ ok: true, declined: true }); }
    if (!pr) return J({ error: "need_profile" }, 409);
    sp = sp.map((x) => (x.t === tok ? { h: pr.handle, n: x.n, ...(x.e ? { e: x.e } : {}), s: "confirmed" } : x));
    await db.batch([db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), se.id), db.prepare("DELETE FROM speaker_invites WHERE token=?").bind(tok)]);
    let claimed = false; if (i.eid) claimed = await claimEntity(db, i.eid, user.id, "invite");
    return J({ ok: true, handle: pr.handle, claimed });
  }
  if (path === "/api/speaker/requests" && method === "GET") {
    if (need()) return need();
    const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=?").bind(user.id).first(); if (!pr?.handle) return J({ items: [] });
    const rows = (await db.prepare("SELECT s.id,s.title,e.title ev,e.handle eh,s.speakers FROM event_sessions s JOIN events e ON e.id=s.event_id WHERE s.speakers LIKE ?").bind(`%"h":"${pr.handle}"%`).all()).results || [];
    return J({ items: rows.filter((r) => parse(r.speakers, []).some((x) => x.h === pr.handle && x.s === "invited")).map((r) => ({ id: r.id, title: r.title, event: r.ev, eh: r.eh })) });
  }
  if (path === "/api/speaker/respond" && method === "POST") {
    if (need()) return need();
    const b = await body(), pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=?").bind(user.id).first(); if (!pr?.handle) return J({ error: "need_profile" }, 409);
    const se = await db.prepare("SELECT id,speakers FROM event_sessions WHERE id=?").bind(+b.id).first(); if (!se) return J({ error: "not_found" }, 404);
    const sp = parse(se.speakers, []).map((x) => (x.h === pr.handle ? { ...x, s: b.ok ? "confirmed" : "declined" } : x));
    await db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), se.id).run();
    return J({ ok: true });
  }
  // ---- Entitaet uebernehmen ----
  if (path === "/api/entity/claim" && method === "POST") {
    if (need()) return need();
    const b = await body(), eid = String(b.eid || "").toLowerCase();
    if (!EID.test(eid)) return J({ error: "bad_id" }, 400);
    const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(user.id).first(); if (!pr) return J({ error: "need_profile" }, 409);
    if (!(await rateLimit(db, `claim:${user.id}`, 5, 86400))) return J({ error: "rate_limit" }, 429);
    const ok = await claimEntity(db, eid, user.id, "manual"); return ok ? J({ ok: true }) : J({ error: "claimed" }, 409);
  }
  if (path === "/api/entity/claims" && method === "GET") {
    const rows = (await db.prepare("SELECT c.eid,p.handle FROM entity_claims c JOIN profiles p ON p.user_id=c.user_id AND p.public=1 WHERE c.status='verified'").all()).results || [];
    return J({ claims: rows }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path === "/api/entity/claim/mine" && method === "GET") {
    if (need()) return need();
    return J({ claims: (await db.prepare("SELECT eid,status FROM entity_claims WHERE user_id=?").bind(user.id).all()).results || [] });
  }
  if (path === "/api/admin/entity/claims" && method === "GET") {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    return J({ claims: (await db.prepare("SELECT c.eid,c.user_id,u.name,p.handle FROM entity_claims c JOIN users u ON u.id=c.user_id LEFT JOIN profiles p ON p.user_id=c.user_id WHERE c.status='pending'").all()).results || [] });
  }
  if (path === "/api/admin/entity/claim" && method === "POST") {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    const b = await body(); if (b.ok) await db.prepare("UPDATE entity_claims SET status='verified' WHERE eid=?").bind(String(b.eid)).run(); else await db.prepare("DELETE FROM entity_claims WHERE eid=?").bind(String(b.eid)).run();
    return J({ ok: true });
  }

  // Sponsoren (Firmen mit aktivem Gesuch) sehen Events, die Sponsoren suchen
  if (path === "/api/events/for-sponsors" && method === "GET") {
    if (need()) return need();
    const o = (await db.prepare("SELECT s.criteria FROM org_sponsor s JOIN org_members m ON m.org_id=s.org_id WHERE s.open=1 AND m.user_id=? AND m.status='active' AND m.role IN ('owner','admin')").bind(user.id).all()).results || [];
    if (!o.length) return J({ error: "forbidden" }, 403);
    const crits = o.map((r) => parse(r.criteria, {}));
    const today = new Date().toISOString().slice(0, 10);
    const evs = (await db.prepare("SELECT * FROM events WHERE seeking_sponsor=1 AND public=1 AND (CASE WHEN end<>'' THEN end ELSE start END)>=? ORDER BY start LIMIT 100").bind(today).all()).results || [];
    const out = []; for (const e of evs) { const v = await evView(db, e, false); delete v.sessions; v.match = crits.some((c) => !c.format || c.format === e.mode); out.push(v); }
    return J({ events: out });
  }
  // Veranstalter fragen Firmen an (2 Wunschfirmen je Event frei, weitere kosten Punkte); Nachricht landet im Postfach der Firma
  if (path === "/api/events/ask-sponsor" && method === "POST") {
    if (need()) return need();
    const b = await body(), ev = await db.prepare("SELECT * FROM events WHERE handle=? AND seeking_sponsor=1").bind(String(b.event || "")).first();
    if (!ev || !(await canManage(db, user, ev))) return J({ error: "forbidden" }, 403);
    const org = await db.prepare("SELECT o.id FROM org_sponsor s JOIN orgs o ON o.id=s.org_id WHERE s.open=1 AND o.handle=?").bind(String(b.org || "")).first(); if (!org) return J({ error: "not_found" }, 404);
    const tx = txt(b.body, 1000); if (tx.length < 10) return J({ error: "too_short" }, 400);
    if (await db.prepare("SELECT 1 x FROM sponsor_asks WHERE event_id=? AND org_id=?").bind(ev.id, org.id).first()) return J({ error: "already" }, 409);
    const used = (await db.prepare("SELECT COUNT(*) n FROM sponsor_asks WHERE event_id=?").bind(ev.id).first()).n;
    let paid = false;
    if (used >= FREE_ASKS) { const st = await stats(db, user.id); if (st.balance < ASK_COST) return J({ error: "need_points", cost: ASK_COST, balance: st.balance }, 402); paid = true; }
    const to = (await db.prepare("SELECT user_id FROM org_members WHERE org_id=? AND role='owner' AND status='active' LIMIT 1").bind(org.id).first())?.user_id; if (!to || to === user.id) return J({ error: "no_recipient" }, 400);
    const t0 = now(); let t = await db.prepare("SELECT * FROM msg_threads WHERE (a_id=?1 AND b_id=?2) OR (a_id=?2 AND b_id=?1)").bind(user.id, to).first();
    const ops = [];
    if (!t) { const r = await db.prepare("INSERT INTO msg_threads(a_id,b_id,ctx,created,last,a_read) VALUES(?,?,?,?,?,?)").bind(user.id, to, "sponsor:" + ev.handle, t0, t0, t0).run(); t = { id: r.meta.last_row_id, a_id: user.id }; }
    ops.push(db.prepare("INSERT INTO msg_messages(thread_id,from_id,body,created) VALUES(?,?,?,?)").bind(t.id, user.id, tx, t0), db.prepare(`UPDATE msg_threads SET last=?,${t.a_id === user.id ? "a_read" : "b_read"}=? WHERE id=?`).bind(t0, t0, t.id),
      db.prepare("INSERT INTO sponsor_asks(event_id,org_id,created) VALUES(?,?,?)").bind(ev.id, org.id, t0));
    if (paid) ops.push(db.prepare("INSERT INTO points_spent(user_id,item,cost,status,note,created) VALUES(?,?,?,?,?,?)").bind(user.id, "sponsor_ask", ASK_COST, "done", ev.handle, t0));
    await db.batch(ops);
    return J({ ok: true, free_left: Math.max(0, FREE_ASKS - used - 1), paid });
  }
  // Veranstalter sehen Firmen, die Sponsoring angeboten haben (nur wer ein Event mit "sucht Sponsoren" hat)
  if (path === "/api/events/sponsors" && method === "GET") {
    if (need()) return need();
    const mine = await db.prepare("SELECT 1 x FROM events WHERE seeking_sponsor=1 AND (owner_id=?1 OR org_id IN (SELECT org_id FROM org_members WHERE user_id=?1 AND status='active' AND role IN ('owner','admin'))) LIMIT 1").bind(user.id).first();
    if (!mine && !user.admin) return J({ error: "forbidden" }, 403);
    const rows = (await db.prepare("SELECT o.handle,o.name,o.public,o.website,s.criteria FROM org_sponsor s JOIN orgs o ON o.id=s.org_id WHERE s.open=1 ORDER BY s.updated DESC LIMIT 100").all()).results || [];
    return J({ free_asks: FREE_ASKS, ask_cost: ASK_COST, sponsors: rows.map((r) => ({ handle: r.handle, name: r.name, website: r.website, criteria: parse(r.criteria, {}) })) });
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
