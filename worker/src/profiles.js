// Experten- und Firmenprofile, Programme (MVP/MCT/...), Kanaele mit Feeds, Upvotes, Bestaetigungen
import { cleanText, rateLimit } from "./util.js";
import { baseIds } from "./entities.js";

export const PROGRAMS = ["mvp", "mct", "rd", "msa", "ms_employee", "partner"];
export const KINDS = ["linkedin", "github", "youtube", "x", "mastodon", "bluesky", "twitch", "blog", "podcast", "newsletter", "website", "other"];
const KIND_HOST = { linkedin: /(^|\.)linkedin\.com$/, github: /(^|\.)github\.com$/, youtube: /(^|\.)(youtube\.com|youtu\.be)$/, x: /(^|\.)(x\.com|twitter\.com)$/, twitch: /(^|\.)twitch\.tv$/, bluesky: /(^|\.)bsky\.app$/ };
const HANDLE = /^[a-z0-9][a-z0-9-]{2,29}$/, ID = /^[a-z0-9-]{2,48}$/;
const SIZES = ["1", "2-10", "11-50", "51-200", "201-1000", "1000+"];
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const long = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();

export function goodHost(h) { return !!h && h.includes(".") && h !== "localhost" && !/^[\d.]+$/.test(h) && !h.includes(":") && !/\.(local|internal|localhost)$/i.test(h); }
export function cleanUrl(s, hostRe) {
  s = String(s || "").trim(); if (!s) return ""; if (s.length > 300) return null;
  try { const u = new URL(s); if (u.protocol !== "https:" || u.username || u.password || !goodHost(u.hostname) || (hostRe && !hostRe.test(u.hostname))) return null; u.hash = ""; return u.href; } catch { return null; }
}
const slug = (s) => String(s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 24);

function channelFeed(kind, url, feed) {
  const m = kind === "youtube" ? /\/channel\/(UC[\w-]{22})/.exec(url) : null;
  if (m) return `https://www.youtube.com/feeds/videos.xml?channel_id=${m[1]}`;
  if (!feed) return ""; return cleanUrl(feed, null);
}
async function checkChannels(list, max = 12) {
  const out = [], seen = new Set();
  for (const c of (Array.isArray(list) ? list : []).slice(0, max)) {
    if (!KINDS.includes(c?.kind)) return { err: "bad_channel" };
    const url = cleanUrl(c.url, KIND_HOST[c.kind]); if (!url) return { err: "bad_channel" };
    const feed = channelFeed(c.kind, url, c.feed); if (feed === null) return { err: "bad_feed" };
    if (!seen.has(url)) { seen.add(url); out.push({ kind: c.kind, url, feed }); }
  }
  return { list: out };
}
async function checkExpertise(env, list, max = 30) {
  const known = await baseIds(env);
  const live = new Set(((await env.DB.prepare("SELECT DISTINCT eid FROM entity_rev WHERE status='live'").all()).results || []).map((r) => r.eid));
  const out = [], seen = new Set();
  for (const x of (Array.isArray(list) ? list : []).slice(0, max)) {
    if (!ID.test(x?.e || "") || !(known.has(x.e) || live.has(x.e))) return { err: "bad_expertise" };
    if (!seen.has(x.e)) { seen.add(x.e); out.push({ e: x.e, level: [1, 2, 3].includes(+x.level) ? +x.level : 2 }); }
  }
  return { list: out };
}
function checkPrograms(list, orgSide) {
  const out = [], seen = new Set();
  for (const p of (Array.isArray(list) ? list : []).slice(0, 8)) {
    if (!PROGRAMS.includes(p?.p) || seen.has(p.p)) return { err: "bad_program" };
    if (orgSide && !["partner"].includes(p.p)) return { err: "bad_program" };
    const url = cleanUrl(p.url, null); if (url === null) return { err: "bad_url" };
    seen.add(p.p); out.push({ p: p.p, year: Math.min(2100, Math.max(0, parseInt(p.year) || 0)), url });
  }
  return { list: out };
}

async function resolve(db, ref) {   // "u:handle" | "o:handle"
  const [t, h] = String(ref || "").split(":"); if (!HANDLE.test(h || "")) return null;
  if (t === "u") { const r = await db.prepare("SELECT p.user_id id FROM profiles p JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.handle=?").bind(h).first(); return r ? { t, id: r.id } : null; }
  if (t === "o") { const r = await db.prepare("SELECT id FROM orgs WHERE handle=?").bind(h).first(); return r ? { t, id: r.id } : null; }
  return null;
}

async function itemsOf(db, where, binds, viewer, limit = 10) {
  const rows = (await db.prepare(`SELECT i.id,i.title,i.url,i.published,i.owner_type ot,i.owner_id oid,c.kind,(SELECT COUNT(*) FROM item_votes v WHERE v.item_id=i.id) votes,
      ${viewer ? "(SELECT COUNT(*) FROM item_votes v WHERE v.item_id=i.id AND v.user_id=" + (+viewer) + ")" : "0"} voted
      FROM feed_items i JOIN channels c ON c.id=i.channel_id WHERE i.hidden=0 AND ${where} ORDER BY i.published DESC LIMIT ${+limit}`).bind(...binds).all()).results || [];
  return rows.map((r) => ({ id: r.id, title: r.title, url: r.url, published: r.published, kind: r.kind, votes: r.votes, voted: !!r.voted, owner: r.ot + ":" + r.oid }));
}

async function personView(db, uid, viewer) {
  const p = await db.prepare("SELECT p.*,u.name,u.bio FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=? AND u.banned=0").bind(uid).first(); if (!p) return null;
  const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results || [];
  const exp = await q("SELECT e.eid e,e.level,e.verified,(SELECT COUNT(*) FROM endorsements n WHERE n.owner_id=e.owner_id AND n.eid=e.eid) endorsed, (SELECT COUNT(*) FROM endorsements n2 WHERE n2.owner_id=e.owner_id AND n2.eid=e.eid AND n2.by_id=?) me FROM expertise e WHERE e.owner_type='u' AND e.owner_id=? ORDER BY e.verified DESC,e.level DESC", +viewer || 0, uid);
  const programs = await q("SELECT program p,year,url,verified FROM programs WHERE owner_type='u' AND owner_id=?", uid);
  const certs = await q("SELECT eid e,year,url FROM certs WHERE user_id=? ORDER BY year DESC", uid);
  const channels = await q("SELECT kind,url,feed FROM channels WHERE owner_type='u' AND owner_id=?", uid);
  const org = p.show_org ? await db.prepare("SELECT o.handle,o.name FROM org_members m JOIN orgs o ON o.id=m.org_id WHERE m.user_id=? AND m.status='active' AND o.public=1 ORDER BY m.created LIMIT 1").bind(uid).first() : null;
  const contrib = [...(await q("SELECT 'wiki' k,term t,lang l,summary s,created c FROM wiki_rev WHERE user_id=? AND status IN ('live','old') ORDER BY created DESC LIMIT 15", uid)),
    ...(await q("SELECT 'entity' k,eid t,'' l,summary s,created c FROM entity_rev WHERE user_id=? AND status IN ('live','old') ORDER BY created DESC LIMIT 15", uid))].sort((a, b) => b.c - a.c).slice(0, 15);
  const counts = { wiki: (await db.prepare("SELECT COUNT(*) n FROM wiki_rev WHERE user_id=? AND status IN ('live','old')").bind(uid).first()).n, entity: (await db.prepare("SELECT COUNT(*) n FROM entity_rev WHERE user_id=? AND status IN ('live','old')").bind(uid).first()).n };
  const badges = (await q("SELECT badge FROM user_badges WHERE user_id=?", uid)).map((b) => b.badge);
  return { type: "u", id: uid, handle: p.handle, name: p.name, bio: p.bio, headline: p.headline, about: p.about, company: p.company, job: p.job, country: p.country, public: !!p.public, show_org: !!p.show_org,
    expertise: exp.map((e) => ({ ...e, verified: !!e.verified, me: !!e.me })), programs: programs.map((x) => ({ ...x, verified: !!x.verified })), certs, channels, org, contrib, counts, badges,
    items: await itemsOf(db, "i.owner_type='u' AND i.owner_id=?", [uid], viewer, 8) };
}
async function orgView(db, oid, viewer) {
  const o = await db.prepare("SELECT * FROM orgs WHERE id=?").bind(oid).first(); if (!o) return null;
  const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results || [];
  return { type: "o", id: o.id, handle: o.handle, name: o.name, tagline: o.tagline, about: o.about, website: o.website, country: o.country, size: o.size, public: !!o.public,
    expertise: (await q("SELECT eid e,level,verified FROM expertise WHERE owner_type='o' AND owner_id=?", oid)).map((e) => ({ ...e, verified: !!e.verified })),
    programs: (await q("SELECT program p,year,url,verified FROM programs WHERE owner_type='o' AND owner_id=?", oid)).map((x) => ({ ...x, verified: !!x.verified })),
    channels: await q("SELECT kind,url,feed FROM channels WHERE owner_type='o' AND owner_id=?", oid),
    members: await q("SELECT p.handle,u.name,m.role,p.headline FROM org_members m JOIN users u ON u.id=m.user_id AND u.banned=0 JOIN profiles p ON p.user_id=m.user_id AND p.public=1 AND p.show_org=1 WHERE m.org_id=? AND m.status='active' ORDER BY m.role='owner' DESC, u.name", oid),
    items: await itemsOf(db, "i.owner_type='o' AND i.owner_id=?", [oid], viewer, 8) };
}

async function replaceLists(db, t, id, { exp, prog, chan, certs }) {
  const ops = [db.prepare("DELETE FROM expertise WHERE owner_type=? AND owner_id=? AND eid NOT IN (SELECT value FROM json_each(?))").bind(t, id, JSON.stringify(exp.map((x) => x.e)))];
  for (const x of exp) ops.push(db.prepare("INSERT INTO expertise(owner_type,owner_id,eid,level) VALUES(?,?,?,?) ON CONFLICT(owner_type,owner_id,eid) DO UPDATE SET level=excluded.level").bind(t, id, x.e, x.level));
  ops.push(db.prepare("DELETE FROM programs WHERE owner_type=? AND owner_id=? AND program NOT IN (SELECT value FROM json_each(?))").bind(t, id, JSON.stringify(prog.map((x) => x.p))));
  for (const x of prog) ops.push(db.prepare("INSERT INTO programs(owner_type,owner_id,program,year,url) VALUES(?,?,?,?,?) ON CONFLICT(owner_type,owner_id,program) DO UPDATE SET year=excluded.year, url=excluded.url, verified=CASE WHEN programs.url=excluded.url THEN programs.verified ELSE 0 END").bind(t, id, x.p, x.year, x.url));
  ops.push(db.prepare("DELETE FROM channels WHERE owner_type=? AND owner_id=? AND url NOT IN (SELECT value FROM json_each(?))").bind(t, id, JSON.stringify(chan.map((x) => x.url))));
  for (const x of chan) ops.push(db.prepare("INSERT INTO channels(owner_type,owner_id,kind,url,feed) VALUES(?,?,?,?,?) ON CONFLICT(owner_type,owner_id,url) DO UPDATE SET kind=excluded.kind, feed=excluded.feed, fails=0").bind(t, id, x.kind, x.url, x.feed));
  if (certs) {
    ops.push(db.prepare("DELETE FROM certs WHERE user_id=?").bind(id));
    for (const x of certs) ops.push(db.prepare("INSERT INTO certs(user_id,eid,year,url) VALUES(?,?,?,?)").bind(id, x.e, x.year, x.url));
  }
  await db.batch(ops);
}

export async function handleProfiles(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m;
  const need = () => (user ? null : J({ error: "login" }, 401));
  const body = async () => await request.json().catch(() => ({}));

  // ---- eigenes Profil ----
  if (path === "/api/profile/me" && method === "GET") {
    if (need()) return need();
    const v = await personView(db, user.id, user.id);
    const orgs = (await db.prepare("SELECT o.handle,o.name,m.role,m.status FROM org_members m JOIN orgs o ON o.id=m.org_id WHERE m.user_id=?").bind(user.id).all()).results || [];
    return J({ profile: v, suggest: slug(user.name), orgs });
  }
  if (path === "/api/profile/me" && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `prof:${user.id}`, 20, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await body();
    let handle = String(b.handle || "").toLowerCase().trim(); const isPublic = b.public ? 1 : 0;
    if (handle && !HANDLE.test(handle)) return J({ error: "bad_handle" }, 400);
    if (isPublic && !handle) return J({ error: "bad_handle" }, 400);
    const taken = handle ? await db.prepare("SELECT user_id FROM profiles WHERE handle=? AND user_id<>?").bind(handle, user.id).first() : null;
    if (taken || (handle && (await db.prepare("SELECT 1 x FROM orgs WHERE handle=?").bind(handle).first()))) return J({ error: "handle_taken" }, 409);
    const ch = await checkChannels(b.channels); if (ch.err) return J({ error: ch.err }, 400);
    const ex = await checkExpertise(env, b.expertise); if (ex.err) return J({ error: ex.err }, 400);
    const pr = checkPrograms(b.programs, false); if (pr.err) return J({ error: pr.err }, 400);
    const known = await baseIds(env), certs = [];
    for (const c of (Array.isArray(b.certs) ? b.certs : []).slice(0, 20)) {
      const u = cleanUrl(c?.url, null); if (!ID.test(c?.e || "") || !known.has(c.e) || u === null) return J({ error: "bad_cert" }, 400);
      certs.push({ e: c.e, year: Math.min(2100, Math.max(0, parseInt(c.year) || 0)), url: u });
    }
    await db.prepare(`INSERT INTO profiles(user_id,public,handle,headline,about,company,job,country,show_org,updated) VALUES(?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(user_id) DO UPDATE SET public=excluded.public,handle=excluded.handle,headline=excluded.headline,about=excluded.about,company=excluded.company,job=excluded.job,country=excluded.country,show_org=excluded.show_org,updated=excluded.updated`)
      .bind(user.id, isPublic, handle || null, txt(b.headline, 100), long(b.about, 1500), txt(b.company, 80), txt(b.job, 80), txt(b.country, 60), b.show_org === false ? 0 : 1, now()).run();
    await replaceLists(db, "u", user.id, { exp: ex.list, prog: pr.list, chan: ch.list, certs });
    return J({ ok: true });
  }
  if ((m = /^\/api\/profile\/([a-z0-9-]{3,30})$/.exec(path)) && method === "GET") {
    const r = await db.prepare("SELECT user_id,public FROM profiles WHERE handle=?").bind(m[1]).first();
    if (!r || (!r.public && r.user_id !== user?.id)) return J({ error: "not_found" }, 404);
    const v = await personView(db, r.user_id, user?.id); if (!v) return J({ error: "not_found" }, 404);
    v.mine = r.user_id === user?.id; delete v.id; return J({ profile: v }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/profiles/export" && method === "GET") {   // oeffentlich: fuer den statischen Seitenbau
    const us = (await db.prepare("SELECT user_id FROM profiles WHERE public=1 AND handle IS NOT NULL ORDER BY updated DESC LIMIT 300").all()).results || [];
    const os = (await db.prepare("SELECT id FROM orgs WHERE public=1 ORDER BY created DESC LIMIT 200").all()).results || [];
    const people = [], orgs = [];
    for (const u of us) { const v = await personView(db, u.user_id, 0); if (v) { delete v.id; people.push(v); } }
    for (const o of os) { const v = await orgView(db, o.id, 0); if (v) { delete v.id; orgs.push(v); } }
    return J({ people, orgs }, 200, { "cache-control": "public, max-age=300" });
  }

  // ---- Bestaetigung durch andere (Endorsements), Upvotes ----
  if (path === "/api/endorse" && (method === "POST" || method === "DELETE")) {
    if (need()) return need();
    const b = await body(); const o = await resolve(db, "u:" + b.handle);
    if (!o || !ID.test(b.e || "") || o.id === user.id) return J({ error: "bad_request" }, 400);
    if (!(await db.prepare("SELECT 1 x FROM expertise WHERE owner_type='u' AND owner_id=? AND eid=?").bind(o.id, b.e).first())) return J({ error: "not_found" }, 404);
    if (method === "POST") {
      if (!(await rateLimit(db, `endorse:${user.id}`, 30, 86400))) return J({ error: "rate_limit" }, 429);
      await db.prepare("INSERT OR IGNORE INTO endorsements(owner_id,eid,by_id,created) VALUES(?,?,?,?)").bind(o.id, b.e, user.id, now()).run();
    } else await db.prepare("DELETE FROM endorsements WHERE owner_id=? AND eid=? AND by_id=?").bind(o.id, b.e, user.id).run();
    return J({ ok: true });
  }
  if ((m = /^\/api\/vote\/(\d+)$/.exec(path)) && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `vote:${user.id}`, 120, 3600))) return J({ error: "rate_limit" }, 429);
    const id = +m[1]; if (!(await db.prepare("SELECT 1 x FROM feed_items WHERE id=? AND hidden=0").bind(id).first())) return J({ error: "not_found" }, 404);
    const has = await db.prepare("SELECT 1 x FROM item_votes WHERE item_id=? AND user_id=?").bind(id, user.id).first();
    if (has) await db.prepare("DELETE FROM item_votes WHERE item_id=? AND user_id=?").bind(id, user.id).run(); else await db.prepare("INSERT INTO item_votes(item_id,user_id,created) VALUES(?,?,?)").bind(id, user.id, now()).run();
    return J({ ok: true, voted: !has, votes: (await db.prepare("SELECT COUNT(*) n FROM item_votes WHERE item_id=?").bind(id).first()).n });
  }
  if (path === "/api/feed" && method === "GET") {   // Neuestes der Creator (nur oeffentliche Profile/Firmen)
    const sort = url.searchParams.get("sort") === "top" ? "votes" : "published";
    const rows = (await db.prepare(`SELECT i.id FROM feed_items i WHERE i.hidden=0 AND ((i.owner_type='u' AND i.owner_id IN (SELECT p.user_id FROM profiles p JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.public=1)) OR (i.owner_type='o' AND i.owner_id IN (SELECT id FROM orgs WHERE public=1)))
       ${sort === "votes" ? "AND i.published>" + (now() - 30 * 86400) : ""} ORDER BY ${sort === "votes" ? "(SELECT COUNT(*) FROM item_votes v WHERE v.item_id=i.id) DESC, i.published" : "i.published"} DESC LIMIT 30`).all()).results || [];
    const ids = rows.map((r) => r.id); if (!ids.length) return J({ items: [] });
    const items = await itemsOf(db, `i.id IN (${ids.join(",")})`, [], user?.id, 30);
    const order = new Map(ids.map((x, i) => [x, i])); items.sort((a, b) => order.get(a.id) - order.get(b.id));
    const names = new Map();
    for (const it of items) { const [t, id] = it.owner.split(":"); const k = it.owner; if (!names.has(k)) names.set(k, t === "u" ? await db.prepare("SELECT p.handle,u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=?").bind(+id).first() : await db.prepare("SELECT handle,name FROM orgs WHERE id=?").bind(+id).first()); const n = names.get(k) || {}; it.by = n.name || ""; it.ref = t + ":" + (n.handle || ""); delete it.owner; }
    return J({ items }, 200, { "cache-control": "no-store" });
  }

  // ---- Firmen ----
  if (path === "/api/org/mine" && method === "GET") {
    if (need()) return need();
    const rows = (await db.prepare("SELECT o.id,o.handle,o.name,m.role,m.status FROM org_members m JOIN orgs o ON o.id=m.org_id WHERE m.user_id=?").bind(user.id).all()).results || [];
    const out = [];
    for (const r of rows) {
      const v = r.status === "active" ? await orgView(db, r.id, user.id) : null;
      const pend = r.status === "active" && ["owner", "admin"].includes(r.role) ? (await db.prepare("SELECT m.user_id,u.name FROM org_members m JOIN users u ON u.id=m.user_id WHERE m.org_id=? AND m.status='pending'").bind(r.id).all()).results || [] : [];
      const team = r.status === "active" && ["owner", "admin"].includes(r.role) ? (await db.prepare("SELECT m.user_id,u.name,m.role FROM org_members m JOIN users u ON u.id=m.user_id WHERE m.org_id=? AND m.status='active'").bind(r.id).all()).results || [] : [];
      out.push({ handle: r.handle, name: r.name, role: r.role, status: r.status, org: v, pending: pend, team });
    }
    return J({ orgs: out });
  }
  if (path === "/api/org" && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `org:${user.id}`, 20, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await body(), handle = String(b.handle || "").toLowerCase().trim(); if (!HANDLE.test(handle)) return J({ error: "bad_handle" }, 400);
    const name = txt(b.name, 80); if (name.length < 2) return J({ error: "bad_name" }, 400);
    const website = cleanUrl(b.website, null); if (website === null) return J({ error: "bad_url" }, 400);
    const ch = await checkChannels(b.channels); if (ch.err) return J({ error: ch.err }, 400);
    const ex = await checkExpertise(env, b.expertise); if (ex.err) return J({ error: ex.err }, 400);
    const pr = checkPrograms(b.programs, true); if (pr.err) return J({ error: pr.err }, 400);
    const size = SIZES.includes(b.size) ? b.size : "";
    let o = await db.prepare("SELECT id FROM orgs WHERE handle=?").bind(handle).first();
    if (!o) {
      if (await db.prepare("SELECT 1 x FROM profiles WHERE handle=?").bind(handle).first()) return J({ error: "handle_taken" }, 409);
      if ((await db.prepare("SELECT COUNT(*) n FROM org_members WHERE user_id=? AND role='owner'").bind(user.id).first()).n >= 3) return J({ error: "limit" }, 400);
      const r = await db.prepare("INSERT INTO orgs(handle,name,tagline,about,website,country,size,public,created) VALUES(?,?,?,?,?,?,?,?,?)").bind(handle, name, txt(b.tagline, 120), long(b.about, 1500), website, txt(b.country, 60), size, b.public ? 1 : 0, now()).run();
      o = { id: r.meta.last_row_id };
      await db.prepare("INSERT INTO org_members(org_id,user_id,role,status,created) VALUES(?,?,'owner','active',?)").bind(o.id, user.id, now()).run();
    } else {
      const mem = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=? AND status='active'").bind(o.id, user.id).first();
      if (!mem || !["owner", "admin"].includes(mem.role)) return J({ error: "forbidden" }, 403);
      await db.prepare("UPDATE orgs SET name=?,tagline=?,about=?,website=?,country=?,size=?,public=? WHERE id=?").bind(name, txt(b.tagline, 120), long(b.about, 1500), website, txt(b.country, 60), size, b.public ? 1 : 0, o.id).run();
    }
    await replaceLists(db, "o", o.id, { exp: ex.list, prog: pr.list, chan: ch.list, certs: null });
    return J({ ok: true });
  }
  if ((m = /^\/api\/org\/([a-z0-9-]{3,30})$/.exec(path)) && method === "GET") {
    const o = await db.prepare("SELECT id,public FROM orgs WHERE handle=?").bind(m[1]).first(); if (!o) return J({ error: "not_found" }, 404);
    const mem = user ? await db.prepare("SELECT 1 x FROM org_members WHERE org_id=? AND user_id=? AND status='active'").bind(o.id, user.id).first() : null;
    if (!o.public && !mem) return J({ error: "not_found" }, 404);
    const v = await orgView(db, o.id, user?.id); delete v.id; return J({ org: v }, 200, { "cache-control": "no-store" });
  }
  if ((m = /^\/api\/org\/([a-z0-9-]{3,30})\/(join|leave|member)$/.exec(path)) && method === "POST") {
    if (need()) return need();
    const o = await db.prepare("SELECT id,public FROM orgs WHERE handle=?").bind(m[1]).first(); if (!o) return J({ error: "not_found" }, 404);
    if (m[2] === "join") {
      if (!(await rateLimit(db, `join:${user.id}`, 10, 86400))) return J({ error: "rate_limit" }, 429);
      await db.prepare("INSERT OR IGNORE INTO org_members(org_id,user_id,role,status,created) VALUES(?,?,'member','pending',?)").bind(o.id, user.id, now()).run(); return J({ ok: true });
    }
    if (m[2] === "leave") {
      const me = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=?").bind(o.id, user.id).first();
      if (me?.role === "owner" && (await db.prepare("SELECT COUNT(*) n FROM org_members WHERE org_id=? AND role='owner' AND status='active'").bind(o.id).first()).n < 2) return J({ error: "last_owner" }, 400);
      await db.prepare("DELETE FROM org_members WHERE org_id=? AND user_id=?").bind(o.id, user.id).run(); return J({ ok: true });
    }
    const me = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=? AND status='active'").bind(o.id, user.id).first();
    if (!me || !["owner", "admin"].includes(me.role)) return J({ error: "forbidden" }, 403);
    const b = await body(), target = +b.user_id; if (!target) return J({ error: "bad_request" }, 400);
    const tr = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=?").bind(o.id, target).first(); if (!tr) return J({ error: "not_found" }, 404);
    if (b.action === "approve") await db.prepare("UPDATE org_members SET status='active' WHERE org_id=? AND user_id=?").bind(o.id, target).run();
    else if (b.action === "remove" && tr.role !== "owner") await db.prepare("DELETE FROM org_members WHERE org_id=? AND user_id=?").bind(o.id, target).run();
    else if ((b.action === "admin" || b.action === "member") && me.role === "owner" && tr.role !== "owner") await db.prepare("UPDATE org_members SET role=? WHERE org_id=? AND user_id=?").bind(b.action, o.id, target).run();
    else return J({ error: "bad_request" }, 400);
    return J({ ok: true });
  }
  if (path === "/api/orgs/search" && method === "GET") {
    const q = String(url.searchParams.get("q") || "").toLowerCase().replace(/[^a-z0-9 -]/g, "").trim(); if (q.length < 2) return J({ items: [] });
    const rows = (await db.prepare("SELECT handle,name FROM orgs WHERE public=1 AND (handle LIKE ? OR lower(name) LIKE ?) LIMIT 8").bind(q + "%", "%" + q + "%").all()).results || [];
    return J({ items: rows });
  }

  // ---- Bestaetigen durch Editor/Admin ----
  if (path === "/api/admin/verify" && method === "POST") {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    const b = await body(), o = await resolve(db, b.owner); if (!o) return J({ error: "not_found" }, 404);
    const v = b.value ? 1 : 0;
    if (b.kind === "program" && PROGRAMS.includes(b.key)) await db.prepare("UPDATE programs SET verified=? WHERE owner_type=? AND owner_id=? AND program=?").bind(v, o.t, o.id, b.key).run();
    else if (b.kind === "exp" && ID.test(b.key || "")) await db.prepare("UPDATE expertise SET verified=? WHERE owner_type=? AND owner_id=? AND eid=?").bind(v, o.t, o.id, b.key).run();
    else return J({ error: "bad_request" }, 400);
    return J({ ok: true });
  }
  if (path === "/api/admin/feed-hide" && method === "POST") {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    const b = await body(); await db.prepare("UPDATE feed_items SET hidden=? WHERE id=?").bind(b.hidden ? 1 : 0, +b.id).run(); return J({ ok: true });
  }
  return null;
}

// Konto loeschen: alle Profil-, Firmen- und Entitaetsdaten des Nutzers entfernen bzw. anonymisieren
export async function deleteUserData(db, id) {
  const own = (await db.prepare("SELECT org_id FROM org_members WHERE user_id=? AND role='owner'").bind(id).all()).results || [];
  const ops = [];
  for (const o of own) {
    const other = await db.prepare("SELECT user_id FROM org_members WHERE org_id=? AND user_id<>? AND status='active' ORDER BY role='admin' DESC, created LIMIT 1").bind(o.org_id, id).first();
    if (other) ops.push(db.prepare("UPDATE org_members SET role='owner' WHERE org_id=? AND user_id=?").bind(o.org_id, other.user_id));
    else ops.push(db.prepare("DELETE FROM expertise WHERE owner_type='o' AND owner_id=?").bind(o.org_id), db.prepare("DELETE FROM programs WHERE owner_type='o' AND owner_id=?").bind(o.org_id),
      db.prepare("DELETE FROM item_votes WHERE item_id IN (SELECT id FROM feed_items WHERE owner_type='o' AND owner_id=?)").bind(o.org_id), db.prepare("DELETE FROM feed_items WHERE owner_type='o' AND owner_id=?").bind(o.org_id),
      db.prepare("DELETE FROM channels WHERE owner_type='o' AND owner_id=?").bind(o.org_id), db.prepare("DELETE FROM org_members WHERE org_id=?").bind(o.org_id), db.prepare("DELETE FROM orgs WHERE id=?").bind(o.org_id));
  }
  ops.push(
    db.prepare("DELETE FROM org_members WHERE user_id=?").bind(id),
    db.prepare("DELETE FROM item_votes WHERE user_id=? OR item_id IN (SELECT id FROM feed_items WHERE owner_type='u' AND owner_id=?)").bind(id, id),
    db.prepare("DELETE FROM feed_items WHERE owner_type='u' AND owner_id=?").bind(id), db.prepare("DELETE FROM channels WHERE owner_type='u' AND owner_id=?").bind(id),
    db.prepare("DELETE FROM expertise WHERE owner_type='u' AND owner_id=?").bind(id), db.prepare("DELETE FROM programs WHERE owner_type='u' AND owner_id=?").bind(id),
    db.prepare("DELETE FROM certs WHERE user_id=?").bind(id), db.prepare("DELETE FROM endorsements WHERE owner_id=? OR by_id=?").bind(id, id),
    db.prepare("DELETE FROM profiles WHERE user_id=?").bind(id),
    db.prepare("DELETE FROM entity_rev WHERE user_id=? AND status IN ('pending','rejected')").bind(id), db.prepare("UPDATE entity_rev SET user_id=0 WHERE user_id=?").bind(id));
  await db.batch(ops);
}
