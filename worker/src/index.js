// Community-API (Cloudflare Worker + D1): Login (Google/Microsoft), Kommentare, Abzeichen, Kurator, Push, E-Mail
import { json, cors, cookie, makeSession, readSession, cleanText, cleanName, randomToken, rateLimit, isLang, esc, b64u, sign, verify } from "./util.js";
import { evalBadges, stats, topUsers, badgesFor, award } from "./badges.js";
import { runDigest, sendMail } from "./digest.js";
import { handleEntity } from "./entities.js";
import { handleProfiles, deleteUserData } from "./profiles.js";
import { handleEvents, deleteUserEvents, ensureM365Con } from "./events.js";
import { handleVotes } from "./votes.js";
import { handleQa, deleteUserQa } from "./qa.js";
import { handleBlog, deleteUserBlog } from "./blog.js";
import { handleUpdates, pollUpdates } from "./updates.js";
import { handleLibrary, deleteUserLibrary } from "./library.js";
import { handleDemo } from "./demo.js";
import { handleGuests, deleteUserGuests } from "./guests.js";
import { handlePodcast, deleteUserPodcast, pollPodcast } from "./podcast.js";
import { handleVideo, deleteUserVideos, pollVideos } from "./youtube.js";
import { handleMcp, handleTokens, deleteUserTokens } from "./mcp.js";
import { handlePoints } from "./points.js";
import { handleMessages, purgeMessages, deleteUserMessages } from "./messages.js";
import { refreshFeeds } from "./feeds.js";
import { autoTranslate, translateStatus, uiI18nExport } from "./translate.js";
import { handleWiki } from "./wiki.js";

const PROVIDERS = {
  google: {
    auth: "https://accounts.google.com/o/oauth2/v2/auth", token: "https://oauth2.googleapis.com/token",
    info: "https://openidconnect.googleapis.com/v1/userinfo", scope: "openid profile", id: (e) => e.GOOGLE_CLIENT_ID, secret: (e) => e.GOOGLE_CLIENT_SECRET,
  },
  microsoft: {
    auth: "https://login.microsoftonline.com/common/oauth2/v2.0/authorize", token: "https://login.microsoftonline.com/common/oauth2/v2.0/token",
    info: "https://graph.microsoft.com/oidc/userinfo", scope: "openid profile", id: (e) => e.MS_CLIENT_ID, secret: (e) => e.MS_CLIENT_SECRET,
  },
  linkedin: {   // "Sign In with LinkedIn using OpenID Connect"
    auth: "https://www.linkedin.com/oauth/v2/authorization", token: "https://www.linkedin.com/oauth/v2/accessToken",
    info: "https://api.linkedin.com/v2/userinfo", scope: "openid profile", id: (e) => e.LINKEDIN_CLIENT_ID, secret: (e) => e.LINKEDIN_CLIENT_SECRET,
  },
};
const VID = /^[A-Za-z0-9_-]{5,24}$/;
const okCl = (vid, lang) => isLang(lang) || (lang === "en" && /^(blog|podcast|video|lib)\d+$/.test(vid));   // Blog-Beitraege gibt es auch auf Englisch
const now = () => Math.floor(Date.now() / 1000);
const ip = (r) => r.headers.get("cf-connecting-ip") || "0";
const html = (body, status = 200) => new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><body style="font-family:system-ui;max-width:32em;margin:12vh auto;padding:0 16px;line-height:1.5">${body}`, { status, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });

// "Mirko Peters" -> "Mirko P." (Datenschutz: nur Vorname + Initiale als Standard)
function shortName(full) {
  const p = cleanName(full).split(" ").filter(Boolean);
  if (p.length < 2) return p[0] || "User";
  return `${p[0]} ${[...p[p.length - 1]][0]}.`;
}
const safeReturn = (env, u) => { try { const x = new URL(u); return x.origin === env.SITE ? x.href : env.SITE + "/"; } catch { return env.SITE + "/"; } };
const isAdmin = (env, u) => (env.ADMIN_SUBS || "").split(",").map((s) => s.trim()).includes(`${u.provider}:${u.sub}`);

const firstName = (full) => cleanName(full).split(" ").filter(Boolean)[0] || "";
async function namePrefs(db, user) {
  const r = await db.prepare("SELECT real_name,name_mode FROM user_prefs WHERE user_id=?").bind(user.id).first();
  const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=?").bind(user.id).first();
  const real = r?.real_name || "";
  return { name_mode: r?.name_mode || "short", name_opts: { short: real ? shortName(real) : "", full: real, first: firstName(real), handle: pr?.handle || "" } };
}
// Rechnet den Anzeigenamen aus dem gewaehlten Modus; liefert null bei "custom" (dann gilt der eingegebene Name)
async function applyNameMode(db, user, b) {
  const mode = ["short", "full", "first", "handle", "custom"].includes(b.name_mode) ? b.name_mode : null;
  if (!mode) return null;
  const { name_opts: o } = await namePrefs(db, user);
  await db.prepare("INSERT INTO user_prefs(user_id,name_mode) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET name_mode=excluded.name_mode").bind(user.id, mode).run();
  if (mode === "custom") return null;
  return cleanName(o[mode]) || null;
}

async function upsertUser(env, provider, sub, name) {
  const db = env.DB;
  let u = await db.prepare("SELECT * FROM users WHERE provider=? AND sub=?").bind(provider, sub).first();
  if (!u) {
    const r = await db.prepare("INSERT INTO users(provider,sub,name,created) VALUES(?,?,?,?)").bind(provider, sub, shortName(name), now()).run();
    u = await db.prepare("SELECT * FROM users WHERE id=?").bind(r.meta.last_row_id).first();
  }
  const rn = cleanName(name);
  if (rn) await env.DB.prepare("INSERT INTO user_prefs(user_id,real_name) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET real_name=excluded.real_name").bind(u.id, rn).run();
  await evalBadges(env, u.id);
  return u;
}

async function auth(env, request, url, path) {
  const m = /^\/auth\/(login|callback)\/(google|microsoft|linkedin)$/.exec(path);
  if (path === "/auth/dev" && env.DEV_LOGIN === "1") {
    const u = await upsertUser(env, "dev", url.searchParams.get("name") || "dev", url.searchParams.get("name") || "Dev User");
    return new Response(null, { status: 302, headers: { location: safeReturn(env, url.searchParams.get("return") || env.SITE), "set-cookie": cookie("m365s", await makeSession(env, u.id), 5184000) } });
  }
  if (!m) return null;
  const P = PROVIDERS[m[2]];
  if (!P.id(env) || !P.secret(env)) return html("<p>Login not configured.</p>", 503);
  const redirect = `${env.API}/auth/callback/${m[2]}`;
  if (m[1] === "login") {
    const state = randomToken(16), ret = safeReturn(env, url.searchParams.get("return") || env.SITE);
    const val = `${state}|${b64u.enc(new TextEncoder().encode(ret))}`;
    const q = new URLSearchParams({ client_id: P.id(env), redirect_uri: redirect, response_type: "code", scope: P.scope, state, ...(m[2] === "linkedin" ? {} : { prompt: "select_account" }) });
    return new Response(null, { status: 302, headers: { location: `${P.auth}?${q}`, "set-cookie": cookie("m365o", `${val}.${await sign(env.SESSION_SECRET, val)}`, 600) } });
  }
  // callback
  const c = /(?:^|;\s*)m365o=([^;]+)/.exec(request.headers.get("cookie") || "");
  const code = url.searchParams.get("code"), st = url.searchParams.get("state");
  if (!c || !code || !st) return html("<p>Login failed (missing data). Please try again.</p>", 400);
  const dot = c[1].lastIndexOf("."), val = c[1].slice(0, dot);
  if (!(await verify(env.SESSION_SECRET, val, c[1].slice(dot + 1))) || val.split("|")[0] !== st) return html("<p>Login failed (invalid state).</p>", 400);
  const ret = safeReturn(env, new TextDecoder().decode(b64u.dec(val.split("|")[1])));
  const tr = await fetch(P.token, { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ code, client_id: P.id(env), client_secret: P.secret(env), redirect_uri: redirect, grant_type: "authorization_code" }) });
  if (!tr.ok) return html("<p>Login failed (token).</p>", 400);
  const tok = await tr.json();
  const ir = await fetch(P.info, { headers: { authorization: `Bearer ${tok.access_token}` } });
  if (!ir.ok) return html("<p>Login failed (profile).</p>", 400);
  const info = await ir.json();
  if (!info.sub) return html("<p>Login failed.</p>", 400);
  const u = await upsertUser(env, m[2], String(info.sub), info.name || info.given_name || "User");
  if (u.banned) return html("<p>This account is blocked.</p>", 403);
  const h = new Headers({ location: ret });
  h.append("set-cookie", cookie("m365s", await makeSession(env, u.id), 5184000));
  h.append("set-cookie", cookie("m365o", "", 0));
  return new Response(null, { status: 302, headers: h });
}

async function me(env, uid) {
  const u = await env.DB.prepare("SELECT id,provider,sub,name,bio,lang,banned,role,created FROM users WHERE id=?").bind(uid).first();
  if (!u || u.banned) return null;
  const pro = !!(await env.DB.prepare("SELECT 1 x FROM programs WHERE owner_type='u' AND owner_id=? AND verified=1 AND program IN ('mvp','mct','rd','msa','ms_employee') LIMIT 1").bind(uid).first());
  return { ...u, admin: isAdmin(env, u), editor: u.role === "editor", pro };
}

function pubComment(c, mine, liked, badges, admin) {
  return { id: c.id, parent: c.parent_id, user: { id: c.user_id, name: c.name, badges: badges.get(c.user_id) || [] }, body: c.status === "hidden" ? "" : c.body,
    hidden: c.status === "hidden", created: c.created, likes: c.likes, liked: liked.has(c.id), mine: mine === c.user_id, canDelete: mine === c.user_id || admin };
}

async function api(env, request, url, path) {
  const method = request.method, J = (d, s = 200, x) => json(d, s, env, request, x);
  if (method === "OPTIONS") return new Response(null, { status: 204, headers: cors(env, request) });
  if (method !== "GET" && request.headers.get("x-requested-with") !== "m365") return J({ error: "bad_request" }, 400);
  const uid = await readSession(env, request), user = uid ? await me(env, uid) : null;
  const need = () => (user ? null : J({ error: "login" }, 401));
  const db = env.DB;

  if (path === "/api/health") return J({ ok: true }, 200);
  if (path === "/api/providers") return J({ providers: Object.keys(PROVIDERS).filter((k) => PROVIDERS[k].id(env) && PROVIDERS[k].secret(env)) }, 200, { "cache-control": "public, max-age=300" });
  if (path === "/api/me/li-follow" && method === "POST") {
    if (need()) return need();
    await award(db, user.id, "li_follower");
    return J({ ok: true });
  }
  if (path === "/api/me") {
    if (method === "GET") return J({ user: user ? { ...(await namePrefs(db, user)), id: user.id, name: user.name, bio: user.bio, lang: user.lang, admin: user.admin, editor: user.editor, provider: user.provider, ...(user.admin || user.editor ? {} : { sub_hint: `${user.provider}:${user.sub}` }), ...(await stats(db, user.id)) } : null });
    if (need()) return need();
    if (method === "POST") {
      const b = await request.json().catch(() => ({}));
      const nm = await applyNameMode(db, user, b);
      const name = nm || cleanName(b.name || user.name) || user.name, bio = cleanText(b.bio ?? user.bio, 280).replace(/https?:\/\/\S+/g, ""), lang = isLang(b.lang) ? b.lang : user.lang;
      await db.prepare("UPDATE users SET name=?,bio=?,lang=? WHERE id=?").bind(name, bio, lang, user.id).run();
      return J({ ok: true });
    }
    if (method === "DELETE") {   // Konto + alle eigenen Daten loeschen (DSGVO)
      const id = user.id;
      await db.batch([
        db.prepare("DELETE FROM likes WHERE user_id=? OR comment_id IN (SELECT id FROM comments WHERE user_id=?)").bind(id, id),
        db.prepare("DELETE FROM reports WHERE user_id=? OR comment_id IN (SELECT id FROM comments WHERE user_id=?)").bind(id, id),
        db.prepare("DELETE FROM comments WHERE user_id=?").bind(id), db.prepare("DELETE FROM user_badges WHERE user_id=?").bind(id),
        db.prepare("DELETE FROM push_subs WHERE user_id=?").bind(id), db.prepare("DELETE FROM wiki_reports WHERE user_id=?").bind(id), db.prepare("DELETE FROM wiki_rev WHERE user_id=? AND status IN ('pending','rejected')").bind(id), db.prepare("UPDATE wiki_rev SET user_id=0 WHERE user_id=?").bind(id), db.prepare("DELETE FROM curators WHERE user_id=?").bind(id), db.prepare("DELETE FROM users WHERE id=?").bind(id),
      ]);
      await deleteUserEvents(db, id);
      await deleteUserMessages(db, id); await deleteUserTokens(db, id); await deleteUserQa(db, id); await deleteUserBlog(db, id); await deleteUserLibrary(db, id); await deleteUserPodcast(db, id); await deleteUserVideos(db, id); await deleteUserGuests(db, id);
      await deleteUserData(db, id);
      return J({ ok: true }, 200, { "set-cookie": cookie("m365s", "", 0) });
    }
  }
  if (path === "/api/logout" && method === "POST") return J({ ok: true }, 200, { "set-cookie": cookie("m365s", "", 0) });

  if (path === "/api/comments" && method === "GET") {
    const vid = url.searchParams.get("vid"), lang = url.searchParams.get("lang");
    if (!VID.test(vid || "") || !okCl(vid, lang)) return J({ error: "bad_request" }, 400);
    const rows = (await db.prepare(
      `SELECT c.id,c.user_id,c.parent_id,c.body,c.status,c.created,u.name,(SELECT COUNT(*) FROM likes l WHERE l.comment_id=c.id) likes
       FROM comments c JOIN users u ON u.id=c.user_id WHERE c.vid=? AND c.lang=? AND u.banned=0 ORDER BY c.created ASC LIMIT 300`).bind(vid, lang).all()).results || [];
    const badges = await badgesFor(db, [...new Set(rows.map((r) => r.user_id))]);
    const liked = new Set(user ? ((await db.prepare("SELECT comment_id FROM likes WHERE user_id=?").bind(user.id).all()).results || []).map((r) => r.comment_id) : []);
    return J({ comments: rows.filter((r) => r.status === "ok" || rows.some((x) => x.parent_id === r.id)).map((r) => pubComment(r, user?.id, liked, badges, user?.admin)) }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/comments" && method === "POST") {
    if (need()) return need();
    const b = await request.json().catch(() => ({}));
    const body = cleanText(b.body, 1500), vid = b.vid, lang = b.lang;
    if (!VID.test(vid || "") || !okCl(vid, lang) || body.length < 2) return J({ error: "bad_request" }, 400);
    if ((body.match(/https?:\/\//gi) || []).length > 2) return J({ error: "links" }, 400);
    if (!(await rateLimit(db, `c20:${user.id}`, 1, 20)) || !(await rateLimit(db, `c24:${user.id}`, 30, 86400))) return J({ error: "rate" }, 429);
    let parent = null;
    if (b.parent) {
      const p = await db.prepare("SELECT id,vid,lang,parent_id FROM comments WHERE id=?").bind(+b.parent).first();
      if (!p || p.vid !== vid || p.lang !== lang) return J({ error: "bad_request" }, 400);
      parent = p.parent_id || p.id;   // nur eine Ebene
    }
    const r = await db.prepare("INSERT INTO comments(vid,lang,user_id,parent_id,body,created) VALUES(?,?,?,?,?,?)").bind(vid, lang, user.id, parent, body, now()).run();
    const earned = await evalBadges(env, user.id);
    return J({ ok: true, id: r.meta.last_row_id, earned });
  }
  let m;
  if ((m = /^\/api\/comments\/(\d+)\/(like|report)$/.exec(path)) && method === "POST") {
    if (need()) return need();
    const id = +m[1], c = await db.prepare("SELECT id,user_id,status FROM comments WHERE id=?").bind(id).first();
    if (!c) return J({ error: "not_found" }, 404);
    if (!(await rateLimit(db, `a60:${user.id}`, 60, 3600))) return J({ error: "rate" }, 429);
    if (m[2] === "like") {
      if (c.user_id === user.id) return J({ error: "own" }, 400);
      const ex = await db.prepare("SELECT 1 x FROM likes WHERE comment_id=? AND user_id=?").bind(id, user.id).first();
      if (ex) await db.prepare("DELETE FROM likes WHERE comment_id=? AND user_id=?").bind(id, user.id).run();
      else { await db.prepare("INSERT INTO likes(comment_id,user_id,created) VALUES(?,?,?)").bind(id, user.id, now()).run(); await evalBadges(env, c.user_id); }
      return J({ ok: true, liked: !ex });
    }
    await db.prepare("INSERT OR IGNORE INTO reports(comment_id,user_id,created) VALUES(?,?,?)").bind(id, user.id, now()).run();
    const n = (await db.prepare("SELECT COUNT(*) n FROM reports WHERE comment_id=?").bind(id).first()).n;
    if (n >= 3 && c.status === "ok") {
      await db.prepare("UPDATE comments SET status='hidden' WHERE id=?").bind(id).run();
      const rs = (await db.prepare("SELECT user_id FROM reports WHERE comment_id=?").bind(id).all()).results || [];
      for (const r of rs) await evalBadges(env, r.user_id);
    }
    return J({ ok: true });
  }
  if ((m = /^\/api\/comments\/(\d+)$/.exec(path)) && method === "DELETE") {
    if (need()) return need();
    const c = await db.prepare("SELECT user_id FROM comments WHERE id=?").bind(+m[1]).first();
    if (!c || (c.user_id !== user.id && !user.admin)) return J({ error: "forbidden" }, 403);
    await db.batch([db.prepare("DELETE FROM likes WHERE comment_id=?").bind(+m[1]), db.prepare("DELETE FROM reports WHERE comment_id=?").bind(+m[1]), db.prepare("DELETE FROM comments WHERE id=? OR parent_id=?").bind(+m[1], +m[1])]);
    return J({ ok: true });
  }

  if (/^\/api\/points(\/|$)/.test(path) || path.startsWith("/api/admin/points/")) { const p = await handlePoints(env, request, url, path, user, J); if (p) return p; }
  if (/^\/api\/msg(\/|$)/.test(path)) { const p = await handleMessages(env, request, url, path, user, J); if (p) { if (user && method !== "GET") await evalBadges(env, user.id).catch(() => 0); return p; } }
  if (/^\/api\/(events?|speaker)(\/|$)/.test(path) || /^\/api\/entity\/claims?(\/|$)/.test(path) || /^\/api\/admin\/entity\/claims?$/.test(path)) { const p = await handleEvents(env, request, url, path, user, J); if (p) { if (user && method !== "GET") await evalBadges(env, user.id).catch(() => 0); return p; } }
  if (path === "/api/ui-i18n" && request.method === "GET") return J(await uiI18nExport(env), 200, { "cache-control": "public, max-age=300" });
  if (path === "/api/admin/translate" && user?.admin) {   // Status und Notaus der Auto-Uebersetzung
    if (request.method === "POST") { const b = await request.json().catch(() => ({})); await env.DB.prepare("INSERT INTO meta(k,v) VALUES('tr_off',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(b.off ? "1" : "0").run(); }
    return J(await translateStatus(env));
  }
  if (path.startsWith("/api/ai-token")) { const k = await handleTokens(env, request, url, path, user, J); if (k) return k; }
  if (path === "/api/admin/demo") { const q = await handleDemo(env, request, url, path, user, J); if (q) return q; }
  if (path.startsWith("/api/guests/")) { const q = await handleGuests(env, request, url, path, user, J); if (q) return q; }
  if (path.startsWith("/api/video/") || path.startsWith("/api/admin/video")) { const q = await handleVideo(env, request, url, path, user, J); if (q) { if (user && method !== "GET") await evalBadges(env, user.id).catch(() => 0); return q; } }
  if (path.startsWith("/api/podcast/") || path.startsWith("/api/admin/podcast")) { const q = await handlePodcast(env, request, url, path, user, J); if (q) { if (user && method !== "GET") await evalBadges(env, user.id).catch(() => 0); return q; } }
  if (path === "/api/updates/export" || path === "/api/admin/updates/poll") { const q = await handleUpdates(env, request, url, path, user, J); if (q) return q; }
  if (path.startsWith("/api/library/")) { const q = await handleLibrary(env, request, url, path, user, J); if (q) return q; }
  if (path === "/api/blog" || path.startsWith("/api/blog/") || path.startsWith("/api/admin/blog")) { const q = await handleBlog(env, request, url, path, user, J); if (q) { if (user && method !== "GET") await evalBadges(env, user.id).catch(() => 0); return q; } }
  if (path === "/api/qa" || path.startsWith("/api/qa/")) { const q = await handleQa(env, request, url, path, user, J); if (q) return q; }
  if (path.startsWith("/api/edits/")) { const v = await handleVotes(env, request, url, path, user, J); if (v) return v; }
  if (path.startsWith("/api/entity") || path.startsWith("/api/admin/entity")) { const e = await handleEntity(env, request, url, path, user, J); if (e) return e; }
  if (/^\/api\/(profile|profiles|endorse|cert-endorse|vote|feed|org|orgs|img|recommend)(\/|$)/.test(path) || path === "/api/admin/verify" || path === "/api/admin/cert-queue" || path === "/api/admin/feed-hide") { const p = await handleProfiles(env, request, url, path, user, J); if (p) { if (user && method !== "GET") await evalBadges(env, user.id).catch(() => 0); return p; } }
  if (path === "/api/wiki" || path.startsWith("/api/wiki/") || path.startsWith("/api/admin/wiki")) { const w = await handleWiki(env, request, url, path, user, J); if (w) return w; }

  if (path === "/api/curator" && method === "GET") {
    const lang = url.searchParams.get("lang");
    if (!isLang(lang)) return J({ error: "bad_request" }, 400);
    const d = new Date(), since = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000;
    const top = await topUsers(db, lang, since, 5), bm = await badgesFor(db, top.map((t) => t.id));
    const last = await db.prepare("SELECT c.month,c.points,u.id,u.name,u.bio FROM curators c JOIN users u ON u.id=c.user_id WHERE c.lang=? ORDER BY c.month DESC LIMIT 1").bind(lang).first();
    return J({ month: d.toISOString().slice(0, 7), top: top.map((t) => ({ ...t, badges: bm.get(t.id) || [] })), last: last || null }, 200, { "cache-control": "public, max-age=300" });
  }
  if ((m = /^\/api\/u\/(\d+)$/.exec(path)) && method === "GET") {
    const u = await db.prepare("SELECT id,name,bio,lang,created FROM users WHERE id=? AND banned=0").bind(+m[1]).first();
    if (!u) return J({ error: "not_found" }, 404);
    const rc = (await db.prepare("SELECT vid,lang,substr(body,1,160) body,created FROM comments WHERE user_id=? AND status='ok' ORDER BY created DESC LIMIT 5").bind(u.id).all()).results || [];
    const cur = (await db.prepare("SELECT lang,month FROM curators WHERE user_id=? ORDER BY month DESC").bind(u.id).all()).results || [];
    return J({ user: u, ...(await stats(db, u.id)), recent: rc, curator: cur }, 200, { "cache-control": "public, max-age=120" });
  }

  if (path === "/api/push/key" && method === "GET") return J({ key: env.VAPID_PUBLIC || "" });
  if (path === "/api/push/subscribe" && method === "POST") {
    const b = await request.json().catch(() => ({}));
    const e = b.endpoint, k = b.keys || {};
    if (!/^https:\/\//.test(e || "") || e.length > 600 || !k.p256dh || !k.auth || !isLang(b.lang)) return J({ error: "bad_request" }, 400);
    if (!(await rateLimit(db, `ps:${ip(request)}`, 20, 3600))) return J({ error: "rate" }, 429);
    await db.prepare("INSERT OR REPLACE INTO push_subs(endpoint,p256dh,auth,lang,user_id,created) VALUES(?,?,?,?,?,?)").bind(e, String(k.p256dh), String(k.auth), b.lang, user?.id ?? null, now()).run();
    if (user) await award(db, user.id, "notified");
    return J({ ok: true });
  }
  if (path === "/api/push/unsubscribe" && method === "POST") {
    const b = await request.json().catch(() => ({}));
    if (b.endpoint) await db.prepare("DELETE FROM push_subs WHERE endpoint=?").bind(String(b.endpoint)).run();
    return J({ ok: true });
  }

  if (path === "/api/email/subscribe" && method === "POST") {
    const b = await request.json().catch(() => ({}));
    const email = String(b.email || "").trim().toLowerCase();
    if (!/^[^\s@<>]{1,64}@[^\s@<>]{1,190}\.[a-z]{2,}$/.test(email) || !isLang(b.lang)) return J({ error: "bad_request" }, 400);
    if (!(await rateLimit(db, `em:${ip(request)}`, 5, 3600)) || !(await rateLimit(db, `em:${email}`, 3, 86400))) return J({ error: "rate" }, 429);
    const ex = await db.prepare("SELECT token,confirmed FROM email_subs WHERE email=? AND lang=?").bind(email, b.lang).first();
    if (ex?.confirmed) return J({ ok: true });
    const token = ex?.token || randomToken(18);
    if (!ex) await db.prepare("INSERT INTO email_subs(email,lang,token,confirmed,created) VALUES(?,?,?,0,?)").bind(email, b.lang, token, now()).run();
    const link = `${env.API}/api/email/confirm?token=${encodeURIComponent(token)}&lang=${b.lang}`;
    await sendMail(env, email, "M365.FM – please confirm / bitte bestätigen",
      `<p>Please confirm your subscription to new M365.FM episodes (${esc(b.lang)}):</p><p><a href="${link}">${link}</a></p><p>Bitte bestätige dein Abo neuer M365.FM-Folgen. Wenn du das nicht warst, ignoriere diese E-Mail.</p>`);
    return J({ ok: true });
  }
  if (path === "/api/email/confirm" && method === "GET") {
    const t = url.searchParams.get("token") || "", lang = isLang(url.searchParams.get("lang")) ? url.searchParams.get("lang") : "en";
    const r = await db.prepare("UPDATE email_subs SET confirmed=1 WHERE token=?").bind(t).run();
    return html(r.meta.changes ? `<h2>✓ Subscription confirmed</h2><p><a href="${env.SITE}/${lang}/">${env.SITE.replace("https://", "")}</a></p>` : "<p>Link invalid or expired.</p>", r.meta.changes ? 200 : 404);
  }
  if (path === "/api/email/unsub" && (method === "GET" || method === "POST")) {
    const t = url.searchParams.get("token") || "";
    await db.prepare("DELETE FROM email_subs WHERE token=?").bind(t).run();
    return method === "POST" ? new Response("ok") : html("<h2>✓ Unsubscribed</h2><p>You will not receive further e-mails.</p>");
  }

  if (path.startsWith("/api/admin/")) {
    const keyOk = env.CRON_KEY && url.searchParams.get("key") === env.CRON_KEY;
    if (path === "/api/admin/run-daily" && keyOk) return J(await runDigest(env, { dry: url.searchParams.get("dry") === "1" }));
    if (!user?.admin) return J({ error: "forbidden" }, 403);
    if (path === "/api/admin/reports" && method === "GET") {
      const rows = (await db.prepare("SELECT c.id,c.vid,c.lang,c.body,c.status,c.user_id,(SELECT COUNT(*) FROM reports r WHERE r.comment_id=c.id) n FROM comments c WHERE c.id IN (SELECT comment_id FROM reports) ORDER BY n DESC LIMIT 50").all()).results || [];
      return J({ reports: rows });
    }
    if ((m = /^\/api\/admin\/(hide|show)\/(\d+)$/.exec(path)) && method === "POST") { await db.prepare("UPDATE comments SET status=? WHERE id=?").bind(m[1] === "hide" ? "hidden" : "ok", +m[2]).run(); return J({ ok: true }); }
    if (path === "/api/admin/users" && method === "GET") {
      const q = cleanName(url.searchParams.get("q") || "").replace(/[%_]/g, "");
      const rows = (await db.prepare("SELECT id,name,role,banned FROM users WHERE name LIKE ? ORDER BY (role='editor') DESC, id DESC LIMIT 20").bind(`%${q}%`).all()).results || [];
      return J({ users: rows });
    }
    if ((m = /^\/api\/admin\/role\/(\d+)$/.exec(path)) && method === "POST") {
      const b = await request.json().catch(() => ({})), role = b.role === "editor" ? "editor" : "user";
      await db.prepare("UPDATE users SET role=? WHERE id=?").bind(role, +m[1]).run();
      await evalBadges(env, +m[1]);
      return J({ ok: true, role });
    }
    if ((m = /^\/api\/admin\/ban\/(\d+)$/.exec(path)) && method === "POST") { await db.prepare("UPDATE users SET banned=1 WHERE id=?").bind(+m[1]).run(); return J({ ok: true }); }
  }
  return J({ error: "not_found" }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url), path = url.pathname.replace(/\/+$/, "") || "/";
    try {
      if (path.startsWith("/auth/")) return (await auth(env, request, url, path)) || new Response("not found", { status: 404 });
      if (path === "/mcp") return await handleMcp(env, request, (uid) => me(env, uid));
      if (path.startsWith("/api/")) return await api(env, request, url, path);
      return new Response("M365.FM community API", { status: 200, headers: { "content-type": "text/plain" } });
    } catch (e) {
      console.log("error", path, String(e && e.stack || e).slice(0, 300));
      return json({ error: "server" }, 500, env, request);
    }
  },
  async scheduled(event, env, ctx) { if (event.cron === "0 6 * * *") ctx.waitUntil(runDigest(env)); ctx.waitUntil(refreshFeeds(env).catch(() => 0)); ctx.waitUntil(pollUpdates(env).catch(() => 0)); ctx.waitUntil(ensureM365Con(env).catch(() => 0)); ctx.waitUntil(purgeMessages(env.DB).catch(() => 0)); ctx.waitUntil(autoTranslate(env).catch(() => 0)); ctx.waitUntil(pollPodcast(env).catch(() => 0)); ctx.waitUntil(pollVideos(env).catch(() => 0)); },
};
