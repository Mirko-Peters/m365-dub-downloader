// Web Push (RFC 8030 + VAPID RFC 8292 + Verschluesselung aes128gcm RFC 8188/8291) mit WebCrypto
import { b64u } from "./util.js";
const te = new TextEncoder();

async function hkdf(salt, ikm, info, len) {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, key, len * 8));
}
const cat = (...a) => { const n = a.reduce((s, x) => s + x.length, 0); const o = new Uint8Array(n); let p = 0; for (const x of a) { o.set(x, p); p += x.length; } return o; };

// Verschluesselt payload (String) fuer eine Subscription {p256dh, auth} (base64url)
export async function encryptPayload(payload, p256dh, auth) {
  const uaPub = b64u.dec(p256dh), authSecret = b64u.dec(auth);
  const eph = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const asPub = new Uint8Array(await crypto.subtle.exportKey("raw", eph.publicKey));
  const uaKey = await crypto.subtle.importKey("raw", uaPub, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({ name: "ECDH", public: uaKey }, eph.privateKey, 256));
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const prk = await hkdf(authSecret, shared, cat(te.encode("WebPush: info\0"), uaPub, asPub), 32);
  const cek = await hkdf(salt, prk, te.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, prk, te.encode("Content-Encoding: nonce\0"), 12);
  const plain = cat(te.encode(payload), new Uint8Array([2]));   // 0x02 = letzter Datensatz
  const aes = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce }, aes, plain));
  const rs = new Uint8Array([0, 0, 0x10, 0]);                   // Record size 4096
  return cat(salt, rs, new Uint8Array([asPub.length]), asPub, ct);
}

async function vapidJwt(env, endpoint) {
  const aud = new URL(endpoint).origin;
  const head = b64u.enc(te.encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const claims = b64u.enc(te.encode(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: env.VAPID_SUBJECT })));
  const jwk = JSON.parse(env.VAPID_PRIVATE_JWK);
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, te.encode(`${head}.${claims}`)));
  return `${head}.${claims}.${b64u.enc(sig)}`;
}

// Rueckgabe: {ok, gone}  gone=true -> Abo loeschen (404/410)
export async function sendPush(env, sub, payloadObj) {
  const body = await encryptPayload(JSON.stringify(payloadObj), sub.p256dh, sub.auth);
  const jwt = await vapidJwt(env, sub.endpoint);
  const r = await fetch(sub.endpoint, {
    method: "POST",
    headers: { "content-encoding": "aes128gcm", "content-type": "application/octet-stream", ttl: "86400", urgency: "normal",
      authorization: `vapid t=${jwt}, k=${env.VAPID_PUBLIC}` },
    body,
  });
  return { ok: r.status >= 200 && r.status < 300, gone: r.status === 404 || r.status === 410, status: r.status };
}
