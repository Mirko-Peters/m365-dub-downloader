// Roadmap & Wunschliste: alle angemeldeten Mitglieder sehen sie und stimmen ab; Admin uebernimmt (planned) und hakt ab (done)
import { cleanText, rateLimit } from "./util.js";

const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();
let ready = false;
async function ensure(db) {
  if (ready) return;
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS wish (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'open', note TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, updated INTEGER NOT NULL, done_at INTEGER NOT NULL DEFAULT 0)"),
    db.prepare("CREATE TABLE IF NOT EXISTS wish_votes (wish_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY (wish_id, user_id))"),
  ]);
  ready = true;
}
const STATUS = ["open", "planned", "done", "declined"];

export async function handleWish(env, request, url, path, user, J) {
  if (!path.startsWith("/api/wish/")) return null;
  const db = env.DB, method = request.method; await ensure(db);
  if (!user) return J({ error: "login" }, 401);                    // nur fuer Mitglieder mit Konto sichtbar
  if (path === "/api/wish/list" && method === "GET") {
    const rows = (await db.prepare("SELECT w.id,w.title,w.body,w.status,w.note,w.created,w.updated,w.done_at,w.user_id=? mine,COALESCE(u.name,'') name,(SELECT COUNT(*) FROM wish_votes v WHERE v.wish_id=w.id) votes,EXISTS(SELECT 1 FROM wish_votes v WHERE v.wish_id=w.id AND v.user_id=?) voted FROM wish w LEFT JOIN users u ON u.id=w.user_id ORDER BY w.created DESC LIMIT 500").bind(user.id, user.id).all()).results || [];
    return J({ admin: !!user.admin, items: rows.map((r) => ({ ...r, mine: !!r.mine, voted: !!r.voted })) });
  }
  if (method !== "POST") return J({ error: "bad_request" }, 400);
  const b = await request.json().catch(() => ({}));
  if (path === "/api/wish/save") {
    if (!(await rateLimit(db, `wish:${user.id}`, 10, 3600))) return J({ error: "rate_limit" }, 429);
    const title = txt(b.title, 120), body = txt(b.body, 1500); if (title.length < 5) return J({ error: "title" }, 400);
    const r = await db.prepare("INSERT INTO wish(user_id,title,body,status,created,updated) VALUES(?,?,?,'open',?,?)").bind(user.id, title, body, now(), now()).run();
    await db.prepare("INSERT OR IGNORE INTO wish_votes(wish_id,user_id) VALUES(?,?)").bind(r.meta.last_row_id, user.id).run();
    return J({ ok: true, id: r.meta.last_row_id });
  }
  if (path === "/api/wish/vote") {
    const id = +b.id, had = await db.prepare("SELECT 1 x FROM wish_votes WHERE wish_id=? AND user_id=?").bind(id, user.id).first();
    if (had) await db.prepare("DELETE FROM wish_votes WHERE wish_id=? AND user_id=?").bind(id, user.id).run(); else await db.prepare("INSERT OR IGNORE INTO wish_votes(wish_id,user_id) VALUES(?,?)").bind(id, user.id).run();
    return J({ ok: true });
  }
  if (path === "/api/wish/status") {                                // Admin: uebernehmen (planned), abhaken (done), ablehnen
    if (!user.admin) return J({ error: "forbidden" }, 403);
    if (!STATUS.includes(b.status)) return J({ error: "bad_status" }, 400);
    await db.prepare("UPDATE wish SET status=?,note=?,updated=?,done_at=CASE WHEN ?='done' THEN ? ELSE 0 END WHERE id=?").bind(b.status, txt(b.note, 300), now(), b.status, now(), +b.id).run();
    return J({ ok: true });
  }
  if (path === "/api/wish/delete") {
    const w = await db.prepare("SELECT user_id FROM wish WHERE id=?").bind(+b.id).first();
    if (!w || (w.user_id !== user.id && !user.admin)) return J({ error: "not_found" }, 404);
    await db.batch([db.prepare("DELETE FROM wish_votes WHERE wish_id=?").bind(+b.id), db.prepare("DELETE FROM wish WHERE id=?").bind(+b.id)]);
    return J({ ok: true });
  }
  return J({ error: "not_found" }, 404);
}
