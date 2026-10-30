// Show Notes der Spreaker-Folgen bearbeiten: Basis = Abruf aus dem Spreaker-RSS (data/show_notes/<sprache>.json, veroeffentlicht unter /show-notes/),
// Override = Bearbeitung hier (Haupttext bis 12000 Zeichen, ohne Mindestlaenge; Kernpunkte und FAQ als eigene Felder). Bearbeiten duerfen Admin und Redaktion.
// Der Seitenbau nimmt den Override, sonst den Spreaker-Text. Zuruecksetzen stellt den Spreaker-Text wieder her.
import { rateLimit } from "./util.js";
import { sanitize } from "./wiki.js";
import { cleanKeypoints, cleanFaq, jsonList } from "./sections.js";

const now = () => Math.floor(Date.now() / 1000);
const LANG = /^[a-z]{2}$/, EID = /^[A-Za-z0-9_-]{3,40}$/;
let tableOk = false;
async function ensure(db) {
  if (tableOk) return;
  await db.prepare("CREATE TABLE IF NOT EXISTS episode_notes (lang TEXT NOT NULL, ep_id TEXT NOT NULL, body TEXT NOT NULL DEFAULT '', keypoints TEXT NOT NULL DEFAULT '[]', faq TEXT NOT NULL DEFAULT '[]', user_id INTEGER NOT NULL DEFAULT 0, updated INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (lang, ep_id))").run();
  tableOk = true;
}
async function base(env, lang) {
  try { const r = await fetch(`${env.SITE}/show-notes/${lang}.json`, { cf: { cacheTtl: 600 } }); if (!r.ok) return {}; return (await r.json()).episodes || {}; } catch { return {}; }
}
const words = (t) => (String(t || "").trim().match(/\S+/g) || []).length;

export async function handleNotes(env, request, url, path, user, J) {
  if (!path.startsWith("/api/notes/")) return null;
  const db = env.DB, method = request.method; await ensure(db);
  if (path === "/api/notes/export" && method === "GET") {   // oeffentlich fuer den Seitenbau
    const rows = (await db.prepare("SELECT lang,ep_id,body,keypoints,faq,updated FROM episode_notes").all()).results || [], out = {};
    for (const r of rows) (out[r.lang] ||= {})[r.ep_id] = { body: r.body, keypoints: jsonList(r.keypoints), faq: jsonList(r.faq), updated: r.updated };
    return J({ notes: out }, 200, { "cache-control": "public, max-age=300" });
  }
  if (!user) return J({ error: "login" }, 401);
  if (!user.admin && !user.editor) return J({ error: "forbidden" }, 403);
  if (!(await rateLimit(db, `notes:${user.id}`, 300, 3600))) return J({ error: "rate_limit" }, 429);

  if (path === "/api/notes/list" && method === "GET") {
    const lang = url.searchParams.get("lang") || "en"; if (!LANG.test(lang)) return J({ error: "bad_request" }, 400);
    const q = (url.searchParams.get("q") || "").toLowerCase().trim(), lim = Math.min(100, Math.max(1, parseInt(url.searchParams.get("limit")) || 30)), off = Math.max(0, parseInt(url.searchParams.get("offset")) || 0);
    const eps = await base(env, lang), ov = new Map(((await db.prepare("SELECT ep_id,updated FROM episode_notes WHERE lang=?").bind(lang).all()).results || []).map((r) => [r.ep_id, r.updated]));
    const all = Object.values(eps).filter((e) => !q || e.title.toLowerCase().includes(q)).sort((a, b) => (b.published || "").localeCompare(a.published || ""));
    return J({ lang, total: all.length, items: all.slice(off, off + lim).map((e) => ({ id: e.id, title: e.title, published: e.published, words: words(e.markup), keypoints: (e.keypoints || []).length, faq: (e.faq || []).length, edited: ov.has(e.id) })) });
  }
  if (path === "/api/notes/get" && method === "GET") {
    const lang = url.searchParams.get("lang") || "en", id = url.searchParams.get("id") || "";
    if (!LANG.test(lang) || !EID.test(id)) return J({ error: "bad_request" }, 400);
    const e = (await base(env, lang))[id]; if (!e) return J({ error: "not_found" }, 404);
    const o = await db.prepare("SELECT body,keypoints,faq,updated FROM episode_notes WHERE lang=? AND ep_id=?").bind(lang, id).first();
    const spreaker = { body: e.markup || "", keypoints: e.keypoints || [], faq: e.faq || [] };
    const effective = o ? { body: o.body, keypoints: jsonList(o.keypoints), faq: jsonList(o.faq) } : spreaker;
    return J({ lang, id, title: e.title, published: e.published, link: e.link || "", persons: e.persons || [], chapters_url: e.chapters_url || "", edited: !!o, updated: o?.updated || 0, spreaker, ...effective });
  }
  if (method !== "POST") return J({ error: "bad_request" }, 400);
  const b = await request.json().catch(() => ({})), lang = String(b.lang || "en"), id = String(b.id || "");
  if (!LANG.test(lang) || !EID.test(id)) return J({ error: "bad_request" }, 400);
  if (!(await base(env, lang))[id]) return J({ error: "not_found" }, 404);
  if (path === "/api/notes/save") {
    const sb = sanitize(String(b.body || ""), { links: true, max: 12000 }); if (sb.err) return J({ error: sb.err }, 400);
    const kp = cleanKeypoints(b.keypoints ?? []), fq = cleanFaq(b.faq ?? []);
    if (kp.err) return J({ error: kp.err }, 400); if (fq.err) return J({ error: fq.err }, 400);
    await db.prepare("INSERT INTO episode_notes(lang,ep_id,body,keypoints,faq,user_id,updated) VALUES(?,?,?,?,?,?,?) ON CONFLICT(lang,ep_id) DO UPDATE SET body=excluded.body,keypoints=excluded.keypoints,faq=excluded.faq,user_id=excluded.user_id,updated=excluded.updated")
      .bind(lang, id, sb.body, JSON.stringify(kp.list), JSON.stringify(fq.list), user.id, now()).run();
    return J({ ok: true, words: words(sb.body), keypoints: kp.list.length, faq: fq.list.length, note: "Visible after the next site build (hourly). Spreaker itself is not changed." });
  }
  if (path === "/api/notes/reset") { await db.prepare("DELETE FROM episode_notes WHERE lang=? AND ep_id=?").bind(lang, id).run(); return J({ ok: true }); }
  return null;
}
