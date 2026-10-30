// Update-Waechter: schaut regelmaessig in offizielle Microsoft-Feeds und ordnet Meldungen den Produkt-Entitaeten zu (nur Titel, Link, Datum)
import { parseFeed } from "./feeds.js";

// Quellen: eid = feste Zuordnung; ohne eid wird ueber Namen/Aliase der Produkt-Entitaeten zugeordnet
export const SOURCES = [
  { name: "Microsoft 365 Roadmap", url: "https://www.microsoft.com/releasecommunications/api/v2/m365/rss" },
  { name: "Azure Updates", url: "https://www.microsoft.com/releasecommunications/api/v2/azure/rss" },
  { name: "Power BI Blog", url: "https://powerbi.microsoft.com/en-us/blog/feed/", eid: "power-bi" },
  { name: "Microsoft Fabric Blog", url: "https://blog.fabric.microsoft.com/en-us/blog/feed/", eid: "fabric" },
  { name: "Power Platform Blog", url: "https://www.microsoft.com/en-us/power-platform/blog/feed/", eid: "power-platform" },
  { name: "Microsoft 365 Blog", url: "https://www.microsoft.com/en-us/microsoft-365/blog/feed/" },
  { name: "Dynamics 365 Blog", url: "https://www.microsoft.com/en-us/dynamics-365/blog/feed/" },
  { name: "Microsoft Security Blog", url: "https://www.microsoft.com/en-us/security/blog/feed/" },
];
const now = () => Math.floor(Date.now() / 1000);
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

async function targets(env) {   // Produkt-/Plattform-Entitaeten mit Namen und Aliasen (Namen ab 4 Zeichen)
  try {
    const r = await fetch(env.SITE + "/entities.json", { cf: { cacheTtl: 600 } }); if (!r.ok) return { list: [], ids: new Set() };
    const ents = ((await r.json()).entities || []).filter((e) => e.type === "product" || e.type === "platform");
    const list = [];
    for (const e of ents) for (const n of new Set([e.name, ...(e.aliases || [])])) if (n && n.length >= 4) list.push({ id: e.id, re: new RegExp(`(^|[^\\p{L}\\p{N}])${esc(n)}($|[^\\p{L}\\p{N}])`, "iu"), len: n.length });
    list.sort((a, b) => b.len - a.len);
    return { list, ids: new Set(ents.map((e) => e.id)) };
  } catch { return { list: [], ids: new Set() }; }
}

export async function pollUpdates(env, max = 3) {
  const db = env.DB, t = now(), T = await targets(env); let n = 0;
  const st = new Map(((await db.prepare("SELECT url,fetched,fails FROM update_src").all()).results || []).map((r) => [r.url, r]));
  const due = SOURCES.filter((s) => (st.get(s.url)?.fails || 0) < 8 && (st.get(s.url)?.fetched || 0) < t - 6 * 3600).sort((a, b) => (st.get(a.url)?.fetched || 0) - (st.get(b.url)?.fetched || 0)).slice(0, max);
  for (const s of due) {
    try {
      const ctl = new AbortController(), to = setTimeout(() => ctl.abort(), 8000);
      const r = await fetch(s.url, { signal: ctl.signal, headers: { "user-agent": "M365FM-update-watch/1.0 (+https://dub.m365.fm)", accept: "application/rss+xml, application/atom+xml, text/xml, */*" } });
      clearTimeout(to); if (!r.ok) throw new Error("http " + r.status);
      const items = parseFeed((await r.text()).slice(0, 900000), 40); if (!items.length) throw new Error("empty");
      const ops = [];
      for (const i of items) {
        let ids = s.eid ? [s.eid] : [];
        if (!ids.length || !s.eid) { for (const c of T.list) { if (ids.length >= 3) break; if (!ids.includes(c.id) && c.re.test(i.title)) ids.push(c.id); } }
        if (s.eid && !T.ids.has(s.eid) && T.ids.size) ids = ids.filter((x) => x !== s.eid);
        for (const id of ids) ops.push(db.prepare("INSERT OR IGNORE INTO product_updates(eid,title,url,published,source) VALUES(?,?,?,?,?)").bind(id, i.title, i.url, i.t, s.name));
      }
      if (ops.length) await db.batch(ops);
      n += ops.length;
      await db.prepare("INSERT INTO update_src(url,fetched,fails) VALUES(?,?,0) ON CONFLICT(url) DO UPDATE SET fetched=excluded.fetched,fails=0").bind(s.url, t).run();
    } catch { await db.prepare("INSERT INTO update_src(url,fetched,fails) VALUES(?,?,1) ON CONFLICT(url) DO UPDATE SET fetched=excluded.fetched,fails=fails+1").bind(s.url, t).run(); }
  }
  await db.prepare("DELETE FROM product_updates WHERE published<?").bind(t - 500 * 86400).run();
  return n;
}

export async function handleUpdates(env, request, url, path, user, J) {
  if (path === "/api/updates/export" && request.method === "GET") {
    const rows = (await env.DB.prepare("SELECT eid,title,url,published,source FROM product_updates WHERE published>? ORDER BY published DESC LIMIT 1500").bind(now() - 400 * 86400).all()).results || [];
    return J({ items: rows }, 200, { "cache-control": "public, max-age=600" });
  }
  if (path === "/api/admin/updates/poll" && request.method === "POST") {
    if (!user || !user.admin) return J({ error: "forbidden" }, 403);
    await env.DB.prepare("UPDATE update_src SET fetched=0").run();
    return J({ ok: true, added: await pollUpdates(env, SOURCES.length) });
  }
  return null;
}
