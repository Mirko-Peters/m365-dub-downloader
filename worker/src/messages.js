// Fluechtige Direktnachrichten: Kontakt aufnehmen (Tageslimit, mit Punkten mehr), Nachrichten werden nach 7 Tagen automatisch geloescht
import { cleanText, rateLimit } from "./util.js";
import { stats } from "./badges.js";

const TTL = 7 * 86400, BASE_LIMIT = 5, MAX_LIMIT = 25;
const now = () => Math.floor(Date.now() / 1000);
const text = (s) => cleanText(s, 1000).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "[Link entfernt]").trim();

export const dailyLimit = async (db, uid) => {
  const bonus = (await db.prepare("SELECT extra FROM msg_bonus WHERE user_id=? AND day=?").bind(uid, new Date().toISOString().slice(0, 10)).first())?.extra || 0;
  return Math.min(MAX_LIMIT, BASE_LIMIT + Math.floor(((await stats(db, uid)).earned || 0) / 50)) + bonus;
};

export async function purgeMessages(db) {
  const cut = now() - TTL;
  await db.batch([db.prepare("DELETE FROM msg_messages WHERE created<?").bind(cut), db.prepare("DELETE FROM msg_threads WHERE id NOT IN (SELECT DISTINCT thread_id FROM msg_messages)").bind()]);
}
export async function deleteUserMessages(db, uid) {
  await db.batch([db.prepare("DELETE FROM msg_messages WHERE thread_id IN (SELECT id FROM msg_threads WHERE a_id=?1 OR b_id=?1)").bind(uid), db.prepare("DELETE FROM msg_threads WHERE a_id=?1 OR b_id=?1").bind(uid),
    db.prepare("DELETE FROM msg_blocks WHERE user_id=?1 OR blocked_id=?1").bind(uid), db.prepare("DELETE FROM msg_prefs WHERE user_id=?").bind(uid)]);
}
const blocked = async (db, a, b) => !!(await db.prepare("SELECT 1 x FROM msg_blocks WHERE (user_id=?1 AND blocked_id=?2) OR (user_id=?2 AND blocked_id=?1)").bind(a, b).first());

export async function handleMessages(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m;
  if (!user) return J({ error: "login" }, 401);
  const body = async () => await request.json().catch(() => ({}));

  if (path === "/api/msg/prefs") {
    if (method === "GET") { const r = await db.prepare("SELECT open FROM msg_prefs WHERE user_id=?").bind(user.id).first(); const used = (await db.prepare("SELECT COUNT(*) n FROM msg_threads WHERE a_id=? AND created>?").bind(user.id, now() - 86400).first()).n;
      return J({ open: r ? !!r.open : true, limit: await dailyLimit(db, user.id), used, ttl_days: 7 }); }
    if (method === "POST") { const b = await body(); await db.prepare("INSERT INTO msg_prefs(user_id,open) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET open=excluded.open").bind(user.id, b.open ? 1 : 0).run(); return J({ ok: true }); }
  }
  if (path === "/api/msg/threads" && method === "GET") {
    const rows = (await db.prepare(`SELECT t.id,t.ctx,t.last,t.a_id,t.b_id,t.a_read,t.b_read,
      CASE WHEN t.a_id=?1 THEN t.b_id ELSE t.a_id END other,
      (SELECT body FROM msg_messages WHERE thread_id=t.id ORDER BY created DESC LIMIT 1) lastbody FROM msg_threads t WHERE t.a_id=?1 OR t.b_id=?1 ORDER BY t.last DESC LIMIT 100`).bind(user.id).all()).results || [];
    const out = [];
    for (const r of rows) { const o = await db.prepare("SELECT u.name,(SELECT handle FROM profiles WHERE user_id=u.id AND public=1) h FROM users u WHERE u.id=?").bind(r.other).first();
      const mine = r.a_id === user.id ? r.a_read : r.b_read; out.push({ id: r.id, ctx: r.ctx, last: r.last, unread: r.last > mine, with: { name: o?.name || "?", handle: o?.h || "" }, preview: (r.lastbody || "").slice(0, 80) }); }
    return J({ threads: out });
  }
  if ((m = path.match(/^\/api\/msg\/thread\/(\d+)$/))) {
    const t = await db.prepare("SELECT * FROM msg_threads WHERE id=? AND (a_id=? OR b_id=?)").bind(+m[1], user.id, user.id).first(); if (!t) return J({ error: "not_found" }, 404);
    const other = t.a_id === user.id ? t.b_id : t.a_id;
    if (method === "GET") {
      const ms = (await db.prepare("SELECT id,from_id,body,created FROM msg_messages WHERE thread_id=? AND created>? ORDER BY created").bind(t.id, now() - TTL).all()).results || [];
      await db.prepare(`UPDATE msg_threads SET ${t.a_id === user.id ? "a_read" : "b_read"}=? WHERE id=?`).bind(now(), t.id).run();
      return J({ messages: ms.map((x) => ({ id: x.id, mine: x.from_id === user.id, body: x.body, created: x.created, expires: x.created + TTL })), blocked: await blocked(db, user.id, other) });
    }
    if (method === "POST") {
      if (await blocked(db, user.id, other)) return J({ error: "blocked" }, 403);
      if (!(await rateLimit(db, `msgs:${user.id}`, 100, 86400))) return J({ error: "rate_limit" }, 429);
      const b = await body(), tx = text(b.body); if (tx.length < 1) return J({ error: "empty" }, 400);
      const t0 = now();
      await db.batch([db.prepare("INSERT INTO msg_messages(thread_id,from_id,body,created) VALUES(?,?,?,?)").bind(t.id, user.id, tx, t0), db.prepare(`UPDATE msg_threads SET last=?,${t.a_id === user.id ? "a_read" : "b_read"}=? WHERE id=?`).bind(t0, t0, t.id)]);
      return J({ ok: true });
    }
    if (method === "DELETE") { await db.batch([db.prepare("DELETE FROM msg_messages WHERE thread_id=?").bind(t.id), db.prepare("DELETE FROM msg_threads WHERE id=?").bind(t.id)]); return J({ ok: true }); }
  }
  if ((m = path.match(/^\/api\/msg\/block\/(\d+)$/)) && (method === "POST" || method === "DELETE")) {
    const t = await db.prepare("SELECT a_id,b_id FROM msg_threads WHERE id=? AND (a_id=? OR b_id=?)").bind(+m[1], user.id, user.id).first(); if (!t) return J({ error: "not_found" }, 404);
    const other = t.a_id === user.id ? t.b_id : t.a_id;
    if (method === "POST") await db.prepare("INSERT OR IGNORE INTO msg_blocks(user_id,blocked_id) VALUES(?,?)").bind(user.id, other).run(); else await db.prepare("DELETE FROM msg_blocks WHERE user_id=? AND blocked_id=?").bind(user.id, other).run();
    return J({ ok: true });
  }
  // Neue Kontaktaufnahme: an ein oeffentliches Profil (to=<handle>) oder an den Veranstalter eines Events (event=<handle>)
  if (path === "/api/msg/start" && method === "POST") {
    const b = await body(), tx = text(b.body); if (tx.length < 5) return J({ error: "too_short" }, 400);
    let to = 0, ctx = "";
    if (b.event) {
      const ev = await db.prepare("SELECT owner_id,handle FROM events WHERE handle=? AND seeking_sponsor=1").bind(String(b.event)).first(); if (!ev) return J({ error: "not_found" }, 404); to = ev.owner_id; ctx = "event:" + ev.handle;
    } else {
      const p = await db.prepare("SELECT p.user_id FROM profiles p JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.handle=? AND p.public=1").bind(String(b.to || "").toLowerCase()).first(); if (!p) return J({ error: "not_found" }, 404); to = p.user_id;
      const pr = await db.prepare("SELECT open FROM msg_prefs WHERE user_id=?").bind(to).first(); if (pr && !pr.open) return J({ error: "closed" }, 403);
    }
    if (to === user.id) return J({ error: "self" }, 400);
    if (await blocked(db, user.id, to)) return J({ error: "blocked" }, 403);
    // bestehender Thread (in beliebiger Richtung) -> Nachricht anhaengen, zaehlt nicht als neuer Kontakt
    let t = await db.prepare("SELECT * FROM msg_threads WHERE (a_id=?1 AND b_id=?2) OR (a_id=?2 AND b_id=?1)").bind(user.id, to).first();
    const t0 = now();
    if (!t) {
      const used = (await db.prepare("SELECT COUNT(*) n FROM msg_threads WHERE a_id=? AND created>?").bind(user.id, t0 - 86400).first()).n, lim = await dailyLimit(db, user.id);
      if (used >= lim) return J({ error: "daily_limit", limit: lim }, 429);
      const r = await db.prepare("INSERT INTO msg_threads(a_id,b_id,ctx,created,last,a_read) VALUES(?,?,?,?,?,?)").bind(user.id, to, ctx, t0, t0, t0).run();
      t = { id: r.meta.last_row_id, a_id: user.id };
    }
    await db.batch([db.prepare("INSERT INTO msg_messages(thread_id,from_id,body,created) VALUES(?,?,?,?)").bind(t.id, user.id, tx, t0), db.prepare(`UPDATE msg_threads SET last=?,${t.a_id === user.id ? "a_read" : "b_read"}=? WHERE id=?`).bind(t0, t0, t.id)]);
    return J({ ok: true, thread: t.id });
  }
  return null;
}
