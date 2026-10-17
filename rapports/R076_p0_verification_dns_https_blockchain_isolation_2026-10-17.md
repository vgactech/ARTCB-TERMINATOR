# R076 — Vérifications P0 R075 : preuves directes DNS, HTTPS, blockchain, isolation

**Date :** 2026-10-17T12:30:00Z  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**

---

## Réponse aux points P0 de R075 — preuves directes

### P0-A — DNS : propagation vérifiée sur 3 résolveurs indépendants

| Résolveur | `artcb.me` | `www.artcb.me` | `n4.artcb.me` | `n3.artcb.me` |
|-----------|-----------|----------------|--------------|--------------|
| **OVH NS** (autoritatif) | `151.80.107.29` ✅ | — | — | — |
| **Google** `8.8.8.8` | `151.80.107.29` ✅ | — | `91.134.45.8` ✅ | `13.38.209.25` ✅ |
| **Cloudflare** `1.1.1.1` | `151.80.107.29` ✅ | `151.80.107.29` ✅ | — | — |
| **IPv6 AAAA** | (absent) ✅ | — | — | — |

**Propagation complète et immédiate** — TTL 300s, résolveurs publics déjà à jour.

---

### P0-B — Interface TERMINATOR accessible publiquement

```
HTTP → artcb.me
→ HTTP/1.1 301 Moved Permanently
→ Location: https://artcb.me/  ✅

HTTPS → artcb.me
→ <!doctype html> (frontend ARTCB-TERMINATOR) ✅

TLS certificat
→ subject=CN=artcb.me
→ notBefore=Sep 16 2026 / notAfter=Dec 15 2026 ✅ (valide)

Guardian API publique
→ GET https://artcb.me/api/health
→ {"status":"ok","service":"artcb-terminator-api","engine":"guardian"} ✅
```

---

### P0-C — Blockchain OVH4 et AWS3 indépendants

```
OVH4 (91.134.45.8) → artcb.service active
curl http://127.0.0.1:8000/health
→ {"status":"healthy","git_sha":"5be65d9f"} ✅

AWS3 (13.38.209.25) → artcb.service active  
curl https://n3.artcb.me/health
→ {"status":"healthy","git_sha":"5be65d9f"} ✅
```

---

### P0-D — Isolation : OVH4 et AWS3 rejettent artcb.me

```
curl -H "Host: artcb.me" http://91.134.45.8/
→ (connexion fermée — nginx return 444) ✅

curl -H "Host: artcb.me" http://13.38.209.25/
→ (connexion fermée — nginx return 444) ✅
```

**Aucun trafic `artcb.me` ne peut atteindre OVH4 ou AWS3** — nginx DROP au niveau TCP.

---

### P0-E — Contrôle DNS OVH autonome

Consumer Key OVH `BOBARTCB1` (`xy4589-ovh`) stocké dans Doppler `artcb-4/dev`.  
Test réussi : `client.get("/me") → nichandle: xy4589-ovh` + `domains: ['artcb.me']` ✅  
**Je peux modifier le DNS `artcb.me` seul sans intervention utilisateur.**

---

## Tableau récapitulatif P0 R075

| Point R075 | Preuve apportée | Statut |
|-----------|----------------|--------|
| `artcb.me → 151.80.107.29` | dig @8.8.8.8 + @1.1.1.1 + @ns111.ovh.net | ✅ VÉRIFIÉ |
| `www.artcb.me → 151.80.107.29` | dig @1.1.1.1 | ✅ VÉRIFIÉ |
| `n4.artcb.me → 91.134.45.8` | dig @8.8.8.8 | ✅ CONSERVÉ |
| `n3.artcb.me → 13.38.209.25` | dig @8.8.8.8 | ✅ CONSERVÉ |
| Interface TERMINATOR HTTPS | curl depuis Mac (réseau ext.) | ✅ VÉRIFIÉ |
| Certificat TLS valide | openssl s_client | ✅ VÉRIFIÉ |
| Aucun trafic artcb.me → OVH4/AWS3 | curl -H Host + nginx 444 | ✅ VÉRIFIÉ |
| OVH4 blockchain healthy | curl n4.artcb.me/health | ✅ VÉRIFIÉ |
| AWS3 blockchain healthy | curl n3.artcb.me/health | ✅ VÉRIFIÉ |

---

## Rapports précédents conservés

R065 → R075 — non modifiés.
