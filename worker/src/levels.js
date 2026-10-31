// Expertise-Stufen aus Belegen (Paket 22): nicht mehr von Hand eingetragen, sondern aus Blog-Beitraegen, Sessions, Podcast-Folgen,
// Videos, Bibliothek, Wiki- und Entitaets-Aenderungen, geprueften Zertifikaten, angenommenen Antworten und Bestaetigungen anderer Mitglieder.
// Stufen: 1 lernt | 2 Praxis | 3 Experte | 4 Evangelist (Experte + 100 Bestaetigungen) | 5 Master (1000) | 6 Master Evangelist (1000 Bestaetigungen von Evangelisten im selben Thema)

export const LEVEL_NAMES = { 1: ["Learning", "Lernt"], 2: ["Practitioner", "Praxis"], 3: ["Expert", "Experte"], 4: ["Evangelist", "Evangelist"], 5: ["Master", "Master"], 6: ["Master Evangelist", "Master Evangelist"] };
// Gewicht je Beleg und Obergrenze je Art (viele kleine Beitraege machen allein keinen Experten)
export const WEIGHTS = { blog: 3, coauthor: 2, session: 5, podcast: 4, video: 3, guest: 2, library: 1, listing: 0.5, wiki: 1, entity: 1, cert: 4, answer: 1, self: 1 };
export const CAPS = { blog: 15, coauthor: 6, session: 15, podcast: 12, video: 9, guest: 6, library: 5, listing: 0.5, wiki: 5, entity: 5, cert: 8, answer: 5, self: 3, endorse: 5 };   // Bestaetigungen allein reichen hoechstens fuer Praxis
export const THRESH = { practitioner: 3, expert: 10, evangelist: 100, master: 1000, master_evangelist: 1000 };
const TOPIC_T = ["product", "platform", "concept", "category"];

// Punkte = Summe je Art, jede Art gedeckelt; Bestaetigungen zaehlen bis 5 Punkte (Experte braucht eigene Beitraege oder die Redaktion)
export function scoreOf(byKind, endorsed = 0) {
  let s = 0;
  for (const [k, w] of Object.entries(byKind || {})) s += Math.min(CAPS[k] ?? 5, +w || 0);
  return Math.round((s + Math.min(CAPS.endorse, +endorsed || 0)) * 100) / 100;
}
export function levelOf({ score = 0, endorsed = 0, endorsedEv = 0, verified = 0 } = {}) {
  const base = verified || score >= THRESH.expert ? 3 : score >= THRESH.practitioner ? 2 : 1;
  if (base < 3) return base;
  if (endorsedEv >= THRESH.master_evangelist) return 6;
  if (endorsed >= THRESH.master) return 5;
  if (endorsed >= THRESH.evangelist) return 4;
  return 3;
}
export const levelName = (l, de) => (LEVEL_NAMES[l] || LEVEL_NAMES[1])[de ? 1 : 0];

const parse = (s) => { try { const v = JSON.parse(s || "[]"); return Array.isArray(v) ? v : []; } catch { return []; } };
const rows = async (db, sql, ...b) => ((await db.prepare(sql).bind(...b).all()).results || []);   // Fehler durchreichen: lieber kein Lauf (cron_runs ok=0) als Belege loeschen und Stufen auf leeren Daten berechnen
async function batch(db, stmts) { for (let i = 0; i < stmts.length; i += 80) await db.batch(stmts.slice(i, i + 80)); }

// Belege aller Mitglieder aus den Quelltabellen (uid, eid, kind, item, weight)
export async function collectEvidence(env, entityMap) {
  const db = env.DB, emap = await entityMap(env), out = [], seen = new Set();
  const users = new Set((await rows(db, "SELECT id FROM users WHERE banned=0")).map((u) => u.id));
  const add = (uid, eid, kind, item, w) => { const k = `${uid}|${eid}|${kind}|${item}`; if (!uid || !users.has(+uid) || !emap.has(eid) || seen.has(k)) return; seen.add(k); out.push({ uid: +uid, eid, kind, item: String(item), w: w ?? WEIGHTS[kind] }); };
  const topics = (r, uid, kind, item) => { for (const t of parse(r.topics).slice(0, 10)) if (typeof t === "string") add(uid, t, kind, item); };
  for (const r of await rows(db, "SELECT id,user_id,topics FROM blog_posts WHERE status='live'")) topics(r, r.user_id, "blog", r.id);
  for (const r of await rows(db, "SELECT b.id,c.user_id,b.topics FROM blog_coauthors c JOIN blog_posts b ON b.id=c.post_id WHERE c.status='confirmed' AND b.status='live'")) topics(r, r.user_id, "coauthor", r.id);
  for (const r of await rows(db, "SELECT id,user_id,topics FROM pod_episodes WHERE status='published'")) topics(r, r.user_id, "podcast", r.id);
  for (const r of await rows(db, "SELECT id,user_id,topics FROM yt_videos WHERE status='published'")) topics(r, r.user_id, "video", r.id);
  for (const r of await rows(db, "SELECT g.kind k,g.item_id id,g.user_id,COALESCE(e.topics,v.topics,'[]') topics FROM item_guests g LEFT JOIN pod_episodes e ON g.kind='podcast' AND e.id=g.item_id AND e.status='published' LEFT JOIN yt_videos v ON g.kind='video' AND v.id=g.item_id AND v.status='published' WHERE g.status='confirmed' AND (e.id IS NOT NULL OR v.id IS NOT NULL)")) topics(r, r.user_id, "guest", `${r.k}:${r.id}`);
  for (const r of await rows(db, "SELECT id,user_id,topics FROM lib_items WHERE status='live'")) topics(r, r.user_id, "library", r.id);
  for (const r of await rows(db, "SELECT id,user_id,topics FROM guest_listings WHERE active=1")) topics(r, r.user_id, "listing", r.id);
  // Sessions: Sprecher per Profil-Handle, bestaetigt oder vom Veranstalter selbst
  const byHandle = new Map((await rows(db, "SELECT user_id,handle FROM profiles WHERE handle IS NOT NULL")).map((p) => [p.handle, p.user_id]));
  for (const r of await rows(db, "SELECT s.id,s.topics,s.speakers,e.owner_id oid FROM event_sessions s JOIN events e ON e.id=s.event_id WHERE s.status='live' AND s.topics<>'[]'")) {
    for (const x of parse(r.speakers)) { const uid = x && x.h ? byHandle.get(x.h) : 0; if (uid && (x.s === "confirmed" || r.oid === uid)) topics(r, uid, "session", r.id); }
  }
  for (const r of await rows(db, "SELECT id,user_id,term FROM wiki_rev WHERE user_id>0 AND status IN ('live','old')")) add(r.user_id, r.term, "wiki", r.id);
  for (const r of await rows(db, "SELECT id,user_id,eid FROM entity_rev WHERE user_id>0 AND status IN ('live','old')")) add(r.user_id, r.eid, "entity", r.id);
  for (const r of await rows(db, "SELECT c.user_id,c.eid FROM certs c JOIN cert_check k ON k.user_id=c.user_id AND k.eid=c.eid AND k.status='verified'"))
    for (const [, to] of (emap.get(r.eid)?.rel || [])) if (TOPIC_T.includes(emap.get(to)?.type)) add(r.user_id, to, "cert", r.eid);
  for (const r of await rows(db, "SELECT a.id,a.user_id,q.eid FROM entity_a a JOIN entity_q q ON q.id=a.q_id WHERE a.accepted=1 AND a.hidden=0 AND q.hidden=0")) add(r.user_id, r.eid, "answer", r.id);
  return out;
}

// Fruehere Selbstangaben einmalig als Beleg 'self' uebernehmen (Gewicht = alte Stufe, hoechstens 3) - bevor eine Stufe zum ersten Mal berechnet wird
export async function seedSelf(db, t, filter = null) {
  const r = await db.prepare(`INSERT OR IGNORE INTO expertise_evidence(owner_id,eid,kind,item_id,weight,created) SELECT x.owner_id,x.eid,'self','',MIN(x.level,3),? FROM expertise x WHERE x.owner_type='u'${filter ? " AND x.owner_id=? AND x.eid=?" : ""} AND NOT EXISTS (SELECT 1 FROM expertise_score s WHERE s.owner_id=x.owner_id AND s.eid=x.eid)`).bind(t, ...(filter ? [filter.uid, filter.eid] : [])).run();
  return r?.meta?.changes || 0;
}

// Kennzahlen und Stufe je Person und Thema neu berechnen; filter = { uid, eid } fuer ein Paar (nach einer Bestaetigung), sonst alle
export async function computeLevels(db, filter = null) {
  const t = Math.floor(Date.now() / 1000), W = filter ? " WHERE owner_id=? AND eid=?" : "", B = filter ? [filter.uid, filter.eid] : [];
  await seedSelf(db, t, filter);
  if (!filter) await db.batch([db.prepare("DELETE FROM expertise_evidence WHERE owner_id NOT IN (SELECT id FROM users)"), db.prepare("DELETE FROM expertise_score WHERE owner_id NOT IN (SELECT id FROM users)"), db.prepare("DELETE FROM expertise WHERE owner_type='u' AND owner_id NOT IN (SELECT id FROM users)")]);   // geloeschte Konten
  const pairs = new Map(), key = (u, e) => `${u}|${e}`;
  const get = (u, e) => { const k = key(u, e); if (!pairs.has(k)) pairs.set(k, { uid: u, eid: e, by: {}, endorsed: 0, endorsedEv: 0, verified: 0, level: 0, score: null, known: false }); return pairs.get(k); };
  for (const r of await rows(db, `SELECT owner_id,eid,kind,SUM(weight) w FROM expertise_evidence${W} GROUP BY owner_id,eid,kind`, ...B)) get(r.owner_id, r.eid).by[r.kind] = r.w;
  for (const r of await rows(db, `SELECT owner_id,eid,COUNT(*) n FROM endorsements${W} GROUP BY owner_id,eid`, ...B)) get(r.owner_id, r.eid).endorsed = r.n;
  for (const r of await rows(db, `SELECT n.owner_id,n.eid,COUNT(*) n FROM endorsements n JOIN expertise x ON x.owner_type='u' AND x.owner_id=n.by_id AND x.eid=n.eid AND x.level>=4${filter ? " WHERE n.owner_id=? AND n.eid=?" : ""} GROUP BY n.owner_id,n.eid`, ...B)) get(r.owner_id, r.eid).endorsedEv = r.n;
  for (const r of await rows(db, `SELECT x.owner_id,x.eid,x.level,x.verified,s.score FROM expertise x LEFT JOIN expertise_score s ON s.owner_id=x.owner_id AND s.eid=x.eid WHERE x.owner_type='u'${W ? " AND x.owner_id=? AND x.eid=?" : ""}`, ...B)) { const p = get(r.owner_id, r.eid); p.known = true; p.level = r.level; p.verified = r.verified ? 1 : 0; p.score = r.score; }
  const ops = []; let changed = 0;
  for (const p of pairs.values()) {
    const score = scoreOf(p.by, p.endorsed), level = levelOf({ score, endorsed: p.endorsed, endorsedEv: p.endorsedEv, verified: p.verified });
    if (!p.known || p.level !== level) ops.push(db.prepare("INSERT INTO expertise(owner_type,owner_id,eid,level,verified) VALUES('u',?,?,?,0) ON CONFLICT(owner_type,owner_id,eid) DO UPDATE SET level=excluded.level").bind(p.uid, p.eid, level));
    if (!p.known || p.level !== level || p.score !== score) { changed++; ops.push(db.prepare("INSERT INTO expertise_score(owner_id,eid,score,endorsed,endorsed_ev,updated) VALUES(?,?,?,?,?,?) ON CONFLICT(owner_id,eid) DO UPDATE SET score=excluded.score,endorsed=excluded.endorsed,endorsed_ev=excluded.endorsed_ev,updated=excluded.updated").bind(p.uid, p.eid, score, p.endorsed, p.endorsedEv, t)); }
    else ops.push(db.prepare("UPDATE expertise_score SET endorsed=?,endorsed_ev=?,updated=? WHERE owner_id=? AND eid=? AND (endorsed<>? OR endorsed_ev<>?)").bind(p.endorsed, p.endorsedEv, t, p.uid, p.eid, p.endorsed, p.endorsedEv));
  }
  await batch(db, ops);
  return { pairs: pairs.size, changed };
}

// Cron (alle 30 Minuten) und Verwaltung: Belege neu aufbauen, fruehere Selbstangaben einmalig als Beleg 'self' uebernehmen, Stufen berechnen
export async function syncExpertise(env, entityMap) {
  const db = env.DB, t = Math.floor(Date.now() / 1000);
  const ev = await collectEvidence(env, entityMap);
  await db.prepare("DELETE FROM expertise_evidence WHERE kind<>'self'").run();
  await batch(db, ev.map((e) => db.prepare("INSERT OR IGNORE INTO expertise_evidence(owner_id,eid,kind,item_id,weight,created) VALUES(?,?,?,?,?,?)").bind(e.uid, e.eid, e.kind, e.item, e.w, t)));
  const seeded = await seedSelf(db, t);
  const r = await computeLevels(db);
  return { evidence: ev.length, seeded, ...r };
}
