// Tests vor dem Deploy (node --test test/): reine Funktionen des Workers und die Schema-Disziplin (Migrationen).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { cleanText, cleanName, esc, isLang, LANGS, b64u, sign, verify } from "../src/util.js";
import { sanitize } from "../src/wiki.js";
import { parseFeed } from "../src/feeds.js";
import { scoreOf, levelOf, levelName, CAPS, THRESH } from "../src/levels.js";

test("util: Texte bereinigen und escapen", () => {
  assert.equal(cleanText("  a<b>c  ", 3), "a<b");
  assert.equal(cleanName("<x> Name  Y"), "x Name Y");
  assert.equal(esc('<a&"'), "&lt;a&amp;&quot;");
  assert.equal(isLang("de"), true);
  assert.equal(isLang("hi"), false, "entfernte Sprache darf nicht mehr gelten");
  assert.equal(LANGS.length, 14);
  assert.equal(b64u.enc(new Uint8Array([1, 2, 3])), "AQID");
});

test("util: HMAC-Signatur ist pruefbar und faelschungssicher", async () => {
  const s = await sign("geheim", "42");
  assert.equal(await verify("geheim", "42", s), true);
  assert.equal(await verify("geheim", "43", s), false);
  assert.equal(await verify("anders", "42", s), false);
});

test("wiki: sanitize entfernt Skripte, laesst Markup und viz nur mit Option", () => {
  const a = sanitize("Hallo **fett** <script>alert(1)</script> [[power-automate]] {{viz|bars|Titel|a~1;b~2}}", { viz: true });
  assert.equal(a.err, null);
  assert.ok(!a.body.includes("<script"), "kein Script-Tag");
  assert.ok(a.body.includes("[[power-automate]]"), "Wiki-Link bleibt");
  assert.ok(a.body.includes("{{viz|bars|Titel|a~1;b~2}}"), "Infografik bleibt mit viz-Option");
  const b = sanitize("{{viz|bars|Titel|a~1;b~2}}");
  assert.equal(b.body, "", "ohne viz-Option faellt die Infografik weg");
});

test("feeds: parseFeed nimmt nur https-Links und liest Titel, Datum, Beschreibung", () => {
  const rss = `<rss><channel>
    <item><title>T1 &amp; mehr</title><link>https://example.com/1</link><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate><description>&lt;p&gt;Hallo https://example.com/x Welt&lt;/p&gt;</description></item>
    <item><title>Unsicher</title><link>http://example.com/2</link></item>
    <entry><title>Atom</title><link rel="alternate" href="https://example.com/3"/><updated>2024-02-01T00:00:00Z</updated></entry>
  </channel></rss>`;
  const out = parseFeed(rss);
  assert.equal(out.length, 2);
  assert.equal(out[0].title, "T1 & mehr");
  assert.equal(out[0].url, "https://example.com/1");
  assert.equal(out[0].t, Date.parse("Mon, 01 Jan 2024 00:00:00 GMT") / 1000);
  assert.equal(out[0].desc, "Hallo Welt");
  assert.equal(out[1].url, "https://example.com/3");
});

test("schema: Migrationen sind idempotent und enthalten jede zur Laufzeit angelegte Tabelle", () => {
  const dir = new URL("../migrations/", import.meta.url);
  const files = readdirSync(dir).filter((f) => f.endsWith(".sql")).sort();
  assert.ok(files.length >= 1 && files[0] === "0001_baseline.sql");
  const sql = files.map((f) => readFileSync(new URL(f, dir), "utf-8")).join("\n");
  const stmts = sql.replace(/--[^\n]*/g, "").split(";").map((s) => s.trim()).filter(Boolean);
  for (const s of stmts) assert.match(s, /^CREATE (TABLE|INDEX|UNIQUE INDEX) IF NOT EXISTS /i, "nur idempotente Anweisungen: " + s.slice(0, 60));
  const inMig = new Set([...sql.matchAll(/CREATE (?:TABLE|UNIQUE INDEX|INDEX) IF NOT EXISTS (\w+)/gi)].map((m) => m[1]));
  const src = new URL("../src/", import.meta.url);
  for (const f of readdirSync(src).filter((f) => f.endsWith(".js"))) {
    const js = readFileSync(new URL(f, src), "utf-8");
    for (const m of js.matchAll(/CREATE (?:TABLE|UNIQUE INDEX|INDEX) IF NOT EXISTS (\w+)/gi)) assert.ok(inMig.has(m[1]), `${m[1]} (aus ${f}) fehlt in migrations/`);
  }
});

test("levels: Punkte sind je Art gedeckelt, Stufen 1-6 folgen Belegen und Bestaetigungen", () => {
  assert.equal(scoreOf({ blog: 3 }), 3, "ein Beitrag = 3 Punkte");
  assert.equal(scoreOf({ library: 40 }), CAPS.library, "viele Bibliotheks-Eintraege zaehlen nur bis zur Obergrenze");
  assert.equal(scoreOf({ self: 3 }, 50), CAPS.self + CAPS.endorse, "Selbstangabe und Bestaetigungen gedeckelt");
  assert.equal(levelOf({ score: 0 }), 1); assert.equal(levelOf({ score: THRESH.practitioner }), 2); assert.equal(levelOf({ score: THRESH.expert }), 3);
  assert.equal(levelOf({ score: 1, verified: 1 }), 3, "Redaktion bestaetigt = Experte");
  assert.equal(levelOf({ score: 2, endorsed: 5000 }), 1, "ohne Expertenstufe keine hoeheren Stufen");
  assert.equal(levelOf({ score: scoreOf({}, 500) }), 2, "Bestaetigungen allein reichen hoechstens fuer Praxis");
  assert.equal(levelOf({ score: 12, endorsed: 99 }), 3); assert.equal(levelOf({ score: 12, endorsed: 100 }), 4, "Evangelist ab 100 Bestaetigungen");
  assert.equal(levelOf({ score: 12, endorsed: 1000 }), 5, "Master ab 1000"); assert.equal(levelOf({ score: 12, endorsed: 1000, endorsedEv: 1000 }), 6, "Master Evangelist ab 1000 Evangelisten");
  assert.equal(levelName(6), "Master Evangelist"); assert.equal(levelName(2, true), "Praxis");
});

// Ablauf gegen SQLite (node:sqlite) mit einem D1-aehnlichen Adapter: Migrationen, Belege einsammeln, Selbstangabe uebernehmen, Stufen berechnen
test("levels: syncExpertise baut Belege aus den Quelltabellen und setzt Stufen (SQLite)", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  const db = { prepare(sql) { const st = raw.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, all: async () => ({ results: st.all(...args) }), first: async () => st.get(...args) ?? null, run: async () => { const r = st.run(...args); return { meta: { changes: Number(r.changes) } }; } }; return o; }, async batch(stmts) { for (const s of stmts) await s.run(); } };
  const t = 1700000000;
  raw.exec(`INSERT INTO users(id,provider,sub,name,role,banned,created) VALUES(1,'g','1','Anna','user',0,${t}),(2,'g','2','Ben','user',0,${t}),(3,'g','3','Cem','user',0,${t});
    INSERT INTO profiles(user_id,public,handle,headline,about,company,job,country,show_org,updated) VALUES(1,1,'anna','','','','','',1,${t}),(2,1,'ben','','','','','',1,${t}),(3,1,'cem','','','','','',1,${t});
    INSERT INTO expertise(owner_type,owner_id,eid,level,verified) VALUES('u',2,'power-bi',3,0),('u',3,'power-bi',2,1);
    INSERT INTO blog_posts(id,user_id,slug,title,body,topics,status,created,updated) VALUES(1,1,'p1','T','B','["power-bi","fabric"]','live',${t},${t}),(2,1,'p2','T','B','["power-bi"]','live',${t},${t}),(3,1,'p3','T','B','["power-bi"]','draft',${t},${t});
    INSERT INTO events(id,owner_id,handle,title,start,created,updated) VALUES(1,2,'ev','E','2026-01-01',${t},${t});
    INSERT INTO event_sessions(id,event_id,title,topics,speakers,status,proposer_id,created) VALUES(1,1,'S','["power-bi"]','[{"h":"anna","n":"Anna","s":"confirmed"},{"h":"ben","n":"Ben"}]','live',2,${t});
    INSERT INTO certs(user_id,eid,year,url) VALUES(1,'pl-300',2025,''); INSERT INTO cert_check(user_id,eid,status,via,created) VALUES(1,'pl-300','verified','auto',${t});
    INSERT INTO endorsements(owner_id,eid,by_id,created) VALUES(1,'power-bi',2,${t}),(1,'power-bi',3,${t});`);
  const emap = new Map([["power-bi", { type: "product", rel: [] }], ["fabric", { type: "platform", rel: [] }], ["pl-300", { type: "cert", rel: [["covers", "power-bi"], ["covers", "fabric"]] }]]);
  const { syncExpertise, computeLevels } = await import("../src/levels.js");
  const r = await syncExpertise({ DB: db }, async () => emap);
  const ev = raw.prepare("SELECT owner_id,eid,kind,COUNT(*) n,SUM(weight) w FROM expertise_evidence GROUP BY owner_id,eid,kind ORDER BY owner_id,eid,kind").all();
  assert.deepEqual(ev.map((x) => [x.owner_id, x.eid, x.kind, x.n, x.w]), [[1, "fabric", "blog", 1, 3], [1, "fabric", "cert", 1, 4], [1, "power-bi", "blog", 2, 6], [1, "power-bi", "cert", 1, 4], [1, "power-bi", "session", 1, 5], [2, "power-bi", "self", 1, 3], [2, "power-bi", "session", 1, 2], [3, "power-bi", "self", 1, 2]],
    "Entwuerfe zaehlen nicht; unbestaetigter Sprecher zaehlt nur, wenn er der Veranstalter ist (Ben, eigene Veranstaltung = Gewicht 2); Selbstangaben einmal als 'self' uebernommen");
  assert.equal(r.seeded, 2);
  const lv = Object.fromEntries(raw.prepare("SELECT owner_id||':'||eid k,level FROM expertise WHERE owner_type='u'").all().map((x) => [x.k, x.level]));
  assert.deepEqual(lv, { "1:fabric": 2, "1:power-bi": 3, "2:power-bi": 2, "3:power-bi": 3 }, "Anna: 6+4+5+2 Punkte = Experte, Fabric 7 = Praxis; Ben: Selbstangabe 3 + eigene Session 2 = 5 -> Praxis; Cem: Redaktion bestaetigt -> Experte");
  const sc = raw.prepare("SELECT score,endorsed FROM expertise_score WHERE owner_id=1 AND eid='power-bi'").get();
  assert.equal(sc.score, 17); assert.equal(sc.endorsed, 2);
  // zweiter Lauf: keine doppelte Uebernahme, nichts aendert sich; Bestaetigungen bis zur Stufe Evangelist werden nachgezogen
  const r2 = await syncExpertise({ DB: db }, async () => emap); assert.equal(r2.seeded, 0); assert.equal(r2.changed, 0);
  for (let i = 10; i < 110; i++) raw.exec(`INSERT INTO endorsements(owner_id,eid,by_id,created) VALUES(1,'power-bi',${i},${t})`);
  await computeLevels(db, { uid: 1, eid: "power-bi" });
  assert.equal(raw.prepare("SELECT level FROM expertise WHERE owner_id=1 AND eid='power-bi'").get().level, 4, "102 Bestaetigungen: Evangelist");
  // Paar-Pfad vor dem ersten vollen Lauf (Bestaetigung direkt nach dem Deploy): Selbstangabe wird trotzdem uebernommen
  raw.exec(`INSERT INTO users(id,provider,sub,name,role,banned,created) VALUES(4,'g','4','Dana','user',0,${t}); INSERT INTO expertise(owner_type,owner_id,eid,level,verified) VALUES('u',4,'fabric',3,0); INSERT INTO endorsements(owner_id,eid,by_id,created) VALUES(4,'fabric',1,${t})`);
  await computeLevels(db, { uid: 4, eid: "fabric" });
  assert.equal(raw.prepare("SELECT COUNT(*) n FROM expertise_evidence WHERE owner_id=4 AND kind='self'").get().n, 1, "self-Beleg auch im Paar-Pfad");
  assert.equal(raw.prepare("SELECT level FROM expertise WHERE owner_id=4 AND eid='fabric'").get().level, 2, "3 (self) + 1 (Bestaetigung) = 4 Punkte -> Praxis");
  // geloeschtes Konto: deleteUserData raeumt Belege und Kennzahlen, der naechste Lauf legt nichts neu an
  const { deleteUserData } = await import("../src/profiles.js");
  await deleteUserData(db, 4); raw.exec("DELETE FROM users WHERE id=4");
  await syncExpertise({ DB: db }, async () => emap);
  assert.equal(raw.prepare("SELECT COUNT(*) n FROM expertise WHERE owner_id=4").get().n + raw.prepare("SELECT COUNT(*) n FROM expertise_evidence WHERE owner_id=4").get().n + raw.prepare("SELECT COUNT(*) n FROM expertise_score WHERE owner_id=4").get().n, 0, "nichts bleibt fuer das geloeschte Konto");
});

test("quotes: importQuotesFromSite schreibt nur Zitate mit Personen-Entitaet und ueberschreibt keine Redaktions-Zitate (SQLite)", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  const db = { prepare(sql) { const st = raw.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, all: async () => ({ results: st.all(...args) }), first: async () => st.get(...args) ?? null, run: async () => st.run(...args) }; return o; }, async batch(s) { for (const x of s) await x.run(); } };
  raw.exec("INSERT INTO quote(id,person_eid,text,lang,src,created) VALUES('2-1','anna','Redaktion','en','admin',1)");
  const file = { quotes: [{ id: "1-1", person: "mirko-peters", text: "Ein Zitat", lang: "de", episode_id: "1", time_s: 12.4, about: ["azure"] }, { id: "1-2", person: "", text: "ohne Person", lang: "en" }, { id: "2-1", person: "anna", text: "Seitenbau", lang: "en" }] };
  const old = globalThis.fetch; globalThis.fetch = async () => ({ json: async () => file });
  try {
    const { importQuotesFromSite, handleQuotes } = await import("../src/quotes.js");
    const r = await importQuotesFromSite({ DB: db, SITE: "https://x" });
    assert.equal(r.imported, 2);
    const rows = raw.prepare("SELECT id,person_eid,text,time_s FROM quote ORDER BY id").all();
    assert.deepEqual(rows.map((x) => [x.id, x.person_eid, x.text, x.time_s]), [["1-1", "mirko-peters", "Ein Zitat", 12], ["2-1", "anna", "Redaktion", null]], "ohne Person verworfen, Redaktions-Zitat bleibt");
    const res = await handleQuotes({ DB: db }, new URL("https://x/api/quotes/export?person=mirko-peters"), (d) => d);
    assert.equal(res.quotes.length, 1); assert.deepEqual(res.quotes[0].about, ["azure"]);
  } finally { globalThis.fetch = old; }
});
