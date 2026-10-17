# R073 — Isolation complète : OVH2=TERMINATOR, OVH4+AWS3=blockchain, indépendants

**Date :** 2026-10-17T11:00:00Z  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**

---

## Décision architecturale actée

| Nœud | IP | Rôle définitif | DNS |
|------|----|---------------|-----|
| **OVH2** | `151.80.107.29` | ARTCB-TERMINATOR frontend + Guardian | `artcb.me` → OVH2 uniquement |
| **OVH4** | `91.134.45.8` | Nœud blockchain ARTCB | `n4.artcb.me` uniquement |
| **AWS3** | `13.38.209.25` | Nœud blockchain ARTCB | `n3.artcb.me` uniquement |
| **Mac** | local | Tests locaux uniquement | aucun rôle production |

---

## 1. OVH4 — nginx reconfiguré : artcb.me retiré

### AVANT
```nginx
server_name artcb.me www.artcb.me n1.artcb.me n2.artcb.me n3.artcb.me n4.artcb.me ...;
# proxyfie vers :8000 pour TOUS les domaines
```

### APRÈS `/etc/nginx/conf.d/artcb-me-http.conf`
```nginx
server { listen 80; server_name n4.artcb.me; return 301 https://n4.artcb.me$request_uri; }
server { listen 80 default_server; server_name _; return 444; }  # rejette artcb.me
server { listen 443 ssl; server_name n4.artcb.me; proxy_pass :8000; }
server { listen 443 ssl default_server; server_name _; return 444; }  # rejette artcb.me
```
Fichier `00-artcb-tls-wildcard.conf` supprimé.

---

## 2. AWS3 — nginx reconfiguré : artcb.me retiré

### AVANT → APRÈS
Même transformation que OVH4, `server_name n3.artcb.me` uniquement.  
`00-artcb-tls-wildcard.conf` supprimé.

---

## 3. Isolation bootstrap blockchain

**Problème identifié :** `src/artcb/config.py` contient `"http://151.80.107.29:8000"` en dur dans `BOOTSTRAP_NODES`.

**Solution appliquée :** OVH2 ne répond plus sur `:8000` (`artcb.service` désactivé).  
Test depuis OVH4 :
```
curl http://151.80.107.29:8000/health → exit=7 (Connection refused)
```
Les nœuds OVH4 et AWS3 tentent OVH2 au bootstrap, échouent silencieusement, et l'éliminent de leurs peers actifs. **Isolation naturelle sans modifier le code.**

**À faire lors d'une prochaine session :** retirer `151.80.107.29:8000` de `BOOTSTRAP_NODES` dans `config.py` via un commit sur `main` et redéployer sur OVH4/AWS3.

---

## 4. DNS artcb.me — action manuelle requise

Le Consumer Key OVH API est **expiré** (`401 Unauthorized`).  
L'enregistrement DNS `artcb.me → 91.134.45.8` (OVH4) doit être **supprimé manuellement**.

**Action utilisateur :**
1. **https://www.ovh.com/manager/#/web/domain/artcb.me/zone**
2. Supprimer le A record `artcb.me → 91.134.45.8`
3. Garder uniquement `artcb.me → 151.80.107.29` (OVH2)
4. Régénérer Consumer Key OVH sur **https://eu.api.ovh.com/createApp/** → stocker dans Doppler `artcb-blockchain/dev` sous `OVH_CONSUMER_KEY`

---

## 5. Vérifications live — preuves directes

```
OVH2 artcb.service  → failed / disabled  ✅ (TERMINATOR uniquement)
OVH2 artcb-guardian → active             ✅ {"status":"ok","engine":"guardian"}
OVH4 artcb.service  → active             ✅ {"status":"healthy","git_sha":"5be65d9f"}
AWS3 artcb.service  → active             ✅ {"status":"healthy","git_sha":"5be65d9f"}
OVH2:8000 depuis OVH4 → Connection refused (exit=7) ✅ isolé
```

---

## 6. Ce qui fonctionne de manière indépendante

```
OVH2 (TERMINATOR)
  nginx :80  → 301 HTTPS
  nginx :443 → /var/www/terminator/index.html + /api/ → Guardian :8002
  artcb-guardian :8002 → Guardian API + ElevenLabs voice ✅
  artcb.service → DÉSACTIVÉ ✅

OVH4 (blockchain)
  nginx :443 → n4.artcb.me → :8000 blockchain ✅
  artcb.me → 444 (rejeté) ✅

AWS3 (blockchain)
  nginx :443 → n3.artcb.me → :8000 blockchain ✅
  artcb.me → 444 (rejeté) ✅
```

---

## Rapports précédents conservés intégralement
R065 → R072 — non modifiés.
