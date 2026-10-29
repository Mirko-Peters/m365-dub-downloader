// Entitaetsdatenbank fuer das Microsoft-Oekosystem: Community-Revisionen ueber den statischen Basisdaten (data/entities.json)
import { cleanText, rateLimit } from "./util.js";
import { stats, evalBadges } from "./badges.js";

const ID = /^[a-z0-9-]{2,48}$/;
export const TYPES = ["product", "platform", "concept", "org", "person", "cert", "event", "media", "category"];
export const PRED = ["instance_of", "part_of", "developed_by", "related_to", "requires", "covers", "created_by", "organized_by", "similar_to"];
const TRUST_POINTS = 25;
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const httpsUrl = (s, ok) => { s = String(s || "").trim(); if (!s) return ""; try { const u = new URL(s); if (u.protocol !== "https:" || s.length > 250 || u.username || !ok(u.hostname)) return null; return u.href; } catch { return null; } };
const isMs = (h) => /(^|\.)(microsoft\.com|azure\.com|office\.com|visualstudio\.com|github\.com|github\.io|microsoft365\.com|linkedin\.com)$/i.test(h);

// Basisliste (statisch veroeffentlicht) fuer Verweisziele; 10 Minuten im Edge-Cache
export async function baseIds(env) {
  try {
    const c = caches.default, key = new Request(env.SITE + "/entities.json");
    let r = await c.match(key);
    if (!r) { r = await fetch(key); if (!r.ok) return new Set(); const cl = new Response(r.body, r); cl.headers.set("cache-control", "max-age=600"); await c.put(key, cl.clone()); r = cl; }
    return new Set(((await r.json()).entities || []).map((e) => e.id));
  } catch { return new Set(); }
}

export async function validate(env, id, raw) {
  const d = {}; const bad = (e) => ({ err: e });
  d.name = txt(raw?.name, 80); if (d.name.length < 2) return bad("bad_name");
  if (!TYPES.includes(raw.type)) return bad("bad_type"); d.type = raw.type;
  d.aliases = [...new Set((Array.isArray(raw.aliases) ? raw.aliases : []).map((a) => txt(a, 60)).filter((a) => a.length >= 2))].slice(0, 10);
  d.desc = { en: txt(raw.desc?.en, 600), de: txt(raw.desc?.de, 600) };
  if (d.desc.en.length + d.desc.de.length < 20) return bad("too_short");
  d.web = httpsUrl(raw.web, () => true); d.docs = httpsUrl(raw.docs, (h) => /(^|\.)(microsoft\.com|azure\.com|github\.com)$/i.test(h));
  d.wikipedia = httpsUrl(raw.wikipedia, (h) => /^[a-z]{2,3}\.wikipedia\.org$/i.test(h));
  if (d.web === null || d.docs === null || d.wikipedia === null) return bad("bad_url");
  d.wikidata = String(raw.wikidata || "").trim(); if (d.wikidata && !/^Q\d{1,10}$/.test(d.wikidata)) return bad("bad_qid");
  const known = await baseIds(env);
  const dbIds = new Set(((await env.DB.prepare("SELECT DISTINCT eid FROM entity_rev WHERE status IN ('live','pending')").all()).results || []).map((r) => r.eid));
  const seen = new Set(); d.rel = [];
  for (const r of (Array.isArray(raw.rel) ? raw.rel : []).slice(0, 30)) {
    const [p, to] = Array.isArray(r) ? r : [r?.p, r?.to];
    if (!PRED.includes(p) || !ID.test(to || "") || to === id || !(known.has(to) || dbIds.has(to))) return bad("bad_relation");
    const k = p + ">" + to; if (!seen.has(k)) { seen.add(k); d.rel.push([p, to]); }
  }
  for (const k of ["same_as", "job", "start", "end"]) if (raw[k] !== undefined && k !== "same_as") d[k] = txt(raw[k], 40);
  return { data: d };
}

async function liveOf(db, eid) {
  return await db.prepare("SELECT r.id,r.data,r.created,r.user_id,COALESCE(u.name,'') name FROM entity_rev r LEFT JOIN users u ON u.id=r.user_id AND u.banned=0 WHERE r.eid=? AND r.status='live' ORDER BY r.created DESC LIMIT 1").bind(eid).first();
}
const trustedUser = async (db, user) => !!(user && (user.admin || user.editor || (await stats(db, user.id)).points >= TRUST_POINTS));

export async function handleEntity(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m;
  const need = () => (user ? null : J({ error: "login" }, 401));

  if (path === "/api/entity" && method === "GET") {
    const id = url.searchParams.get("id"); if (!ID.test(id || "")) return J({ error: "bad_request" }, 400);
    const live = await liveOf(db, id);
    const hist = ((await db.prepare("SELECT r.id,r.data,r.summary,r.created,COALESCE(u.name,'') name FROM entity_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.eid=? AND r.status IN ('live','old') ORDER BY r.created DESC LIMIT 15").bind(id).all()).results || []);
    let mine = null; if (user) mine = await db.prepare("SELECT id,data FROM entity_rev WHERE eid=? AND user_id=? AND status='pending' ORDER BY created DESC LIMIT 1").bind(id, user.id).first();
    return J({ live: live ? { id: live.id, data: JSON.parse(live.data), name: live.name, created: live.created } : null, history: hist.map((h) => ({ ...h, data: JSON.parse(h.data) })), mine: mine ? { id: mine.id, data: JSON.parse(mine.data) } : null,
      loggedIn: !!user, trusted: await trustedUser(db, user), admin: !!(user?.admin || user?.editor) });
  }
  if (path === "/api/entity" && method === "POST") {
    if (need()) return need();
    const b = await request.json().catch(() => ({})), id = String(b.id || "");
    if (!ID.test(id)) return J({ error: "bad_id" }, 400);
    if (!(await rateLimit(db, `ent:h:${user.id}`, 8, 3600)) || !(await rateLimit(db, `ent:d:${user.id}`, 30, 86400))) return J({ error: "rate_limit" }, 429);
    const v = await validate(env, id, b.data || {}); if (v.err) return J({ error: v.err }, 400);
    const data = JSON.stringify(v.data), summary = cleanText(b.summary || "", 140).replace(/[<>]/g, "");
    const cur = await liveOf(db, id); if (cur && cur.data === data) return J({ error: "unchanged" }, 400);
    const t = now();
    if (await trustedUser(db, user)) {
      await db.batch([db.prepare("UPDATE entity_rev SET status='old' WHERE eid=? AND status='live'").bind(id), db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,'live',?)").bind(id, data, summary, user.id, t)]);
      await evalBadges(env, user.id); return J({ ok: true, status: "live" });
    }
    await db.prepare("DELETE FROM entity_rev WHERE eid=? AND user_id=? AND status='pending'").bind(id, user.id).run();
    await db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,'pending',?)").bind(id, data, summary, user.id, t).run();
    return J({ ok: true, status: "pending" });
  }
  if (path === "/api/entity/export" && method === "GET") {
    const rows = (await db.prepare("SELECT r.eid,r.data,r.created,r.user_id FROM entity_rev r WHERE r.status='live'").all()).results || [];
    return J({ items: rows.map((r) => ({ id: r.eid, data: JSON.parse(r.data), created: r.created, uid: r.user_id })) }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path.startsWith("/api/admin/entity")) {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    if (path === "/api/admin/entity/pending" && method === "GET") {
      const rows = (await db.prepare("SELECT r.id,r.eid,r.data,r.summary,r.created,COALESCE(u.name,'') name FROM entity_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.status='pending' ORDER BY r.created ASC LIMIT 50").all()).results || [];
      return J({ pending: rows.map((r) => ({ ...r, data: JSON.parse(r.data) })) });
    }
    if ((m = /^\/api\/admin\/entity\/(approve|reject)\/(\d+)$/.exec(path)) && method === "POST") {
      const r = await db.prepare("SELECT id,eid,user_id FROM entity_rev WHERE id=?").bind(+m[2]).first(); if (!r) return J({ error: "not_found" }, 404);
      if (m[1] === "reject") { await db.prepare("UPDATE entity_rev SET status='rejected' WHERE id=?").bind(r.id).run(); return J({ ok: true }); }
      await db.batch([db.prepare("UPDATE entity_rev SET status='old' WHERE eid=? AND status='live'").bind(r.eid), db.prepare("UPDATE entity_rev SET status='live' WHERE id=?").bind(r.id)]);
      if (r.user_id) await evalBadges(env, r.user_id); return J({ ok: true });
    }
  }
  return null;
}
