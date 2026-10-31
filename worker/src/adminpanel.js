// Verwaltung (No-Code-Backend unter /admin/): Uebersicht, Uebernahme der Entitaeten in die Datenbank, Schalter. Nur fuer Admins.
const now = () => Math.floor(Date.now() / 1000);
async function n(db, sql, ...b) { try { return (await db.prepare(sql).bind(...b).first())?.n ?? 0; } catch { return null; } }   // Tabelle fehlt -> null
async function meta(db, k) { try { return (await db.prepare("SELECT v FROM meta WHERE k=?").bind(k).first())?.v ?? ""; } catch { return ""; } }
const FLAGS = { tr_off: /^[01]$/, atr_off: /^[01]$/, atr_ent_cap: /^\d{1,4}$/, tr_queue_on: /^[01]$/, entity_source: /^(json|db)$/ };
const QKINDS = new Set(["blog", "podcast", "video", "entity", "lblog", "notes"]), QLANGS = new Set(["en", "de", "fr", "es", "it", "nl", "pt", "pl", "id", "ru", "uk", "ar", "he", "ja", "ko"]);
import { audit } from "./util.js";

export async function handleAdminPanel(env, request, url, path, user, J) {
  if (!path.startsWith("/api/admin/panel/")) return null;
  if (!user?.admin) return J({ error: "forbidden" }, 403);
  const db = env.DB, day = new Date().toISOString().slice(0, 10);

  if (path === "/api/admin/panel/overview" && request.method === "GET") {
    let base = null; try { base = ((await (await fetch(env.SITE + "/entities.json", { cf: { cacheTtl: 300 } })).json()).entities || []).length; } catch { /* Seite nicht erreichbar */ }
    const exp = await db.prepare("SELECT updated FROM export_cache WHERE k='profiles'").first().catch(() => null);
    return J({
      queues: {
        blog: await n(db, "SELECT COUNT(*) n FROM blog_posts WHERE status='pending'"),
        podcast: await n(db, "SELECT COUNT(*) n FROM pod_episodes WHERE status IN ('submitted','review')"),
        video: await n(db, "SELECT COUNT(*) n FROM yt_videos WHERE status IN ('submitted','review')"),
        wiki: await n(db, "SELECT COUNT(*) n FROM wiki_rev WHERE status='pending'"),
        entity: await n(db, "SELECT COUNT(*) n FROM entity_rev WHERE status='pending'"),
        claims: await n(db, "SELECT COUNT(*) n FROM entity_claims WHERE status='pending'"),
        certs: await n(db, "SELECT COUNT(*) n FROM cert_check WHERE status='pending'"),
        reports: await n(db, "SELECT COUNT(*) n FROM reports"),
      },
      db: {
        entities_db: await n(db, "SELECT COUNT(DISTINCT eid) n FROM entity_rev WHERE status='live'"), entities_file: base,
        blog_live: await n(db, "SELECT COUNT(*) n FROM blog_posts WHERE status='live'"), blog_legacy: await n(db, "SELECT COUNT(*) n FROM blog_posts WHERE html<>''"),
        blog_import_offset: +(await n(db, "SELECT v n FROM blog_import WHERE k='offset'")) || 0,
        users: await n(db, "SELECT COUNT(*) n FROM users"), profiles: await n(db, "SELECT COUNT(*) n FROM profiles WHERE public=1 AND handle IS NOT NULL"),
        profiles_export_age: exp ? now() - exp.updated : null,
        item_tr: await n(db, "SELECT COUNT(*) n FROM item_tr"), ent_tr: await n(db, "SELECT COUNT(*) n FROM ent_tr"),
      },
      flags: { tr_off: await meta(db, "tr_off"), atr_off: await meta(db, "atr_off"), atr_ent_cap: await meta(db, "atr_ent_cap"), entity_source: (await meta(db, "entity_source")) || "json",
        atr_today: +(await meta(db, "atr_count:" + day)) || 0, atr_ent_today: +(await meta(db, "atr_ent:" + day)) || 0, key: !!env.ANTHROPIC_API_KEY },
    });
  }

  if (path === "/api/admin/panel/import-entities" && request.method === "POST") {   // Basis-Entitaeten aus entities.json einmalig als live-Revision in die Datenbank
    let list = []; try { list = (await (await fetch(env.SITE + "/entities.json", { cf: { cacheTtl: 0 } })).json()).entities || []; } catch { return J({ error: "site_unreachable" }, 502); }
    const have = new Set(((await db.prepare("SELECT DISTINCT eid FROM entity_rev WHERE status='live'").all()).results || []).map((r) => r.eid));
    const todo = list.filter((e) => e && /^[a-z0-9][a-z0-9-]{1,79}$/.test(e.id || "") && !have.has(e.id)), t = now();
    for (let i = 0; i < todo.length; i += 50) {
      await db.batch(todo.slice(i, i + 50).map((e) => { const { id, ...data } = e; return db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,0,'live',?)").bind(id, JSON.stringify(data), "Übernahme aus entities.json", t); }));
    }
    return J({ ok: true, imported: todo.length, already: have.size, total: list.length });
  }

  if (path === "/api/admin/panel/flag" && request.method === "POST") {
    const b = await request.json().catch(() => ({})), k = String(b.k || ""), v = String(b.v ?? "");
    if (!FLAGS[k] || !FLAGS[k].test(v)) return J({ error: "bad_request" }, 400);
    await db.prepare("INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(k, v).run(); await audit(db, user.id, "flag", k, v);
    return J({ ok: true });
  }

  if (path === "/api/admin/panel/ops" && request.method === "GET") {   // Betrieb: letzter Lauf je Cron-Aufgabe, Audit-Protokoll
    const runs = (await db.prepare("SELECT name,started,finished,ok,info FROM cron_runs WHERE id IN (SELECT MAX(id) FROM cron_runs GROUP BY name) ORDER BY name").all().catch(() => ({ results: [] }))).results || [];
    const fails = (await db.prepare("SELECT name,COUNT(*) n FROM cron_runs WHERE ok=0 AND finished>0 AND started>? GROUP BY name").bind(now() - 86400).all().catch(() => ({ results: [] }))).results || [];
    const log = (await db.prepare("SELECT a.user_id,u.name,a.action,a.target,a.detail,a.created FROM audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 50").all().catch(() => ({ results: [] }))).results || [];
    return J({ runs, fails, audit: log });
  }

  if (path === "/api/admin/panel/translations" && request.method === "GET") {   // Uebersicht: jeder Inhalt mit vorhandenen Sprachfassungen; Grundlage aus dem Seitenbau (translation-status.json) plus Datenbank
    let site = { rows: [], langs: [] }; try { site = await (await fetch(env.SITE + "/translation-status.json", { cf: { cacheTtl: 300 } })).json(); } catch { /* Seite nicht erreichbar: nur Datenbank */ }
    const rows = (site.rows || []).map((r) => ({ k: r.k, id: r.id, t: r.t, lang: r.lang || "en", langs: r.langs || [] }));
    const byKey = new Map(rows.map((r) => [r.k + "|" + r.id, r]));
    const ent = (await db.prepare("SELECT eid,lang,COUNT(*) n FROM ent_tr GROUP BY eid,lang").all().catch(() => ({ results: [] }))).results || [];
    for (const e of ent) { const r = byKey.get("entity|" + e.eid); if (r && !r.langs.includes(e.lang)) r.langs.push(e.lang); }
    const Q = { blog: "SELECT id,title,lang FROM blog_posts WHERE status='live' AND html='' ORDER BY published DESC LIMIT 2000", podcast: "SELECT id,title,lang FROM pod_episodes WHERE published>0 ORDER BY published DESC LIMIT 2000", video: "SELECT id,title,lang FROM yt_videos WHERE published>0 ORDER BY published DESC LIMIT 2000" };
    const tr = (await db.prepare("SELECT kind,item_id,lang FROM item_tr").all().catch(() => ({ results: [] }))).results || [];
    const trBy = new Map(); for (const x of tr) (trBy.get(x.kind + "|" + x.item_id) || trBy.set(x.kind + "|" + x.item_id, []).get(x.kind + "|" + x.item_id)).push(x.lang);
    for (const [k, sql] of Object.entries(Q)) for (const r of (await db.prepare(sql).all().catch(() => ({ results: [] }))).results || []) rows.push({ k, id: String(r.id), t: r.title, lang: r.lang || "en", langs: trBy.get(k + "|" + r.id) || [] });
    const queue = (await db.prepare("SELECT kind,item_id,lang,status,info FROM tr_queue").all().catch(() => ({ results: [] }))).results || [];
    return J({ langs: site.langs || [...QLANGS].filter((l) => l !== "en"), rows, queue, generated: site.generated || null, flags: { tr_queue_on: await meta(db, "tr_queue_on"), key: !!env.ANTHROPIC_API_KEY } });
  }

  if (path === "/api/admin/panel/tr-queue" && request.method === "POST") {   // vormerken / zuruecknehmen, einzeln oder gebuendelt (bis 500)
    const b = await request.json().catch(() => ({})), items = Array.isArray(b.items) ? b.items.slice(0, 500) : [b], on = b.on !== false, t = now();
    const stmts = [];
    for (const it of items) {
      const kind = String(it.kind || ""), id = String(it.id || "").slice(0, 120), lang = String(it.lang || "");
      if (!QKINDS.has(kind) || !id || !QLANGS.has(lang)) continue;
      stmts.push(on ? db.prepare("INSERT INTO tr_queue(kind,item_id,lang,title,requested_by,created,status) VALUES(?,?,?,?,?,?,'open') ON CONFLICT(kind,item_id,lang) DO UPDATE SET status='open',info=''").bind(kind, id, lang, String(it.title || "").slice(0, 200), user.id, t)
                   : db.prepare("DELETE FROM tr_queue WHERE kind=? AND item_id=? AND lang=?").bind(kind, id, lang));
    }
    for (let i = 0; i < stmts.length; i += 50) await db.batch(stmts.slice(i, i + 50));
    await audit(db, user.id, on ? "tr_queue_add" : "tr_queue_remove", String(stmts.length));
    return J({ ok: true, n: stmts.length });
  }
  return J({ error: "not_found" }, 404);
}
