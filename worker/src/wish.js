// Roadmap & Wunschliste: alle angemeldeten Mitglieder sehen sie und stimmen ab; Admin uebernimmt (planned) und hakt ab (done)
import { cleanText, rateLimit, esc } from "./util.js";
import { notify } from "./mail.js";

const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();
let ready = false;
async function ensure(db) {
  if (ready) return;
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS wish (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'open', note TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, updated INTEGER NOT NULL, done_at INTEGER NOT NULL DEFAULT 0)"),
    db.prepare("CREATE TABLE IF NOT EXISTS wish_votes (wish_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY (wish_id, user_id))"),
  ]);
  ready = true;
}
const STATUS = ["open", "planned", "done", "declined"];

export async function handleWish(env, request, url, path, user, J) {
  if (!path.startsWith("/api/wish/")) return null;
  const db = env.DB, method = request.method; await ensure(db);
  if (!user) return J({ error: "login" }, 401);                    // nur fuer Mitglieder mit Konto sichtbar
  if (path === "/api/wish/list" && method === "GET") {
    const rows = (await db.prepare("SELECT w.id,w.title,w.body,w.status,w.note,w.created,w.updated,w.done_at,w.user_id=? mine,COALESCE(u.name,'') name,(SELECT COUNT(*) FROM wish_votes v WHERE v.wish_id=w.id) votes,EXISTS(SELECT 1 FROM wish_votes v WHERE v.wish_id=w.id AND v.user_id=?) voted FROM wish w LEFT JOIN users u ON u.id=w.user_id ORDER BY w.created DESC LIMIT 500").bind(user.id, user.id).all()).results || [];
    return J({ admin: !!user.admin, items: rows.map((r) => ({ ...r, mine: !!r.mine, voted: !!r.voted })) });
  }
  if (method !== "POST") return J({ error: "bad_request" }, 400);
  const b = await request.json().catch(() => ({}));
  if (path === "/api/wish/save") {
    if (!(await rateLimit(db, `wish:${user.id}`, 10, 3600))) return J({ error: "rate_limit" }, 429);
    const title = txt(b.title, 120), body = txt(b.body, 1500); if (title.length < 5) return J({ error: "title" }, 400);
    const r = await db.prepare("INSERT INTO wish(user_id,title,body,status,created,updated) VALUES(?,?,?,'open',?,?)").bind(user.id, title, body, now(), now()).run();
    await db.prepare("INSERT OR IGNORE INTO wish_votes(wish_id,user_id) VALUES(?,?)").bind(r.meta.last_row_id, user.id).run();
    return J({ ok: true, id: r.meta.last_row_id });
  }
  if (path === "/api/wish/vote") {
    const id = +b.id, had = await db.prepare("SELECT 1 x FROM wish_votes WHERE wish_id=? AND user_id=?").bind(id, user.id).first();
    if (had) await db.prepare("DELETE FROM wish_votes WHERE wish_id=? AND user_id=?").bind(id, user.id).run(); else await db.prepare("INSERT OR IGNORE INTO wish_votes(wish_id,user_id) VALUES(?,?)").bind(id, user.id).run();
    return J({ ok: true });
  }
  if (path === "/api/wish/status") {                                // Admin: uebernehmen (planned), abhaken (done), ablehnen
    if (!user.admin) return J({ error: "forbidden" }, 403);
    if (!STATUS.includes(b.status)) return J({ error: "bad_status" }, 400);
    await db.prepare("UPDATE wish SET status=?,note=?,updated=?,done_at=CASE WHEN ?='done' THEN ? ELSE 0 END WHERE id=?").bind(b.status, txt(b.note, 300), now(), b.status, now(), +b.id).run();
    const wo = await db.prepare("SELECT user_id,title FROM wish WHERE id=?").bind(+b.id).first();
    const SL = { planned: "in die Roadmap übernommen", done: "umgesetzt", declined: "abgelehnt", open: "wieder offen" };
    if (wo && wo.user_id !== user.id && SL[b.status]) await notify(env, wo.user_id, "wish", `Dein Wunsch „${wo.title.slice(0, 80)}“ wurde ${SL[b.status]}`, `<p>Dein Wunsch <b>${esc(wo.title)}</b> ist jetzt: <b>${SL[b.status]}</b>.</p>${txt(b.note, 300) ? `<p>${esc(txt(b.note, 300))}</p>` : ""}<p><a href="${env.SITE}/community/#c-wish">Roadmap &amp; Wunschliste</a></p>`, `wish:${+b.id}:${b.status}`);
    return J({ ok: true });
  }
  if (path === "/api/wish/delete") {
    const w = await db.prepare("SELECT user_id FROM wish WHERE id=?").bind(+b.id).first();
    if (!w || (w.user_id !== user.id && !user.admin)) return J({ error: "not_found" }, 404);
    await db.batch([db.prepare("DELETE FROM wish_votes WHERE wish_id=?").bind(+b.id), db.prepare("DELETE FROM wish WHERE id=?").bind(+b.id)]);
    return J({ ok: true });
  }
  return J({ error: "not_found" }, 404);
}

// Offene Punkte der Plattform als "planned" in die Roadmap eintragen (einmalig je Titel, Eigentuemer = Admin)
const PLAN = [
  ["Englische Show (/show/) in weitere Sprachen übersetzen", "Titel, Zusammenfassungen und Seiten zuerst in 5–6 Sprachen (ca. 25–30 $, mit Batch weniger); Show Notes und Transkripte nur für die meistgehörten Folgen. Vollständig 19 Sprachen: ca. 95 $ (ohne Show Notes), ca. 2.000 $ mit Show Notes. Wartet auf Sprachauswahl und Anthropic-Credits."],
  ["Podpage-Import vervollständigen: Gäste (178) und Blogposts", "Podpage-API lieferte Bad Gateway. Gäste als Personen-Entitäten (site_podpage.make_guest_entities), Blog nach /show/blog/."],
  ["Podcast-Umzug: Bedingungen, Werbeplatz, eigener Feed je Show", "Nutzungsbedingungen juristisch formulieren (Werbeeinnahmen auf den Show-Seiten an M365.FM, eigenes Sponsoring des Podcasters bleibt bei ihm), Werbeplatz auf /shows/, M365.FM-Feed je Show mit itunes:new-feed-url."],
  ["Podcast-Umzug über die Spreaker-API (Audio-Hosting bei M365.FM)", "Beim Umzug legt ein Job (GitHub Action, nicht der Worker) per Spreaker-API eine Show im M365.FM-Konto an, lädt die Folgen aus dem alten Feed hoch und liefert einen neuen Feed (itunes:new-feed-url). Damit steuert M365.FM Verbreitung und Werbung. Zu klären: Spreaker-Tarif (Speicher/Stunden), Rechte-Einwilligung, Wiederholung für neue Folgen, Abgleich mit dem Import unter /shows/."],
  ["Mitgliedschaft für Hörer: werbefreier Feed und keine Ads auf der Seite", "Hörer zahlen bei M365.FM (Zahlungsanbieter mit Webhook, Status in der Datenbank). Mitglieder bekommen (1) einen persönlichen Feed-Link mit geheimem Token, der nur werbefreie Audiodateien enthält (Spreaker-Folgen als werbefrei markiert oder eigener Speicher), und (2) keine AdSense-Anzeigen auf der Seite (Skript wird erst nach Login-Prüfung geladen, Einwilligung in der EU nötig). Spreaker Supporters Club hat laut API-Doku keine Endpunkte für Mitglieder; Nachfrage beim Spreaker-Support offen. Preis (von Mirko festgelegt): 6,99 USD pro Monat. Abgrenzung: Hosting-Preise 5 $ / 10 $ gelten für Podcaster, die ihre Show bei uns hosten lassen."],
  ["Podcast-Umzug: Option „Neue Show bei Spreaker anlegen“ mit Zugriff nur auf die eigene Show", "M365.FM legt die Show im eigenen Spreaker-Konto an (Daten des Podcasters), der Podcaster wird als Mitarbeiter (Collaborator) nur dieser Show eingeladen. Kostenpflichtig; Preise (von Mirko festgelegt): Gehostet 5 $ pro Monat, gehostet und werbefrei 10 $ pro Monat. Spreaker-Plan Anchorman (50 $/Monat) für unbegrenzte Collaborators nötig. Von Mirko bestätigt: Spreaker erlaubt, Shows für Dritte anzulegen und sie als Mitarbeiter einzuladen. Offen: Collaborator-Zugriff auf einzelne Shows begrenzbar? Zahlungsanbieter mit Abos und Umsatzsteuer."],
  ["Podcast-Umzug: Bezahl-Option ohne Werbung", "Bezahlte Stufe für umgezogene Shows: Solange bezahlt wird, ist die Werbung auf der Show und ihren Folgenseiten abgeschaltet; endet die Zahlung, wird sie wieder eingeblendet. Braucht Zahlungsanbieter, Abo-Status je Show und ein Werbe-Flag im Seitenbau."],
  ["Microsoft-Login (Entra-App, Anmeldung mit Microsoft-Konto)", "Benötigt Entra-App und die Secrets MS_CLIENT_ID / MS_CLIENT_SECRET."],
  ["Mail-System (Benachrichtigungen per E-Mail)", "Resend-Anbindung; E-Mail bei Antworten, Roadmap-Statuswechseln und neuen Updates."],
  ["Roadmap & Wunschliste: Benachrichtigung bei Statuswechsel", "E-Mail und Push, wenn ein Wunsch übernommen oder umgesetzt wird."],
  ["Entitäten-Seiten: Produkte und Services der Firmen anzeigen", "Firmen-Angebote und Follower-Zahlen direkt auf den Entitäten-Seiten."],
  ["Update-Wächter: Wichtigkeitsbewertung und mehr Quellen", "Tech-Community-Blogs, Learn „What’s new“, Bewertung nach Wichtigkeit, E-Mail/Push je Produkt."],
  ["Bibliothek: Versionsverlauf, Forks und Badges", "Frühere Versionen ansehen, Einträge forken, Auszeichnungen für beliebte Einträge."],
  ["Seitenbau beschleunigen: Teilen-Bilder nur für neue Seiten", "Open-Graph-Bilder inkrementell erzeugen, Browser-Cache zwischen Läufen."],
  ["YouTube: API-Audit und Kontingent beantragen", "Damit Creator-Uploads dauerhaft und ohne 7-Tage-Token-Ablauf laufen."],
  ["Creator-Videos live testen (YouTube-Upload)", "Upload, Freigabe-Schwelle und Seiten mit echtem YouTube-Konto prüfen."],
  ["HeySummit: Registrierungen übertragen (Test)", "Übertragung von Anmeldungen mit einer Test-Registrierung verifizieren."],
];
export async function seedRoadmap(env) {
  const db = env.DB; await ensure(db);
  const subs = (env.ADMIN_SUBS || "").split(",").map((x) => x.trim()).filter(Boolean);
  let owner = null;
  for (const a of subs) { const [pr, ...rest] = a.split(":"); owner = await db.prepare("SELECT id FROM users WHERE provider=? AND sub=?").bind(pr, rest.join(":")).first(); if (owner) break; }
  if (!owner) return 0;
  let n = 0;
  for (const [title, body] of PLAN) {
    if (await db.prepare("SELECT 1 x FROM wish WHERE title=?").bind(title).first()) continue;
    const t = now();
    const r = await db.prepare("INSERT INTO wish(user_id,title,body,status,created,updated) VALUES(?,?,?,'planned',?,?)").bind(owner.id, title, body, t, t).run();
    await db.prepare("INSERT OR IGNORE INTO wish_votes(wish_id,user_id) VALUES(?,?)").bind(r.meta.last_row_id, owner.id).run(); n++;
  }
  return n;
}
