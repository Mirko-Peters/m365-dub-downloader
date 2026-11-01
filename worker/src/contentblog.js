// T15: Content-Pakete (imports/blog/<sprache>/<slug>.md, im Seitenbau geprueft und gerendert) in blog_posts uebernehmen.
// Quelle: SITE/blog-content/index.json (site_content_blog.py, nur freigegebene Pakete). Neue Beitraege: publish=true -> 'live',
// sonst 'pending' (Freigabe in der Verwaltung, Blog-Pruefung). Geaenderte Pakete (anderer hash) erneuern nur Beitraege, die seit der
// letzten Uebernahme niemand im Editor geaendert hat; ein spaeter gesetztes publish-Flag schaltet einen wartenden Beitrag live.
// Nichts wird geloescht: ein Paket, das aus dem Index verschwindet, laesst den Beitrag unveraendert.
import { ensureSectionCols } from "./sections.js";

const BATCH = 40;
const clean = (s, n) => String(s || "").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "").slice(0, n);
const SLUG = /^[a-z0-9][a-z0-9-]{1,100}$/, LANG = /^[a-z]{2}$/;

export async function importContentBlog(env, now = () => Math.floor(Date.now() / 1000)) {
  const db = env.DB; await ensureSectionCols(db);
  const idx = await fetch(env.SITE + "/blog-content/index.json", { cf: { cacheTtl: 60 } }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const items = Array.isArray(idx?.items) ? idx.items : [];
  const res = { created: 0, updated: 0, published: 0, skipped: 0 };
  const owners = new Map();
  for (const p of items.slice(0, 500)) {
    if (res.created + res.updated >= BATCH) break;
    const slug = String(p.slug || "").toLowerCase(), lang = String(p.lang || "");
    if (!SLUG.test(slug) || !LANG.test(lang) || !p.title || !p.html || /<\s*(script|iframe|style|form)/i.test(p.html) || !p.hash) { res.skipped++; continue; }
    const handle = String(p.author || "mirko-p").toLowerCase();
    if (!owners.has(handle)) owners.set(handle, (await db.prepare("SELECT p.user_id uid FROM profiles p JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.handle=?").bind(handle).first())?.uid || 0);
    const uid = owners.get(handle);
    if (!uid) { res.skipped++; continue; }
    const k = `${lang}/${slug}`, t = now(), pub = Number(p.published) || t;
    const prev = await db.prepare("SELECT post_id,hash,imported FROM content_import WHERE k=?").bind(k).first();
    const vals = [clean(p.title, 140), clean(p.summary, 300), clean(p.html, 900000), JSON.stringify((p.topics || []).filter((x) => typeof x === "string").slice(0, 10)),
      JSON.stringify((p.faq || []).filter((q) => q && q.q && q.a).slice(0, 10).map((q) => ({ q: clean(q.q, 200), a: clean(q.a, 600) })))];
    if (!prev) {
      const ex = await db.prepare("SELECT id FROM blog_posts WHERE user_id=? AND slug=?").bind(uid, slug).first();
      if (ex) { res.skipped++; continue; }   // Slug schon von Hand vergeben: nicht ueberschreiben
      const st = p.publish ? "live" : "pending";
      await db.prepare("INSERT INTO blog_posts(user_id,slug,title,summary,body,html,lang,topics,keypoints,faq,status,note,created,updated,published) VALUES(?,?,?,?,'',?,?,?,'[]',?,?,'content-import',?,?,?)")
        .bind(uid, slug, vals[0], vals[1], vals[2], lang, vals[3], vals[4], st, t, t, st === "live" ? pub : 0).run();
      const row = await db.prepare("SELECT id FROM blog_posts WHERE user_id=? AND slug=?").bind(uid, slug).first();
      await db.prepare("INSERT INTO content_import(k,post_id,hash,imported) VALUES(?,?,?,?)").bind(k, row.id, String(p.hash), t).run();
      res.created++; if (st === "live") res.published++;
      continue;
    }
    const cur = await db.prepare("SELECT id,status,updated FROM blog_posts WHERE id=?").bind(prev.post_id).first();
    if (!cur) { res.skipped++; continue; }
    const edited = cur.updated > prev.imported;   // im Editor oder in der Verwaltung geaendert: Inhalt bleibt, wie er ist (dauerhaft)
    let wrote = false;
    if (prev.hash !== String(p.hash) && !edited) {
      await db.prepare("UPDATE blog_posts SET title=?,summary=?,html=?,topics=?,faq=?,updated=? WHERE id=?").bind(vals[0], vals[1], vals[2], vals[3], vals[4], t, cur.id).run();
      res.updated++; wrote = true;
    }
    if (p.publish && cur.status === "pending" && !edited) {
      await db.prepare("UPDATE blog_posts SET status='live',published=COALESCE(NULLIF(published,0),?),updated=? WHERE id=?").bind(pub, t, cur.id).run();
      res.published++; wrote = true;
    }
    if (wrote) await db.prepare("UPDATE content_import SET hash=?,imported=? WHERE k=?").bind(String(p.hash), t, k).run();
  }
  return res;
}
