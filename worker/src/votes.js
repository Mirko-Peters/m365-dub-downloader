// Community-Abstimmung ueber offene Aenderungen (Wiki, Entitaeten): vertrauenswuerdige Mitglieder stimmen ab
import { stats, evalBadges } from "./badges.js";
const NEED = 3, TRUST = 25;
const now = () => Math.floor(Date.now() / 1000);
const trusted = async (db, u) => !!(u && (u.admin || u.editor || u.pro || (await stats(db, u.id)).points >= TRUST));

export async function handleVotes(env, request, url, path, user, J) {
  const db = env.DB;
  if (path === "/api/edits/pending" && request.method === "GET") {
    const kind = url.searchParams.get("kind") === "entity" ? "entity" : "wiki", key = url.searchParams.get("key") || "", lang = url.searchParams.get("lang") || "";
    const rows = kind === "wiki"
      ? (await db.prepare("SELECT r.id,r.body,r.summary,r.created,r.user_id,COALESCE(u.name,'') name FROM wiki_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.term=? AND r.lang=? AND r.status='pending' ORDER BY r.created DESC LIMIT 10").bind(key, lang).all()).results || []
      : (await db.prepare("SELECT r.id,r.data body,r.summary,r.created,r.user_id,COALESCE(u.name,'') name FROM entity_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.eid=? AND r.status='pending' ORDER BY r.created DESC LIMIT 10").bind(key).all()).results || [];
    const out = [];
    for (const r of rows) {
      const v = await db.prepare("SELECT COALESCE(SUM(v),0) net, COUNT(*) n FROM edit_votes WHERE kind=? AND rev_id=?").bind(kind, r.id).first();
      const mine = user ? await db.prepare("SELECT v FROM edit_votes WHERE kind=? AND rev_id=? AND user_id=?").bind(kind, r.id, user.id).first() : null;
      out.push({ id: r.id, body: r.body, summary: r.summary, name: r.name, created: r.created, net: v.net, votes: v.n, need: NEED, mine: mine?.v || 0, own: user?.id === r.user_id });
    }
    return J({ kind, can_vote: await trusted(db, user), edits: out });
  }
  if (path === "/api/edits/vote" && request.method === "POST") {
    if (!user) return J({ error: "login" }, 401);
    if (!(await trusted(db, user))) return J({ error: "not_trusted" }, 403);
    const b = await request.json().catch(() => ({})), kind = b.kind === "entity" ? "entity" : "wiki", v = b.v === -1 ? -1 : 1, id = +b.id;
    const r = kind === "wiki" ? await db.prepare("SELECT id,term,lang,user_id,status FROM wiki_rev WHERE id=?").bind(id).first() : await db.prepare("SELECT id,eid,user_id,status FROM entity_rev WHERE id=?").bind(id).first();
    if (!r || r.status !== "pending") return J({ error: "not_pending" }, 404);
    if (r.user_id === user.id) return J({ error: "own_edit" }, 403);
    await db.prepare("INSERT INTO edit_votes(kind,rev_id,user_id,v,created) VALUES(?,?,?,?,?) ON CONFLICT(kind,rev_id,user_id) DO UPDATE SET v=excluded.v").bind(kind, id, user.id, v, now()).run();
    const t = await db.prepare("SELECT COALESCE(SUM(v),0) net FROM edit_votes WHERE kind=? AND rev_id=?").bind(kind, id).first();
    let status = "pending";
    if (t.net >= NEED) {
      status = "live";
      if (kind === "wiki") await db.batch([db.prepare("UPDATE wiki_rev SET status='old' WHERE term=? AND lang=? AND status='live'").bind(r.term, r.lang), db.prepare("UPDATE wiki_rev SET status='live' WHERE id=?").bind(id)]);
      else await db.batch([db.prepare("UPDATE entity_rev SET status='old' WHERE eid=? AND status='live'").bind(r.eid), db.prepare("UPDATE entity_rev SET status='live' WHERE id=?").bind(id)]);
      if (r.user_id) await evalBadges(env, r.user_id);
    } else if (t.net <= -NEED) {
      status = "rejected";
      await db.prepare(`UPDATE ${kind === "wiki" ? "wiki_rev" : "entity_rev"} SET status='rejected' WHERE id=?`).bind(id).run();
    }
    return J({ ok: true, net: t.net, need: NEED, status });
  }
  return null;
}
