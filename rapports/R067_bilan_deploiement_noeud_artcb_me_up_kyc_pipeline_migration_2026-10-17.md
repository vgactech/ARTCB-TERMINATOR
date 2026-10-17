# R067 — Bilan déploiement : artcb.me UP, pipeline KYC migré, état nœuds

**Date :** 2026-10-17T03:50:36Z  
**Session :** reprise après interruption R066  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**  

---

## 1. Objectifs de cette session

| # | Objectif | Statut |
|---|----------|--------|
| 1 | Arrêter Guardian TERMINATOR `:8001` sur OVH2 | ✅ |
| 2 | Redémarrer `artcb.service` OVH2 (OOM) | ✅ |
| 3 | Redémarrer `artcb.service` OVH4 (OOM) | ✅ |
| 4 | Vérifier `https://artcb.me/health` UP | ✅ |
| 5 | Vérifier AWS3 healthy | ✅ |
| 6 | Fermer PR#1 stale `artcb_TERMINATOR_FRONTEND` | ⚠️ BLOQUÉ — token sans permission |
| 7 | Confirmer `kyc_pipeline.py` migration complète | ✅ |
| 8 | Confirmer frontend index.html Guardian SSE `:8002` | ✅ |

---

## 2. Diagnostic OOM — cause identifiée

### AVANT (état constaté à l'arrivée en session)

| Nœud | RAM utilisée | RAM totale | artcb.service | Réponse `:8000` |
|------|-------------|-----------|---------------|----------------|
| OVH2 | **6.7 Go** | 7.7 Go | active (running) | `503 Service Unavailable` |
| OVH4 | **7.3 Go** | 7.7 Go | active (running) | `503 Service Unavailable` |
| AWS3 | 1.1 Go | 1.9 Go | active (running) | `200 healthy` ✅ |

**Cause OOM :** Uvicorn a saturé la mémoire après plusieurs heures de BFT P2P + watchdog consensus.  
`Exceeded concurrency limit` → toutes les requêtes refusées avec 503.

**Aggravant OVH2 :** Guardian TERMINATOR `PID 3560488` (`:8001`) encore actif depuis session R064 — consommait ~50 Mo supplémentaires.

### APRÈS

| Nœud | RAM utilisée | RAM libre | artcb.service | Réponse `:8000` |
|------|-------------|-----------|---------------|----------------|
| OVH2 | 616 Mo | **6.5 Go** | active (running) | `200 healthy` ✅ |
| OVH4 | 580 Mo | **7.0 Go** | active (running) | `200 healthy` ✅ |
| AWS3 | 1.1 Go | 730 Mo | active (running) | `200 healthy` ✅ |

---

## 3. Actions effectuées

### 3.1 OVH2 — Guardian TERMINATOR :8001 tué

**Avant :**
```
/home/ubuntu/ARTCB-TERMINATOR/.venv/bin/python3 .venv/bin/uvicorn guardian_api.app:app --host 0.0.0.0 --port 8001
PID 3560488 — actif depuis Oct16
```

**Commande :**
```bash
sudo kill -9 3560488
```

**Après :**  
`lsof -ti :8001` = vide (aucun processus)

### 3.2 OVH2 — artcb.service redémarré

**Avant :** `Active: active (running) since Oct16` / mémoire saturée / toutes requêtes 503  
**Commande :** `sudo systemctl restart artcb.service` (timeout → OOM killer a terminé le process) + restart automatique systemd  
**Après :** `Active: active (running) since 2026-10-17 03:47:33 UTC` / `/health` → `{"status":"healthy"}`

### 3.3 OVH4 — artcb.service redémarré

**Avant :** `Active: active (running) since Oct16` / 7.3 Go RAM / 503  
**Commande :** `sudo pkill -9 -f uvicorn && sudo systemctl start artcb.service`  
**Après :** `Active: active (running) since 2026-10-17 03:47:59 UTC` / `/health` → `{"status":"healthy"}`

### 3.4 artcb.me — résolution du 502

**Avant :**  
```
curl https://artcb.me/health → 502 Bad Gateway
```
**Cause :** Nginx proxyfie vers `:8000` — backend était en OOM/503 → nginx retournait 502.  
**Action :** Reload nginx après restart artcb.service  
**Après :**
```
curl https://artcb.me/health → {"status":"healthy","service":"ARTCB API","version":"0.3.0",...}
```

**⚠️ Note config nginx :**  
Deux fichiers en conflit sur `:443` (`artcb-me-http.conf` + `00-artcb-tls-wildcard.conf`) — 8 warnings  
`nginx -t` dit "syntax ok" malgré les warnings.  
Le bloc `:80` ne redirige pas vers HTTPS (retourne 404) — issue mineure, HTTP→HTTPS non configuré.  
**À corriger lors d'une prochaine session.**

---

## 4. État réseau ARTCB Mainnet

```
https://artcb.me/health
→ {"status":"healthy","network_id":"artcb-mainnet-1","protocol_version":"189-mainnet-1"}

OVH2 (151.80.107.29:8000) → healthy ✅  git_sha=5be65d9f
OVH4  (91.134.45.8:8000)   → healthy ✅  git_sha=5be65d9f
AWS3  (13.38.209.25:8000)  → healthy ✅  git_sha=5be65d9f
```

---

## 5. Migration KYC pipeline — confirmée (commit 983f972)

### Correspondance dossiers

| Dossier original (lynadatacraft) | Renommé dans vgactech/artcb_kyc |
|----------------------------------|--------------------------------|
| `Berquecha_Benkmil` | `MODELE_1` |
| `achavaud` | `MODELE_2` |
| `amira_bou` | `MODELE_3` |
| `b` | `MODELE_4` |
| `jz` | `MODELE_5` |
| `leslie_cabanes` | `MODELE_6` |
| `lyna_participante` | `MODELE_7` |
| `nastia` | `MODELE_8` |
| `rendu_iandry` | `MODELE_9` |
| `vgactech_artcb` | `MODELE_10` |

### kyc_pipeline.py — migration dual-path

**Source A :** `MODELE_10/pipeline.py` → logique rule-based déterministe (tables JSON)  
**Source B :** `MODELE_9/run_kyc.py` → interface CLI + orchestration

**Avant (MODELE_9/run_kyc.py, lignes 1-5) :**
```python
#!/usr/bin/env python3
"""run_kyc.py — CLI for running KYC form completion (rendu_iandry)"""
```

**Avant (MODELE_10/pipeline.py, lignes 1-5) :**
```python
#!/usr/bin/env python3
"""pipeline.py — KYC form resolver with rule-based JSON context tables"""
```

**Après (kyc_pipeline.py — point d'entrée unifié) :**
```python
#!/usr/bin/env python3
"""
kyc_pipeline.py — Unified KYC form resolution pipeline

Combines two approaches:
  A) Rule-based deterministic resolver (from MODELE_10/pipeline.py logic)
  B) CLI orchestrator compatible with MODELE_9/run_kyc.py interface
"""
```

**Chemin fichier :** `/Users/deyi/.bob/playground/artcb_kyc/kyc_pipeline.py`  
**Commit :** `983f972`

---

## 6. Frontend ARTCB-TERMINATOR — état confirmé

**Fichier :** `/Users/deyi/.bob/artcb_TERMINATOR_FRONTEND/index.html`  
**Commit :** `56b75ca`

- Guardian API URL : `const API = (window.GUARDIAN_API_URL || 'http://localhost:8002').replace(/\/$/, '')`
- KYC SSE : `EventSource` sur `/api/v1/demo/kyc/stream`
- Réseau métro 3D : 3 lignes (MediaPipe, Guardian, ARTCB Chain), 11 stations
- MediaPipe : fallback GPU→CPU inclus (correction R065)
- Frontend local accessible : `http://localhost:9000/`
- Guardian local `:8002` : actif (PID 21169)

---

## 7. Problèmes non résolus

| Problème | Impact | Priorité |
|----------|--------|----------|
| PR#1 `artcb_TERMINATOR_FRONTEND` non fermée — token sans permission `pull_request:write` | Faible — PR déjà `mergeable:false` | 🟡 Basse |
| Nginx `:80` retourne 404 au lieu de rediriger HTTPS | HTTP ne redirige pas vers HTTPS sur artcb.me | 🟡 Basse |
| Conflit server_name nginx (8 warnings) | Fonctionnel mais config à nettoyer | 🟡 Basse |
| OVH2 config ARTCB_TERMINATOR_FRONTEND non déployée en public | Frontend accessible en local seulement | 🔵 Info |

---

## 8. Rapport précédent

`R066_fix_port_8002_start_guardian_demo_live_2026-10-17.md` — conservé intégralement, non modifié.

---

## 9. Résumé final

```
artcb.me HTTPS    → ✅ UP  (healthy, mainnet-1, protocol 189)
OVH2 :8000        → ✅ UP  (restart OOM)
OVH4 :8000        → ✅ UP  (restart OOM)  
AWS3 :8000        → ✅ UP  (était déjà UP)
Guardian OVH2     → ✅ Arrêté (PID 3560488 killed)
kyc_pipeline.py   → ✅ Migré (MODELE_9 + MODELE_10 fusionnés)
artcb_kyc MODELE  → ✅ 10 dossiers renommés + poussés
index.html métro  → ✅ Commit 56b75ca (Guardian SSE :8002)
```
