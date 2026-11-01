// Folgen-Register (episode, episode_text, episode_guest) und Uebersetzungen (translation) aus den Registerdateien des Seitenbaus uebernehmen,
// schrittweise (je Lauf begrenzt), nur geaenderte Zeilen (Hash). Exporte fuer Seitenbau und Agenten.
const now = () => Math.floor(Date.now() / 1000);
const hash = (x) => { let h = 5381; const s = String(x); for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0; return (h >>> 0).toString(16); };
const PER_RUN_EP = 400, PER_RUN_TR = 2500;

async function getJson(env, path) { try { const r = await fetch(env.SITE + path, { cf: { cacheTtl: 600 } }); return r.ok ? await r.json() : null; } catch { return null; } }

export async function importEpisodes(env) {
  const db = env.DB, j = await getJson(env, "/episodes-register.json");
  if (!j || !j.parts) return { skipped: "episodes-register.json nicht erreichbar" };
  const renamed = await applyRenames(db, j.renames);
  const have = new Map(((await db.prepare("SELECT id,slug,h FROM episode").all()).results || []).map((r) => [r.slug, r]));
  const t = now(); let done = 0, texts = 0;
  const part = ((+(await db.prepare("SELECT v FROM meta WHERE k='ep_import_part'").first().catch(() => null))?.v || 0) % j.parts) + 1;   // je Lauf ein Teil (Reihum), Aenderungen per Hash
  await db.prepare("INSERT INTO meta(k,v) VALUES('ep_import_part',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(String(part)).run();
  const pj = await getJson(env, `/episodes-register-${part}.json`);
  if (!pj || !Array.isArray(pj.episodes)) return { skipped: `Teil ${part} nicht erreichbar` };
  for (const e of pj.episodes) {
    if (done >= PER_RUN_EP) break;
    if (!e.slug || !e.title) continue;
    const base = { spreaker_id: e.spreaker_id || "", title: e.title, summary: e.summary || "", published: e.published || "", duration: +e.duration || 0, season: String(e.season || ""), number: String(e.number || ""), image: e.image || "", audio: e.audio || "", youtube_id: e.youtube_id || "", meta_title: e.meta_title || "", meta_description: e.meta_description || "" };
    const h = hash(JSON.stringify(base) + JSON.stringify(e.texts || {}) + JSON.stringify(e.guests || []));
    const ex = have.get(e.slug);
    if (ex && ex.h === h) continue;
    let id = ex?.id;
    if (ex) await db.prepare("UPDATE episode SET spreaker_id=?,title=?,summary=?,published=?,duration=?,season=?,number=?,image=?,audio=?,youtube_id=?,meta_title=?,meta_description=?,h=?,updated=? WHERE id=?").bind(...Object.values(base), h, t, id).run();
    else id = (await db.prepare("INSERT INTO episode(slug,spreaker_id,title,summary,published,duration,season,number,image,audio,youtube_id,meta_title,meta_description,lang,h,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'en',?,?) RETURNING id").bind(e.slug, ...Object.values(base), h, t).first())?.id;
    const stmts = [];
    for (const [f, v] of Object.entries(e.texts || {})) { const txt = typeof v === "string" ? v : JSON.stringify(v); if (!txt || txt === "[]") { stmts.push(db.prepare("DELETE FROM episode_text WHERE episode_id=? AND field=?").bind(id, f)); continue; } stmts.push(db.prepare("INSERT INTO episode_text(episode_id,field,text,h,updated) VALUES(?,?,?,?,?) ON CONFLICT(episode_id,field) DO UPDATE SET text=excluded.text,h=excluded.h,updated=excluded.updated WHERE episode_text.h<>excluded.h").bind(id, f, txt, hash(txt), t)); texts++; }
    stmts.push(db.prepare("DELETE FROM episode_guest WHERE episode_id=?").bind(id));
    for (const g of (e.guests || []).slice(0, 10)) stmts.push(db.prepare("INSERT OR IGNORE INTO episode_guest(episode_id,eid) VALUES(?,?)").bind(id, String(g)));
    for (let i = 0; i < stmts.length; i += 50) await db.batch(stmts.slice(i, i + 50));
    done++;
  }
  const total = (await db.prepare("SELECT COUNT(*) n FROM episode").first())?.n || 0;
  return { part, changed: done, texts, total, source: j.count, ...(renamed.length ? { renamed } : {}) };
}

// T12: umbenannte Folgen (data/slug_renames.json, alt -> neu): die vorhandene Zeile behaelt id, Texte und Gaeste und bekommt den neuen Slug;
// Uebersetzungen (kind 'episode') wandern mit. Gibt es den neuen Slug schon, bleibt die alte Zeile unveraendert und wird gemeldet (nichts loeschen).
export async function applyRenames(db, renames) {
  const out = [];
  for (const [from, to] of Object.entries(renames || {})) {
    if (!from || !to || from === to) continue;
    const old = await db.prepare("SELECT id FROM episode WHERE slug=?").bind(from).first();
    if (!old) continue;
    const clash = await db.prepare("SELECT id FROM episode WHERE slug=?").bind(to).first();
    if (clash) { out.push({ from, to, conflict: true }); continue; }
    await db.prepare("UPDATE episode SET slug=?,h='',updated=? WHERE id=?").bind(to, now(), old.id).run();
    await db.prepare("UPDATE OR IGNORE translation SET item_id=? WHERE kind='episode' AND item_id=?").bind(to, from).run();
    out.push({ from, to });
  }
  return out;
}

// Uebersetzungen: (1) vorhandene Tabellen ent_tr und item_tr einmalig kopieren, (2) Registerdateien des Seitenbaus (Folgen-Titel/Teaser/Notes je Sprache, Blog-Sprachfassungen) schrittweise
export async function importTranslations(env) {
  const db = env.DB, t = now(); let copied = 0, done = 0, skipped = 0;
  try {
    const a = await db.prepare("INSERT OR IGNORE INTO translation(kind,item_id,lang,field,text,src,created) SELECT 'entity',eid,lang,field,text,'auto',created FROM ent_tr").run(); copied += a.meta?.changes || 0;
    const b = await db.prepare("INSERT OR IGNORE INTO translation(kind,item_id,lang,field,text,src,created) SELECT kind,CAST(item_id AS TEXT),lang,'title',title,src,created FROM item_tr WHERE title<>''").run(); copied += b.meta?.changes || 0;
    const c = await db.prepare("INSERT OR IGNORE INTO translation(kind,item_id,lang,field,text,src,created) SELECT kind,CAST(item_id AS TEXT),lang,'summary',summary,src,created FROM item_tr WHERE summary<>''").run(); copied += c.meta?.changes || 0;
    const d = await db.prepare("INSERT OR IGNORE INTO translation(kind,item_id,lang,field,text,src,created) SELECT kind,CAST(item_id AS TEXT),lang,'body',body,src,created FROM item_tr WHERE body<>''").run(); copied += d.meta?.changes || 0;
  } catch { /* Tabellen fehlen auf frischer Datenbank */ }
  const LANGS = ["de", "fr", "es", "it", "nl", "pt", "pl", "id", "ru", "uk", "ar", "he", "ja", "ko"];
  const li = (+(await db.prepare("SELECT v FROM meta WHERE k='tr_import_i'").first().catch(() => null))?.v || 0) % (LANGS.length + 1);   // reihum: 14 Sprachdateien der Folgen, dann die Blog-Datei
  await db.prepare("INSERT INTO meta(k,v) VALUES('tr_import_i',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(String(li + 1)).run();
  for (const path of [li < LANGS.length ? `/translations-register-${LANGS[li]}.json` : "/translations-blog.json"]) {
    if (done >= PER_RUN_TR) break;
    const j = await getJson(env, path); if (!j || !Array.isArray(j.items)) continue;
    const have = new Map(((await db.prepare("SELECT kind,item_id,lang,field,h FROM translation WHERE kind=?" + (j.lang ? " AND lang=?" : "")).bind(...(j.lang ? [j.kind, j.lang] : [j.kind || j.items[0]?.kind || ""])).all()).results || []).map((r) => [r.kind + "|" + r.item_id + "|" + r.lang + "|" + r.field, r.h]));
    const stmts = [];
    for (const it of j.items) {
      if (!it.kind || !it.id || !it.lang || !it.field || !it.text) continue;
      const k = it.kind + "|" + it.id + "|" + it.lang + "|" + it.field, h = hash(it.text);
      if (have.get(k) === h) { skipped++; continue; }
      stmts.push(db.prepare("INSERT INTO translation(kind,item_id,lang,field,text,src,quality,h,created) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(kind,item_id,lang,field) DO UPDATE SET text=excluded.text,src=excluded.src,quality=excluded.quality,h=excluded.h,created=excluded.created").bind(it.kind, String(it.id).slice(0, 120), it.lang, it.field, String(it.text), it.src || "auto", it.quality || "", h, t));
      if (stmts.length >= PER_RUN_TR - done) break;
    }
    for (let i = 0; i < stmts.length; i += 100) await db.batch(stmts.slice(i, i + 100));
    done += stmts.length;
  }
  const total = (await db.prepare("SELECT COUNT(*) n FROM translation").first())?.n || 0;
  return { copied, imported: done, unchanged: skipped, total };
}

export async function handleRegister(env, request, url, path, user, J) {
  const db = env.DB;
  if (path === "/api/episodes/export" && request.method === "GET") {   // Folgen-Register mit Texten und Gaesten (Seitenbau, Agenten)
    const eps = (await db.prepare("SELECT * FROM episode ORDER BY published DESC LIMIT 3000").all().catch(() => ({ results: [] }))).results || [];
    const texts = (await db.prepare("SELECT episode_id,field,text FROM episode_text").all().catch(() => ({ results: [] }))).results || [];
    const guests = (await db.prepare("SELECT episode_id,eid FROM episode_guest").all().catch(() => ({ results: [] }))).results || [];
    const T = new Map(), G = new Map();
    for (const r of texts) (T.get(r.episode_id) || T.set(r.episode_id, {}).get(r.episode_id))[r.field] = r.field === "keypoints" || r.field === "faq" ? JSON.parse(r.text || "[]") : r.text;
    for (const r of guests) (G.get(r.episode_id) || G.set(r.episode_id, []).get(r.episode_id)).push(r.eid);
    return J({ count: eps.length, episodes: eps.map((e) => ({ ...e, h: undefined, texts: T.get(e.id) || {}, guests: G.get(e.id) || [] })) }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path === "/api/translations/export" && request.method === "GET") {   // ?kind=episode|blog|lblog|entity|notes&lang=de (Pflicht: kind)
    const kind = url.searchParams.get("kind") || "", lang = url.searchParams.get("lang") || "";
    if (!kind) return J({ error: "bad_request" }, 400);
    const rows = (await db.prepare("SELECT item_id,lang,field,text,src,quality FROM translation WHERE kind=?" + (lang ? " AND lang=?" : "") + " LIMIT 60000").bind(...(lang ? [kind, lang] : [kind])).all().catch(() => ({ results: [] }))).results || [];
    return J({ kind, count: rows.length, items: rows }, 200, { "cache-control": "public, max-age=300" });
  }
  return null;
}
