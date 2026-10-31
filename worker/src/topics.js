// Inhalt <-> Entitaet (content_topic): Uebernahme aus den topics-Spalten der Datenbank und aus dem Seitenbau (SITE/topics.json: fruehere Beitraege und
// Folgen der Hauptshow mit Gewicht), Export fuer den Seitenbau und Agenten, Pflege von Hand ueber die Verwaltung.
const now = () => Math.floor(Date.now() / 1000);
const DBKINDS = { blog: "SELECT id,topics FROM blog_posts WHERE status='live'", podcast: "SELECT id,topics FROM pod_episodes WHERE published>0", video: "SELECT id,topics FROM yt_videos WHERE published>0", library: "SELECT id,topics FROM lib_items WHERE status='live'", session: "SELECT id,topics FROM event_sessions WHERE status='live'" };

export async function syncContentTopics(env) {
  const db = env.DB, t = now(); let fromDb = 0, fromSite = 0;
  // 1) topics-Spalten der Datenbank (Reihenfolge = Gewicht 1.0, 0.8, 0.6 ...), nur fehlende Zeilen
  for (const [kind, sql] of Object.entries(DBKINDS)) {
    let rows = []; try { rows = (await db.prepare(sql).all()).results || []; } catch { continue; }
    const stmts = [];
    for (const r of rows) {
      let tp = []; try { tp = JSON.parse(r.topics || "[]"); } catch { continue; }
      tp.slice(0, 10).forEach((eid, i) => { if (typeof eid === "string" && /^[a-z0-9][a-z0-9-]{1,79}$/.test(eid)) stmts.push(db.prepare("INSERT OR IGNORE INTO content_topic(kind,item_id,eid,weight,src,created) VALUES(?,?,?,?,'db',?)").bind(kind, String(r.id), eid, Math.max(0.2, 1 - i * 0.2), t)); });
    }
    for (let i = 0; i < stmts.length; i += 100) { const res = await db.batch(stmts.slice(i, i + 100)); fromDb += res.reduce((a, x) => a + (x.meta?.changes || 0), 0); }
  }
  // 2) Seitenbau: fruehere Beitraege und Folgen der Hauptshow mit Gewicht (SITE/topics.json); 'site' ueberschreibt eigene aeltere Zuordnungen, nie 'admin'
  let j = null; try { j = await (await fetch(env.SITE + "/topics.json", { cf: { cacheTtl: 600 } })).json(); } catch { /* Seite nicht erreichbar */ }
  if (j && Array.isArray(j.items)) {
    const stmts = [];
    for (const it of j.items.slice(0, 60000)) {
      if (!it.kind || !it.id || !it.eid) continue;
      stmts.push(db.prepare("INSERT INTO content_topic(kind,item_id,eid,weight,src,created) VALUES(?,?,?,?,'site',?) ON CONFLICT(kind,item_id,eid) DO UPDATE SET weight=excluded.weight,created=excluded.created WHERE content_topic.src<>'admin'").bind(String(it.kind), String(it.id).slice(0, 120), String(it.eid), +it.w || 1, t));
    }
    for (let i = 0; i < stmts.length; i += 100) { const res = await db.batch(stmts.slice(i, i + 100)); fromSite += res.reduce((a, x) => a + (x.meta?.changes || 0), 0); }
    // vom Seitenbau nicht mehr gelieferte Zuordnungen (Beitrag umgeschrieben) entfernen
    const seen = new Set(j.items.map((it) => it.kind + "|" + it.id + "|" + it.eid)), kinds = [...new Set(j.items.map((it) => String(it.kind)))];
    for (const k of kinds) {
      const rows = (await db.prepare("SELECT item_id,eid FROM content_topic WHERE kind=? AND src='site'").bind(k).all()).results || [];
      const gone = rows.filter((r) => !seen.has(k + "|" + r.item_id + "|" + r.eid)).slice(0, 2000);
      for (let i = 0; i < gone.length; i += 100) await db.batch(gone.slice(i, i + 100).map((r) => db.prepare("DELETE FROM content_topic WHERE kind=? AND item_id=? AND eid=? AND src='site'").bind(k, r.item_id, r.eid)));
    }
  }
  const total = (await db.prepare("SELECT COUNT(*) n FROM content_topic").first())?.n || 0;
  return { fromDb, fromSite, total };
}

export async function handleTopics(env, request, url, path, user, J) {
  const db = env.DB;
  if (path === "/api/topics/export" && request.method === "GET") {   // alle Zuordnungen (Seitenbau, Agenten); optional ?eid= oder ?kind=
    const eid = url.searchParams.get("eid") || "", kind = url.searchParams.get("kind") || "";
    const rows = (await db.prepare("SELECT kind,item_id,eid,weight,src FROM content_topic" + (eid ? " WHERE eid=?" : kind ? " WHERE kind=?" : "") + " ORDER BY kind,item_id,weight DESC LIMIT 80000").bind(...(eid ? [eid] : kind ? [kind] : [])).all().catch(() => ({ results: [] }))).results || [];
    return J({ items: rows }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path === "/api/admin/panel/topic" && request.method === "POST") {   // Verwaltung: Zuordnung setzen oder entfernen (src admin, wird vom Seitenbau nicht ueberschrieben)
    if (!user?.admin) return J({ error: "forbidden" }, 403);
    const b = await request.json().catch(() => ({})), kind = String(b.kind || ""), id = String(b.id || "").slice(0, 120), eid = String(b.eid || "");
    if (!/^[a-z]+$/.test(kind) || !id || !/^[a-z0-9][a-z0-9-]{1,79}$/.test(eid)) return J({ error: "bad_request" }, 400);
    if (b.on === false) await db.prepare("DELETE FROM content_topic WHERE kind=? AND item_id=? AND eid=?").bind(kind, id, eid).run();
    else await db.prepare("INSERT INTO content_topic(kind,item_id,eid,weight,src,created) VALUES(?,?,?,?,'admin',?) ON CONFLICT(kind,item_id,eid) DO UPDATE SET weight=excluded.weight,src='admin'").bind(kind, id, eid, Math.min(2, Math.max(0.1, +b.weight || 1)), now()).run();
    return J({ ok: true });
  }
  return null;
}
