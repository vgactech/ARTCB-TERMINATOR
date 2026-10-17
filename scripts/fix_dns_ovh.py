#!/usr/bin/env python3
"""
fix_dns_ovh.py — Corrige les enregistrements DNS artcb.me via API OVH
Actions :
  1. Lister les A records de artcb.me (racine)
  2. Supprimer le record pointant vers OVH4 (91.134.45.8)
  3. Créer CNAME terminator.artcb.me → OVH2 (151.80.107.29)
  4. Rafraîchir la zone DNS
Exécuter depuis OVH2 avec doppler-artcb-blockchain.token présent.
"""
import hmac, hashlib, time, requests, subprocess, json, sys

TOKEN_FILE = "/home/ubuntu/.doppler-artcb-blockchain.token"
OVH2_IP    = "151.80.107.29"
OVH4_IP    = "91.134.45.8"
ZONE       = "artcb.me"
BASE       = "https://eu.api.ovh.com/1.0"

def dget(k):
    t = open(TOKEN_FILE).read().strip()
    return subprocess.check_output(
        ["doppler","secrets","get",k,
         "--project","artcb-blockchain","--config","dev",
         "--token",t,"--plain"],
        stderr=subprocess.DEVNULL).decode().strip()

APP_KEY    = dget("OVH_APPLICATION_KEY")
APP_SECRET = dget("OVH_APPLICATION_SECRET")
CONSUMER   = dget("OVH_CONSUMER_KEY")

def _sig(method, full_url, body, ts):
    pre = "+".join([APP_SECRET, CONSUMER, method, full_url, body, ts])
    h = hmac.new(APP_SECRET.encode(), pre.encode(), hashlib.sha1).hexdigest()
    return "$1$" + h

def hdrs(method, full_url, body=""):
    ts = str(int(time.time()))
    return {
        "X-Ovh-Application": APP_KEY,
        "X-Ovh-Consumer":    CONSUMER,
        "X-Ovh-Timestamp":   ts,
        "X-Ovh-Signature":   _sig(method, full_url, body, ts),
        "Content-Type":      "application/json",
    }

def get(path):
    url = BASE + path
    r = requests.get(url, headers=hdrs("GET", url))
    r.raise_for_status()
    return r.json()

def post(path, data):
    url = BASE + path
    body = json.dumps(data)
    r = requests.post(url, headers=hdrs("POST", url, body), data=body)
    r.raise_for_status()
    return r.json()

def delete(path):
    url = BASE + path
    r = requests.delete(url, headers=hdrs("DELETE", url))
    r.raise_for_status()
    return r.status_code

# --- 1. Lister A records racine ---
print("[1] Listing A records for artcb.me ...")
ids = get(f"/domain/zone/{ZONE}/record?fieldType=A")
print(f"    Found {len(ids)} root A record(s): {ids}")

for rid in ids:
    rec = get(f"/domain/zone/{ZONE}/record/{rid}")
    target = rec.get("target","")
    sub    = rec.get("subDomain","")
    print(f"    id={rid} subDomain='{sub}' target={target}")

    # --- 2. Supprimer OVH4 du DNS racine ---
    if target == OVH4_IP and sub == "":
        print(f"[2] Deleting record {rid} → {OVH4_IP} (OVH4, not TERMINATOR) ...")
        sc = delete(f"/domain/zone/{ZONE}/record/{rid}")
        print(f"    Deleted — HTTP {sc}")
    else:
        print(f"    Keeping record {rid} → {target}")

# --- 3. Créer A record terminator.artcb.me → OVH2 ---
print(f"[3] Creating A record: terminator.{ZONE} → {OVH2_IP} ...")
# Vérifier s'il existe déjà
existing = get(f"/domain/zone/{ZONE}/record?fieldType=A&subDomain=terminator")
if existing:
    print(f"    Already exists: {existing} — skipping")
else:
    result = post(f"/domain/zone/{ZONE}/record", {
        "fieldType": "A",
        "subDomain": "terminator",
        "target":    OVH2_IP,
        "ttl":       300,
    })
    print(f"    Created: id={result.get('id')} → {OVH2_IP}")

# --- 4. Rafraîchir la zone ---
print("[4] Refreshing DNS zone ...")
r = requests.post(
    BASE + f"/domain/zone/{ZONE}/refresh",
    headers=hdrs("POST", f"/domain/zone/{ZONE}/refresh", ""))
print(f"    Refresh HTTP {r.status_code}")

print("\n[DONE] DNS changes applied.")
print(f"  artcb.me         → {OVH2_IP} only (OVH4 removed)")
print(f"  terminator.artcb.me → {OVH2_IP} (new)")
