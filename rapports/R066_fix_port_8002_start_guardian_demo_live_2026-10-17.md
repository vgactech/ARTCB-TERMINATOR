# R066 — Fix port 8002 + start_guardian.sh + démo live APPROVED

**Date :** 2026-10-17  
**Projet :** `vgactech/ARTCB-TERMINATOR` + `vgactech/artcb_TERMINATOR_FRONTEND`  
**Commits :** TERMINATOR `6fe4bb3` | Frontend `56b75ca`  
**Mode DEBUG actif.** `CERTIFIED_100=false` | `unique_human_proven=false`

---

## Problème résolu

L'utilisateur a tenté de lancer Guardian avec `uvicorn guardian_api.app:app` mais obtenait :
```
zsh: command not found: uvicorn
```

**Cause racine :** `uvicorn` est installé via `python3 -m uvicorn` mais son binaire (`~/.local/bin/uvicorn`) n'est pas dans le `$PATH` zsh de l'utilisateur sur macOS.

**Cause secondaire :** Le port 8001 était déjà occupé par `src.api.main:app` (frontend Vite du playground ARTCB blockchain, PID 1076).

---

## Avant / Après

### `index.html` — port API

| | AVANT | APRÈS |
|---|---|---|
| Port défaut | `localhost:8001` | `localhost:8002` |
| Commit | `2739715` | `56b75ca` |
| Fichier source | `artcb_TERMINATOR_FRONTEND/index.html` ligne 237 | idem |

**AVANT (ligne 237) :**
```javascript
const API = (window.GUARDIAN_API_URL || 'http://localhost:8001').replace(/\/$/, '');
```

**APRÈS :**
```javascript
const API = (window.GUARDIAN_API_URL || 'http://localhost:8002').replace(/\/$/, '');
```

### `start_guardian.sh` — NOUVEAU

**Fichier :** `terminator_repo/start_guardian.sh`

Script de démarrage complet :
- Détecte si Guardian est déjà actif (no double-launch)
- Lance `python3 -m uvicorn guardian_api.app:app --port 8002` (contourne le PATH zsh)
- Attend que l'API soit prête (max 8s, 16 tentatives × 0.5s)
- Exécute un test KYC rapide (Alice Martin) pour valider le pipeline
- Ouvre `artcb_TERMINATOR_FRONTEND/index.html` automatiquement

---

## Test d'exécution — logs réels

```
✅ Guardian déjà actif sur :8002

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Guardian API  →  http://localhost:8002/api/health
  KYC stream    →  http://localhost:8002/api/kyc/stream
  Scénarios     →  http://localhost:8002/api/scenarios
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 Test KYC rapide (Alice Martin)...
   Verdict: APPROVED ✅
```

---

## Test SSE KYC complet — événements réels reçus

| Événement | Contenu clé |
|-----------|-------------|
| `session_opened` | `session:b332d915…`, 4 agents |
| `kyc_identity_check` | `status: PASS` |
| `attack_generated` | `wallet.sign` → `kyc-fraud-DOC-001.invalid` |
| `propagation` | `payload_content_hash: e3ed70cf…` |
| `guardian_decision` | `decision: BLOCK` — `SensitiveToolBlocked` |
| `chain_verified` | `R0 PASS`, 2 events replayed |
| `kyc_result` | `verdict: APPROVED`, `score: 95`, `attacks_blocked: 1` |
| `done` | `pdf_b64` présent, `pdf_size_kb: 0.8` |

---

## Comment utiliser maintenant

```bash
cd /Users/deyi/.bob/terminator_repo
./start_guardian.sh
# → Frontend s'ouvre automatiquement
# → Chip "API ONLINE" s'allume (vert)
# → Cliquer ▶ Run KYC → stations 3D s'activent en temps réel
# → À la fin : PDF forensic téléchargé automatiquement
```

Pour arrêter Guardian :
```bash
kill $(lsof -ti :8002)
```

---

## Ports sur cette machine

| Port | Process | Note |
|------|---------|------|
| 8001 | `src.api.main:app` (PID 1076) | Playground ARTCB blockchain — NE PAS TUER |
| 8002 | `guardian_api.app:app` | Guardian TERMINATOR — actif ✅ |

---

## Rapport précédent R065 conservé intégralement.
