// Einrichtung/Deploy des Community-Workers (laeuft im GitHub-Workflow). Erzeugt fehlende Schluessel selbst, schreibt nie Secrets ins Log.
import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { webcrypto as crypto } from "node:crypto";

const run = (args, input) => { const r = spawnSync("npx", ["wrangler", ...args], { input, encoding: "utf8" }); return r; };
const fail = (m) => { console.error("::error::" + String(m).replace(/\r?\n/g, " | ").slice(0, 900)); process.exit(1); };
const b64u = (b) => Buffer.from(b).toString("base64url");

// 1) D1-Datenbank finden oder anlegen, ID in wrangler.toml eintragen
let list = run(["d1", "list", "--json"]);
let dbs = []; try { dbs = JSON.parse(list.stdout); } catch { fail("d1 list: " + (list.stderr || list.stdout)); }
let db = dbs.find((d) => d.name === "m365-dub");
if (!db) { const c = run(["d1", "create", "m365-dub"]); console.log(c.stdout.split("\n").slice(0, 3).join("\n")); dbs = JSON.parse(run(["d1", "list", "--json"]).stdout); db = dbs.find((d) => d.name === "m365-dub"); }
if (!db) { fail("D1 konnte nicht angelegt werden"); }
const id = db.uuid || db.id;
let toml = readFileSync("wrangler.toml", "utf8").replace(/database_id = "[^"]*"/, `database_id = "${id}"`);
writeFileSync("wrangler.toml", toml);
console.log("D1:", db.name);

// 2) Schema anwenden (idempotent)
const sch = run(["d1", "execute", "m365-dub", "--remote", "--file=schema.sql"]);
if (sch.status !== 0) fail("Schema: " + sch.stderr);
console.log("Schema ok");

// 3) Erstmal deployen (damit Secrets einen Worker haben), dann Secrets
const dep = run(["deploy"]);
console.log(dep.stdout.split("\n").slice(-6).join("\n")); if (dep.status !== 0) fail("Deploy: " + dep.stderr);

let have = [];
try { have = JSON.parse(run(["secret", "list", "--format", "json"]).stdout).map((s) => s.name); } catch {}
const put = (k, v) => { const r = run(["secret", "put", k], v); console.log(k, r.status === 0 ? "gesetzt" : "FEHLER " + r.stderr.slice(0, 200)); };

const gen = {
  SESSION_SECRET: () => b64u(crypto.getRandomValues(new Uint8Array(32))),
  CRON_KEY: () => b64u(crypto.getRandomValues(new Uint8Array(24))),
};
for (const [k, f] of Object.entries(gen)) if (!have.includes(k)) put(k, f());

if (!have.includes("VAPID_PRIVATE_JWK") || !have.includes("VAPID_PUBLIC")) {
  const kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign"]);
  const jwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  const pub = b64u(await crypto.subtle.exportKey("raw", kp.publicKey));
  put("VAPID_PRIVATE_JWK", JSON.stringify(jwk)); put("VAPID_PUBLIC", pub);
}
// Vom Betreiber gelieferte Secrets (GitHub-Secrets -> Umgebung); nur setzen, wenn vorhanden
for (const k of ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "MS_CLIENT_ID", "MS_CLIENT_SECRET", "RESEND_API_KEY", "ADMIN_SUBS"]) if (process.env[k]) put(k, process.env[k]);
console.log("Fertig. Worker: https://api.dub.m365.fm");
