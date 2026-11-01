// Entitaetsdatenbank fuer das Microsoft-Oekosystem: Community-Revisionen ueber den statischen Basisdaten (data/entities.json)
import { cleanText, rateLimit } from "./util.js";
import { entityTranslations } from "./autotr.js";
import { stats, evalBadges } from "./badges.js";

const ID = /^[a-z0-9-]{2,48}$/;
export const TYPES = ["product", "platform", "concept", "org", "person", "cert", "event", "media", "category"];
export const PRED = ["instance_of", "part_of", "developed_by", "related_to", "requires", "covers", "created_by", "organized_by", "similar_to"];
const TRUST_POINTS = 25;
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const httpsUrl = (s, ok) => { s = String(s || "").trim(); if (!s) return ""; try { const u = new URL(s); if (u.protocol !== "https:" || s.length > 250 || u.username || !ok(u.hostname)) return null; return u.href; } catch { return null; } };
const longTxt = (s, n) => String(s || "").replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\r/g, "").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim().slice(0, n);
const isMs = (h) => /(^|\.)(microsoft\.com|azure\.com|office\.com|visualstudio\.com|github\.com|github\.io|microsoft365\.com|linkedin\.com)$/i.test(h);

// Basisliste (statisch veroeffentlicht) fuer Verweisziele; 10 Minuten im Edge-Cache
// Quelle der Entitaeten (Paket 14): meta entity_source = "db" -> die Datenbank (entity_rev live) ist die einzige Quelle, entities.json der Seite wird nicht mehr gelesen;
// Standard "json" -> wie bisher Datei plus Datenbank. Rueckfallschalter in der Verwaltung; der Cron importEntitiesFromSite holt neue Eintraege der Datei in die Datenbank.
async function source(env) { try { return (await env.DB.prepare("SELECT v FROM meta WHERE k='entity_source'").first())?.v || "json"; } catch { return "json"; } }

async function siteEntities(env, ttl = 600) {
  try { return ((await (await fetch(env.SITE + "/entities.json", { cf: { cacheTtl: ttl } })).json()).entities || []); } catch { return []; }
}

export async function baseIds(env) {
  const ids = new Set(((await env.DB.prepare("SELECT DISTINCT eid FROM entity_rev WHERE status='live'").all().catch(() => ({ results: [] }))).results || []).map((r) => r.eid));
  if ((await source(env)) === "db") return ids;
  for (const e of await siteEntities(env)) ids.add(e.id);
  return ids;
}

// Alle Entitaeten als Map: Datenbank (live) und, solange entity_source=json, die Datei als Grundlage darunter
export async function entityMap(env) {
  const base = new Map();
  if ((await source(env)) !== "db") for (const e of await siteEntities(env)) base.set(e.id, e);
  const rows = (await env.DB.prepare("SELECT eid,data FROM entity_rev WHERE status='live' ORDER BY id").all()).results || [];
  for (const r of rows) { try { base.set(r.eid, { id: r.eid, ...JSON.parse(r.data) }); } catch { /* defekte Zeile ignorieren */ } }
  return base;
}

// Cron: neue Eintraege aus entities.json (Repo) in die Datenbank uebernehmen (nur IDs ohne live-Fassung; nichts wird ueberschrieben) - ersetzt den Knopf in der Verwaltung fuer den laufenden Betrieb
export async function importEntitiesFromSite(env) {
  const db = env.DB, list = await siteEntities(env, 0);
  if (!list.length) return { skipped: "entities.json nicht erreichbar" };
  const have = new Set(((await db.prepare("SELECT DISTINCT eid FROM entity_rev WHERE status='live'").all()).results || []).map((r) => r.eid));
  const todo = list.filter((e) => e && /^[a-z0-9][a-z0-9-]{1,79}$/.test(e.id || "") && e.name && e.type && !have.has(e.id)), t = Math.floor(Date.now() / 1000);
  for (let i = 0; i < todo.length; i += 50)
    await db.batch(todo.slice(i, i + 50).map((e) => { const { id, ...data } = e; return db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,0,'live',?)").bind(id, JSON.stringify(data), "Übernahme aus entities.json", t); }));
  const synced = await syncEntitiesFromSite(env).catch((e) => ({ error: String(e).slice(0, 120) }));
  return { imported: todo.length, db: have.size + todo.length, file: list.length, synced };
}

// T30: Abgleich JSON -> D1 fuer Entitaeten, die schon in der Datenbank sind. Grundlage ist /entities-src.json (Repo-Fassung ohne
// D1-Ueberlagerung; /entities.json enthaelt schon die D1-Fassung). Je Feld (desc und long je Sprache) zaehlt, wer es zuletzt
// geaendert hat: eine Maschine (user_id 0: Uebernahme, Abgleich, Auto-Uebersetzung) -> die JSON gewinnt; ein Mensch -> D1 bleibt.
// Nur Felder mit Wert in der JSON werden uebernommen, nichts wird geloescht. Neue live-Fassung "Abgleich mit entities.json".
const NESTED = new Set(["desc", "long"]);
const isObj = (v) => v && typeof v === "object" && !Array.isArray(v);
const canon = (v) => JSON.stringify(v, (k, x) => (isObj(x) ? Object.fromEntries(Object.keys(x).sort().map((y) => [y, x[y]])) : x));
const blank = (v) => v === undefined || v === null || v === "" || (Array.isArray(v) && !v.length) || (isObj(v) && !Object.keys(v).length);
const paths = (d) => { const out = []; for (const [k, v] of Object.entries(d || {})) { if (k === "id" || k === "edited") continue; if (NESTED.has(k) && isObj(v)) for (const l of Object.keys(v)) out.push([k, l]); else out.push([k]); } return out; };
const at = (d, p) => (p.length === 2 ? (isObj(d?.[p[0]]) ? d[p[0]][p[1]] : undefined) : d?.[p[0]]);
const put = (d, p, v) => { if (p.length === 2) d[p[0]] = { ...(isObj(d[p[0]]) ? d[p[0]] : {}), [p[1]]: v }; else d[p[0]] = v; };

// Maschine = user_id 0 UND eine Maschinen-Zusammenfassung. user_id 0 allein reicht nicht: beim Loeschen eines Kontos setzt
// profiles.js die Revisionen des Menschen auf user_id 0 ("geloeschtes Konto"), das bleibt eine Menschen-Aenderung.
const MACHINE = /^(Übernahme aus entities\.json|Abgleich mit entities\.json|Auto-Übersetzung)/;
export const isMachine = (r) => !r.user_id && MACHINE.test(r.summary || "");

// Felder, die validate() bei jeder Bearbeitung ausgibt (long, desc.en/de nur mit Wert): fehlen sie in einer Menschen-Fassung, hat der
// Mensch sie geleert. Alle anderen (image, same_as, guest, desc.<weitere Sprachen> ...) zeigt das Formular nicht -> "nicht gesehen".
const FORM_KEYS = new Set(["name", "type", "aliases", "web", "docs", "wikipedia", "wikidata", "rel", "logo", "version", "released", "license", "level", "valid_months", "exam", "outdated", "replaced_by"]);
const FORM_SUB = new Set(["desc.en", "desc.de", "long.en", "long.de"]);

export function mergeFromJson(json, revs) {
  // revs: Historie (live und old) [{id, data, user_id, summary, status}], die live-Fassung als LETZTER Eintrag.
  // Ein Feld gehoert einem Menschen, wenn eine Menschen-Fassung genau den aktuellen live-Wert enthaelt UND ihn gegenueber ihrer
  // Vorgaengerin (hoechste kleinere id = Stand beim Einreichen) geaendert hat. Keine Annahme ueber die Reihenfolge, in der Fassungen
  // live waren (freigegebene Vorschlaege behalten ihre aeltere id). Leere Werte (fehlt, '', [], {}) zaehlen als ein Wert; eine
  // Menschen-Fassung ohne das Feld hat es nicht gesehen (validate() laesst es weg). Uebernommen wird nur, was keinem Menschen gehoert.
  const liveRev = revs[revs.length - 1], live = liveRev?.data || {}, data = JSON.parse(JSON.stringify(live)), fields = [], kept = [];
  const val = (d, p) => { const v = at(d, p); return blank(v) ? "" : canon(v); };
  const has = (d, p) => (p.length === 2 ? FORM_SUB.has(p.join(".")) || (isObj(d?.[p[0]]) && p[1] in d[p[0]]) : FORM_KEYS.has(p[0]) || (!!d && p[0] in d));
  const byId = [...revs].sort((x, y) => (x.id ?? 0) - (y.id ?? 0));
  const pred = (r) => { let q = null; for (const x of byId) { if ((x.id ?? 0) < (r.id ?? 0)) q = x; else break; } return q; };
  for (const p of paths(json)) {
    const jv = at(json, p); if (blank(jv)) continue;
    const lv = val(live, p); if (lv === canon(jv)) continue;
    const human = revs.some((r) => !isMachine(r) && has(r.data, p) && val(r.data, p) === lv && val(r.data, p) !== (pred(r) ? val(pred(r).data, p) : ""));
    if (human) kept.push(p.join(".")); else { put(data, p, jv); fields.push(p.join(".")); }
  }
  return { data, fields, kept };
}

export async function syncEntitiesFromSite(env, opts = {}) {
  const db = env.DB;
  if ((await source(env)) === "db") return { skipped: "entity_source=db" };
  let list = [];
  try { const r = await fetch(env.SITE + "/entities-src.json", { cf: { cacheTtl: 0 } }); if (r.ok) list = (await r.json()).entities || []; } catch { /* noch nicht veroeffentlicht */ }
  if (!list.length) return { skipped: "entities-src.json nicht erreichbar" };
  const last = +(await db.prepare("SELECT v FROM meta WHERE k='ent_src_n'").first().catch(() => null))?.v || 0;
  if (last && list.length < last * 0.8) return { skipped: `entities-src.json unvollstaendig (${list.length} statt ${last})` };   // Schutz vor einem halben Seitenbau
  await db.prepare("INSERT INTO meta(k,v) VALUES('ent_src_n',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(String(list.length)).run();
  const live = new Map(((await db.prepare("SELECT eid,data FROM entity_rev WHERE status='live'").all()).results || []).map((r) => [r.eid, r.data]));
  const owned = new Set(((await db.prepare("SELECT DISTINCT eid FROM entity_claims WHERE status='verified'").all().catch(() => ({ results: [] }))).results || []).map((r) => r.eid));   // selbst verwaltet: nie abgleichen
  const cand = [];
  for (const e of list) {   // Vorauswahl ohne Historie: nur Eintraege, deren JSON-Felder nicht schon so in D1 stehen
    if (!e?.id || !live.has(e.id) || owned.has(e.id)) continue;
    let d; try { d = JSON.parse(live.get(e.id)); } catch { continue; }
    const { id, ...j } = e;
    if (paths(j).some((p) => !blank(at(j, p)) && canon(at(d, p)) !== canon(at(j, p)))) cand.push(e);
  }
  const max = opts.max || 200, t = now(); let updated = 0, kept = 0; const sample = [];
  // reihum: Kandidaten, bei denen nur von Menschen geaenderte Felder abweichen, bleiben Kandidaten und duerfen neue nicht verdraengen
  const off = cand.length > max ? (+(await db.prepare("SELECT v FROM meta WHERE k='ent_sync_off'").first().catch(() => null))?.v || 0) % cand.length : 0;
  const todo = cand.length > max ? [...cand.slice(off), ...cand.slice(0, off)].slice(0, max) : cand;
  if (cand.length > max) await db.prepare("INSERT INTO meta(k,v) VALUES('ent_sync_off',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(String((off + max) % cand.length)).run();
  for (let i = 0; i < todo.length; i += 50) {
    const part = todo.slice(i, i + 50), ids = part.map((e) => e.id);
    // live-Zeile zuletzt: ein freigegebener Vorschlag behaelt seine aeltere id, die hoechste id ist dann eine abgeloeste Fassung
    const rows = (await db.prepare(`SELECT id,eid,data,user_id,summary,status FROM entity_rev WHERE status IN ('live','old') AND eid IN (${ids.map(() => "?").join(",")}) ORDER BY (status='live'), id`).bind(...ids).all()).results || [];
    const by = new Map(); for (const r of rows) { try { (by.get(r.eid) || by.set(r.eid, []).get(r.eid)).push({ id: r.id, data: JSON.parse(r.data), user_id: r.user_id, summary: r.summary, status: r.status }); } catch { /* defekte Zeile */ } }
    const stmts = [];
    for (const e of part) {
      const revs = by.get(e.id); if (!revs?.length || revs[revs.length - 1].status !== "live") continue;
      const { id, ...j } = e, m = mergeFromJson(j, revs);
      kept += m.kept.length;
      if (!m.fields.length) continue;
      // nur schreiben, wenn die gelesene live-Fassung noch live ist (sonst hat jemand dazwischen gespeichert -> naechster Lauf)
      stmts.push(db.prepare("UPDATE entity_rev SET status='old' WHERE id=? AND status='live'").bind(revs[revs.length - 1].id),
        db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) SELECT ?,?,?,0,'live',? WHERE NOT EXISTS (SELECT 1 FROM entity_rev WHERE eid=? AND status='live')").bind(id, JSON.stringify(m.data), "Abgleich mit entities.json: " + m.fields.join(", ").slice(0, 100), t, id));
      updated++; if (sample.length < 10) sample.push({ id, fields: m.fields });
    }
    for (let k = 0; k < stmts.length; k += 50) await db.batch(stmts.slice(k, k + 50));
  }
  return { candidates: cand.length, checked: todo.length, updated, kept_human_fields: kept, sample };
}

// Wer ein geprueftes Zertifikat hat, darf direkt Themen/Konzepte bearbeiten und abstimmen, die mit diesem Zertifikat verknuepft sind
export async function certScoped(env, user, eid) {
  if (!user || !eid) return false;
  const certs = ((await env.DB.prepare("SELECT c.eid FROM certs c JOIN cert_check k ON k.user_id=c.user_id AND k.eid=c.eid WHERE c.user_id=? AND k.status='verified'").bind(user.id).all()).results || []).map((r) => r.eid);
  if (!certs.length) return false;
  if (certs.includes(eid)) return true;
  const map = await entityMap(env);
  for (const c of certs) if ((map.get(c)?.rel || []).some((r) => r[1] === eid)) return true;
  return (map.get(eid)?.rel || []).some((r) => certs.includes(r[1]));
}

// Basis + live veroeffentlichte Community-Entitaeten (z. B. direkt im Profil neu angelegt)
export async function knownIds(env) {
  const k = await baseIds(env);
  try { for (const r of ((await env.DB.prepare("SELECT DISTINCT eid FROM entity_rev WHERE status='live'").all()).results || [])) k.add(r.eid); } catch {}
  return k;
}

export async function validate(env, id, raw) {
  const d = {}; const bad = (e) => ({ err: e });
  d.name = txt(raw?.name, 80); if (d.name.length < 2) return bad("bad_name");
  if (!TYPES.includes(raw.type)) return bad("bad_type"); d.type = raw.type;
  d.aliases = [...new Set((Array.isArray(raw.aliases) ? raw.aliases : []).map((a) => txt(a, 60)).filter((a) => a.length >= 2))].slice(0, 10);
  d.desc = { en: txt(raw.desc?.en, 600), de: txt(raw.desc?.de, 600) };
  if (d.desc.en.length < 20 && d.desc.de.length < 20) return bad("too_short");   // Kurzbeschreibung ist Pflicht, in mindestens einer Sprache (Hover-Text in Artikeln)
  if (d.desc.en.length > 300 || d.desc.de.length > 300) return bad("too_long");
  const lg = { en: longTxt(raw.long?.en, 3000), de: longTxt(raw.long?.de, 3000) };   // Lange Beschreibung (wichtiges Feld, optional)
  if (lg.en || lg.de) d.long = lg;
  d.web = httpsUrl(raw.web, () => true); d.docs = httpsUrl(raw.docs, (h) => /(^|\.)(microsoft\.com|azure\.com|github\.com)$/i.test(h));
  d.wikipedia = httpsUrl(raw.wikipedia, (h) => /^[a-z]{2,3}\.wikipedia\.org$/i.test(h));
  if (d.web === null || d.docs === null || d.wikipedia === null) return bad("bad_url");
  d.wikidata = String(raw.wikidata || "").trim(); if (d.wikidata && !/^Q\d{1,10}$/.test(d.wikidata)) return bad("bad_qid");
  const known = await baseIds(env);
  const dbIds = new Set(((await env.DB.prepare("SELECT DISTINCT eid FROM entity_rev WHERE status IN ('live','pending')").all()).results || []).map((r) => r.eid));
  const seen = new Set(); d.rel = [];
  for (const r of (Array.isArray(raw.rel) ? raw.rel : []).slice(0, 30)) {
    const [p, to] = Array.isArray(r) ? r : [r?.p, r?.to];
    if (!PRED.includes(p) || !ID.test(to || "") || to === id || !(known.has(to) || dbIds.has(to))) return bad("bad_relation");
    const k = p + ">" + to; if (!seen.has(k)) { seen.add(k); d.rel.push([p, to]); }
  }
  // Weitere schema.org-Felder (alle optional): Logo, Version, Veroeffentlichung, Lizenz, Zertifikatsstufe/-gueltigkeit, Pruefungscode
  d.logo = httpsUrl(raw.logo, () => true); if (d.logo === null) return bad("bad_url");
  d.version = txt(raw.version, 30);
  d.released = String(raw.released || "").trim(); if (d.released && !/^\d{4}(-\d{2}(-\d{2})?)?$/.test(d.released)) return bad("bad_date");
  d.license = String(raw.license || "").trim(); if (d.license && !["free", "included", "addon", "paid"].includes(d.license)) return bad("bad_license");
  d.level = String(raw.level || "").trim(); if (d.level && !["fundamentals", "associate", "expert", "specialty"].includes(d.level)) return bad("bad_level");
  d.valid_months = Math.max(0, Math.min(120, parseInt(raw.valid_months, 10) || 0));
  d.exam = txt(raw.exam, 20);
  d.outdated = !!raw.outdated;   // nicht mehr aktuell: Seite bleibt, wird aber standardmaessig ausgeblendet
  d.replaced_by = String(raw.replaced_by || "").trim();
  if (d.replaced_by) { if (!ID.test(d.replaced_by) || d.replaced_by === id || !(known.has(d.replaced_by) || dbIds.has(d.replaced_by))) return bad("bad_relation"); d.outdated = true; }
  for (const k of ["same_as", "job", "start", "end"]) if (raw[k] !== undefined && k !== "same_as") d[k] = txt(raw[k], 40);
  return { data: d };
}

async function liveOf(db, eid) {
  return await db.prepare("SELECT r.id,r.data,r.created,r.user_id,COALESCE(u.name,'') name FROM entity_rev r LEFT JOIN users u ON u.id=r.user_id AND u.banned=0 WHERE r.eid=? AND r.status='live' ORDER BY r.created DESC LIMIT 1").bind(eid).first();
}
export const trustedUser = async (db, user) => !!(user && (user.admin || user.editor || user.pro || (await stats(db, user.id)).points >= TRUST_POINTS));

export async function handleEntity(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m;
  const need = () => (user ? null : J({ error: "login" }, 401));

  if (path === "/api/entity" && method === "GET") {
    const id = url.searchParams.get("id"); if (!ID.test(id || "")) return J({ error: "bad_request" }, 400);
    const live = await liveOf(db, id);
    const hist = ((await db.prepare("SELECT r.id,r.data,r.summary,r.created,COALESCE(u.name,'') name FROM entity_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.eid=? AND r.status IN ('live','old') ORDER BY r.created DESC LIMIT 15").bind(id).all()).results || []);
    let mine = null; if (user) mine = await db.prepare("SELECT id,data FROM entity_rev WHERE eid=? AND user_id=? AND status='pending' ORDER BY created DESC LIMIT 1").bind(id, user.id).first();
    return J({ live: live ? { id: live.id, data: JSON.parse(live.data), name: live.name, created: live.created } : null, history: hist.map((h) => ({ ...h, data: JSON.parse(h.data) })), mine: mine ? { id: mine.id, data: JSON.parse(mine.data) } : null,
      loggedIn: !!user, trusted: await trustedUser(db, user), admin: !!(user?.admin || user?.editor) });
  }
  if (path === "/api/entity" && method === "POST") {
    if (need()) return need();
    const b = await request.json().catch(() => ({})), id = String(b.id || "");
    if (!ID.test(id)) return J({ error: "bad_id" }, 400);
    if (!(await rateLimit(db, `ent:h:${user.id}`, 8, 3600)) || !(await rateLimit(db, `ent:d:${user.id}`, 30, 86400))) return J({ error: "rate_limit" }, 429);
    const v = await validate(env, id, b.data || {}); if (v.err) return J({ error: v.err }, 400);
    const data = JSON.stringify(v.data), summary = cleanText(b.summary || "", 140).replace(/[<>]/g, "");
    const cur = await liveOf(db, id); if (cur && cur.data === data) return J({ error: "unchanged" }, 400);
    const t = now();
    const claimed = await db.prepare("SELECT 1 x FROM entity_claims WHERE eid=? AND user_id=? AND status='verified'").bind(id, user.id).first();
    if (!claimed && !(user.admin || user.editor)) {   // Selbst verwaltete Entitaeten (Event, Profil, Firma): lange Beschreibung nur durch den Eigentuemer
      const hasOwner = await db.prepare("SELECT 1 x FROM entity_claims WHERE eid=? AND status='verified'").bind(id).first();
      const oldLong = JSON.stringify((cur ? JSON.parse(cur.data) : (await entityMap(env)).get(id) || {}).long || {}), newLong = JSON.stringify(v.data.long || {});
      if (hasOwner && oldLong !== newLong) return J({ error: "owner_only" }, 403);
    }
    if (claimed || (await trustedUser(db, user)) || (await certScoped(env, user, id))) {
      await db.batch([db.prepare("UPDATE entity_rev SET status='old' WHERE eid=? AND status='live'").bind(id), db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,'live',?)").bind(id, data, summary, user.id, t)]);
      await evalBadges(env, user.id); return J({ ok: true, status: "live" });
    }
    await db.prepare("DELETE FROM entity_rev WHERE eid=? AND user_id=? AND status='pending'").bind(id, user.id).run();
    await db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,'pending',?)").bind(id, data, summary, user.id, t).run();
    return J({ ok: true, status: "pending" });
  }
  if (path === "/api/entity/tr" && method === "GET") return J({ items: await entityTranslations(env.DB) }, 200, { "cache-control": "public, max-age=300" });   // automatische Uebersetzungen (autotr.js)
  if (path === "/api/entity/export" && method === "GET") {
    const rows = (await db.prepare("SELECT r.eid,r.data,r.created,r.user_id FROM entity_rev r WHERE r.status='live'").all()).results || [];
    return J({ items: rows.map((r) => ({ id: r.eid, data: JSON.parse(r.data), created: r.created, uid: r.user_id })) }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path.startsWith("/api/admin/entity")) {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    if (path === "/api/admin/entity/pending" && method === "GET") {
      const rows = (await db.prepare("SELECT r.id,r.eid,r.data,r.summary,r.created,COALESCE(u.name,'') name FROM entity_rev r LEFT JOIN users u ON u.id=r.user_id WHERE r.status='pending' ORDER BY r.created ASC LIMIT 50").all()).results || [];
      return J({ pending: rows.map((r) => ({ ...r, data: JSON.parse(r.data) })) });
    }
    if ((m = /^\/api\/admin\/entity\/(approve|reject)\/(\d+)$/.exec(path)) && method === "POST") {
      const r = await db.prepare("SELECT id,eid,user_id FROM entity_rev WHERE id=?").bind(+m[2]).first(); if (!r) return J({ error: "not_found" }, 404);
      if (m[1] === "reject") { await db.prepare("UPDATE entity_rev SET status='rejected' WHERE id=?").bind(r.id).run(); return J({ ok: true }); }
      await db.batch([db.prepare("UPDATE entity_rev SET status='old' WHERE eid=? AND status='live'").bind(r.eid), db.prepare("UPDATE entity_rev SET status='live' WHERE id=?").bind(r.id)]);
      if (r.user_id) await evalBadges(env, r.user_id); return J({ ok: true });
    }
  }
  return null;
}
