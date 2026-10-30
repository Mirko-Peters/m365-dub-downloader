// Produkte und Services von Firmen: jedes Angebot wird eine Entitaet (Typ product, "entwickelt von" die Firma)
import { baseIds, validate, trustedUser } from "./entities.js";
import { cleanText, rateLimit } from "./util.js";

const now = () => Math.floor(Date.now() / 1000);
const slug = (s) => String(s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
export const MS_AREAS = ["modern_work", "business_apps", "data_ai", "infrastructure", "digital_app", "security", "csp", "msp", "isv", "inner_circle", "other"];
export const MS_LEVELS = ["solutions_partner", "specialization", "advanced_specialization", "inner_circle", "poty_finalist", "poty_winner", "registered", "other"];
let ready = false;
async function ensure(db) {
  if (ready) return;
  await db.prepare("CREATE TABLE IF NOT EXISTS org_offers (org_id INTEGER NOT NULL, eid TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'product', created INTEGER NOT NULL, PRIMARY KEY (org_id, eid))").run();
  ready = true;
}

export async function handleOrgOffers(env, request, url, path, user, J) {
  const db = env.DB, method = request.method;
  if (!path.startsWith("/api/orgoffer")) return null;
  await ensure(db);
  const orgOf = async (handle) => await db.prepare("SELECT o.id,o.name,o.website,(SELECT eid FROM org_entity WHERE org_id=o.id) eid FROM orgs o WHERE o.handle=?").bind(String(handle || "").toLowerCase()).first();

  if (path === "/api/orgoffer/list" && method === "GET") {
    const o = await orgOf(url.searchParams.get("handle")); if (!o) return J({ error: "not_found" }, 404);
    const rows = (await db.prepare("SELECT eid,kind,created FROM org_offers WHERE org_id=? ORDER BY created DESC").bind(o.id).all()).results || [];
    return J({ items: rows, org_eid: o.eid || "" });
  }
  if (path === "/api/orgoffer/save" && method === "POST") {
    if (!user) return J({ error: "login" }, 401);
    if (!(await rateLimit(db, `offer:${user.id}`, 30, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await request.json().catch(() => ({}));
    const o = await orgOf(b.handle); if (!o) return J({ error: "not_found" }, 404);
    const mem = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=? AND status='active'").bind(o.id, user.id).first();
    if (!mem || !["owner", "admin", "editor"].includes(mem.role)) return J({ error: "forbidden" }, 403);
    const kind = b.kind === "service" ? "service" : "product";
    const name = txt(b.name, 80); if (name.length < 2) return J({ error: "bad_name" }, 400);
    const desc = txt(b.desc, 300); if (desc.length < 20) return J({ error: "too_short" }, 400);
    const web = String(b.web || "").trim(); if (!/^https:\/\//i.test(web)) return J({ error: "need_link" }, 400);   // Link zur Produktseite ist Pflicht
    const lang = b.lang === "de" ? "de" : "en";
    const known = await baseIds(env);
    let eid = slug(name).slice(0, 40) || `angebot-${o.id}`, n = 1;
    const taken = async (e) => known.has(e) || !!(await db.prepare("SELECT 1 x FROM entity_rev WHERE eid=? AND status IN ('live','pending')").bind(e).first());
    while (await taken(eid)) eid = `${slug(name).slice(0, 36)}-${++n}`;
    const rel = o.eid ? [["developed_by", o.eid]] : [];
    const v = await validate(env, eid, { name, type: "product", desc: { en: lang === "en" ? desc : "", de: lang === "de" ? desc : "" }, web, rel, license: "paid" });
    if (v.err) return J({ error: v.err }, 400);
    if (kind === "service") v.data.aliases = [...(v.data.aliases || [])];
    const st = (await trustedUser(db, user)) ? "live" : "pending";
    await db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,?,?)").bind(eid, JSON.stringify(v.data), `${kind === "service" ? "Service" : "Produkt"} von ${o.name}`, user.id, st, now()).run();
    await db.prepare("INSERT INTO org_offers(org_id,eid,kind,created) VALUES(?,?,?,?)").bind(o.id, eid, kind, now()).run();
    return J({ ok: true, eid, status: st });
  }
  if (path === "/api/orgoffer/ms" && method === "POST") {   // Microsoft-Status der Firma: Bereich + Stufe (selbst angegeben, nicht geprueft)
    if (!user) return J({ error: "login" }, 401);
    const b = await request.json().catch(() => ({}));
    const o = await orgOf(b.handle); if (!o) return J({ error: "not_found" }, 404);
    const mem = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=? AND status='active'").bind(o.id, user.id).first();
    if (!mem || !["owner", "admin"].includes(mem.role)) return J({ error: "forbidden" }, 403);
    await db.prepare("CREATE TABLE IF NOT EXISTS org_ms (org_id INTEGER NOT NULL, area TEXT NOT NULL, level TEXT NOT NULL, since TEXT NOT NULL DEFAULT '', PRIMARY KEY (org_id, area))").run();
    const list = [], seen = new Set();
    for (const x of (Array.isArray(b.items) ? b.items : []).slice(0, 20)) {
      if (!MS_AREAS.includes(x?.area) || !MS_LEVELS.includes(x?.level) || seen.has(x.area)) return J({ error: "bad_status" }, 400);
      seen.add(x.area); const since = /^\d{4}$/.test(String(x.since || "")) ? String(x.since) : ""; list.push([x.area, x.level, since]);
    }
    await db.batch([db.prepare("DELETE FROM org_ms WHERE org_id=?").bind(o.id), ...list.map((r) => db.prepare("INSERT INTO org_ms(org_id,area,level,since) VALUES(?,?,?,?)").bind(o.id, ...r))]);
    return J({ ok: true });
  }
  return J({ error: "not_found" }, 404);
}
