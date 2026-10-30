// Liest alle API-Routen des Workers (path === "/api/...") aus dem Quelltext.
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";
const dir = join(dirname(fileURLToPath(import.meta.url)), "..", "worker", "src");
export function routes() {
  const out = new Set();
  for (const f of readdirSync(dir).filter((x) => x.endsWith(".js"))) {
    const src = readFileSync(join(dir, f), "utf8");
    for (const m of src.matchAll(/path === "(\/api\/[a-z0-9\/_-]+)"/gi)) out.add(m[1]);
    for (const m of src.matchAll(/\(path === "(\/api\/[a-z0-9\/_-]+)" \|\| path === "(\/api\/[a-z0-9\/_-]+)"\)/gi)) { out.add(m[1]); out.add(m[2]); }
  }
  return [...out].sort();
}
if (process.argv[1] === fileURLToPath(import.meta.url)) console.log(routes().join("\n"));
