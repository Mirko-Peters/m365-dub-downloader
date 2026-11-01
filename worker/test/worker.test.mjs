// Tests vor dem Deploy (node --test test/): reine Funktionen des Workers und die Schema-Disziplin (Migrationen).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { cleanText, cleanName, esc, isLang, LANGS, b64u, sign, verify } from "../src/util.js";
import { sanitize } from "../src/wiki.js";
import { parseFeed } from "../src/feeds.js";
import { scoreOf, levelOf, levelName, CAPS, THRESH } from "../src/levels.js";
import { handleSponsor } from "../src/sponsor.js";
import { handleAdminPanel } from "../src/adminpanel.js";

async function searchDb(failTrigram = false) {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  let trigramFailed = false, indexWrites = 0, searchQueries = 0;
  const db = {
    prepare(sql) {
      if (sql.includes("eligible AS (")) searchQueries++;
      const st = raw.prepare(sql); let args = [];
      const o = {
        bind(...a) { args = a; return o; },
        all: async () => ({ results: st.all(...args) }),
        first: async () => st.get(...args) ?? null,
        run: async () => {
          if (failTrigram && !trigramFailed && /CREATE VIRTUAL TABLE IF NOT EXISTS search_fts .*tokenize='trigram'/.test(sql)) {
            trigramFailed = true;
            throw new Error("trigram tokenizer unavailable");
          }
          const r = st.run(...args), n = Number(r.changes);
          if (/^\s*(INSERT|UPDATE|DELETE)/i.test(sql) && /search_doc|search_fts/.test(sql)) indexWrites += n;
          return { meta: { changes: n } };
        },
      };
      return o;
    },
    async batch(stmts) { for (const st of stmts) await st.run(); },
  };
  return { db, raw, indexWrites: () => indexWrites, searchQueries: () => searchQueries };
}

function seedSearchDocs(raw, docs) {
  raw.exec("CREATE VIRTUAL TABLE search_fts USING fts5(title,keywords,summary,tokenize='trigram'); INSERT INTO meta(k,v) VALUES('search_fts_tokenizer','trigram')");
  const insert = raw.prepare("INSERT INTO search_doc(id,url,lang,type,title,summary,keywords,entities,date,image,h,gone,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,0,1)");
  const fts = raw.prepare("INSERT INTO search_fts(rowid,title,keywords,summary) VALUES(?,?,?,?)");
  raw.exec("BEGIN");
  try {
    for (const doc of docs) {
      insert.run(doc.id, doc.url, doc.lang, doc.type, doc.title, doc.summary || "", doc.keywords || "", (doc.entities || []).join(","), doc.date || "", "", doc.id);
      const { rowid } = raw.prepare("SELECT rowid FROM search_doc WHERE id=?").get(doc.id);
      fts.run(rowid, doc.title, doc.keywords || "", doc.summary || "");
    }
    raw.exec("COMMIT");
  } catch (error) {
    raw.exec("ROLLBACK");
    throw error;
  }
}

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

test("contentblog: importContentBlog legt Pakete pending/live an, erneuert nur unveraenderte und schuetzt Editor-Aenderungen (SQLite)", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  const db = { prepare(sql) { const st = raw.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, all: async () => ({ results: st.all(...args) }), first: async () => st.get(...args) ?? null, run: async () => st.run(...args) }; return o; }, async batch(s) { for (const x of s) await x.run(); } };
  raw.exec(`INSERT INTO users(id,provider,sub,name,role,banned,created) VALUES(1,'g','1','Mirko','user',0,1);
    INSERT INTO profiles(user_id,public,handle,headline,about,company,job,country,show_org,updated) VALUES(1,1,'mirko-p','','','','','',1,1);
    INSERT INTO blog_posts(user_id,slug,title,created,updated) VALUES(1,'von-hand','Von Hand',1,1)`);
  const P = (o) => ({ slug: "a-post", lang: "de", title: "Ein Beitrag", summary: "Kurz", html: "<p>Text</p>", author: "mirko-p", topics: ["azure"], faq: [], publish: false, published: 100, hash: "h1", ...o });
  let file = { items: [P(), P({ slug: "b-post", publish: true }), P({ slug: "von-hand" }), P({ slug: "boese", html: "<script>x</script>" }), P({ slug: "fremd", author: "niemand" })] };
  const old = globalThis.fetch; globalThis.fetch = async () => ({ ok: true, json: async () => file });
  let clock = 1000; const now = () => clock;
  try {
    const { importContentBlog } = await import("../src/contentblog.js");
    let r = await importContentBlog({ DB: db, SITE: "https://x" }, now);
    assert.deepEqual([r.created, r.published, r.skipped], [2, 1, 3], "zwei neu, einer live; Slug von Hand, Skript, unbekannter Autor uebersprungen");
    const st = (s) => raw.prepare("SELECT status,title,published FROM blog_posts WHERE slug=?").get(s);
    assert.equal(st("a-post").status, "pending"); assert.equal(st("b-post").status, "live"); assert.equal(st("b-post").published, 100);
    assert.equal(st("von-hand").title, "Von Hand", "Beitrag von Hand bleibt");
    clock = 2000; file = { items: [P({ title: "Neuer Titel", hash: "h2", publish: true }), P({ slug: "b-post", publish: true, title: "B neu", hash: "h3" })] };
    raw.exec("UPDATE blog_posts SET title='Im Editor', updated=1500 WHERE slug='b-post'");
    r = await importContentBlog({ DB: db, SITE: "https://x" }, now);
    assert.equal(st("a-post").title, "Neuer Titel"); assert.equal(st("a-post").status, "live", "publish-Flag schaltet wartenden Beitrag live");
    assert.equal(st("b-post").title, "Im Editor", "im Editor geaendert: Paket ueberschreibt nicht");
    clock = 3000; file = { items: [P({ slug: "b-post", publish: true, title: "B noch neuer", hash: "h4" })] };
    await importContentBlog({ DB: db, SITE: "https://x" }, now);
    assert.equal(st("b-post").title, "Im Editor", "Schutz bleibt dauerhaft");
  } finally { globalThis.fetch = old; }
});

test("register: applyRenames gibt der vorhandenen Folge den neuen Slug, nimmt Uebersetzungen mit und legt keine zweite Zeile an (SQLite)", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  const db = { prepare(sql) { const st = raw.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, all: async () => ({ results: st.all(...args) }), first: async () => st.get(...args) ?? null, run: async () => st.run(...args) }; return o; }, async batch(s) { for (const x of s) await x.run(); } };
  raw.exec("INSERT INTO episode(slug,spreaker_id,title,lang,h,updated) VALUES('alt','73815737','Titel','en','x',1)");
  raw.exec("INSERT INTO episode_text(episode_id,field,text,h,updated) VALUES(1,'notes','Notizen','y',1)");
  raw.exec("INSERT INTO translation(kind,item_id,lang,field,text,src,created) VALUES('episode','alt','de','title','Titel DE','haiku',1)");
  raw.exec("INSERT INTO episode(slug,spreaker_id,title,lang,h,updated) VALUES('b','2','B','en','x',1),('b-neu','3','B neu','en','x',1)");
  const { applyRenames } = await import("../src/register.js");
  const r = await applyRenames(db, { alt: "neu", b: "b-neu", fehlt: "egal" });
  assert.deepEqual(r, [{ from: "alt", to: "neu" }, { from: "b", to: "b-neu", conflict: true }]);
  assert.deepEqual(raw.prepare("SELECT id,slug,h FROM episode ORDER BY id").all().map((x) => [x.id, x.slug, x.h]), [[1, "neu", ""], [2, "b", "x"], [3, "b-neu", "x"]], "id bleibt, Konflikt laesst beide Zeilen stehen");
  assert.equal(raw.prepare("SELECT text FROM episode_text WHERE episode_id=1").get().text, "Notizen");
  assert.equal(raw.prepare("SELECT item_id FROM translation WHERE kind='episode'").get().item_id, "neu");
  assert.deepEqual(await applyRenames(db, { alt: "neu" }), [], "zweiter Lauf aendert nichts");
});

test("entities: syncEntitiesFromSite uebernimmt JSON-Aenderungen, wenn zuletzt eine Maschine das Feld gesetzt hat, und laesst Menschen-Aenderungen stehen (SQLite)", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  const db = { prepare(sql) { const st = raw.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, all: async () => ({ results: st.all(...args) }), first: async () => st.get(...args) ?? null, run: async () => st.run(...args) }; return o; }, async batch(s) { for (const x of s) await x.run(); } };
  const ins = (eid, data, uid, status, summary) => raw.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,?,1)").run(eid, JSON.stringify(data), summary, uid, status);
  // a: nur importiert -> Name und Doku-Link aus der JSON
  ins("a", { type: "person", name: "Yves HABERSAAT", desc: { en: "Bio" } }, 0, "live", "Übernahme aus entities.json");
  // b: Mensch hat den Namen geaendert, danach Auto-Uebersetzung -> Name bleibt, neuer Doku-Link kommt, fr-Uebersetzung bleibt
  ins("b", { type: "product", name: "Alt", desc: { en: "E" } }, 0, "old", "Übernahme aus entities.json");
  ins("b", { type: "product", name: "Von Hand", desc: { en: "E" } }, 7, "old", "Korrektur");
  ins("b", { type: "product", name: "Von Hand", desc: { en: "E", fr: "F" } }, 0, "live", "Auto-Übersetzung (Claude Haiku)");
  // c: unveraendert -> nichts
  ins("c", { type: "concept", name: "C" }, 0, "live", "Übernahme aus entities.json");
  const src = [{ id: "a", type: "person", name: "Yves Habersaat", desc: { en: "Bio" }, docs: "https://learn.microsoft.com/x" },
    { id: "b", type: "product", name: "JSON-Name", desc: { en: "E" }, docs: "https://learn.microsoft.com/b", wikidata: "Q42" },
    { id: "c", type: "concept", name: "C" }, { id: "neu", type: "concept", name: "Neu" }];
  const old = globalThis.fetch; let body = { entities: src };
  globalThis.fetch = async (u) => ({ ok: true, json: async () => (String(u).endsWith("/entities-src.json") ? body : { entities: src }) });
  try {
    const { syncEntitiesFromSite, importEntitiesFromSite } = await import("../src/entities.js");
    const r = await syncEntitiesFromSite({ DB: db, SITE: "https://x" });
    assert.equal(r.updated, 2); assert.equal(r.candidates, 2);
    const live = (id) => JSON.parse(raw.prepare("SELECT data FROM entity_rev WHERE eid=? AND status='live'").get(id).data);
    assert.equal(live("a").name, "Yves Habersaat"); assert.equal(live("a").docs, "https://learn.microsoft.com/x");
    assert.equal(live("b").name, "Von Hand", "Menschen-Aenderung bleibt"); assert.equal(live("b").docs, "https://learn.microsoft.com/b"); assert.equal(live("b").wikidata, "Q42"); assert.equal(live("b").desc.fr, "F", "Uebersetzung bleibt");
    assert.equal(raw.prepare("SELECT COUNT(*) n FROM entity_rev WHERE eid='c'").get().n, 1, "unveraendert -> keine neue Fassung");
    assert.equal(raw.prepare("SELECT COUNT(*) n FROM entity_rev WHERE eid IN ('a','b')").get().n, 6, "alte Fassungen bleiben (status old), nichts geloescht");
    const r2 = await syncEntitiesFromSite({ DB: db, SITE: "https://x" });
    assert.equal(r2.updated, 0, "zweiter Lauf aendert nichts"); assert.equal(r2.candidates, 1, "b bleibt Kandidat wegen des Menschen-Namens");
    body = { entities: src.slice(0, 2) };   // halber Seitenbau
    const r3 = await syncEntitiesFromSite({ DB: db, SITE: "https://x" });
    assert.match(r3.skipped || "", /unvollstaendig/);
    body = { entities: src };
    const r4 = await importEntitiesFromSite({ DB: db, SITE: "https://x" });
    assert.equal(r4.imported, 1, "neue ID wird wie bisher uebernommen"); assert.equal(r4.synced.updated, 0);
    raw.exec("INSERT INTO meta(k,v) VALUES('entity_source','db') ON CONFLICT(k) DO UPDATE SET v='db'");
    assert.match((await syncEntitiesFromSite({ DB: db, SITE: "https://x" })).skipped, /entity_source=db/);
  } finally { globalThis.fetch = old; }
});

test("sponsor: Anfragen, Honeypot, Rate-Limit und Admin-Panel (SQLite)", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  const db = { prepare(sql) { const st = raw.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, all: async () => ({ results: st.all(...args) }), first: async () => st.get(...args) ?? null, run: async () => { const r = st.run(...args); return { meta: { changes: Number(r.changes), last_row_id: Number(r.lastInsertRowid) } }; } }; return o; }, async batch(s) { for (const x of s) await x.run(); } };
  const env = { DB: db, SESSION_SECRET: "test-secret", SITE: "https://www.m365.fm", ADMIN_SUBS: "google:sub2" };
  raw.exec("INSERT INTO users(id,provider,sub,name,role,banned,created) VALUES(1,'google','sub1','Admin 1','admin',0,1),(2,'google','sub2','Admin 2','user',0,1)");
  raw.exec("INSERT INTO mail_addr(user_id,email,verified,created) VALUES(1,'admin1@example.com',1,1),(2,'admin2@example.com',1,1)");
  const J = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json" } });
  const payload = (extra = {}) => ({ company: "Contoso", name: "Ada Beispiel", email: "ada@example.com", message: "Bitte melden.", package: { ziel: "Azure", themen: ["Cloud"], laufzeit: "3 Monate", bausteine: ["Podcast"], preisMonat: 500, gesamtpreis: 1500 }, lang: "de", ...extra });
  const request = (body) => new Request("https://api.example/api/sponsor/request", { method: "POST", headers: { "cf-connecting-ip": "203.0.113.8", "content-type": "application/json" }, body: JSON.stringify(body) });
  const post = (body) => handleSponsor(env, request(body), new URL("https://api.example/api/sponsor/request"), "/api/sponsor/request", J);

  assert.equal((await post(null)).status, 400, "ungueltige JSON-Form wird kontrolliert abgewiesen");
  assert.equal((await post(payload({ email: "nicht-eine-mail" }))).status, 400);
  let response = await post(payload());
  assert.equal(response.status, 200);
  let rows = raw.prepare("SELECT id,status,ip_hash,package FROM sponsor_requests ORDER BY id").all();
  assert.equal(rows[0].status, "new");
  assert.match(rows[0].ip_hash, /^[a-f0-9]{64}$/);
  assert.notEqual(rows[0].ip_hash, "203.0.113.8");
  assert.equal(JSON.parse(rows[0].package).preisMonat, 500);
  let outbox = raw.prepare("SELECT user_id,key,html FROM mail_outbox ORDER BY user_id").all();
  assert.deepEqual(outbox.map((x) => x.user_id), [1, 2], "beide Admin-Konten bekommen eine Outbox-Mail");
  assert.ok(outbox.some((x) => x.key === `sponsor:${rows[0].id}`));
  assert.match(outbox[0].html, /Contoso/);
  assert.match(outbox[0].html, /USD 500\/Monat/);
  assert.match(outbox[0].html, /\/admin\//);

  response = await post(payload({ website: "gefüllt" }));
  assert.equal(response.status, 200);
  rows = raw.prepare("SELECT id,status FROM sponsor_requests ORDER BY id").all();
  assert.equal(rows[1].status, "spam");
  assert.equal(raw.prepare("SELECT COUNT(*) n FROM mail_outbox").get().n, 2, "Honeypot erzeugt keine Mail");

  for (let i = 0; i < 3; i++) assert.equal((await post(payload())).status, 200);
  assert.equal((await post(payload())).status, 429, "sechste Anfrage innerhalb einer Stunde wird abgewiesen");
  assert.equal(raw.prepare("SELECT COUNT(*) n FROM sponsor_requests").get().n, 5);

  const adminReq = new Request("https://api.example/api/admin/panel/sponsor-requests?status=spam&limit=10");
  response = await handleAdminPanel(env, adminReq, new URL(adminReq.url), "/api/admin/panel/sponsor-requests", { id: 3, admin: false }, J);
  assert.equal(response.status, 403, "Liste ist nur fuer Admins");
  response = await handleAdminPanel(env, adminReq, new URL(adminReq.url), "/api/admin/panel/sponsor-requests", { id: 1, admin: true }, J);
  let result = await response.json();
  assert.equal(result.total, 1);
  assert.equal(result.items[0].status, "spam");
  response = await handleAdminPanel(env, new Request("https://api.example/api/admin/panel/sponsor-requests/status", { method: "POST", body: JSON.stringify({ id: rows[0].id, status: "contacted" }) }), new URL("https://api.example/api/admin/panel/sponsor-requests/status"), "/api/admin/panel/sponsor-requests/status", { id: 1, admin: true }, J);
  assert.equal(response.status, 200);
  assert.equal(raw.prepare("SELECT status FROM sponsor_requests WHERE id=?").get(rows[0].id).status, "contacted");
  raw.close();
});

test("entities: Abgleich ueberschreibt keine Menschen (freigegebener Vorschlag mit aelterer id, geloeschtes Konto, absichtlich geleertes Feld, selbst verwaltet) (SQLite)", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const raw = new DatabaseSync(":memory:");
  const dir = new URL("../migrations/", import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".sql")).sort()) raw.exec(readFileSync(new URL(f, dir), "utf-8"));
  const db = { prepare(sql) { const st = raw.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, all: async () => ({ results: st.all(...args) }), first: async () => st.get(...args) ?? null, run: async () => st.run(...args) }; return o; }, async batch(s) { for (const x of s) await x.run(); } };
  const ins = (eid, data, uid, status, summary) => raw.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,?,?,1)").run(eid, JSON.stringify(data), summary, uid, status);
  const IMP = "Übernahme aus entities.json", TR = "Auto-Übersetzung (Claude Haiku)";
  // p: Vorschlag (id 2) erst nach einer Maschinen-Fassung (id 3) freigegeben -> live hat die kleinere id
  ins("p", { type: "product", name: "Teams Alt" }, 0, "old", IMP);
  ins("p", { type: "product", name: "Microsoft Teams" }, 7, "live", "Name korrigiert");
  ins("p", { type: "product", name: "Teams Alt", desc: { fr: "x" } }, 0, "old", TR);
  // d: Mensch korrigiert, Konto spaeter geloescht (user_id 0, Zusammenfassung bleibt)
  ins("d", { type: "person", name: "Yves HABERSAAT", job: "CTO" }, 0, "old", IMP);
  ins("d", { type: "person", name: "Yves Habersaat", job: "Principal Architect" }, 0, "live", "Eigenes Profil");
  // w: Mensch entfernt eine falsche Wikidata-ID
  ins("w", { type: "product", name: "W", wikidata: "Q1" }, 0, "old", IMP);
  ins("w", { type: "product", name: "W", wikidata: "" }, 9, "live", "falsche Q-ID entfernt");
  // o: selbst verwaltet (verifizierter Claim)
  ins("o", { type: "org", name: "Firma" }, 0, "live", IMP);
  raw.exec("INSERT INTO entity_claims(eid,user_id,status,created) VALUES('o',5,'verified',1)");
  const src = [{ id: "p", type: "product", name: "Teams Alt", wikidata: "Q2" }, { id: "d", type: "person", name: "Yves HABERSAAT", job: "CTO" },
    { id: "w", type: "product", name: "W", wikidata: "Q1", docs: "https://learn.microsoft.com/w" }, { id: "o", type: "org", name: "JSON-Firma" }];
  const old = globalThis.fetch; globalThis.fetch = async () => ({ ok: true, json: async () => ({ entities: src }) });
  try {
    const { syncEntitiesFromSite } = await import("../src/entities.js");
    const r = await syncEntitiesFromSite({ DB: db, SITE: "https://x" });
    const live = (id) => JSON.parse(raw.prepare("SELECT data FROM entity_rev WHERE eid=? AND status='live'").get(id).data);
    assert.equal(raw.prepare("SELECT COUNT(*) n FROM entity_rev WHERE status='live' GROUP BY eid HAVING n>1").all().length, 0, "je Entitaet genau eine live-Fassung");
    assert.equal(live("p").name, "Microsoft Teams", "freigegebener Vorschlag bleibt"); assert.equal(live("p").wikidata, "Q2");
    assert.equal(live("d").name, "Yves Habersaat", "Aenderung eines geloeschten Kontos bleibt"); assert.equal(live("d").job, "Principal Architect");
    assert.equal(live("w").wikidata, "", "absichtlich geleert bleibt leer"); assert.equal(live("w").docs, "https://learn.microsoft.com/w", "nie gesetztes Feld wird gefuellt");
    assert.equal(live("o").name, "Firma", "selbst verwaltet wird nicht abgeglichen");
    assert.equal(r.updated, 2);
    // Wettlauf: live wechselt zwischen Lesen und Schreiben -> nichts geschrieben
    const before = raw.prepare("SELECT COUNT(*) n FROM entity_rev").get().n;
    const st = raw.prepare("SELECT id FROM entity_rev WHERE eid='w' AND status='live'").get().id;
    raw.exec(`UPDATE entity_rev SET status='old' WHERE id=${st}`); ins("w", { type: "product", name: "W2" }, 9, "live", "neu");
    raw.prepare("UPDATE entity_rev SET status='old' WHERE id=? AND status='live'").run(st);
    raw.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) SELECT ?,?,?,0,'live',1 WHERE NOT EXISTS (SELECT 1 FROM entity_rev WHERE eid=? AND status='live')").run("w", "{}", "Abgleich mit entities.json: x", "w");
    assert.equal(raw.prepare("SELECT COUNT(*) n FROM entity_rev").get().n, before + 1, "bedingtes Schreiben greift nicht, wenn live gewechselt hat");
    assert.equal(live("w").name, "W2");
  } finally { globalThis.fetch = old; }
});

test("search: Import, Trigramm-Suche, Filter, Facetten und gone-Markierung (SQLite)", async () => {
  const { db, raw, indexWrites } = await searchDb();
  const docs = [
    { id: "en:/entity/aaron-siller/", url: "https://www.m365.fm/entity/aaron-siller/", lang: "en", type: "person", title: "Aaron Siller", summary: "Cloud expert", keywords: "Azure identity", entities: ["azure"], date: "2024-05-01", image: "" },
    { id: "de:/entity/purview/", url: "https://www.m365.fm/de/entity/purview/", lang: "de", type: "entity", title: "Microsoft Purview", summary: "Informationsschutz", keywords: "Azure Purview", entities: ["azure", "purview"], date: "2025-03-10", image: "" },
    { id: "ja:/azure/", url: "https://www.m365.fm/ja/azure/", lang: "ja", type: "page", title: "Azure 日本語の検索", summary: "クラウド検索", keywords: "Azure 日本語 検索", entities: ["azure"], date: "2026-01-20", image: "" },
  ];
  let generated = "2026-11-01", parts = [[docs[0], docs[1]], [docs[2]]];
  const oldFetch = globalThis.fetch;
  let handleSearch;
  globalThis.fetch = async (input) => {
    const path = new URL(input).pathname;
    if (path === "/search/manifest.json") return { ok: true, json: async () => ({ generated, parts: 2, count: parts.flat().length }) };
    const number = Number(/part-(\d+)\.json$/.exec(path)?.[1]);
    return { ok: true, json: async () => ({ part: number, docs: parts[number - 1] }) };
  };
  const env = { DB: db, SITE: "https://www.m365.fm" };
  const call = async (params, ip = "203.0.113.8") => {
    const request = new Request(`https://api.m365.fm/api/search?${params}`, { headers: { "cf-connecting-ip": ip } });
    return handleSearch(env, request, new URL(request.url), (data, status = 200, headers = {}) => ({ data, status, headers }));
  };
  try {
    const { importSearchIndex, handleSearch: search } = await import("../src/search.js");
    handleSearch = search;
    assert.equal((await importSearchIndex(env)).changed, 2);
    const imported = await importSearchIndex(env);
    assert.equal(imported.changed, 1);
    assert.equal(imported.gone, 0);

    const typo = await call("q=Aron+Soller");
    assert.equal(typo.status, 200);
    assert.equal(typo.data.results[0].title, "Aaron Siller");
    assert.equal((await call("q=purvew")).data.results[0].title, "Microsoft Purview");
    assert.equal((await call("q=" + encodeURIComponent("日本語の検索"))).data.results[0].lang, "ja");
    assert.equal((await call("q=Mi")).data.results[0].title, "Microsoft Purview", "kurze Suche nutzt Titel-Praefix");

    const all = await call("q=Azure");
    assert.equal(all.data.total, 3);
    assert.deepEqual(all.data.facets.type, { entity: 1, page: 1, person: 1 });
    assert.deepEqual(all.data.facets.lang, { de: 1, en: 1, ja: 1 });
    assert.deepEqual(all.data.facets.year, { 2024: 1, 2025: 1, 2026: 1 });
    assert.equal(all.data.facets.entity.azure, 3);
    assert.equal(all.data.facets.entity.purview, 1);
    assert.equal((await call("q=Azure&lang=de")).data.total, 1);
    const typeFiltered = await call("q=Azure&type=page");
    assert.equal(typeFiltered.data.total, 1);
    assert.equal(typeFiltered.data.facets.type.person, 1, "type-Facette ignoriert den eigenen Filter");
    assert.equal((await call("q=Azure&entity=purview")).data.results[0].title, "Microsoft Purview");
    assert.equal((await call("q=Azure&year=2025")).data.total, 1);

    const before = indexWrites();
    assert.equal((await importSearchIndex(env)).changed, 0);
    assert.equal((await importSearchIndex(env)).changed, 0);
    assert.equal(indexWrites(), before, "unveraenderte Dokumente werden nicht erneut geschrieben");

    generated = "2026-11-02";
    parts = [[{ ...docs[0], title: "Aaron Siller Updated" }, docs[1]], []];
    assert.equal((await importSearchIndex(env)).changed, 1);
    assert.equal(raw.prepare("SELECT title FROM search_doc WHERE id=?").get(docs[0].id).title, "Aaron Siller Updated");
    const final = await importSearchIndex(env);
    assert.equal(final.gone, 1);
    assert.equal(raw.prepare("SELECT gone FROM search_doc WHERE id=?").get(docs[2].id).gone, 1);
    assert.equal((await call("q=Azure")).data.total, 2, "gone-Dokumente erscheinen nicht in der Suche");

    const limitedIp = "198.51.100.27";
    let response;
    for (let i = 0; i < 61; i++) response = await call("q=Azure", limitedIp);
    assert.equal(response.status, 429);
    assert.equal(raw.prepare("SELECT COUNT(*) n FROM ratelimit WHERE k LIKE ?").get(`%${limitedIp}%`).n, 0, "IP-Adresse wird nicht gespeichert");
  } finally {
    globalThis.fetch = oldFetch;
  }
});

test("search: unicode61-Fallback findet Titel per LIKE (SQLite)", async () => {
  const { db, raw } = await searchDb(true);
  const doc = { id: "en:/purview/", url: "https://www.m365.fm/purview/", lang: "en", type: "entity", title: "Microsoft Purview", summary: "", keywords: "", entities: [], date: "", image: "" };
  const oldFetch = globalThis.fetch;
  globalThis.fetch = async (input) => {
    const path = new URL(input).pathname;
    if (path === "/search/manifest.json") return { ok: true, json: async () => ({ generated: "2026-11-01", parts: 1, count: 1 }) };
    return { ok: true, json: async () => ({ part: 1, docs: [doc] }) };
  };
  try {
    const { importSearchIndex, handleSearch } = await import("../src/search.js");
    const env = { DB: db, SITE: "https://www.m365.fm" };
    assert.equal((await importSearchIndex(env)).tokenizer, "unicode61");
    const request = new Request("https://api.m365.fm/api/search?q=purview", { headers: { "cf-connecting-ip": "203.0.113.9" } });
    const response = await handleSearch(env, request, new URL(request.url), (data, status = 200) => ({ data, status }));
    assert.equal(response.status, 200);
    assert.equal(response.data.results[0].title, "Microsoft Purview");
    assert.equal(raw.prepare("SELECT v FROM meta WHERE k='search_fts_tokenizer'").get().v, "unicode61");
  } finally {
    globalThis.fetch = oldFetch;
  }
});

test("search: Tippfehler-Ranking, Sprach-Deduplizierung und Titelprioritaet (SQLite)", async () => {
  const { db, raw } = await searchDb();
  const docs = [
    { id: "en:aaron", url: "https://www.m365.fm/entity/aaron-siller/", lang: "en", type: "person", title: "Aaron Siller – Person", keywords: "Microsoft Azure" },
    { id: "de:aaron", url: "https://www.m365.fm/de/entity/aaron-siller/", lang: "de", type: "person", title: "Aaron Siller – Person", keywords: "Microsoft Azure" },
    { id: "en:patrick", url: "https://www.m365.fm/entity/patrick-gruenauer/", lang: "en", type: "person", title: "Patrick Gruenauer – Person" },
    { id: "en:purview", url: "https://www.m365.fm/entity/microsoft-purview/", lang: "en", type: "entity", title: "Microsoft Purview – Produkt", entities: ["purview"] },
    { id: "en:avd", url: "https://www.m365.fm/entity/azure-virtual-desktop/", lang: "en", type: "entity", title: "Azure Virtual Desktop – Product", entities: ["azure-virtual-desktop"] },
  ];
  for (let i = 0; i < 25; i++) docs.push({
    id: `en:blog-${i}`, url: `https://www.m365.fm/blog/blog-${i}/`, lang: "en", type: "blog",
    title: `Azure sollten Entwickler surveillance ${i}`, summary: "Microsoft developers should consider surveillance and privacy",
  });
  seedSearchDocs(raw, docs);
  const { handleSearch } = await import("../src/search.js");
  const env = { DB: db, SITE: "https://www.m365.fm" };
  const call = async (q, extra = "") => {
    const request = new Request(`https://api.m365.fm/api/search?q=${encodeURIComponent(q)}${extra}`, { headers: { "cf-connecting-ip": `${q}:${extra}` } });
    return handleSearch(env, request, new URL(request.url), (data) => data);
  };
  const aron = await call("Aron Soller");
  assert.equal(aron.results[0].title, "Aaron Siller – Person");
  assert.equal(aron.results.filter((row) => row.title === "Aaron Siller – Person").length, 1, "de/en werden zusammengefuehrt");
  const aronDe = await call("Aron Soller", "&pref=de");
  assert.equal(aronDe.results[0].lang, "de", "bevorzugte Sprachfassung bleibt");
  const patrick = await call("Patrik Grünauer");
  assert.equal(patrick.results[0].title, "Patrick Gruenauer – Person");
  const purview = await call("purvew");
  assert.ok(purview.results.slice(0, 3).some((row) => row.title.startsWith("Microsoft Purview")));
  const avd = await call("Azure Virtual Desktop");
  assert.equal(avd.results[0].title, "Azure Virtual Desktop – Product");
});

test("search: 40.000 Dokumente mit einer Kandidatenabfrage unter 200 ms (SQLite)", async () => {
  const { db, raw, searchQueries } = await searchDb();
  const docs = Array.from({ length: 40000 }, (_, i) => ({
    id: `en:synthetic-${i}`, url: `https://www.m365.fm/page/${i}/`, lang: "en", type: i % 8 ? "page" : "entity",
    title: `Common search document ${i}`, summary: "Common content for performance testing", keywords: "Common search",
  }));
  seedSearchDocs(raw, docs);
  const { handleSearch } = await import("../src/search.js");
  const env = { DB: db, SITE: "https://www.m365.fm" };
  const request = new Request("https://api.m365.fm/api/search?q=common", { headers: { "cf-connecting-ip": "load-test-ip" } });
  const started = performance.now();
  const result = await handleSearch(env, request, new URL(request.url), (data) => data);
  const elapsed = performance.now() - started;
  assert.ok(elapsed < 200, `Suche dauerte ${elapsed.toFixed(1)} ms`);
  assert.equal(result.results.length, 20);
  assert.ok(result.total <= 1000, "Kandidatenpool ist begrenzt");
  assert.equal(searchQueries(), 1, "pro Suchanfrage wird eine Kandidatenabfrage ausgefuehrt");
});
