// Blog je Mitglied: Beitraege schreiben (Wiki-Markup mit Quellen), Pruefung fuer Neue, Upvotes, Export fuer den Seitenbau
import { cleanText, rateLimit, isLang } from "./util.js";
import { stats } from "./badges.js";
import { baseIds } from "./entities.js";
import { sanitize } from "./wiki.js";

const TRUST_POINTS = 25, MAX_POSTS_DAY = 5;
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const okLang = (l) => l === "en" || isLang(l);
const slugify = (t) => t.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);
const parse = (s, d) => { try { return JSON.parse(s); } catch { return d; } };
const FIELDS = "id,slug,title,summary,body,lang,status,topics,note,created,updated,published";

const view = (r) => ({ ...r, topics: parse(r.topics, []) });

async function trusted(db, user) { return !!(user.admin || user.editor || user.pro || (await stats(db, user.id)).points >= TRUST_POINTS); }

const postUrl = (env, lang, handle, slug) => `${env.SITE}${lang === "en" ? "" : "/" + lang}/community/u/${handle}/blog/${slug}/`;
// Creator-Feed: veroeffentlichte Beitraege erscheinen im Feed des Profils (Kanal-Art "blog", ohne eigenen RSS-Abruf)
export async function syncFeed(env, db, uid, post, handle, live) {
  const url = postUrl(env, post.lang, handle, post.slug);
  if (!live) { await db.prepare("DELETE FROM feed_items WHERE url=? AND owner_type='u' AND owner_id=?").bind(url, uid).run(); return; }
  const curl = `${env.SITE}/community/u/${handle}/blog/`;
  await db.prepare("INSERT OR IGNORE INTO channels(owner_type,owner_id,kind,url,feed) VALUES('u',?,'blog',?,'')").bind(uid, curl).run();
  const ch = await db.prepare("SELECT id FROM channels WHERE owner_type='u' AND owner_id=? AND url=?").bind(uid, curl).first(); if (!ch) return;
  await db.prepare("INSERT INTO feed_items(channel_id,owner_type,owner_id,url,title,published) VALUES(?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET title=excluded.title,hidden=0").bind(ch.id, "u", uid, url, post.title, post.published || now()).run();
}

export async function deleteUserBlog(db, uid) {
  await db.batch([db.prepare("DELETE FROM blog_follows WHERE user_id=?").bind(uid), db.prepare("DELETE FROM blog_votes WHERE post_id IN (SELECT id FROM blog_posts WHERE user_id=?) OR user_id=?").bind(uid, uid), db.prepare("DELETE FROM blog_coauthors WHERE post_id IN (SELECT id FROM blog_posts WHERE user_id=?) OR user_id=?").bind(uid, uid), db.prepare("DELETE FROM blog_posts WHERE user_id=?").bind(uid)]);
}

// Co-Autoren: Profil-Adressen (max. 3, oeffentliche Profile, nicht man selbst). Eingeladene bestaetigen selbst - erst dann erscheinen sie auf der Seite.
async function resolveCoauthors(db, user, raw) {
  if (raw === undefined) return {};   // nicht mitgeschickt: unveraendert lassen
  const hs = [...new Set((Array.isArray(raw) ? raw : []).map((x) => String(x || "").toLowerCase().trim()).filter(Boolean))].slice(0, 3), list = [];
  for (const h of hs) {
    const pr = await db.prepare("SELECT user_id FROM profiles WHERE handle=? AND public=1").bind(h).first(); if (!pr) return { err: "bad_coauthor", handle: h };
    if (pr.user_id === user.id) return { err: "bad_coauthor", handle: h };
    list.push(pr.user_id);
  }
  return { list };
}
async function saveCoauthors(db, postId, list) {
  const have = new Map(((await db.prepare("SELECT user_id,status FROM blog_coauthors WHERE post_id=?").bind(postId).all()).results || []).map((r) => [r.user_id, r.status]));
  for (const uid of have.keys()) if (!list.includes(uid)) await db.prepare("DELETE FROM blog_coauthors WHERE post_id=? AND user_id=?").bind(postId, uid).run();
  for (const uid of list) if (!have.has(uid)) await db.prepare("INSERT INTO blog_coauthors(post_id,user_id,status,created) VALUES(?,?,'invited',?)").bind(postId, uid, now()).run();
}
const invites = async (db, uid) => (await db.prepare("SELECT b.id post_id,b.title,b.lang,u.name author,p.handle author_handle FROM blog_coauthors c JOIN blog_posts b ON b.id=c.post_id JOIN users u ON u.id=b.user_id LEFT JOIN profiles p ON p.user_id=b.user_id WHERE c.user_id=? AND c.status='invited' ORDER BY c.created DESC LIMIT 50").bind(uid).all()).results || [];

export async function handleBlog(env, request, url, path, user, J) {
  const db = env.DB, method = request.method;

  if (path === "/api/blog/export" && method === "GET") {   // oeffentlich: freigegebene Beitraege oeffentlicher Profile
    const rows = (await db.prepare(
      `SELECT b.id,b.slug,b.title,b.summary,b.body,b.lang,b.topics,b.created,b.published,b.updated,p.handle,u.name,(SELECT COUNT(*) FROM blog_votes v WHERE v.post_id=b.id) votes
       FROM blog_posts b JOIN profiles p ON p.user_id=b.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=b.user_id AND u.banned=0
       WHERE b.status='live' ORDER BY b.published DESC LIMIT 1000`).all()).results || [];
    const co = (await db.prepare("SELECT c.post_id,p.handle,u.name FROM blog_coauthors c JOIN profiles p ON p.user_id=c.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=c.user_id AND u.banned=0 WHERE c.status='confirmed' ORDER BY c.created").all()).results || [], by = {};
    for (const c of co) (by[c.post_id] ||= []).push({ handle: c.handle, name: c.name });
    return J({ items: rows.map((r) => ({ ...r, topics: parse(r.topics, []), coauthors: by[r.id] || [] })) }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path === "/api/blog/followers" && method === "GET") {   // Anzahl Abonnenten eines Blogs (oeffentlich)
    const n = (await db.prepare("SELECT COUNT(*) n FROM blog_follows WHERE handle=?").bind(url.searchParams.get("handle") || "").first()).n;
    return J({ followers: n }, 200, { "cache-control": "public, max-age=120" });
  }
  if (path === "/api/blog/votes" && method === "GET") {   // Upvote-Zahlen live (fuer die statischen Seiten)
    const h = url.searchParams.get("handle") || "";
    const rows = (await db.prepare("SELECT b.slug,(SELECT COUNT(*) FROM blog_votes v WHERE v.post_id=b.id) votes FROM blog_posts b JOIN profiles p ON p.user_id=b.user_id WHERE p.handle=? AND b.status='live'").bind(h).all()).results || [];
    let mine = [];
    if (user) mine = ((await db.prepare("SELECT b.slug FROM blog_votes v JOIN blog_posts b ON b.id=v.post_id JOIN profiles p ON p.user_id=b.user_id WHERE v.user_id=? AND p.handle=?").bind(user.id, h).all()).results || []).map((x) => x.slug);
    return J({ votes: Object.fromEntries(rows.map((r) => [r.slug, r.votes])), mine });
  }

  if (path.startsWith("/api/admin/blog")) {
    if (!user || !(user.admin || user.editor)) return J({ error: "forbidden" }, 403);
    if (path === "/api/admin/blog" && method === "GET") {
      const rows = (await db.prepare("SELECT b.id,b.title,b.summary,b.body,b.lang,b.created,u.name FROM blog_posts b JOIN users u ON u.id=b.user_id WHERE b.status='pending' ORDER BY b.created").all()).results || [];
      return J({ items: rows });
    }
    if (path === "/api/admin/blog/decide" && method === "POST") {
      const b = await request.json().catch(() => ({})), id = +b.id;
      const p = await db.prepare("SELECT id FROM blog_posts WHERE id=? AND status='pending'").bind(id).first(); if (!p) return J({ error: "not_found" }, 404);
      if (b.ok) await db.prepare("UPDATE blog_posts SET status='live',published=COALESCE(NULLIF(published,0),?),note='',updated=? WHERE id=?").bind(now(), now(), id).run();
      else await db.prepare("UPDATE blog_posts SET status='rejected',note=?,updated=? WHERE id=?").bind(txt(b.note || "", 300), now(), id).run();
      return J({ ok: true });
    }
    return null;
  }

  if (!user) return J({ error: "login" }, 401);

  if (path === "/api/blog/mine" && method === "GET") {
    const rows = (await db.prepare(`SELECT ${FIELDS},(SELECT COUNT(*) FROM blog_votes v WHERE v.post_id=blog_posts.id) votes FROM blog_posts WHERE user_id=? ORDER BY updated DESC LIMIT 100`).bind(user.id).all()).results || [];
    const pr = await db.prepare("SELECT handle,public FROM profiles WHERE user_id=?").bind(user.id).first();
    const co = (await db.prepare("SELECT c.post_id,c.status,p.handle,u.name FROM blog_coauthors c JOIN blog_posts b ON b.id=c.post_id AND b.user_id=? JOIN profiles p ON p.user_id=c.user_id JOIN users u ON u.id=c.user_id").bind(user.id).all()).results || [], by = {};
    for (const c of co) (by[c.post_id] ||= []).push({ handle: c.handle, name: c.name, status: c.status });
    return J({ items: rows.map((r) => ({ ...view(r), coauthors: by[r.id] || [] })), handle: pr?.handle || "", public: !!pr?.public, trusted: await trusted(db, user), invites: await invites(db, user.id) });
  }

  if (path === "/api/blog/save" && method === "POST") {
    if (!(await rateLimit(db, `blog:${user.id}`, 30, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await request.json().catch(() => ({}));
    const title = txt(b.title || "", 140), summary = txt(b.summary || "", 300), lang = String(b.lang || "en");
    if (title.length < 5) return J({ error: "title" }, 400);
    if (!okLang(lang)) return J({ error: "bad_lang" }, 400);
    const sb = sanitize(String(b.body || "")); if (sb.err) return J({ error: sb.err }, 400);
    if (b.submit && sb.body.length < 300) return J({ error: "too_short" }, 400);
    const known = await baseIds(env), topics = [];
    for (const t of (Array.isArray(b.topics) ? b.topics : []).slice(0, 10)) { if (!known.has(t)) return J({ error: "bad_topic", topic: t }, 400); if (!topics.includes(t)) topics.push(t); }
    const pr = await db.prepare("SELECT handle,public FROM profiles WHERE user_id=?").bind(user.id).first();
    if (b.submit && !(pr?.public && pr.handle)) return J({ error: "need_profile" }, 400);
    const cos = await resolveCoauthors(db, user, b.coauthors); if (cos.err) return J({ error: cos.err, handle: cos.handle }, 400);
    const t = now();
    let cur = b.id ? await db.prepare(`SELECT ${FIELDS} FROM blog_posts WHERE id=? AND user_id=?`).bind(+b.id, user.id).first() : null;
    if (b.id && !cur) return J({ error: "not_found" }, 404);
    const status = !b.submit ? (cur && cur.status === "live" ? "live" : "draft") : "live";
    if (cur) {
      await db.prepare("UPDATE blog_posts SET title=?,summary=?,body=?,lang=?,topics=?,status=?,updated=?,published=CASE WHEN ?='live' AND published=0 THEN ? ELSE published END,note='' WHERE id=?")
        .bind(title, summary, sb.body, lang, JSON.stringify(topics), status, t, status, t, cur.id).run();
      await syncFeed(env, db, user.id, { lang, slug: cur.slug, title, published: cur.published || t }, pr?.handle, status === "live" && !!pr?.handle);
      if (cos.list) await saveCoauthors(db, cur.id, cos.list);
      return J({ ok: true, id: cur.id, slug: cur.slug, status });
    }
    const day = (await db.prepare("SELECT COUNT(*) n FROM blog_posts WHERE user_id=? AND created>?").bind(user.id, t - 86400).first())?.n || 0;
    if (day >= MAX_POSTS_DAY) return J({ error: "rate_limit" }, 429);
    let slug = slugify(title) || "post", n = 1;
    while (await db.prepare("SELECT 1 x FROM blog_posts WHERE user_id=? AND slug=?").bind(user.id, slug).first()) slug = `${slugify(title).slice(0, 52) || "post"}-${++n}`;
    const r = await db.prepare("INSERT INTO blog_posts(user_id,slug,title,summary,body,lang,topics,status,note,created,updated,published) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)")
      .bind(user.id, slug, title, summary, sb.body, lang, JSON.stringify(topics), status, "", t, t, status === "live" ? t : 0).run();
    await syncFeed(env, db, user.id, { lang, slug, title, published: t }, pr?.handle, status === "live" && !!pr?.handle);
    if (cos.list) await saveCoauthors(db, r.meta.last_row_id, cos.list);
    return J({ ok: true, id: r.meta.last_row_id, slug, status });
  }

  if (path === "/api/blog/coauthor/mine" && method === "GET") {   // Einladungen als Co-Autor und bereits bestaetigte Beitraege
    const done = (await db.prepare("SELECT b.id,b.title,b.slug,b.lang,b.status,p.handle author FROM blog_coauthors c JOIN blog_posts b ON b.id=c.post_id LEFT JOIN profiles p ON p.user_id=b.user_id WHERE c.user_id=? AND c.status='confirmed' ORDER BY b.updated DESC LIMIT 100").bind(user.id).all()).results || [];
    return J({ invites: await invites(db, user.id), coauthored: done });
  }
  if (path === "/api/blog/coauthor" && method === "POST") {   // Einladung annehmen oder ablehnen (nur wer eingeladen ist)
    if (!(await rateLimit(db, `blogco:${user.id}`, 60, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await request.json().catch(() => ({}));
    const row = await db.prepare("SELECT 1 x FROM blog_coauthors WHERE post_id=? AND user_id=? AND status='invited'").bind(+b.id, user.id).first(); if (!row) return J({ error: "not_found" }, 404);
    if (b.accept && !(await db.prepare("SELECT 1 x FROM profiles WHERE user_id=? AND public=1 AND handle IS NOT NULL").bind(user.id).first())) return J({ error: "need_profile" }, 400);
    await db.prepare("UPDATE blog_coauthors SET status=? WHERE post_id=? AND user_id=?").bind(b.accept ? "confirmed" : "declined", +b.id, user.id).run();
    return J({ ok: true, status: b.accept ? "confirmed" : "declined" });
  }

  if (path === "/api/blog/delete" && method === "POST") {
    const b = await request.json().catch(() => ({})), p = await db.prepare("SELECT b.id,b.user_id,b.lang,b.slug,b.title,p.handle FROM blog_posts b LEFT JOIN profiles p ON p.user_id=b.user_id WHERE b.id=? AND (b.user_id=? OR ?=1)").bind(+b.id, user.id, user.admin ? 1 : 0).first();
    if (!p) return J({ error: "not_found" }, 404);
    if (p.handle) await syncFeed(env, db, p.user_id, p, p.handle, false);
    await db.prepare("DELETE FROM comments WHERE vid=?").bind("blog" + p.id).run();
    await db.batch([db.prepare("DELETE FROM blog_votes WHERE post_id=?").bind(p.id), db.prepare("DELETE FROM blog_coauthors WHERE post_id=?").bind(p.id), db.prepare("DELETE FROM blog_posts WHERE id=?").bind(p.id)]);
    return J({ ok: true });
  }

  if (path === "/api/blog/following" && method === "GET") {
    return J({ following: ((await db.prepare("SELECT handle FROM blog_follows WHERE user_id=?").bind(user.id).all()).results || []).map((x) => x.handle) });
  }
  if (path === "/api/blog/follow" && method === "POST") {
    if (!(await rateLimit(db, `blogf:${user.id}`, 60, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await request.json().catch(() => ({})), h = String(b.handle || "");
    const pr = await db.prepare("SELECT user_id FROM profiles WHERE handle=? AND public=1").bind(h).first(); if (!pr) return J({ error: "not_found" }, 404);
    if (pr.user_id === user.id) return J({ error: "own" }, 400);
    if (b.on) await db.prepare("INSERT OR IGNORE INTO blog_follows(user_id,handle,created) VALUES(?,?,?)").bind(user.id, h, now()).run();
    else await db.prepare("DELETE FROM blog_follows WHERE user_id=? AND handle=?").bind(user.id, h).run();
    return J({ ok: true, following: !!b.on });
  }

  if (path === "/api/blog/vote" && method === "POST") {
    if (!(await rateLimit(db, `blogv:${user.id}`, 60, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await request.json().catch(() => ({}));
    const p = await db.prepare("SELECT b.id,b.user_id FROM blog_posts b JOIN profiles p ON p.user_id=b.user_id AND p.handle=? WHERE b.slug=? AND b.status='live'").bind(String(b.handle || ""), String(b.slug || "")).first();
    if (!p) return J({ error: "not_found" }, 404);
    if (p.user_id === user.id) return J({ error: "own" }, 400);
    const has = await db.prepare("SELECT 1 x FROM blog_votes WHERE post_id=? AND user_id=?").bind(p.id, user.id).first();
    if (has) await db.prepare("DELETE FROM blog_votes WHERE post_id=? AND user_id=?").bind(p.id, user.id).run();
    else await db.prepare("INSERT INTO blog_votes(post_id,user_id,created) VALUES(?,?,?)").bind(p.id, user.id, now()).run();
    const n = (await db.prepare("SELECT COUNT(*) n FROM blog_votes WHERE post_id=?").bind(p.id).first()).n;
    return J({ ok: true, votes: n, voted: !has });
  }
  return null;
}
