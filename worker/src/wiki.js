// Community-Wiki fuer Glossarbegriffe: kurze Ergaenzung zur Kurzinfo, Revisionen, Moderation
import { cleanText, rateLimit, isLang } from "./util.js";
import { stats, evalBadges } from "./badges.js";

const TERM = /^[a-z0-9-]{2,48}$/;
const okLang = (l) => l === "en" || isLang(l);
const now = () => Math.floor(Date.now() / 1000);
const TRUST_POINTS = 25;   // ab so vielen Punkten duerfen Beitraege sofort live gehen
const AUTO_REVERT = 3;     // so viele Meldungen blenden eine Revision aus

const clean = (s) => cleanText(s, 1500).replace(/https?:\/\/\S+/gi, "").replace(/www\.\S+/gi, "").replace(/[<>]/g, "").trim();

async function liveOf(db, term, lang) {
  return await db.prepare(
    "SELECT r.id,r.body,r.summary,r.created,r.user_id,COALESCE(u.name,'') name FROM wiki_rev r LEFT JOIN users u ON u.id=r.user_id AND u.banned=0 WHERE r.term=? AND r.lang=? AND r.status='live' ORDER BY r.created DESC LIMIT 1").bind(term, lang).first();
}

export async function handleWiki(env, request, url, path, user, J) {
  const db = env.DB, method = request.method;
  const need = () => (user ? null : J({ error: "login" }, 401));

  if (path === "/api/wiki" && method === "GET") {
    const term = url.searchParams.get("term"), lang = url.searchParams.get("lang");
    if (!TERM.test(term || "") || !okLang(lang)) return J({ error: "bad_request" }, 400);
    const live = await liveOf(db, term, lang);
    const hist = ((await db.prepare("SELECT r.id,r.summary,r.created,COALESCE(u.name,'') name FROM wiki_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.term=? AND r.lang=? AND r.status IN ('live','old') ORDER BY r.created DESC LIMIT 10").bind(term, lang).all()).results || []);
    let mine = null, trusted = false;
    if (user) {
      mine = await db.prepare("SELECT id,body,created FROM wiki_rev WHERE term=? AND lang=? AND user_id=? AND status='pending' ORDER BY created DESC LIMIT 1").bind(term, lang, user.id).first();
      trusted = user.admin || user.editor || (await stats(db, user.id)).points >= TRUST_POINTS;
    }
    return J({ live: live ? { id: live.id, body: live.body, name: live.name || "", created: live.created } : null, history: hist, mine, loggedIn: !!user, trusted, admin: !!(user?.admin || user?.editor), owner: !!user?.admin });
  }

  if (path === "/api/wiki" && method === "POST") {
    if (need()) return need();
    const b = await request.json().catch(() => ({}));
    const term = b.term, lang = b.lang, body = clean(b.body), summary = cleanText(b.summary || "", 140).replace(/[<>]/g, "");
    if (!TERM.test(term || "") || !okLang(lang)) return J({ error: "bad_request" }, 400);
    if (body.length < 20) return J({ error: "too_short" }, 400);
    if (!(await rateLimit(db, `wiki:h:${user.id}`, 6, 3600)) || !(await rateLimit(db, `wiki:d:${user.id}`, 25, 86400))) return J({ error: "rate_limit" }, 429);
    const cur = await liveOf(db, term, lang);
    if (cur && cur.body === body) return J({ error: "unchanged" }, 400);
    const trusted = user.admin || user.editor || (await stats(db, user.id)).points >= TRUST_POINTS;
    const t = now();
    if (trusted) {
      await db.batch([
        db.prepare("UPDATE wiki_rev SET status='old' WHERE term=? AND lang=? AND status='live'").bind(term, lang),
        db.prepare("INSERT INTO wiki_rev(term,lang,body,summary,user_id,status,created) VALUES(?,?,?,?,?,'live',?)").bind(term, lang, body, summary, user.id, t),
      ]);
      await evalBadges(env, user.id);
      return J({ ok: true, status: "live" });
    }
    await db.prepare("DELETE FROM wiki_rev WHERE term=? AND lang=? AND user_id=? AND status='pending'").bind(term, lang, user.id).run();   // je Nutzer nur ein offener Vorschlag
    await db.prepare("INSERT INTO wiki_rev(term,lang,body,summary,user_id,status,created) VALUES(?,?,?,?,?,'pending',?)").bind(term, lang, body, summary, user.id, t).run();
    return J({ ok: true, status: "pending" });
  }

  let m;
  if ((m = /^\/api\/wiki\/report\/(\d+)$/.exec(path)) && method === "POST") {
    if (need()) return need();
    const id = +m[1];
    const r = await db.prepare("SELECT id,term,lang,status,user_id FROM wiki_rev WHERE id=?").bind(id).first();
    if (!r || r.status !== "live" || r.user_id === user.id) return J({ error: "bad_request" }, 400);
    await db.prepare("INSERT OR IGNORE INTO wiki_reports(rev_id,user_id,created) VALUES(?,?,?)").bind(id, user.id, now()).run();
    const n = (await db.prepare("SELECT COUNT(*) n FROM wiki_reports WHERE rev_id=?").bind(id).first()).n;
    if (n >= AUTO_REVERT) await revert(db, r);
    return J({ ok: true });
  }

  if (path === "/api/wiki/export" && method === "GET") {   // oeffentlich: freigegebene Texte fuer den statischen Seitenbau
    const lang = url.searchParams.get("lang");
    if (!okLang(lang)) return J({ error: "bad_request" }, 400);
    const rows = (await db.prepare("SELECT r.term,r.body,r.created,COALESCE(u.name,'') name FROM wiki_rev r LEFT JOIN users u ON u.id=r.user_id AND u.banned=0 WHERE r.lang=? AND r.status='live'").bind(lang).all()).results || [];
    return J({ items: rows }, 200, { "cache-control": "public, max-age=300" });
  }

  if (path.startsWith("/api/admin/wiki")) {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    if (path === "/api/admin/wiki/pending" && method === "GET") {
      const rows = (await db.prepare("SELECT r.id,r.term,r.lang,r.body,r.summary,r.created,COALESCE(u.name,'') name FROM wiki_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.status='pending' ORDER BY r.created ASC LIMIT 50").all()).results || [];
      return J({ pending: rows });
    }
    if ((m = /^\/api\/admin\/wiki\/(approve|reject|restore)\/(\d+)$/.exec(path)) && method === "POST") {
      const r = await db.prepare("SELECT id,term,lang,status,user_id FROM wiki_rev WHERE id=?").bind(+m[2]).first();
      if (!r) return J({ error: "not_found" }, 404);
      if (m[1] === "reject") { await db.prepare("UPDATE wiki_rev SET status='rejected' WHERE id=?").bind(r.id).run(); return J({ ok: true }); }
      await db.batch([
        db.prepare("UPDATE wiki_rev SET status='old' WHERE term=? AND lang=? AND status='live'").bind(r.term, r.lang),
        db.prepare("UPDATE wiki_rev SET status='live' WHERE id=?").bind(r.id),
      ]);
      if (r.user_id) await evalBadges(env, r.user_id);
      return J({ ok: true });
    }
  }
  return null;
}

async function revert(db, r) {   // gemeldete Revision ausblenden, vorherige Fassung wieder live
  const prev = await db.prepare("SELECT id FROM wiki_rev WHERE term=? AND lang=? AND status='old' AND id<? ORDER BY id DESC LIMIT 1").bind(r.term, r.lang, r.id).first();
  const ops = [db.prepare("UPDATE wiki_rev SET status='rejected' WHERE id=?").bind(r.id)];
  if (prev) ops.push(db.prepare("UPDATE wiki_rev SET status='live' WHERE id=?").bind(prev.id));
  await db.batch(ops);
}
