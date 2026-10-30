#!/usr/bin/env python3
"""Spreaker-OAuth ohne PC: Token wird mit dem Client-Secret verschluesselt in data/spreaker_auth.enc abgelegt (Repo ist oeffentlich,
die Datei ohne das Secret unbrauchbar). Befehle: connect <code> (einmalig, tauscht den Code), refresh (erneuert bei Bedarf)."""
import base64, hashlib, json, os, sys, time
from pathlib import Path
import requests
from cryptography.fernet import Fernet

ROOT = Path(__file__).parent
FILE = ROOT / "data" / "spreaker_auth.enc"
TOKEN_URL = "https://api.spreaker.com/oauth2/token"
REDIRECT = "https://dub.m365.fm/callback"


def _key():
    sec = os.environ.get("SPREAKER_CLIENT_SECRET", "").strip()
    if not sec:
        fail("SPREAKER_CLIENT_SECRET fehlt")
    return base64.urlsafe_b64encode(hashlib.sha256(("m365dub|" + sec).encode()).digest())


def load():
    if not FILE.exists():
        return None
    try:
        return json.loads(Fernet(_key()).decrypt(FILE.read_bytes()))
    except Exception:
        return None


def save(d):
    FILE.parent.mkdir(exist_ok=True)
    FILE.write_bytes(Fernet(_key()).encrypt(json.dumps(d).encode()))


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def exchange(data):
    cid, sec = os.environ.get("SPREAKER_CLIENT_ID", "").strip(), os.environ.get("SPREAKER_CLIENT_SECRET", "").strip()
    if not cid or not sec:
        fail("Secret SPREAKER_CLIENT_ID oder SPREAKER_CLIENT_SECRET fehlt/leer im Repo (Settings > Secrets > Actions).")
    r = requests.post(TOKEN_URL, data={**data, "client_id": cid, "client_secret": sec}, timeout=60)
    if r.status_code != 200:
        fail(f"Spreaker-Token-Fehler {r.status_code}: {r.text[:300]} (Code abgelaufen/schon benutzt? Neu anmelden und sofort einfuegen; Callback-URL muss {REDIRECT} sein.)")
    return r.json()


def connect(code):
    code = code.strip()
    if "code=" in code:
        code = code.split("code=")[1].split("&")[0]
    j = exchange({"grant_type": "authorization_code", "redirect_uri": REDIRECT, "code": code})
    save({"access_token": j["access_token"], "refresh_token": j.get("refresh_token", ""), "at": int(time.time())})
    print("Spreaker verbunden, Token verschluesselt gespeichert.")


def refresh():
    d = load()
    if not d or not d.get("refresh_token"):
        fail("Kein Refresh-Token vorhanden – Workflow 'Spreaker verbinden' neu ausfuehren.")
    j = exchange({"grant_type": "refresh_token", "refresh_token": d["refresh_token"]})
    d["access_token"] = j["access_token"]
    if j.get("refresh_token"):
        d["refresh_token"] = j["refresh_token"]
    d["at"] = int(time.time())
    save(d)
    return d["access_token"]


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "connect":
        connect(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "refresh":
        refresh()
    elif len(sys.argv) > 1 and sys.argv[1] == "env":   # erneuert und legt den Token maskiert als SPREAKER_TOKEN in $GITHUB_ENV (fuer den Worker-Deploy)
        tok = refresh()
        print(f"::add-mask::{tok}")
        with open(os.environ["GITHUB_ENV"], "a") as f:
            f.write(f"SPREAKER_TOKEN={tok}\n")
        print("Spreaker-Token erneuert.")
