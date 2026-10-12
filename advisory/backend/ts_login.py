"""Get a TradeSmart API access token (Noren v2 OAuth flow).

Needs env vars TS_APP_KEY, TS_SECRET_KEY, TS_CLIENT_ID (from TradeSmart's API app creation page).
  1. Run this script; it prints the login URL. Open it, log in to TradeSmart.
  2. You are redirected to your registered Redirect URL with ?code=... in the address bar. Paste that code.
  3. It prints the access token. Set TS_ACCESS_TOKEN to it before starting the backend.
"""
import hashlib
import json
import os
import urllib.parse
import urllib.request

BASE = "https://v2api.tradesmartonline.in/NorenWClientAPIv2"
app_key, secret, client_id = (os.environ[k] for k in ("TS_APP_KEY", "TS_SECRET_KEY", "TS_CLIENT_ID"))

print("Open and log in:\nhttps://v2api.tradesmartonline.in/OAuthlogin/authorize/oauth?client_id="
      + urllib.parse.quote(app_key))
code = input("\nPaste the code from the redirect URL: ").strip()

checksum = hashlib.sha256((app_key + secret + code).encode()).hexdigest()
body = ("jData=" + json.dumps({"code": code, "checksum": checksum})).encode()
with urllib.request.urlopen(urllib.request.Request(f"{BASE}/GenAcsTok", data=body), timeout=15) as r:
    data = json.load(r)
if data.get("stat") == "Not_Ok":
    raise SystemExit(f"GenAcsTok failed: {data.get('emsg')}")
print("\nAccess token (keep it secret):\n" + data["access_token"])
