// Experten zu einem Thema, auch ueber verwandte Entitaeten (Graph-Suche im Entitaetsnetz, bis zu 2 Schritte).
// Der Graph kommt aus entityMap (Basis-Entitaeten + bestaetigte Aenderungen); Kanten gelten in beide Richtungen.
import { entityMap } from "./entities.js";

const EDGE = { instance_of: 0.9, part_of: 0.8, requires: 0.8, covers: 0.7, related_to: 0.6, similar_to: 0.5, developed_by: 0.4, created_by: 0.4 };
const LEVEL = { 1: 0.4, 2: 0.7, 3: 1, 4: 1.2, 5: 1.4, 6: 1.6 };   // Stufen 4-6: Evangelist, Master, Master Evangelist (levels.js)

// Entfernung und Gewicht aller Entitaeten innerhalb von maxHops Schritten (Breitensuche; das beste Gewicht je Entitaet zaehlt)
export function neighbourhood(map, eid, maxHops = 2) {
  const adj = new Map();
  const add = (a, b, p) => { if (!adj.has(a)) adj.set(a, []); adj.get(a).push([b, EDGE[p] ?? 0.5]); };
  for (const [id, e] of map) for (const [p, to] of e.rel || []) if (map.has(to) && to !== id) { add(id, to, p); add(to, id, p); }
  const best = new Map([[eid, { hops: 0, w: 1 }]]);
  let frontier = [eid];
  for (let h = 1; h <= maxHops; h++) {
    const next = [];
    for (const a of frontier) for (const [b, w] of adj.get(a) || []) {
      const nw = best.get(a).w * w * 0.7;   // jeder Schritt wertet deutlich ab: direkte Experten stehen vor verwandten
      const old = best.get(b);
      if (!old || nw > old.w) { if (!old) next.push(b); best.set(b, { hops: old ? Math.min(old.hops, h) : h, w: nw }); }
    }
    frontier = next;
  }
  return best;
}

export async function findExperts(env, eid, maxHops = 2, limit = 12) {
  const map = await entityMap(env);
  const ent = map.get(eid); if (!ent) return null;
  const near = neighbourhood(map, eid, Math.min(Math.max(maxHops, 0), 2));
  const ids = [...near.keys()], rows = [];
  for (let i = 0; i < ids.length; i += 60) {   // D1 begrenzt die Zahl der Platzhalter
    const part = ids.slice(i, i + 60);
    rows.push(...((await env.DB.prepare(`SELECT x.owner_id uid,x.eid,x.level,x.verified,p.handle,p.headline,u.name FROM expertise x JOIN profiles p ON p.user_id=x.owner_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=x.owner_id AND u.banned=0 WHERE x.owner_type='u' AND x.eid IN (${part.map(() => "?").join(",")})`).bind(...part).all()).results || []));
  }
  const by = new Map();
  for (const r of rows) {
    const n = near.get(r.eid); const score = n.w * (LEVEL[r.level] || 0.7) * (r.verified ? 1.2 : 1);
    const cur = by.get(r.uid);
    if (!cur || score > cur.score) by.set(r.uid, { handle: r.handle, name: r.name, headline: r.headline, score: Math.round(score * 1000) / 1000, level: r.level, verified: !!r.verified, via: { eid: r.eid, name: map.get(r.eid)?.name || r.eid, hops: n.hops } });
  }
  const experts = [...by.values()].sort((a, b) => b.score - a.score || a.name.localeCompare(b.name)).slice(0, limit);
  return { entity: { id: eid, name: ent.name, type: ent.type }, hops: maxHops, experts };
}
