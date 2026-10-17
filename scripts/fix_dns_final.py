#!/usr/bin/env python3
"""
fix_dns_final.py — Supprime OVH4 du DNS artcb.me, garde OVH2 uniquement.
Tous les secrets lus depuis Doppler — aucun secret hardcodé.
"""
import ovh
import subprocess

TOKEN_FILE = "/tmp/doppler-artcb-4.token"
OVH4_IP = "91.134.45.8"
ZONE = "artcb.me"


def dg(k):
    t = open(TOKEN_FILE).read().strip()
    return subprocess.check_output(
        ["doppler", "secrets", "get", k,
         "--project", "artcb-4", "--config", "dev",
         "--token", t, "--plain"],
        stderr=subprocess.DEVNULL
    ).decode().strip()


client = ovh.Client(
    endpoint="ovh-eu",
    application_key=dg("OVH_APPLICATION_KEY"),
    application_secret=dg("OVH_APPLICATION_SECRET"),
    consumer_key=dg("OVH_CONSUMER_KEY"),
)

me = client.get("/me")
print("Connecté:", me["nichandle"])

# Lister tous les A records
records = client.get(f"/domain/zone/{ZONE}/record", fieldType="A")
print("A records IDs:", records)

for rid in records:
    rec = client.get(f"/domain/zone/{ZONE}/record/{rid}")
    sub = rec.get("subDomain", "")
    tgt = rec.get("target", "")
    print(f"  id={rid} sub='{sub}' target={tgt}")
    if tgt == OVH4_IP and sub == "":
        print(f"  -> SUPPRESSION {OVH4_IP} (OVH4) ...")
        client.delete(f"/domain/zone/{ZONE}/record/{rid}")
        print(f"  -> SUPPRIME OK")

client.post(f"/domain/zone/{ZONE}/refresh")
print("Zone DNS rafraichie")

# Verification finale
remaining = client.get(f"/domain/zone/{ZONE}/record", fieldType="A")
print("A records restants apres correction:")
for rid in remaining:
    rec = client.get(f"/domain/zone/{ZONE}/record/{rid}")
    print(f"  id={rid} sub='{rec.get('subDomain','')}' target={rec.get('target')}")
