// Experten- und Firmenprofile, Programme (MVP/MCT/...), Kanaele mit Feeds, Upvotes, Bestaetigungen
import { cleanKeypoints, cleanFaq, jsonList, ensureSectionCols } from "./sections.js";
import { sanitize } from "./wiki.js";
import { cleanText, rateLimit } from "./util.js";
import { baseIds, knownIds, validate, trustedUser, entityMap } from "./entities.js";
import { findExperts } from "./experts.js";

export const PROGRAMS = ["mvp", "mct", "rd", "msa", "ms_employee", "partner"];
export const RELATIONS = ["colleague", "manager", "report", "client", "trainer", "student", "cospeaker", "podcast", "community", "mentor", "other"];
export const KINDS = ["linkedin", "github", "youtube", "x", "mastodon", "bluesky", "twitch", "spotify", "apple", "amazon", "deezer", "instagram", "tiktok", "facebook", "blog", "podcast", "newsletter", "website", "other"];
const KIND_HOST = { linkedin: /(^|\.)linkedin\.com$/, github: /(^|\.)github\.com$/, youtube: /(^|\.)(youtube\.com|youtu\.be)$/, x: /(^|\.)(x\.com|twitter\.com)$/, twitch: /(^|\.)twitch\.tv$/, bluesky: /(^|\.)bsky\.app$/, spotify: /(^|\.)spotify\.com$/, apple: /(^|\.)(podcasts|music)\.apple\.com$/, amazon: /(^|\.)(music\.amazon\.[a-z.]+|audible\.[a-z.]+)$/, deezer: /(^|\.)deezer\.com$/, instagram: /(^|\.)instagram\.com$/, tiktok: /(^|\.)tiktok\.com$/, facebook: /(^|\.)(facebook\.com|fb\.com)$/ };
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
// Selbst verwaltete Entitaet (Profil, Firma, Event): gleiche Struktur wie jede Entitaet, aber der Eigentuemer pflegt sie ueber seinen eigenen Bereich
export async function ownedEntity(env, user, o) {
  const db = env.DB; try {
    if (!ID.test(o.eid)) return "";
    const known = (await baseIds(env)).has(o.eid), ex = await db.prepare("SELECT 1 x FROM entity_rev WHERE eid=? AND status IN ('live','pending')").bind(o.eid).first();
    let created = false;
    if (!known && !ex) {
      const v = await validate(env, o.eid, { name: o.name, type: o.type, desc: { en: o.en, de: o.de }, web: o.web || "", rel: [] });
      if (v.err) return "";
      await db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,'live',?)").bind(o.eid, JSON.stringify(v.data), "Selbst verwaltet", user.id, now()).run(); created = true;
    }
    if (created || user.admin) await db.prepare("INSERT INTO entity_claims(eid,user_id,status,via,created) VALUES(?,?,'verified','owner',?) ON CONFLICT(eid) DO NOTHING").bind(o.eid, user.id, now()).run();
    return o.eid;
  } catch (e) { return ""; }
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
    const fo = Math.max(0, Math.min(2e9, parseInt(c.followers, 10) || 0));
    if (!seen.has(url)) { seen.add(url); out.push({ kind: c.kind, url, feed, followers: fo }); }
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

// Zertifikats-Nachweis: automatische Pruefung fuer Credly / Microsoft Learn (Seite muss Zertifikat und Namen des Mitglieds nennen). Sonst Pruefung durch die Redaktion.
export async function autoVerifyCert(url, ent, name) {
  try {
    const u = new URL(url);
    if (u.protocol !== "https:" || !/^(www\.)?(credly|youracclaim)\.com$|^learn\.microsoft\.com$/i.test(u.hostname)) return false;
    const r = await fetch(url, { redirect: "manual", signal: AbortSignal.timeout(6000), headers: { "user-agent": "Mozilla/5.0 (compatible; M365FM-CertCheck/1.0)", accept: "text/html" } });
    if (r.status !== 200) return false;
    const text = (await r.text()).slice(0, 500000).toLowerCase();
    const code = ((ent?.aliases || [])[0] || "").toLowerCase(), title = String(ent?.name || "").toLowerCase().replace(/\s*\([^)]*\)\s*/g, "").trim();
    const tokens = String(name || "").toLowerCase().split(/\s+/).filter((t) => t.length > 1);
    return !!tokens.length && tokens.every((t) => text.includes(t)) && ((code && text.includes(code)) || (title.length > 8 && text.includes(title)));
  } catch { return false; }
}

// Bestaetigte (abgeleitete) Expertise: Themen aus bestaetigten Speaker-Sessions und aus geprueften Zertifikaten - nicht selbst gewaehlt
const TOPIC_T = ["product", "platform", "concept", "category"];
// via: session (bestaetigte Session), cert (geprueftes Zertifikat), post (eigene veroeffentlichte Beitraege zum Thema)
export async function derivedExpertise(db, uid, handle, map, pre) {
  const out = new Map();
  const nm = ((await db.prepare("SELECT lower(name) n FROM users WHERE id=?").bind(uid).first())?.n) || "";
  const rows = pre || (await db.prepare("SELECT s.topics,s.speakers,e.owner_id oid FROM event_sessions s JOIN events e ON e.id=s.event_id WHERE s.status='live' AND s.topics<>'[]'").all()).results || [];   // pre: im Export einmal fuer alle Profile geladen
  for (const r of rows) {
    let sp = [], tp = []; try { sp = JSON.parse(r.speakers || "[]"); tp = JSON.parse(r.topics || "[]"); } catch { continue; }
    // zaehlt: per Handle oder Name zugeordnet; bestaetigt, oder vom Veranstalter selbst (Organisator nimmt seine eigene Session an)
    if (!sp.some((x) => ((handle && x.h === handle) || (!x.h && nm && String(x.n || "").toLowerCase() === nm)) && (x.s === "confirmed" || r.oid === uid))) continue;
    for (const t of tp) { const o = out.get(t) || { via: "session", n: 0 }; o.n++; out.set(t, o); }
  }
  // Themen (Entitaeten) der eigenen veroeffentlichten Community-Beitraege: Blog, Bibliothek, Podcast, Video, Gaeste-Boerse
  const posts = (await db.prepare("SELECT topics FROM blog_posts WHERE user_id=?1 AND status='live' UNION ALL SELECT b.topics FROM blog_coauthors c JOIN blog_posts b ON b.id=c.post_id WHERE c.user_id=?1 AND c.status='confirmed' AND b.status='live' UNION ALL SELECT e.topics FROM item_guests g JOIN pod_episodes e ON g.kind='podcast' AND e.id=g.item_id WHERE g.user_id=?1 AND g.status='confirmed' AND e.status='published' UNION ALL SELECT v.topics FROM item_guests g JOIN yt_videos v ON g.kind='video' AND v.id=g.item_id WHERE g.user_id=?1 AND g.status='confirmed' AND v.status='published' UNION ALL SELECT topics FROM lib_items WHERE user_id=?1 AND status='live' UNION ALL SELECT topics FROM pod_episodes WHERE user_id=?1 AND status='published' UNION ALL SELECT topics FROM yt_videos WHERE user_id=?1 AND status='published' UNION ALL SELECT topics FROM guest_listings WHERE user_id=?1 AND active=1").bind(uid).all()).results || [];
  for (const r of posts) { let tp = []; try { tp = JSON.parse(r.topics || "[]"); } catch { continue; } for (const t of tp) if (map.has(t) && !out.has(t)) out.set(t, { via: "post", n: 1 }); else if (out.has(t) && out.get(t).via === "post") out.get(t).n++; }
  const certs = ((await db.prepare("SELECT c.eid FROM certs c JOIN cert_check k ON k.user_id=c.user_id AND k.eid=c.eid WHERE c.user_id=? AND k.status='verified'").bind(uid).all()).results || []).map((r) => r.eid);
  for (const c of certs) for (const [, to] of (map.get(c)?.rel || [])) if (TOPIC_T.includes(map.get(to)?.type) && !out.has(to)) out.set(to, { via: "cert", n: 1 });
  return out;
}

// Uebersetzungen von Kurzzeile und Bio (Sprachcode -> {headline, about}); Grundtext bleibt in profiles
const LANG = /^[a-z]{2}(-[A-Z]{2})?$/;
export function cleanI18n(raw) {
  const out = {};
  if (raw && typeof raw === "object") for (const [l, v] of Object.entries(raw).slice(0, 30)) if (LANG.test(l) && v && typeof v === "object") { const h = txt(v.headline, 100), a = long(v.about, 1500); if (h || a) out[l] = { headline: h, about: a }; }
  return out;
}
export async function saveI18n(db, uid, map) {
  await db.prepare("DELETE FROM profile_i18n WHERE user_id=?").bind(uid).run();
  for (const [l, v] of Object.entries(map)) await db.prepare("INSERT INTO profile_i18n(user_id,lang,headline,about,updated) VALUES(?,?,?,?,?)").bind(uid, l, v.headline, v.about, now()).run();
}
export async function readI18n(db, uid) {
  const r = (await db.prepare("SELECT lang,headline,about FROM profile_i18n WHERE user_id=?").bind(uid).all()).results || [], o = {};
  for (const x of r) o[x.lang] = { headline: x.headline, about: x.about };
  return o;
}

// Rollen in Firmen: owner (alles) > admin (Mitglieder + Profil) > editor (Profil) / events (Events und Sponsoring) > member
const ORG_ROLES = ["owner", "admin", "editor", "events", "member"];
const assignable = (mine, role) => ORG_ROLES.includes(role) && (mine === "owner" || (mine === "admin" && ["editor", "events", "member"].includes(role)));

async function personView(db, uid, viewer) {
  const p = await db.prepare("SELECT p.*,u.name,u.bio FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=? AND u.banned=0").bind(uid).first(); if (!p) return null;
  const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results || [];
  const exp = await q("SELECT e.eid e,e.level,e.verified,(SELECT COUNT(*) FROM endorsements n WHERE n.owner_id=e.owner_id AND n.eid=e.eid) endorsed, (SELECT COUNT(*) FROM endorsements n2 WHERE n2.owner_id=e.owner_id AND n2.eid=e.eid AND n2.by_id=?) me FROM expertise e WHERE e.owner_type='u' AND e.owner_id=? ORDER BY e.verified DESC,e.level DESC", +viewer || 0, uid);
  const programs = await q("SELECT program p,year,url,verified FROM programs WHERE owner_type='u' AND owner_id=?", uid);
  const certs = (await q("SELECT c.eid e,c.year,c.url,COALESCE(k.status,'') st,(SELECT COUNT(*) FROM cert_endorse n WHERE n.owner_id=c.user_id AND n.eid=c.eid) endorsed,(SELECT COUNT(*) FROM cert_endorse n2 WHERE n2.owner_id=c.user_id AND n2.eid=c.eid AND n2.by_id=?) me FROM certs c LEFT JOIN cert_check k ON k.user_id=c.user_id AND k.eid=c.eid WHERE c.user_id=? ORDER BY endorsed DESC, (k.status='verified') DESC, c.year DESC", +viewer || 0, uid)).map((x) => ({ e: x.e, year: x.year, url: x.url, verified: x.st === "verified", pending: x.st === "pending", rejected: x.st === "rejected", endorsed: x.endorsed, me: !!x.me }));
  const channels = await q("SELECT kind,url,feed,followers FROM channels WHERE owner_type='u' AND owner_id=?", uid);
  const org = p.show_org ? await db.prepare("SELECT o.handle,o.name FROM org_members m JOIN orgs o ON o.id=m.org_id WHERE m.user_id=? AND m.status='active' AND o.public=1 ORDER BY m.created LIMIT 1").bind(uid).first() : null;
  const contrib = [...(await q("SELECT 'wiki' k,term t,lang l,summary s,created c FROM wiki_rev WHERE user_id=? AND status IN ('live','old') ORDER BY created DESC LIMIT 15", uid)),
    ...(await q("SELECT 'entity' k,eid t,'' l,summary s,created c FROM entity_rev WHERE user_id=? AND status IN ('live','old') ORDER BY created DESC LIMIT 15", uid))].sort((a, b) => b.c - a.c).slice(0, 15);
  const counts = { wiki: (await db.prepare("SELECT COUNT(*) n FROM wiki_rev WHERE user_id=? AND status IN ('live','old')").bind(uid).first()).n, entity: (await db.prepare("SELECT COUNT(*) n FROM entity_rev WHERE user_id=? AND status IN ('live','old')").bind(uid).first()).n };
  const badges = (await q("SELECT badge FROM user_badges WHERE user_id=?", uid)).map((b) => b.badge);
  const recs = (await q("SELECT r.id,r.relation,r.body,r.created,u.name,(SELECT handle FROM profiles WHERE user_id=r.author_id AND public=1) h FROM recommendations r JOIN users u ON u.id=r.author_id AND u.banned=0 WHERE r.subject_id=? AND r.status='live' ORDER BY r.created DESC LIMIT 30", uid)).map((r) => ({ id: r.id, relation: r.relation, body: r.body, created: r.created, by: { name: r.name, handle: r.h || "" } }));
  const im = await db.prepare("SELECT updated FROM images WHERE kind='u' AND owner_id=?").bind(uid).first();
  const pce = (await db.prepare("SELECT eid FROM profile_company WHERE user_id=?").bind(uid).first())?.eid || "";
  const pv = await db.prepare("SELECT * FROM profile_private WHERE user_id=?").bind(uid).first(), CF = ["city", "zip", "street", "email", "phone"];
  const contact = {}; let priv = null;
  if (pv) { for (const k of CF) if (pv["vis_" + k] === "all" && pv[k]) contact[k] = pv[k]; if (+viewer === uid) priv = Object.fromEntries([...CF.map((k) => [k, pv[k]]), ...CF.map((k) => ["vis_" + k, pv["vis_" + k]])]); }
  return { type: "u", i18n: await readI18n(db, uid), contact, ...(priv ? { private: priv } : {}), img: im?.updated || 0, company_eid: pce, id: uid, handle: p.handle, name: p.name, bio: p.bio, headline: p.headline, about: p.about, company: p.company, job: p.job, country: p.country, public: !!p.public, show_org: !!p.show_org,
    expertise: exp.map((e) => ({ ...e, verified: !!e.verified, me: !!e.me })), programs: programs.map((x) => ({ ...x, verified: !!x.verified })), certs, channels, org, contrib, counts, badges, recs,
    items: await itemsOf(db, "i.owner_type='u' AND i.owner_id=?", [uid], viewer, 8) };
}
export async function ensureFeedCols(db) {
  try { await db.prepare("SELECT summary,thumb,body,topics FROM feed_items LIMIT 1").first(); } catch {
    for (const c of ["summary TEXT NOT NULL DEFAULT ''", "thumb TEXT NOT NULL DEFAULT ''", "body TEXT NOT NULL DEFAULT ''", "topics TEXT NOT NULL DEFAULT '[]'", "seo_at INTEGER NOT NULL DEFAULT 0"]) { try { await db.prepare("ALTER TABLE feed_items ADD COLUMN " + c).run(); } catch {} }
  }
}
let colsOk = false;
async function ensureCols(db) {
  if (colsOk) return;
  try { await db.prepare("SELECT followers FROM channels LIMIT 1").first(); } catch { for (const c of ["followers INTEGER NOT NULL DEFAULT 0", "followers_at INTEGER NOT NULL DEFAULT 0"]) { try { await db.prepare("ALTER TABLE channels ADD COLUMN " + c).run(); } catch {} } }
  try { await db.prepare("CREATE TABLE IF NOT EXISTS org_ms (org_id INTEGER NOT NULL, area TEXT NOT NULL, level TEXT NOT NULL, since TEXT NOT NULL DEFAULT '', PRIMARY KEY (org_id, area))").run(); } catch {}
  await ensureFeedCols(db);
  colsOk = true;
}
async function orgView(db, oid, viewer) {
  const o = await db.prepare("SELECT * FROM orgs WHERE id=?").bind(oid).first(); if (!o) return null;
  const q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results || [];
  const im = await db.prepare("SELECT updated FROM images WHERE kind='o' AND owner_id=?").bind(oid).first();
  const oe = (await db.prepare("SELECT eid FROM org_entity WHERE org_id=?").bind(oid).first())?.eid || "";
  return { type: "o", eid: oe, img: im?.updated || 0, id: o.id, handle: o.handle, name: o.name, tagline: o.tagline, about: o.about, website: o.website, country: o.country, size: o.size, public: !!o.public,
    expertise: (await q("SELECT eid e,level,verified FROM expertise WHERE owner_type='o' AND owner_id=?", oid)).map((e) => ({ ...e, verified: !!e.verified })),
    programs: (await q("SELECT program p,year,url,verified FROM programs WHERE owner_type='o' AND owner_id=?", oid)).map((x) => ({ ...x, verified: !!x.verified })),
    channels: await q("SELECT kind,url,feed,followers FROM channels WHERE owner_type='o' AND owner_id=?", oid),
    ms: await q("SELECT area,level,since FROM org_ms WHERE org_id=? ORDER BY area", oid),
    members: await q("SELECT p.handle,u.name,m.role,p.headline FROM org_members m JOIN users u ON u.id=m.user_id AND u.banned=0 JOIN profiles p ON p.user_id=m.user_id AND p.public=1 AND p.show_org=1 WHERE m.org_id=? AND m.status='active' ORDER BY m.role='owner' DESC, u.name", oid),
    items: await itemsOf(db, "i.owner_type='o' AND i.owner_id=?", [oid], viewer, 8) };
}

async function replaceLists(db, t, id, { exp, prog, chan, certs }) {
  const ops = [db.prepare("DELETE FROM expertise WHERE owner_type=? AND owner_id=? AND eid NOT IN (SELECT value FROM json_each(?))").bind(t, id, JSON.stringify(exp.map((x) => x.e)))];
  for (const x of exp) ops.push(db.prepare("INSERT INTO expertise(owner_type,owner_id,eid,level) VALUES(?,?,?,?) ON CONFLICT(owner_type,owner_id,eid) DO UPDATE SET level=excluded.level").bind(t, id, x.e, x.level));
  ops.push(db.prepare("DELETE FROM programs WHERE owner_type=? AND owner_id=? AND program NOT IN (SELECT value FROM json_each(?))").bind(t, id, JSON.stringify(prog.map((x) => x.p))));
  for (const x of prog) ops.push(db.prepare("INSERT INTO programs(owner_type,owner_id,program,year,url) VALUES(?,?,?,?,?) ON CONFLICT(owner_type,owner_id,program) DO UPDATE SET year=excluded.year, url=excluded.url, verified=CASE WHEN programs.url=excluded.url THEN programs.verified ELSE 0 END").bind(t, id, x.p, x.year, x.url));
  ops.push(db.prepare("DELETE FROM channels WHERE owner_type=? AND owner_id=? AND url NOT IN (SELECT value FROM json_each(?))").bind(t, id, JSON.stringify(chan.map((x) => x.url))));
  for (const x of chan) ops.push(db.prepare("INSERT INTO channels(owner_type,owner_id,kind,url,feed,followers,followers_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner_type,owner_id,url) DO UPDATE SET followers=excluded.followers, followers_at=CASE WHEN excluded.followers<>channels.followers THEN excluded.followers_at ELSE channels.followers_at END, kind=excluded.kind, feed=CASE WHEN excluded.feed<>'' THEN excluded.feed ELSE channels.feed END, fails=0").bind(t, id, x.kind, x.url, x.feed, x.followers || 0, now()));
  if (certs) {
    ops.push(db.prepare("DELETE FROM certs WHERE user_id=?").bind(id));
    for (const x of certs) ops.push(db.prepare("INSERT INTO certs(user_id,eid,year,url) VALUES(?,?,?,?)").bind(id, x.e, x.year, x.url));
  }
  await db.batch(ops);
}

// Profil-Export fuer den Seitenbau: alle Profile lesen und in D1 zwischenspeichern (Cron alle 30 Minuten), damit der Abruf eine einzige Zeile liest
export async function refreshProfilesExport(env) {
  const db = env.DB;
  await db.prepare("CREATE TABLE IF NOT EXISTS export_cache (k TEXT PRIMARY KEY, v TEXT NOT NULL, updated INTEGER NOT NULL)").run();
    const us = (await db.prepare("SELECT user_id FROM profiles WHERE public=1 AND handle IS NOT NULL ORDER BY updated DESC LIMIT 300").all()).results || [];
    const os = (await db.prepare("SELECT id FROM orgs WHERE public=1 ORDER BY created DESC LIMIT 200").all()).results || [];
    const people = [], orgs = [];
    const emap = await entityMap(env);
    const sess = (await db.prepare("SELECT s.topics,s.speakers,e.owner_id oid FROM event_sessions s JOIN events e ON e.id=s.event_id WHERE s.status='live' AND s.topics<>'[]'").all()).results || [];   // einmal fuer alle Profile
    const one = async (u) => {
      const v = await personView(db, u.user_id, 0); if (!v) return null;
      for (const [eid, d] of await derivedExpertise(db, u.user_id, v.handle, emap, sess)) if (emap.has(eid)) { const ex = v.expertise.find((e) => e.e === eid); if (ex) ex.via = d.via; else v.expertise.push({ e: eid, level: 2, verified: false, endorsed: 0, me: false, via: d.via, confirmed: true }); }   // bestaetigte Expertise aus Sessions/Zertifikaten ergaenzen
      delete v.id; return v;
    };
    for (let k = 0; k < us.length; k += 6) for (const v of await Promise.all(us.slice(k, k + 6).map((u) => one(u).catch(() => null)))) if (v) people.push(v);   // in Gruppen parallel, Reihenfolge bleibt; ein defektes Profil stoppt den Export nicht
    for (const o of os) { const v = await orgView(db, o.id, 0); if (v) { delete v.id; orgs.push(v); } }
  const out = { people, orgs };
  await db.prepare("INSERT INTO export_cache(k,v,updated) VALUES('profiles',?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v,updated=excluded.updated").bind(JSON.stringify(out), now()).run();
  return out;
}

export async function handleProfiles(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m; await ensureCols(db);
  const need = () => (user ? null : J({ error: "login" }, 401));
  const body = async () => await request.json().catch(() => ({}));

  // ---- Sponsoring-Gesuch (privat) ----
  if ((m = path.match(/^\/api\/org\/sponsor\/([a-z0-9-]{2,30})$/))) {
    if (need()) return need();
    const o = await db.prepare("SELECT o.id FROM orgs o JOIN org_members mm ON mm.org_id=o.id WHERE o.handle=? AND mm.user_id=? AND mm.status='active' AND mm.role IN ('owner','admin','editor')").bind(m[1], user.id).first();
    if (!o) return J({ error: "forbidden" }, 403);
    if (method === "GET") {
      const r = await db.prepare("SELECT open,criteria FROM org_sponsor WHERE org_id=?").bind(o.id).first();
      return J({ open: !!r?.open, criteria: r ? JSON.parse(r.criteria || "{}") : {} });
    }
    if (method === "POST") {
      if (!(await rateLimit(db, `spons:${user.id}`, 30, 3600))) return J({ error: "rate_limit" }, 429);
      const b = await body(), c = b.criteria || {};
      const crit = { topics: txt(c.topics, 300), format: ["", "online", "onsite", "hybrid"].includes(c.format) ? c.format : "", min_audience: Math.max(0, Math.min(1e6, +c.min_audience || 0)), regions: txt(c.regions, 200), budget: txt(c.budget, 100), notes: txt(c.notes, 800) };
      await db.prepare("INSERT INTO org_sponsor(org_id,open,criteria,updated) VALUES(?,?,?,?) ON CONFLICT(org_id) DO UPDATE SET open=excluded.open,criteria=excluded.criteria,updated=excluded.updated").bind(o.id, b.open ? 1 : 0, JSON.stringify(crit), Math.floor(Date.now() / 1000)).run();
      return J({ ok: true });
    }
  }

  // ---- Firma als Entitaet anlegen/wiederverwenden ----
  if (path === "/api/profile/company" && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `co:${user.id}`, 5, 86400))) return J({ error: "rate_limit" }, 429);
    const b = await body(), name = txt(b.name, 80); if (name.length < 2) return J({ error: "bad_name" }, 400);
    const id = slug(name).replace(/-+$/g, "") || "firma"; if (id.length < 2) return J({ error: "bad_name" }, 400);
    const known = await baseIds(env);
    const row = await db.prepare("SELECT 1 x FROM entity_rev WHERE eid=? AND status IN ('live','pending')").bind(id).first();
    if (known.has(id) || row) return J({ ok: true, eid: id, existing: true });
    const web = cleanUrl(b.web, null); if (web === null) return J({ error: "bad_url" }, 400);
    const v = await validate(env, id, { name, type: "org", desc: { en: `${name} is a company in the Microsoft ecosystem.`, de: `${name} ist ein Unternehmen im Microsoft-Umfeld.` }, web, rel: [] }); if (v.err) return J({ error: v.err }, 400);
    const st = (await trustedUser(db, user)) ? "live" : "pending";
    await db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,?,?)").bind(id, JSON.stringify(v.data), "Firma über Profil angelegt", user.id, st, now()).run();
    return J({ ok: true, eid: id, status: st });
  }

  // ---- Empfehlungen ----
  if (path === "/api/recommend" && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `rec:${user.id}`, 10, 86400))) return J({ error: "rate_limit" }, 429);
    const b = await body(), handle = String(b.handle || "").toLowerCase();
    const t = await db.prepare("SELECT p.user_id FROM profiles p JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.handle=? AND p.public=1").bind(handle).first();
    if (!t) return J({ error: "not_found" }, 404);
    if (t.user_id === user.id) return J({ error: "self" }, 400);
    if (!RELATIONS.includes(b.relation)) return J({ error: "bad_relation" }, 400);
    const text = long(b.body, 1200); if (text.length < 40) return J({ error: "too_short" }, 400);
    await db.prepare("INSERT INTO recommendations(author_id,subject_id,relation,body,status,created) VALUES(?,?,?,?,'pending',?) ON CONFLICT(author_id,subject_id) DO UPDATE SET relation=excluded.relation,body=excluded.body,status='pending',created=excluded.created").bind(user.id, t.user_id, b.relation, text, now()).run();
    return J({ ok: true, status: "pending" });
  }
  if (path === "/api/recommend/inbox" && method === "GET") {
    if (need()) return need();
    const rows = (await db.prepare("SELECT r.id,r.relation,r.body,r.status,r.created,u.name FROM recommendations r JOIN users u ON u.id=r.author_id WHERE r.subject_id=? ORDER BY r.status='pending' DESC, r.created DESC LIMIT 100").bind(user.id).all()).results || [];
    return J({ items: rows });
  }
  if ((m = path.match(/^\/api\/recommend\/(\d+)$/))) {
    if (need()) return need();
    const r = await db.prepare("SELECT * FROM recommendations WHERE id=?").bind(+m[1]).first(); if (!r) return J({ error: "not_found" }, 404);
    if (method === "POST" && r.subject_id === user.id) { const b = await body(); if (b.ok) await db.prepare("UPDATE recommendations SET status='live' WHERE id=?").bind(r.id).run(); else await db.prepare("DELETE FROM recommendations WHERE id=?").bind(r.id).run(); return J({ ok: true }); }
    if (method === "DELETE" && (r.author_id === user.id || r.subject_id === user.id || user.admin)) { await db.prepare("DELETE FROM recommendations WHERE id=?").bind(r.id).run(); return J({ ok: true }); }
    return J({ error: "forbidden" }, 403);
  }

  // ---- Bilder (Profilbild / Firmenlogo) ----
  if ((m = path.match(/^\/api\/img\/(u|o)\/([a-z0-9-]{2,30})(?:\.jpg)?$/))) {
    const kind = m[1], handle = m[2];
    if (method === "GET") {
      const row = kind === "u"
        ? await db.prepare("SELECT i.data,i.updated FROM images i JOIN profiles p ON p.user_id=i.owner_id AND i.kind='u' JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.handle=? AND p.public=1").bind(handle).first()
        : await db.prepare("SELECT i.data,i.updated FROM images i JOIN orgs o ON o.id=i.owner_id AND i.kind='o' WHERE o.handle=? AND o.public=1").bind(handle).first();
      if (!row) return new Response("not found", { status: 404, headers: { "access-control-allow-origin": "*" } });
      const bin = Uint8Array.from(atob(row.data), (c) => c.charCodeAt(0));
      return new Response(bin, { headers: { "content-type": "image/jpeg", "cache-control": "public, max-age=86400", "access-control-allow-origin": "*", "cross-origin-resource-policy": "cross-origin" } });
    }
    if (method === "POST" || method === "DELETE") {
      if (need()) return need();
      let id;
      if (kind === "u") { const p = await db.prepare("SELECT user_id FROM profiles WHERE user_id=?").bind(user.id).first(); if (!p || (await db.prepare("SELECT handle FROM profiles WHERE user_id=?").bind(user.id).first()).handle !== handle) return J({ error: "forbidden" }, 403); id = user.id; }
      else {
        const o = await db.prepare("SELECT o.id FROM orgs o JOIN org_members m ON m.org_id=o.id WHERE o.handle=? AND m.user_id=? AND m.status='active' AND m.role IN ('owner','admin','editor')").bind(handle, user.id).first();
        if (!o) return J({ error: "forbidden" }, 403); id = o.id;
      }
      if (method === "DELETE") { await db.prepare("DELETE FROM images WHERE kind=? AND owner_id=?").bind(kind, id).run(); return J({ ok: true }); }
      if (!(await rateLimit(db, `img:${user.id}`, 10, 3600))) return J({ error: "rate_limit" }, 429);
      const buf = new Uint8Array(await request.arrayBuffer());
      if (buf.length < 200 || buf.length > 150000) return J({ error: "img_size" }, 400);
      if (!(buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff)) return J({ error: "img_type" }, 400);
      let bin = ""; for (let i = 0; i < buf.length; i += 8192) bin += String.fromCharCode(...buf.subarray(i, i + 8192));
      const now = Math.floor(Date.now() / 1000);
      await db.prepare("INSERT INTO images(kind,owner_id,data,updated) VALUES(?,?,?,?) ON CONFLICT(kind,owner_id) DO UPDATE SET data=excluded.data,updated=excluded.updated").bind(kind, id, btoa(bin), now).run();
      return J({ ok: true, img: now });
    }
  }

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
    const known = await knownIds(env), certs = [];
    for (const c of (Array.isArray(b.certs) ? b.certs : []).slice(0, 20)) {
      const u = cleanUrl(c?.url, null); if (!ID.test(c?.e || "") || !known.has(c.e) || u === null) return J({ error: "bad_cert" }, 400);
      certs.push({ e: c.e, year: Math.min(2100, Math.max(0, parseInt(c.year) || 0)), url: u });
    }
    await db.prepare(`INSERT INTO profiles(user_id,public,handle,headline,about,company,job,country,show_org,updated) VALUES(?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(user_id) DO UPDATE SET public=excluded.public,handle=excluded.handle,headline=excluded.headline,about=excluded.about,company=excluded.company,job=excluded.job,country=excluded.country,show_org=excluded.show_org,updated=excluded.updated`)
      .bind(user.id, isPublic, handle || null, txt(b.headline, 100), long(b.about, 1500), txt(b.company, 80), txt(b.job, 80), txt(b.country, 60), b.show_org === false ? 0 : 1, now()).run();
    await db.prepare("UPDATE users SET bio=? WHERE id=?").bind(txt(b.headline, 100), user.id).run();
    if (b.i18n && typeof b.i18n === "object") await saveI18n(db, user.id, cleanI18n(b.i18n));
    const ce = String(b.company_eid || "").toLowerCase();
    if (ce) { if (ID.test(ce) && ((await baseIds(env)).has(ce) || (await db.prepare("SELECT 1 x FROM entity_rev WHERE eid=? AND status IN ('live','pending')").bind(ce).first()))) await db.prepare("INSERT INTO profile_company(user_id,eid) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET eid=excluded.eid").bind(user.id, ce).run(); }
    else await db.prepare("DELETE FROM profile_company WHERE user_id=?").bind(user.id).run();
    if (b.private && typeof b.private === "object") {   // Kontakt- und Adressdaten (privat, Sichtbarkeit je Feld)
      const pr = b.private, V = (x) => (["all", "contacts", "none"].includes(x) ? x : "none"), vis = pr.vis || {};
      const city = txt(pr.city, 80), zip = String(pr.zip || "").replace(/[^A-Za-z0-9 -]/g, "").slice(0, 10).trim(), street = txt(pr.street, 120);
      const email = String(pr.email || "").trim().slice(0, 120), phone = String(pr.phone || "").replace(/[^0-9+()\- ]/g, "").slice(0, 30).trim();
      if (email && !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email)) return J({ error: "bad_email" }, 400);
      await db.prepare(`INSERT INTO profile_private(user_id,city,zip,street,email,phone,vis_city,vis_zip,vis_street,vis_email,vis_phone,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET city=excluded.city,zip=excluded.zip,street=excluded.street,email=excluded.email,phone=excluded.phone,vis_city=excluded.vis_city,vis_zip=excluded.vis_zip,vis_street=excluded.vis_street,vis_email=excluded.vis_email,vis_phone=excluded.vis_phone,updated=excluded.updated`)
        .bind(user.id, city, zip, street, email, phone, V(vis.city), V(vis.zip), V(vis.street), V(vis.email), V(vis.phone), now()).run();
    }
    const oldC = Object.fromEntries(((await db.prepare("SELECT eid,url FROM certs WHERE user_id=?").bind(user.id).all()).results || []).map((x) => [x.eid, x.url]));
    await replaceLists(db, "u", user.id, { exp: ex.list, prog: pr.list, chan: ch.list, certs });
    {   // Pruefstatus: entfernte Zertifikate/geaenderte Nachweise zuruecksetzen, neue Nachweise pruefen
      const keep = new Set(certs.map((c) => c.e));
      for (const e of Object.keys(oldC)) if (!keep.has(e)) await db.prepare("DELETE FROM cert_check WHERE user_id=? AND eid=?").bind(user.id, e).run();
      const map = certs.some((c) => c.url) ? await entityMap(env) : null;
      for (const c of certs) {
        if (oldC[c.e] !== c.url) await db.prepare("DELETE FROM cert_check WHERE user_id=? AND eid=? AND NOT (via='admin' AND status='verified')").bind(user.id, c.e).run();
        if (!c.url) continue;
        if (await db.prepare("SELECT 1 x FROM cert_check WHERE user_id=? AND eid=? AND status IN ('verified','rejected')").bind(user.id, c.e).first()) continue;
        const ok = await autoVerifyCert(c.url, map.get(c.e), user.name);
        await db.prepare("INSERT INTO cert_check(user_id,eid,status,via,created) VALUES(?,?,?,?,?) ON CONFLICT(user_id,eid) DO UPDATE SET status=excluded.status,via=excluded.via,created=excluded.created").bind(user.id, c.e, ok ? "verified" : "pending", ok ? "auto" : "", now()).run();
      }
    }
    if (isPublic && handle) { const nm = user.name || handle, hl = txt(b.headline, 100); await ownedEntity(env, user, { eid: handle, type: "person", name: nm, en: `${nm} is a member of the Microsoft community${hl ? ": " + hl : ""}.`, de: `${nm} ist Mitglied der Microsoft-Community${hl ? ": " + hl : ""}.` }); }
    return J({ ok: true });
  }
  if ((m = /^\/api\/profile\/([a-z0-9-]{3,30})$/.exec(path)) && method === "GET") {
    const r = await db.prepare("SELECT user_id,public FROM profiles WHERE handle=?").bind(m[1]).first();
    if (!r || (!r.public && r.user_id !== user?.id)) return J({ error: "not_found" }, 404);
    const v = await personView(db, r.user_id, user?.id); if (!v) return J({ error: "not_found" }, 404);
    v.mine = r.user_id === user?.id; delete v.id; return J({ profile: v }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/experts" && method === "GET") {   // oeffentlich: Experten zu einem Thema, auch ueber verwandte Themen
    const e = url.searchParams.get("e") || ""; if (!ID.test(e)) return J({ error: "bad_request" }, 400);
    const r = await findExperts(env, e, +url.searchParams.get("hops") || 2, Math.min(+url.searchParams.get("limit") || 12, 30));
    return r ? J(r, 200, { "cache-control": "public, max-age=300" }) : J({ error: "not_found" }, 404);
  }
  if (path === "/api/profiles/export" && method === "GET") {   // oeffentlich: fuer den statischen Seitenbau; aus dem Zwischenspeicher, der per Cron erneuert wird
    const hit = url.searchParams.get("fresh") === "1" && user?.admin ? null : await db.prepare("SELECT v,updated FROM export_cache WHERE k='profiles'").first().catch(() => null);
    if (hit && now() - hit.updated < 7200) return J(JSON.parse(hit.v), 200, { "cache-control": "public, max-age=300", "x-export-age": String(now() - hit.updated) });
    try { return J(await refreshProfilesExport(env), 200, { "cache-control": "public, max-age=300", "x-export-age": "0" }); }
    catch (e) { if (hit) return J(JSON.parse(hit.v), 200, { "cache-control": "public, max-age=60", "x-export-age": String(now() - hit.updated), "x-export-stale": "1" }); throw e; }   // lieber eine aeltere Fassung als ein Fehler
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
  if (path === "/api/cert-endorse" && (method === "POST" || method === "DELETE")) {
    if (need()) return need();
    const b = await body(); const o = await resolve(db, "u:" + b.handle);
    if (!o || !ID.test(b.e || "") || o.id === user.id) return J({ error: "bad_request" }, 400);
    if (!(await db.prepare("SELECT 1 x FROM certs WHERE user_id=? AND eid=?").bind(o.id, b.e).first())) return J({ error: "not_found" }, 404);
    if (method === "POST") {
      if (!(await rateLimit(db, `endorse:${user.id}`, 30, 86400))) return J({ error: "rate_limit" }, 429);
      await db.prepare("INSERT OR IGNORE INTO cert_endorse(owner_id,eid,by_id,created) VALUES(?,?,?,?)").bind(o.id, b.e, user.id, now()).run();
    } else await db.prepare("DELETE FROM cert_endorse WHERE owner_id=? AND eid=? AND by_id=?").bind(o.id, b.e, user.id).run();
    return J({ ok: true });
  }
  if (path === "/api/admin/cert-queue" && method === "GET") {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    const rows = (await db.prepare("SELECT c.user_id uid,c.eid e,c.year,c.url,u.name,p.handle FROM cert_check k JOIN certs c ON c.user_id=k.user_id AND c.eid=k.eid JOIN users u ON u.id=c.user_id LEFT JOIN profiles p ON p.user_id=c.user_id WHERE k.status='pending' ORDER BY k.created LIMIT 50").all()).results || [];
    return J({ items: rows });
  }
  if ((m = /^\/api\/vote\/(\d+)$/.exec(path)) && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `vote:${user.id}`, 120, 3600))) return J({ error: "rate_limit" }, 429);
    const id = +m[1]; if (!(await db.prepare("SELECT 1 x FROM feed_items WHERE id=? AND hidden=0").bind(id).first())) return J({ error: "not_found" }, 404);
    const has = await db.prepare("SELECT 1 x FROM item_votes WHERE item_id=? AND user_id=?").bind(id, user.id).first();
    if (has) await db.prepare("DELETE FROM item_votes WHERE item_id=? AND user_id=?").bind(id, user.id).run(); else await db.prepare("INSERT INTO item_votes(item_id,user_id,created) VALUES(?,?,?)").bind(id, user.id, now()).run();
    return J({ ok: true, voted: !has, votes: (await db.prepare("SELECT COUNT(*) n FROM item_votes WHERE item_id=?").bind(id).first()).n });
  }
  if (path === "/api/feed/mine" && method === "GET") {   // eigene gezogene Inhalte (fuer SEO-Texte, auch per MCP)
    if (need()) return need();
    await ensureSectionCols(db);
    const rows = (await db.prepare("SELECT id,title,url,summary,thumb,body,published,topics,keypoints,faq,CASE WHEN length(body)>0 THEN 1 ELSE 0 END has_text FROM feed_items WHERE owner_type='u' AND owner_id=? ORDER BY published DESC LIMIT 100").bind(user.id).all()).results || [];
    return J({ items: rows.map((r) => ({ ...r, has_text: !!r.has_text, keypoints: jsonList(r.keypoints), faq: jsonList(r.faq), topics: (() => { try { return JSON.parse(r.topics || "[]"); } catch { return []; } })() })) });
  }
  if (path === "/api/feed/text" && method === "POST") {   // Creator ergaenzt den gezogenen Inhalt um eigenen Text (Wiki-Markup, Quellen nur als {{ref}})
    if (need()) return need();
    if (!(await rateLimit(db, `ftext:${user.id}`, 60, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await body(), it = await db.prepare("SELECT id FROM feed_items WHERE id=? AND owner_type='u' AND owner_id=?").bind(+b.id, user.id).first(); if (!it) return J({ error: "not_found" }, 404);
    const sb = sanitize(String(b.body || ""), { viz: true }); if (sb.err) return J({ error: sb.err }, 400);
    if (sb.body && sb.body.length < 300) return J({ error: "too_short" }, 400);
    const known = await baseIds(env), topics = [];
    for (const t of (Array.isArray(b.topics) ? b.topics : []).slice(0, 10)) { if (!known.has(t)) return J({ error: "bad_topic", topic: t }, 400); if (!topics.includes(t)) topics.push(t); }
    const sum = b.summary ? txt(b.summary, 300) : null;
    await ensureSectionCols(db);
    const kp = b.keypoints === undefined ? null : cleanKeypoints(b.keypoints), fq = b.faq === undefined ? null : cleanFaq(b.faq);
    if (kp?.err) return J({ error: kp.err }, 400); if (fq?.err) return J({ error: fq.err }, 400);
    await db.prepare("UPDATE feed_items SET body=?, topics=?, keypoints=COALESCE(?,keypoints), faq=COALESCE(?,faq), summary=CASE WHEN ? IS NULL THEN summary ELSE ? END, seo_at=? WHERE id=?").bind(sb.body, JSON.stringify(topics), kp ? JSON.stringify(kp.list) : null, fq ? JSON.stringify(fq.list) : null, sum, sum, now(), it.id).run();
    return J({ ok: true });
  }
  if (path === "/api/feed/export" && method === "GET") {   // oeffentlich fuer den Seitenbau: externe Quellen (nur Titel+Link), eigene Seiten ausgenommen
    await ensureSectionCols(db);
    const rows = (await db.prepare(`SELECT i.id,i.title,i.url,i.summary,i.thumb,i.body,i.topics,i.keypoints,i.faq,i.published,c.kind,i.owner_type,i.owner_id,(SELECT COUNT(*) FROM item_votes v WHERE v.item_id=i.id) votes FROM feed_items i JOIN channels c ON c.id=i.channel_id
      WHERE i.hidden=0 AND i.url NOT LIKE ? AND i.published>? AND ((i.owner_type='u' AND i.owner_id IN (SELECT p.user_id FROM profiles p JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.public=1)) OR (i.owner_type='o' AND i.owner_id IN (SELECT id FROM orgs WHERE public=1)))
      ORDER BY i.published DESC LIMIT 300`).bind(env.SITE + "%", now() - 120 * 86400).all()).results || [];
    const names = new Map(), out = [];
    for (const r of rows) {
      const k = r.owner_type + r.owner_id;
      if (!names.has(k)) names.set(k, r.owner_type === "u" ? await db.prepare("SELECT p.handle,u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=?").bind(r.owner_id).first() : await db.prepare("SELECT handle,name FROM orgs WHERE id=?").bind(r.owner_id).first());
      const o = names.get(k); if (o) out.push({ id: r.id, summary: r.summary || "", thumb: r.thumb || "", body: r.body || "", keypoints: jsonList(r.keypoints), faq: jsonList(r.faq), topics: (() => { try { return JSON.parse(r.topics || "[]"); } catch { return []; } })(), title: r.title, url: r.url, published: r.published, kind: r.kind, votes: r.votes, type: r.owner_type, handle: o.handle, name: o.name });
    }
    return J({ items: out }, 200, { "cache-control": "public, max-age=300" });
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
      // Firmen-Entitaet erzeugen oder wiederverwenden (nie Freitext): gleiche Namen -> gleiche Entitaet
      try {
        const eid = slug(name).replace(/-+$/g, "") || `firma-${o.id}`;
        const known = await baseIds(env), ex = await db.prepare("SELECT 1 x FROM entity_rev WHERE eid=? AND status IN ('live','pending')").bind(eid).first();
        if (!known.has(eid) && !ex) {
          const v = await validate(env, eid, { name, type: "org", desc: { en: `${name} is a company in the Microsoft ecosystem.`, de: `${name} ist ein Unternehmen im Microsoft-Umfeld.` }, web: website || "", rel: [] });
          if (!v.err) await db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,?,?)").bind(eid, JSON.stringify(v.data), "Firma angelegt", user.id, (await trustedUser(db, user)) ? "live" : "pending", now()).run();
        }
        await db.prepare("INSERT OR REPLACE INTO org_entity(org_id,eid) VALUES(?,?)").bind(o.id, eid).run();
        if (!known.has(eid) && !ex) await db.prepare("INSERT INTO entity_claims(eid,user_id,status,via,created) VALUES(?,?,'verified','owner',?) ON CONFLICT(eid) DO NOTHING").bind(eid, user.id, now()).run();
      } catch (e) { /* Entitaet ist optional, Firmenkonto bleibt gueltig */ }
    } else {
      const mem = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=? AND status='active'").bind(o.id, user.id).first();
      if (!mem || !["owner", "admin", "editor"].includes(mem.role)) return J({ error: "forbidden" }, 403);
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
    const role = String(b.role || "member");
    if (b.action === "approve") {
      if (!assignable(me.role, role)) return J({ error: "forbidden" }, 403);
      await db.prepare("UPDATE org_members SET status='active',role=? WHERE org_id=? AND user_id=?").bind(role, o.id, target).run();
    }
    else if (b.action === "remove" && tr.role !== "owner" && (me.role === "owner" || !["admin"].includes(tr.role))) await db.prepare("DELETE FROM org_members WHERE org_id=? AND user_id=?").bind(o.id, target).run();
    else if (b.action === "role") {   // Rolle aendern: Inhaber alles, Admins nur Redakteur/Events/Mitglied bei Nicht-Admins
      if (!assignable(me.role, role) || (["owner", "admin"].includes(tr.role) && me.role !== "owner")) return J({ error: "forbidden" }, 403);
      if (tr.role === "owner" && role !== "owner" && (await db.prepare("SELECT COUNT(*) n FROM org_members WHERE org_id=? AND role='owner' AND status='active'").bind(o.id).first()).n < 2) return J({ error: "last_owner" }, 400);
      await db.prepare("UPDATE org_members SET role=? WHERE org_id=? AND user_id=?").bind(role, o.id, target).run();
    }
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
    else if (b.kind === "cert" && o.t === "u" && ID.test(b.key || "")) {
      if (v) await db.prepare("INSERT INTO cert_check(user_id,eid,status,via,created) VALUES(?,?,'verified','admin',?) ON CONFLICT(user_id,eid) DO UPDATE SET status='verified',via='admin',created=excluded.created").bind(o.id, b.key, now()).run();
      else await db.prepare("INSERT INTO cert_check(user_id,eid,status,via,created) VALUES(?,?,'rejected','admin',?) ON CONFLICT(user_id,eid) DO UPDATE SET status='rejected',via='admin',created=excluded.created").bind(o.id, b.key, now()).run();
    }
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
  await db.prepare("DELETE FROM recommendations WHERE author_id=? OR subject_id=?").bind(id, id).run();
  await db.prepare("DELETE FROM profile_company WHERE user_id=?").bind(id).run();
  await db.prepare("DELETE FROM images WHERE kind='u' AND owner_id=?").bind(id).run();
  const own = (await db.prepare("SELECT org_id FROM org_members WHERE user_id=? AND role='owner'").bind(id).all()).results || [];
  const ops = [];
  for (const o of own) {
    const other = await db.prepare("SELECT user_id FROM org_members WHERE org_id=? AND user_id<>? AND status='active' ORDER BY role='admin' DESC, created LIMIT 1").bind(o.org_id, id).first();
    if (other) ops.push(db.prepare("UPDATE org_members SET role='owner' WHERE org_id=? AND user_id=?").bind(o.org_id, other.user_id));
    else ops.push(db.prepare("DELETE FROM org_sponsor WHERE org_id=?").bind(o.org_id), db.prepare("DELETE FROM images WHERE kind='o' AND owner_id=?").bind(o.org_id), db.prepare("DELETE FROM expertise WHERE owner_type='o' AND owner_id=?").bind(o.org_id), db.prepare("DELETE FROM programs WHERE owner_type='o' AND owner_id=?").bind(o.org_id),
      db.prepare("DELETE FROM item_votes WHERE item_id IN (SELECT id FROM feed_items WHERE owner_type='o' AND owner_id=?)").bind(o.org_id), db.prepare("DELETE FROM feed_items WHERE owner_type='o' AND owner_id=?").bind(o.org_id),
      db.prepare("DELETE FROM channels WHERE owner_type='o' AND owner_id=?").bind(o.org_id), db.prepare("DELETE FROM org_members WHERE org_id=?").bind(o.org_id), db.prepare("DELETE FROM orgs WHERE id=?").bind(o.org_id));
  }
  ops.push(
    db.prepare("DELETE FROM org_members WHERE user_id=?").bind(id),
    db.prepare("DELETE FROM item_votes WHERE user_id=? OR item_id IN (SELECT id FROM feed_items WHERE owner_type='u' AND owner_id=?)").bind(id, id),
    db.prepare("DELETE FROM feed_items WHERE owner_type='u' AND owner_id=?").bind(id), db.prepare("DELETE FROM channels WHERE owner_type='u' AND owner_id=?").bind(id),
    db.prepare("DELETE FROM expertise WHERE owner_type='u' AND owner_id=?").bind(id), db.prepare("DELETE FROM programs WHERE owner_type='u' AND owner_id=?").bind(id),
    db.prepare("DELETE FROM profile_private WHERE user_id=?").bind(id), db.prepare("DELETE FROM profile_i18n WHERE user_id=?").bind(id), db.prepare("DELETE FROM certs WHERE user_id=?").bind(id), db.prepare("DELETE FROM cert_check WHERE user_id=?").bind(id), db.prepare("DELETE FROM cert_endorse WHERE owner_id=? OR by_id=?").bind(id, id), db.prepare("DELETE FROM endorsements WHERE owner_id=? OR by_id=?").bind(id, id),
    db.prepare("DELETE FROM profiles WHERE user_id=?").bind(id),
    db.prepare("DELETE FROM entity_rev WHERE user_id=? AND status IN ('pending','rejected')").bind(id), db.prepare("UPDATE entity_rev SET user_id=0 WHERE user_id=?").bind(id));
  await db.batch(ops);
}
