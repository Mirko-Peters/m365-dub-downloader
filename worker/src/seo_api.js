// SEO-Check fuer eigene Community-Inhalte (Blog, Videos/Podcasts aus den Kanaelen, eingereichte Folgen und Videos).
// Dieselbe Pruefung wie im Seitenbau (seo.js); MCP-Tools: check_seo, list_my_seo, check_seo_text, suggest_entities.
import { seoCheck, aiPrompt, suggestEntities } from "./seo.js";
import { entityMap } from "./entities.js";
import { rateLimit } from "./util.js";
import { ensureSectionCols, parseKeypointsText, parseFaqText } from "./sections.js";

const jp = (s) => { try { const v = JSON.parse(s || "[]"); return Array.isArray(v) ? v : []; } catch { return []; } };
const KINDS = ["blog", "feed", "podcast", "video"];

// Autor-Daten fuer den E-E-A-T-Check: aus dem oeffentlichen Profil, das auch die Author-Box der Seite speist
async function authorInfo(db, uid, postId) {
  const p = await db.prepare("SELECT public,handle,headline,about FROM profiles WHERE user_id=?").bind(uid).first();
  const n = async (sql) => (await db.prepare(sql).bind(uid).first())?.n || 0;
  return {
    profile: !!(p && p.public && p.handle), photo: !!(await db.prepare("SELECT 1 x FROM images WHERE kind='u' AND owner_id=?").bind(uid).first()),
    bio: ((p?.about || p?.headline || "").trim()).length, expertise: await n("SELECT COUNT(*) n FROM expertise WHERE owner_type='u' AND owner_id=?"),
    channels: await n("SELECT COUNT(*) n FROM channels WHERE owner_type='u' AND owner_id=?"),
    coauthors: postId ? (await db.prepare(typeof postId === "number" ? "SELECT COUNT(*) n FROM blog_coauthors WHERE post_id=? AND status='confirmed'" : "SELECT COUNT(*) n FROM item_guests WHERE kind=? AND item_id=? AND status='confirmed'").bind(...(typeof postId === "number" ? [postId] : postId)).first())?.n || 0 : 0,
    verified: !!(await n("SELECT COUNT(*) n FROM programs WHERE owner_type='u' AND owner_id=? AND verified=1")) || !!(await n("SELECT COUNT(*) n FROM cert_check WHERE user_id=? AND status='verified'")),
  };
}
// Datensatz -> Eingabe fuer seoCheck. Titelbild ist immer da (die Seite erzeugt es automatisch); Bilder im Text zaehlt der Check aus dem Markup ({{img|...}}).
function input(kind, r, author) {
  const base = { kind, lang: r.lang || "en", title: r.title, topics: jp(r.topics), header: true, author, transcript: null };
  if (kind === "blog" || kind === "feed") return { ...base, description: r.summary || "", body: r.body || "", keypoints: jp(r.keypoints), faq: jp(r.faq) };
  return { ...base, description: String(r.description || "").slice(0, 300), body: r.description || "" };
}
const ROWS = {
  blog: "SELECT id,title,summary,body,lang,topics,keypoints,faq,status FROM blog_posts WHERE user_id=?1",
  feed: "SELECT id,title,summary,body,'' lang,topics,keypoints,faq,'' status FROM feed_items WHERE owner_type='u' AND owner_id=?1 AND body<>''",
  podcast: "SELECT id,title,description,lang,topics,status FROM pod_episodes WHERE user_id=?1",
  video: "SELECT id,title,description,lang,topics,status FROM yt_videos WHERE user_id=?1",
};
const slim = (r) => ({ score: r.score, grade: r.grade, words: r.words, todo: r.todo });

export async function handleSeo(env, request, url, path, user, J) {
  if (!path.startsWith("/api/seo/")) return null;
  if (!user) return J({ error: "login" }, 401);
  const db = env.DB, method = request.method;
  if (!(await rateLimit(db, `seo:${user.id}`, 120, 3600))) return J({ error: "rate_limit" }, 429);
  const ents = await entityMap(env);
  await ensureSectionCols(db);
  if (path === "/api/seo/mine" && method === "GET") {
    const author = await authorInfo(db, user.id), items = [];
    const co = Object.fromEntries(((await db.prepare("SELECT c.post_id,COUNT(*) n FROM blog_coauthors c JOIN blog_posts b ON b.id=c.post_id WHERE b.user_id=? AND c.status='confirmed' GROUP BY c.post_id").bind(user.id).all()).results || []).map((x) => [x.post_id, x.n]));
    const gc = {}; for (const g of (await db.prepare("SELECT g.kind,g.item_id,COUNT(*) n FROM item_guests g WHERE g.status='confirmed' AND ((g.kind='podcast' AND g.item_id IN (SELECT id FROM pod_episodes WHERE user_id=?1)) OR (g.kind='video' AND g.item_id IN (SELECT id FROM yt_videos WHERE user_id=?1))) GROUP BY g.kind,g.item_id").bind(user.id).all()).results || []) gc[g.kind + ":" + g.item_id] = g.n;
    for (const kind of KINDS) for (const r of ((await db.prepare(ROWS[kind]).bind(user.id).all()).results || []).slice(0, 100)) {
      const rep = seoCheck(input(kind, r, kind === "blog" ? { ...author, coauthors: co[r.id] || 0 } : { ...author, coauthors: gc[kind + ":" + r.id] || 0 }), { entities: ents });
      items.push({ kind, id: r.id, title: r.title, status: r.status, ...slim(rep) });
    }
    items.sort((a, b) => a.score - b.score);
    return J({ items, average: items.length ? Math.round(items.reduce((a, x) => a + x.score, 0) / items.length) : null, hint: "Lowest score first. Fix with check_seo (details + suggestions) and then save_blog_post / save_feed_item_text." });
  }
  if (path === "/api/seo/check" && method === "GET") {
    const kind = url.searchParams.get("kind") || "", id = +url.searchParams.get("id");
    if (!KINDS.includes(kind) || !id) return J({ error: "bad_request" }, 400);
    const r = await db.prepare(ROWS[kind] + " AND id=?2").bind(user.id, id).first();
    if (!r) return J({ error: "not_found" }, 404);
    const rep = seoCheck(input(kind, r, await authorInfo(db, user.id, kind === "blog" ? id : kind === "podcast" || kind === "video" ? [kind, id] : 0)), { entities: ents });
    const ref = `${kind} #${id} „${r.title}“`;
    return J({ item: { kind, id, title: r.title }, ...rep, ask: "Soll ich die Punkte selbst verbessern, oder möchtest du, dass deine KI sie über den MCP (save_blog_post / save_feed_item_text) behebt?", ai_prompt: { de: aiPrompt(rep, ref, "de"), en: aiPrompt(rep, ref, "en") } });
  }
  if ((path === "/api/seo/preview" || path === "/api/seo/suggest") && method === "POST") {
    const b = await request.json().catch(() => ({})), kind = KINDS.includes(b.kind) ? b.kind : "blog";
    const inp = { ...input(kind, { title: String(b.title || "").slice(0, 200), summary: String(b.summary || b.description || "").slice(0, 400), body: String(b.body || b.text || "").slice(0, 40000), description: b.body || b.text || "", lang: b.lang, topics: JSON.stringify(Array.isArray(b.topics) ? b.topics.slice(0, 10) : []), keypoints: JSON.stringify(Array.isArray(b.keypoints) ? b.keypoints : parseKeypointsText(b.keypoints)), faq: JSON.stringify(Array.isArray(b.faq) ? b.faq : parseFaqText(b.faq)) }, await authorInfo(db, user.id)) };
    if (path === "/api/seo/suggest") return J(suggestEntities(inp, ents));
    const rep = seoCheck(inp, { entities: ents });
    return J({ ...rep, ai_prompt: { de: aiPrompt(rep, "diesen Entwurf", "de"), en: aiPrompt(rep, "this draft", "en") } });
  }
  return null;
}
