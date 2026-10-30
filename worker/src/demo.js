// Testinhalte fuer den Admin: legt in seinem Profil je Bereich einen "[Test]"-Eintrag an und entfernt sie wieder
import { baseIds } from "./entities.js";
import { syncFeed } from "./blog.js";

const now = () => Math.floor(Date.now() / 1000);
const TAG = "[Test]";

export async function handleDemo(env, request, url, path, user, J) {
  if (path !== "/api/admin/demo" || request.method !== "POST") return null;
  if (!user || !user.admin) return J({ error: "forbidden" }, 403);
  const db = env.DB, b = await request.json().catch(() => ({})), uid = user.id;
  const pr = await db.prepare("SELECT handle,public FROM profiles WHERE user_id=?").bind(uid).first();
  const drop = async () => {
    const posts = (await db.prepare("SELECT id,lang,slug,title FROM blog_posts WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%").all()).results || [];
    for (const p of posts) { if (pr?.handle) await syncFeed(env, db, uid, p, pr.handle, false).catch(() => 0); await db.prepare("DELETE FROM comments WHERE vid=?").bind("blog" + p.id).run(); await db.prepare("DELETE FROM blog_votes WHERE post_id=?").bind(p.id).run(); }
    const eps = (await db.prepare("SELECT id FROM pod_episodes WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%").all()).results || [];
    for (const e of eps) { await db.prepare("DELETE FROM pod_votes WHERE ep_id=?").bind(e.id).run(); await db.prepare("DELETE FROM comments WHERE vid=?").bind("podcast" + e.id).run(); }
    const vids = (await db.prepare("SELECT id FROM yt_videos WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%").all()).results || [];
    for (const v of vids) { await db.prepare("DELETE FROM yt_votes WHERE vid_id=?").bind(v.id).run(); await db.prepare("DELETE FROM comments WHERE vid=?").bind("video" + v.id).run(); }
    const libs = (await db.prepare("SELECT id FROM lib_items WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%").all()).results || [];
    for (const l of libs) { await db.prepare("DELETE FROM lib_votes WHERE item_id=?").bind(l.id).run(); await db.prepare("DELETE FROM comments WHERE vid=?").bind("lib" + l.id).run(); }
    await db.prepare("DELETE FROM lib_items WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%").run();
    await db.batch([db.prepare("DELETE FROM blog_posts WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%"), db.prepare("DELETE FROM pod_episodes WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%"),
      db.prepare("DELETE FROM yt_videos WHERE user_id=? AND title LIKE ?").bind(uid, TAG + "%"), db.prepare("DELETE FROM guest_listings WHERE user_id=? AND note LIKE ?").bind(uid, TAG + "%")]);
  };
  await drop();
  if (!b.on) return J({ ok: true, removed: true });
  if (!(pr?.public && pr.handle)) return J({ error: "need_profile" }, 400);
  const known = await baseIds(env), pick = ["microsoft-365-copilot", "copilot", "power-platform", "sharepoint", "teams"].filter((x) => known.has(x)); for (const k of known) { if (pick.length >= 3) break; if (!pick.includes(k)) pick.push(k); }
  const topics = JSON.stringify(pick.slice(0, 3)), t = now();
  let vid = "dQw4w9WgXcQ"; try { const j = await (await fetch(`${env.SITE}/episodes.json`)).json(); vid = (j.episodes || []).find((e) => e.youtube)?.youtube?.split("/").pop() || vid; } catch {}
  const body = `## Worum es geht\n\nDies ist ein **Testbeitrag**, damit du siehst, wie Blogbeiträge auf der Startseite und im Blog aussehen. Du kannst ihn jederzeit entfernen. Er verlinkt auf ein Thema: [[${pick[0]}|${pick[0]}]]{{ref|Microsoft Learn|https://learn.microsoft.com/|Microsoft|2026}}.\n\n## Warum ein Blog\n\n- Beiträge sind sofort sichtbar\n- Bei Google erscheinen sie ab 10 Upvotes\n- Themen verbinden Beiträge mit Podcasts, Videos und Events\n\n> Ein Zitat sieht so aus.\n\n${"Zusätzlicher Text, damit der Beitrag lang genug ist. ".repeat(8)}`;
  const enBody = body.replace("Worum es geht", "What this is about").replace("Dies ist ein **Testbeitrag**, damit du siehst, wie Blogbeiträge auf der Startseite und im Blog aussehen. Du kannst ihn jederzeit entfernen.", "This is a **test post** so you can see how blog posts look on the home page and in the blog. You can remove it any time.").replace("Warum ein Blog", "Why a blog");
  for (const [lang, title, text] of [["de", `${TAG} Mein erster Beitrag`, body], ["en", `${TAG} My first post`, enBody]]) {
    const slug = "test-beitrag-" + lang, r = await db.prepare("INSERT INTO blog_posts(user_id,slug,title,summary,body,lang,topics,status,note,created,updated,published) VALUES(?,?,?,?,?,?,?,'live','',?,?,?)")
      .bind(uid, slug, title, "Ein Testbeitrag – kann gelöscht werden.", text, lang, topics, t, t, t).run().catch(() => null);
    if (r) await syncFeed(env, db, uid, { lang, slug, title, published: t }, pr.handle, true).catch(() => 0);
  }
  await db.prepare("INSERT INTO pod_episodes(user_id,title,description,lang,topics,status,spreaker_id,show_id,ai,created,updated,published,ep_url) VALUES(?,?,?,?,?,'published',0,0,0,?,?,?,?)")
    .bind(uid, `${TAG} Erste Community-Folge`, "Eine Testfolge, damit du die Podcast-Karten und -Seiten siehst. Sie kann gelöscht werden.", "de", topics, t, t, t, `${env.SITE}/de/`).run();
  await db.prepare("INSERT INTO yt_videos(user_id,title,description,lang,topics,status,video_id,created,updated,published) VALUES(?,?,?,?,?,'published',?,?,?,?)")
    .bind(uid, `${TAG} Erstes Creator-Video`, "Ein Testvideo (ein vorhandenes Video des Kanals), damit du die Video-Karten und -Seiten siehst. Es kann gelöscht werden.", "de", topics, vid, t, t, t).run();
  const g = (kind, title) => db.prepare("INSERT INTO guest_listings(user_id,kind,title,formats,langs,topics,note,link,active,created,updated) VALUES(?,?,?,?,?,?,?,?,1,?,?)")
    .bind(uid, kind, title, '["podcast","youtube"]', '["de","en"]', topics, `${TAG} Testeintrag, kann gelöscht werden.`, "", t, t).run();
  await db.prepare("INSERT INTO lib_items(user_id,slug,kind,title,summary,body,lang,topics,version,status,created,updated,published) VALUES(?,?,?,?,?,?,?,?,1,'live',?,?,?)")
    .bind(uid, "test-prompt", "prompt", `${TAG} Meeting-Zusammenfassung mit Copilot`, "Ein Test-Prompt – kann gelöscht werden.", "Fasse das Meeting in fünf Stichpunkten zusammen.\nNenne danach alle Aufgaben mit Verantwortlichen und Terminen.\nSchreibe zuletzt offene Fragen auf.", "de", topics, t, t, t).run();
  await g("speaker", "Copilot und Microsoft 365"); await g("host", "Testshow");
  return J({ ok: true, created: ["blog (de, en)", "podcast", "video", "library (prompt)", "guests (speaker, host)"], note: "Sichtbar nach dem nächsten Seitenbau (stündlich)." });
}
