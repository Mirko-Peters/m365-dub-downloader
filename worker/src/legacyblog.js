// Fruehere Podpage-Blogbeitraege nach und nach als Community-Beitraege von mirko-peters in die Datenbank uebernehmen.
// Quelle: statische Dateien der eigenen Seite (SITE/blog-import/index.json + part-N.json, vom Seitenbau erzeugt, HTML bereits bereinigt).
// Je Cron-Lauf hoechstens BATCH Beitraege; der Fortschritt steht in blog_import. Wiederholbar: UNIQUE(user_id, slug) verhindert Doppelte.
import { ensureSectionCols } from "./sections.js";

const BATCH = 60, OWNER = "mirko-peters";
const clean = (s, n) => String(s || "").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "").slice(0, n);

export async function importLegacyBlog(env) {
  const db = env.DB; await ensureSectionCols(db);
  await db.prepare("CREATE TABLE IF NOT EXISTS blog_import (k TEXT PRIMARY KEY, v INTEGER NOT NULL)").run();
  const offset = (await db.prepare("SELECT v FROM blog_import WHERE k='offset'").first())?.v || 0;
  const man = await fetch(env.SITE + "/blog-import/index.json", { cf: { cacheTtl: 60 } }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  if (!man || !man.total || !man.per || offset >= man.total) return 0;
  const owner = await db.prepare("SELECT p.user_id uid FROM profiles p JOIN users u ON u.id=p.user_id AND u.banned=0 WHERE p.handle=?").bind(OWNER).first();
  if (!owner) return 0;
  const part = Math.floor(offset / man.per), from = offset - part * man.per;
  const data = await fetch(`${env.SITE}/blog-import/part-${part + 1}.json`).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  if (!Array.isArray(data)) return 0;
  const slice = data.slice(from, from + BATCH), st = [];
  for (const p of slice) {
    const slug = String(p.slug || "").toLowerCase();
    if (!/^[a-z0-9][a-z0-9-]{1,100}$/.test(slug) || !p.title || !p.html || /<script/i.test(p.html)) continue;
    const t = Number(p.published) || Math.floor(Date.now() / 1000), u = Number(p.updated) || t;
    st.push(db.prepare("INSERT OR IGNORE INTO blog_posts(user_id,slug,title,summary,body,html,lang,topics,keypoints,faq,status,note,created,updated,published) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
      .bind(owner.uid, slug, clean(p.title, 140), clean(p.summary, 300), "", clean(p.html, 900000), "en", JSON.stringify((p.topics || []).filter((x) => typeof x === "string").slice(0, 10)),
        "[]", JSON.stringify((p.faq || []).filter((q) => q && q.q && q.a).slice(0, 10).map((q) => ({ q: clean(q.q, 200), a: clean(q.a, 600) }))), "live", "", t, u, t));
  }
  if (st.length) await db.batch(st);
  await db.prepare("INSERT INTO blog_import(k,v) VALUES('offset',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(offset + slice.length).run();
  return st.length;
}
