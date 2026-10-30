// Podcast-Umzug: Mitglied traegt seine RSS-URL ein, alle Folgen (Text, Audio, Dauer, Transkript) werden importiert und taeglich abgeglichen.
// Die Show erscheint nach Freigabe (Admin/Editor) auf /shows/<slug>/ der Plattform.
import { cleanText, rateLimit } from "./util.js";

const now = () => Math.floor(Date.now() / 1000);
const MAX_EPS = 2000, MAX_SHOWS = 3, TR_PER_SYNC = 25;
let ready = false;
async function ensure(db) {
  if (ready) return;
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS shows (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, descr TEXT NOT NULL DEFAULT '', feed TEXT NOT NULL, site TEXT NOT NULL DEFAULT '', image TEXT NOT NULL DEFAULT '', lang TEXT NOT NULL DEFAULT 'en', status TEXT NOT NULL DEFAULT 'pending', created INTEGER NOT NULL, synced INTEGER NOT NULL DEFAULT 0, err TEXT NOT NULL DEFAULT '', consent INTEGER NOT NULL DEFAULT 0)"),
    db.prepare("CREATE TABLE IF NOT EXISTS show_eps (id INTEGER PRIMARY KEY AUTOINCREMENT, show_id INTEGER NOT NULL, guid TEXT NOT NULL, slug TEXT NOT NULL, title TEXT NOT NULL, descr TEXT NOT NULL DEFAULT '', pub INTEGER NOT NULL DEFAULT 0, audio TEXT NOT NULL DEFAULT '', dur TEXT NOT NULL DEFAULT '', image TEXT NOT NULL DEFAULT '', season INTEGER, num INTEGER, link TEXT NOT NULL DEFAULT '', tr_url TEXT NOT NULL DEFAULT '', transcript TEXT NOT NULL DEFAULT '', UNIQUE(show_id, guid))"),
  ]);
  ready = true;
}
const slugify = (s) => String(s).toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "show";
const ent = (s) => String(s).replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'").replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n)).replace(/&amp;/g, "&");
const cd = (s) => { const m = /^\s*<!\[CDATA\[([\s\S]*?)\]\]>\s*$/.exec(s); return m ? m[1] : ent(s); };
const tag = (x, name) => { const m = new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, "i").exec(x); return m ? cd(m[1]).trim() : ""; };
const attr = (x, name, a) => { const m = new RegExp(`<${name}\\b[^>]*\\b${a}="([^"]*)"`, "i").exec(x); return m ? ent(m[1]) : ""; };
const plainTxt = (s) => cleanText(String(s).replace(/<[^>]+>/g, " ").replace(/\s+/g, " "), 400);

// SSRF-Schutz: nur https, kein localhost/IP-Literal/interne Namen
export function safeUrl(u) {
  try { const x = new URL(u); if (x.protocol !== "https:" || x.username || x.password) return ""; const h = x.hostname.toLowerCase();
    if (!h.includes(".") || /^[\d.]+$/.test(h) || h.includes(":") || /(^|\.)(localhost|local|internal|lan|home|corp)$/.test(h) || h.endsWith(".workers.dev") && false) return ""; return x.href; } catch { return ""; }
}
async function get(url, max = 20e6) {
  const r = await fetch(url, { headers: { "user-agent": "M365FM-ShowImport/1.0", accept: "application/rss+xml, application/xml, text/xml, text/vtt, text/plain, application/json, */*" }, redirect: "follow", signal: AbortSignal.timeout(25000) });
  if (!r.ok) throw new Error("http_" + r.status);
  const t = await r.text(); return t.length > max ? t.slice(0, max) : t;
}
function cleanTranscript(t) {
  t = t.trim();
  if (t[0] === "{" || t[0] === "[") { try { const j = JSON.parse(t), seg = Array.isArray(j) ? j : j.segments || []; return seg.map((s) => s.body || s.text || "").join(" ").replace(/\s+/g, " ").trim().slice(0, 120000); } catch { /* weiter */ } }
  const out = []; let last = "";
  for (let ln of t.split(/\r?\n/)) { ln = ln.replace(/<[^>]+>/g, "").trim(); if (!ln || ln.includes("-->") || /^(WEBVTT|NOTE)/.test(ln) || /^\d+$/.test(ln)) continue; if (ln !== last) { out.push(ln); last = ln; } }
  return out.join(" ").slice(0, 120000);
}
export function parseRss(xml) {
  const ci = xml.indexOf("<item"), head = ci > 0 ? xml.slice(0, ci) : xml.slice(0, 20000);
  const show = { title: plainTxt(tag(head, "title")).slice(0, 140), descr: cleanText(tag(head, "description").replace(/<[^>]+>/g, " ").replace(/\s+/g, " "), 1500) || cleanText(tag(head, "itunes:summary"), 1500), site: safeUrl(tag(head, "link")), image: safeUrl(attr(head, "itunes:image", "href")) || safeUrl(tag(head.slice(head.indexOf("<image")), "url")), lang: (tag(head, "language") || "en").slice(0, 2).toLowerCase() };
  const items = [];
  for (const m of xml.matchAll(/<item[\s>][\s\S]*?<\/item>/gi)) {
    const x = m[0], title = plainTxt(tag(x, "title")).slice(0, 200); if (!title) continue;
    const pub = Date.parse(tag(x, "pubDate")) || 0;
    items.push({ guid: (tag(x, "guid") || attr(x, "enclosure", "url") || title).slice(0, 300), title, descr: cleanText(tag(x, "content:encoded") || tag(x, "description") || tag(x, "itunes:summary"), 20000),
      pub: pub ? Math.floor(pub / 1000) : 0, audio: safeUrl(attr(x, "enclosure", "url")), dur: tag(x, "itunes:duration").slice(0, 12), image: safeUrl(attr(x, "itunes:image", "href")),
      season: parseInt(tag(x, "itunes:season")) || null, num: parseInt(tag(x, "itunes:episode")) || null, link: safeUrl(tag(x, "link")), tr_url: safeUrl(attr(x, "podcast:transcript", "url")) });
    if (items.length >= MAX_EPS) break;
  }
  return { show, items };
}
export async function syncShow(env, s) {
  const db = env.DB;
  try {
    const { show, items } = parseRss(await get(s.feed));
    if (!items.length) throw new Error("no_items");
    const used = new Set(((await db.prepare("SELECT slug FROM show_eps WHERE show_id=?").bind(s.id).all()).results || []).map((r) => r.slug));
    const stmts = [];
    for (const it of items) {
      const have = await db.prepare("SELECT slug FROM show_eps WHERE show_id=? AND guid=?").bind(s.id, it.guid).first();
      if (have) { stmts.push(db.prepare("UPDATE show_eps SET title=?,descr=?,pub=?,audio=?,dur=?,image=?,season=?,num=?,link=?,tr_url=? WHERE show_id=? AND guid=?").bind(it.title, it.descr, it.pub, it.audio, it.dur, it.image, it.season, it.num, it.link, it.tr_url, s.id, it.guid)); continue; }
      let sl = slugify(it.title), n = 2; while (used.has(sl)) sl = slugify(it.title).slice(0, 55) + "-" + n++; used.add(sl);
      stmts.push(db.prepare("INSERT INTO show_eps(show_id,guid,slug,title,descr,pub,audio,dur,image,season,num,link,tr_url) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(s.id, it.guid, sl, it.title, it.descr, it.pub, it.audio, it.dur, it.image, it.season, it.num, it.link, it.tr_url));
    }
    for (let i = 0; i < stmts.length; i += 50) await db.batch(stmts.slice(i, i + 50));
    await db.prepare("UPDATE shows SET title=?,descr=?,site=?,image=?,lang=?,synced=?,err='' WHERE id=?").bind(s.title || show.title, show.descr || s.descr, show.site, show.image, show.lang, now(), s.id).run();
    // Transkripte schrittweise nachladen
    const todo = (await db.prepare("SELECT id,tr_url FROM show_eps WHERE show_id=? AND tr_url!='' AND transcript='' ORDER BY pub DESC LIMIT ?").bind(s.id, TR_PER_SYNC).all()).results || [];
    for (const t of todo) { try { const tx = cleanTranscript(await get(t.tr_url, 3e6)); await db.prepare("UPDATE show_eps SET transcript=? WHERE id=?").bind(tx || "-", t.id).run(); } catch { await db.prepare("UPDATE show_eps SET transcript='-' WHERE id=?").bind(t.id).run(); } }
    return { ok: true, eps: items.length };
  } catch (e) {
    await db.prepare("UPDATE shows SET err=?,synced=? WHERE id=?").bind(String(e.message || e).slice(0, 100), now(), s.id).run();
    return { ok: false, error: String(e.message || e) };
  }
}
export async function syncShows(env) {   // Cron: je Lauf wenige Shows, die laenger als 20 h nicht abgeglichen wurden (oder noch Transkripte offen haben)
  await ensure(env.DB);
  const rows = (await env.DB.prepare("SELECT * FROM shows WHERE status IN ('live','pending') AND (synced < ? OR EXISTS(SELECT 1 FROM show_eps e WHERE e.show_id=shows.id AND e.tr_url!='' AND e.transcript='')) ORDER BY synced LIMIT 2").bind(now() - 20 * 3600).all()).results || [];
  for (const s of rows) await syncShow(env, s);
  return rows.length;
}

export async function handleShows(env, request, url, path, user, J) {
  if (!path.startsWith("/api/show/") && !path.startsWith("/api/admin/show")) return null;
  const db = env.DB, method = request.method; await ensure(db);
  if (path === "/api/show/export" && method === "GET") {
    const shows = (await db.prepare("SELECT s.id,s.slug,s.title,s.descr,s.site,s.image,s.lang,s.synced,p.handle,u.name FROM shows s JOIN profiles p ON p.user_id=s.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=s.user_id AND u.banned=0 WHERE s.status='live'").all()).results || [];
    for (const s of shows) s.eps = (await db.prepare("SELECT slug,title,descr,pub,audio,dur,image,season,num,link,CASE WHEN transcript='-' THEN '' ELSE transcript END transcript FROM show_eps WHERE show_id=? ORDER BY pub DESC LIMIT 2000").bind(s.id).all()).results || [];
    return J({ items: shows }, 200, { "cache-control": "public, max-age=300" });
  }
  if (!user) return J({ error: "login" }, 401);
  if (path === "/api/show/mine" && method === "GET") {
    const rows = (await db.prepare("SELECT s.id,s.slug,s.title,s.feed,s.status,s.synced,s.err,(SELECT COUNT(*) FROM show_eps e WHERE e.show_id=s.id) eps,(SELECT COUNT(*) FROM show_eps e WHERE e.show_id=s.id AND e.transcript NOT IN ('','-')) trs FROM shows s WHERE s.user_id=? ORDER BY s.created").bind(user.id).all()).results || [];
    return J({ items: rows }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/admin/show" && method === "GET") {
    if (!user.admin && !user.editor) return J({ error: "forbidden" }, 403);
    return J({ items: (await db.prepare("SELECT s.id,s.slug,s.title,s.feed,s.status,s.err,s.created,u.name FROM shows s JOIN users u ON u.id=s.user_id ORDER BY (s.status='pending') DESC, s.created DESC LIMIT 200").all()).results || [] });
  }
  if (method !== "POST") return J({ error: "bad_request" }, 400);
  const b = await request.json().catch(() => ({}));
  if (path === "/api/show/save") {   // Feed-URL eintragen = Umzug starten
    if (!(await rateLimit(db, `show:${user.id}`, 6, 3600))) return J({ error: "rate_limit" }, 429);
    const prof = await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1 AND handle IS NOT NULL").bind(user.id).first();
    if (!prof) return J({ error: "profile" }, 400);
    if (!b.agree) return J({ error: "agree" }, 400);   // Einwilligung: Verteilung ueber das Netzwerk, Werbung/Sponsoring auf den Show-Seiten
    const feed = safeUrl(String(b.feed || "").trim()); if (!feed) return J({ error: "feed" }, 400);
    if ((await db.prepare("SELECT COUNT(*) c FROM shows WHERE user_id=?").bind(user.id).first()).c >= MAX_SHOWS) return J({ error: "limit" }, 400);
    if (await db.prepare("SELECT 1 x FROM shows WHERE feed=?").bind(feed).first()) return J({ error: "exists" }, 400);
    let parsed; try { parsed = parseRss(await get(feed)); } catch (e) { return J({ error: "fetch" }, 400); }
    if (!parsed.items.length || !parsed.show.title) return J({ error: "rss" }, 400);
    let sl = slugify(parsed.show.title), n = 2; while (await db.prepare("SELECT 1 x FROM shows WHERE slug=?").bind(sl).first()) sl = slugify(parsed.show.title).slice(0, 55) + "-" + n++;
    const r = await db.prepare("INSERT INTO shows(user_id,slug,title,descr,feed,site,image,lang,status,created,consent) VALUES(?,?,?,?,?,?,?,?,?,?,?)").bind(user.id, sl, parsed.show.title, parsed.show.descr, feed, parsed.show.site, parsed.show.image, parsed.show.lang, user.admin || user.editor ? "live" : "pending", now(), now()).run();
    const out = await syncShow(env, { id: r.meta.last_row_id, feed, title: parsed.show.title, descr: parsed.show.descr });
    return J({ ok: true, id: r.meta.last_row_id, eps: out.eps || 0, status: user.admin || user.editor ? "live" : "pending" });
  }
  if (path === "/api/show/sync") {
    const s = await db.prepare("SELECT * FROM shows WHERE id=? AND (user_id=? OR ?=1)").bind(+b.id, user.id, user.admin ? 1 : 0).first(); if (!s) return J({ error: "not_found" }, 404);
    if (!(await rateLimit(db, `showsync:${user.id}`, 6, 3600))) return J({ error: "rate_limit" }, 429);
    return J(await syncShow(env, s));
  }
  if (path === "/api/show/delete") {
    const s = await db.prepare("SELECT id FROM shows WHERE id=? AND (user_id=? OR ?=1)").bind(+b.id, user.id, user.admin ? 1 : 0).first(); if (!s) return J({ error: "not_found" }, 404);
    await db.batch([db.prepare("DELETE FROM show_eps WHERE show_id=?").bind(s.id), db.prepare("DELETE FROM shows WHERE id=?").bind(s.id)]); return J({ ok: true });
  }
  if (path === "/api/admin/show/status") {
    if (!user.admin && !user.editor) return J({ error: "forbidden" }, 403);
    if (!["live", "pending", "rejected"].includes(b.status)) return J({ error: "bad_status" }, 400);
    await db.prepare("UPDATE shows SET status=? WHERE id=?").bind(b.status, +b.id).run(); return J({ ok: true });
  }
  return J({ error: "not_found" }, 404);
}
