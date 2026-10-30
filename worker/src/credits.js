// Gaeste bei Community-Podcast und Video (Gegenstueck zu Co-Autoren im Blog): der Host nennt Profil-Adressen, der Eingeladene bestaetigt selbst -
// erst dann erscheint er auf der Seite, im Schema (Gast/Mitwirkende) und seine Themen zaehlen fuer seine Expertise.
import { rateLimit } from "./util.js";

const now = () => Math.floor(Date.now() / 1000);
export const KINDS = { podcast: { table: "pod_episodes", comments: "podcast" }, video: { table: "yt_videos", comments: "video" } };
const MAX_GUESTS = 5;

// Bestaetigte (oder alle, fuer den Host) Gaeste je Eintrag: Map id -> [{handle,name,status?}]
export async function guestsOf(db, kind, ids, all = false) {
  const by = {}; if (!ids.length) return by;
  const rows = (await db.prepare(`SELECT g.item_id,g.status,p.handle,u.name FROM item_guests g JOIN profiles p ON p.user_id=g.user_id ${all ? "" : "AND p.public=1 AND p.handle IS NOT NULL"} JOIN users u ON u.id=g.user_id AND u.banned=0 WHERE g.kind=? AND g.item_id IN (${ids.map(() => "?").join(",")})${all ? "" : " AND g.status='confirmed'"} ORDER BY g.created`).bind(kind, ...ids).all()).results || [];
  for (const r of rows) (by[r.item_id] ||= []).push(all ? { handle: r.handle, name: r.name, status: r.status } : { handle: r.handle, name: r.name });
  return by;
}
export async function dropGuests(db, kind, id) { await db.prepare("DELETE FROM item_guests WHERE kind=? AND item_id=?").bind(kind, id).run(); }
export async function deleteUserGuestCredits(db, uid) {
  await db.batch([db.prepare("DELETE FROM item_guests WHERE user_id=?").bind(uid), db.prepare("DELETE FROM item_guests WHERE (kind='podcast' AND item_id IN (SELECT id FROM pod_episodes WHERE user_id=?)) OR (kind='video' AND item_id IN (SELECT id FROM yt_videos WHERE user_id=?))").bind(uid, uid)]);
}
const invites = async (db, uid) => (await db.prepare(
  `SELECT g.kind,g.item_id id,COALESCE(e.title,v.title) title,u.name host,p.handle host_handle FROM item_guests g
   LEFT JOIN pod_episodes e ON g.kind='podcast' AND e.id=g.item_id LEFT JOIN yt_videos v ON g.kind='video' AND v.id=g.item_id
   JOIN users u ON u.id=COALESCE(e.user_id,v.user_id) LEFT JOIN profiles p ON p.user_id=u.id WHERE g.user_id=? AND g.status='invited' ORDER BY g.created DESC LIMIT 50`).bind(uid).all()).results || [];

export async function handleCredits(env, request, url, path, user, J) {
  if (!path.startsWith("/api/credit/")) return null;
  if (!user) return J({ error: "login" }, 401);
  const db = env.DB, method = request.method;
  if (path === "/api/credit/mine" && method === "GET") {   // Einladungen als Gast und bereits bestaetigte Auftritte
    const done = (await db.prepare(
      `SELECT g.kind,g.item_id id,COALESCE(e.title,v.title) title,COALESCE(e.status,v.status) status FROM item_guests g
       LEFT JOIN pod_episodes e ON g.kind='podcast' AND e.id=g.item_id LEFT JOIN yt_videos v ON g.kind='video' AND v.id=g.item_id WHERE g.user_id=? AND g.status='confirmed' ORDER BY g.created DESC LIMIT 100`).bind(user.id).all()).results || [];
    return J({ invites: await invites(db, user.id), appearances: done });
  }
  if (method !== "POST") return J({ error: "bad_request" }, 400);
  const b = await request.json().catch(() => ({})), k = KINDS[b.kind];
  if (!k) return J({ error: "bad_kind" }, 400);
  if (!(await rateLimit(db, `credit:${user.id}`, 60, 3600))) return J({ error: "rate_limit" }, 429);
  if (path === "/api/credit/set") {   // Host setzt die Gaeste (ersetzt die Liste; bestehende Zusagen bleiben)
    const item = await db.prepare(`SELECT id FROM ${k.table} WHERE id=? AND user_id=?`).bind(+b.id, user.id).first(); if (!item) return J({ error: "not_found" }, 404);
    const hs = [...new Set((Array.isArray(b.guests) ? b.guests : []).map((x) => String(x || "").toLowerCase().trim()).filter(Boolean))].slice(0, MAX_GUESTS), want = [];
    for (const h of hs) {
      const pr = await db.prepare("SELECT user_id FROM profiles WHERE handle=? AND public=1").bind(h).first();
      if (!pr || pr.user_id === user.id) return J({ error: "bad_guest", handle: h }, 400);
      want.push(pr.user_id);
    }
    const have = new Map(((await db.prepare("SELECT user_id,status FROM item_guests WHERE kind=? AND item_id=?").bind(b.kind, item.id).all()).results || []).map((r) => [r.user_id, r.status]));
    for (const uid of have.keys()) if (!want.includes(uid)) await db.prepare("DELETE FROM item_guests WHERE kind=? AND item_id=? AND user_id=?").bind(b.kind, item.id, uid).run();
    for (const uid of want) if (!have.has(uid)) await db.prepare("INSERT INTO item_guests(kind,item_id,user_id,status,created) VALUES(?,?,?,'invited',?)").bind(b.kind, item.id, uid, now()).run();
    return J({ ok: true, guests: (await guestsOf(db, b.kind, [item.id], true))[item.id] || [] });
  }
  if (path === "/api/credit/respond") {   // Eingeladener bestaetigt oder lehnt ab
    const row = await db.prepare("SELECT 1 x FROM item_guests WHERE kind=? AND item_id=? AND user_id=? AND status='invited'").bind(b.kind, +b.id, user.id).first(); if (!row) return J({ error: "not_found" }, 404);
    if (b.accept && !(await db.prepare("SELECT 1 x FROM profiles WHERE user_id=? AND public=1 AND handle IS NOT NULL").bind(user.id).first())) return J({ error: "need_profile" }, 400);
    await db.prepare("UPDATE item_guests SET status=? WHERE kind=? AND item_id=? AND user_id=?").bind(b.accept ? "confirmed" : "declined", b.kind, +b.id, user.id).run();
    return J({ ok: true, status: b.accept ? "confirmed" : "declined" });
  }
  return null;
}
