#!/usr/bin/env python3
"""YouTube-OAuth fuer den Worker (Kanal m365 Show): Refresh-Token wird mit dem Client-Secret verschluesselt in data/yt_auth.enc abgelegt.
connect <code>: tauscht den Code (einmalig). env: legt YT_REFRESH_TOKEN maskiert in $GITHUB_ENV (fuer den Worker-Deploy)."""
import base64, hashlib, json, os, sys
from pathlib import Path
import requests
from cryptography.fernet import Fernet

FILE = Path(__file__).parent / "data" / "yt_auth.enc"
REDIRECT = "https://dub.m365.fm/callback"


def fail(m):
    print(f"::error::{m}"); sys.exit(1)


def key():
    s = os.environ.get("YT_CLIENT_SECRET", "").strip()
    if not s: fail("Secret YT_CLIENT_SECRET fehlt")
    return base64.urlsafe_b64encode(hashlib.sha256(("m365yt|" + s).encode()).digest())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "connect" and len(sys.argv) > 2:
        code = sys.argv[2].strip()
        if "code=" in code: code = code.split("code=")[1].split("&")[0]
        cid = os.environ.get("YT_CLIENT_ID", "").strip()
        if not cid: fail("Secret YT_CLIENT_ID fehlt")
        r = requests.post("https://oauth2.googleapis.com/token", data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT, "client_id": cid, "client_secret": os.environ["YT_CLIENT_SECRET"].strip()}, timeout=60)
        if r.status_code != 200: fail(f"Google-Fehler {r.status_code}: {r.text[:300]} (Code abgelaufen/benutzt? Neu anmelden.)")
        rt = r.json().get("refresh_token")
        if not rt: fail("Kein Refresh-Token erhalten – Zugriff in myaccount.google.com/permissions entziehen und mit prompt=consent neu anmelden.")
        FILE.parent.mkdir(exist_ok=True); FILE.write_bytes(Fernet(key()).encrypt(json.dumps({"refresh_token": rt}).encode()))
        print("YouTube verbunden, Refresh-Token verschluesselt gespeichert.")
    elif cmd == "env":
        if not FILE.exists(): fail("data/yt_auth.enc fehlt – Workflow 'YouTube verbinden' ausfuehren.")
        rt = json.loads(Fernet(key()).decrypt(FILE.read_bytes()))["refresh_token"]
        print(f"::add-mask::{rt}")
        open(os.environ["GITHUB_ENV"], "a").write(f"YT_REFRESH_TOKEN={rt}\n"); print("YouTube-Token bereit.")
