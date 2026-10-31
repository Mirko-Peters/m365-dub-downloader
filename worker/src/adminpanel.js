// Verwaltung (No-Code-Backend unter /admin/): Uebersicht, Uebernahme der Entitaeten in die Datenbank, Schalter. Nur fuer Admins.
const now = () => Math.floor(Date.now() / 1000);
async function n(db, sql, ...b) { try { return (await db.prepare(sql).bind(...b).first())?.n ?? 0; } catch { return null; } }   // Tabelle fehlt -> null
async function meta(db, k) { try { return (await db.prepare("SELECT v FROM meta WHERE k=?").bind(k).first())?.v ?? ""; } catch { return ""; } }
const FLAGS = { tr_off: /^[01]$/, atr_off: /^[01]$/, atr_ent_cap: /^\d{1,4}$/ };

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
      flags: { tr_off: await meta(db, "tr_off"), atr_off: await meta(db, "atr_off"), atr_ent_cap: await meta(db, "atr_ent_cap"),
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
    await db.prepare("INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(k, v).run();
    return J({ ok: true });
  }
  return J({ error: "not_found" }, 404);
}
