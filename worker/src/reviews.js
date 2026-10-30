// Hoerer-Bewertungen fuer den Podcast (Show "en" = M365.FM): 1–5 Sterne + Text, eine Bewertung je Mitglied, "hilfreich"-Stimmen, Moderation durch Admin/Editor.
import { cleanText, rateLimit } from "./util.js";
const now = () => Math.floor(Date.now() / 1000);
const SHOW = /^[a-z]{2,3}$/;
let ready = false;
async function ensure(db) {
  if (ready) return;
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS show_reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, show TEXT NOT NULL, user_id INTEGER NOT NULL, rating INTEGER NOT NULL, title TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'published', created INTEGER NOT NULL, updated INTEGER NOT NULL, UNIQUE(show,user_id))"),
    db.prepare("CREATE TABLE IF NOT EXISTS review_helpful (review_id INTEGER NOT NULL, user_id INTEGER NOT NULL, created INTEGER NOT NULL, PRIMARY KEY(review_id,user_id))"),
  ]);
  ready = true;
}
const strip = (s, n) => cleanText(String(s || "").replace(/<[^>]*>/g, " ").replace(/[ \t]+/g, " "), n).trim();

export async function handleReviews(env, request, url, path, user, J) {
  if (!path.startsWith("/api/reviews")) return null;
  const db = env.DB, method = request.method; await ensure(db);
  if (path === "/api/reviews" && method === "GET") {
    const show = SHOW.test(url.searchParams.get("show") || "") ? url.searchParams.get("show") : "en";
    const rows = (await db.prepare(`SELECT r.id,r.user_id,r.rating,r.title,r.body,r.created,COALESCE(u.name,'Member') name,(SELECT COUNT(*) FROM review_helpful h WHERE h.review_id=r.id) helpful,(SELECT handle FROM profiles p WHERE p.user_id=r.user_id AND p.public=1) handle FROM show_reviews r LEFT JOIN users u ON u.id=r.user_id AND u.banned=0 WHERE r.show=? AND r.status='published' ORDER BY helpful DESC, r.created DESC LIMIT 200`).bind(show).all().catch(() => ({ results: [] }))).results || [];
    const agg = await db.prepare("SELECT COUNT(*) n, COALESCE(SUM(rating),0) s, SUM(rating=5) c5, SUM(rating=4) c4, SUM(rating=3) c3, SUM(rating=2) c2, SUM(rating=1) c1 FROM show_reviews WHERE show=? AND status='published'").bind(show).first();
    let mine = null, voted = [];
    if (user) {
      mine = await db.prepare("SELECT id,rating,title,body,status FROM show_reviews WHERE show=? AND user_id=?").bind(show, user.id).first();
      voted = ((await db.prepare("SELECT review_id FROM review_helpful WHERE user_id=?").bind(user.id).all()).results || []).map((x) => x.review_id);
    }
    return J({ show, count: agg.n, sum: agg.s, dist: [agg.c1 || 0, agg.c2 || 0, agg.c3 || 0, agg.c4 || 0, agg.c5 || 0],
      items: rows.map((r) => ({ id: r.id, rating: r.rating, title: r.title, body: r.body, name: r.name, handle: r.handle || "", created: r.created, helpful: r.helpful, own: !!user && r.user_id === user.id, voted: voted.includes(r.id) })), mine, can_moderate: !!(user && (user.admin || user.editor)) },
      200, { "cache-control": user ? "no-store" : "public, max-age=60" });
  }
  if (!user) return J({ error: "login" }, 401);
  const body = async () => request.json().catch(() => ({}));
  if (path === "/api/reviews" && method === "POST") {
    const b = await body(), show = SHOW.test(b.show || "") ? b.show : "en", rating = Math.round(+b.rating), title = strip(b.title, 80), text = strip(b.body, 2000);
    if (!(rating >= 1 && rating <= 5)) return J({ error: "bad_rating" }, 400);
    if (text.length < 10 && !(rating && !text)) return J({ error: "too_short" }, 400);
    if (/https?:\/\/|www\./i.test(title + " " + text)) return J({ error: "no_links" }, 400);
    if (!(await rateLimit(db, `rev:${user.id}`, 10, 86400))) return J({ error: "rate_limit" }, 429);
    const old = await db.prepare("SELECT id,status FROM show_reviews WHERE show=? AND user_id=?").bind(show, user.id).first();
    if (old && old.status === "hidden") return J({ error: "hidden" }, 403);
    await db.prepare("INSERT INTO show_reviews(show,user_id,rating,title,body,status,created,updated) VALUES(?,?,?,?,?, 'published',?,?) ON CONFLICT(show,user_id) DO UPDATE SET rating=excluded.rating,title=excluded.title,body=excluded.body,updated=excluded.updated").bind(show, user.id, rating, title, text, now(), now()).run();
    return J({ ok: true });
  }
  if (path === "/api/reviews/helpful" && method === "POST") {
    const b = await body(), id = +b.id, r = await db.prepare("SELECT user_id FROM show_reviews WHERE id=? AND status='published'").bind(id).first();
    if (!r) return J({ error: "not_found" }, 404); if (r.user_id === user.id) return J({ error: "own" }, 403);
    if (!(await rateLimit(db, `revh:${user.id}`, 100, 3600))) return J({ error: "rate_limit" }, 429);
    const had = await db.prepare("SELECT 1 x FROM review_helpful WHERE review_id=? AND user_id=?").bind(id, user.id).first();
    if (had) await db.prepare("DELETE FROM review_helpful WHERE review_id=? AND user_id=?").bind(id, user.id).run(); else await db.prepare("INSERT INTO review_helpful(review_id,user_id,created) VALUES(?,?,?)").bind(id, user.id, now()).run();
    const n = await db.prepare("SELECT COUNT(*) n FROM review_helpful WHERE review_id=?").bind(id).first();
    return J({ ok: true, voted: !had, helpful: n.n });
  }
  if (path === "/api/reviews/delete" && method === "POST") {
    const b = await body(), id = +b.id, r = await db.prepare("SELECT user_id FROM show_reviews WHERE id=?").bind(id).first();
    if (!r || (r.user_id !== user.id && !user.admin && !user.editor)) return J({ error: "forbidden" }, 403);
    if (r.user_id === user.id && !(user.admin || user.editor)) await db.prepare("DELETE FROM show_reviews WHERE id=?").bind(id).run();
    else await db.prepare("UPDATE show_reviews SET status='hidden' WHERE id=?").bind(id).run();   // Moderation: ausblenden, Autor kann nicht neu schreiben
    return J({ ok: true });
  }
  return J({ error: "not_found" }, 404);
}
