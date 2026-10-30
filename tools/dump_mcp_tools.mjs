import { TOOLS } from "../worker/src/mcp.js";
console.log(JSON.stringify(TOOLS.map(t => ({ name: t.name, write: !!t.write, en: t.description, de: t.de || t.description }))));
