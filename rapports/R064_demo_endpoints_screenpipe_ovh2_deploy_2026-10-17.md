# R064 — Demo Endpoints + Screenpipe Fallback + Déploiement OVH2

**Date :** 2026-10-17  
**Projet :** ARTCB-TERMINATOR  
**Espace de numérotation :** TERMINATOR (R001–R064+)  
**Commit :** `8b2db2c` (main)  
**HEAD précédent :** `1e33f31`  
**Mode DEBUG actif.** `CERTIFIED_100=false` | `unique_human_proven=false`

---

## Résumé

Reprise de la tâche interrompue à 55 %. Ajout des 6 nouveaux endpoints démo
(`ScenarioController`) + 1 endpoint Screenpipe fallback dans `guardian_api/app.py`,
accompagnés de 16 nouveaux tests (185 PASS total). Déploiement live sur OVH2
(`151.80.107.29:8001`).

---

## Contexte hackathon Screenpipe

- **Événement :** Hackathon Screenpipe — 42 Paris, 16–18 octobre 2026
- **Track :** "Expliquez votre flux de travail à un agent"
- **Contrainte** : Screenpipe optionnel — la démo doit fonctionner sans installation locale
- **Décisions architecturales confirmées :**
  - Q1 : Fixture KYC = `SIMULATED` (pas de données réelles)
  - Q2 : Screenpipe = offline fallback par défaut
  - Q3 : Frontend séparé (`artcb_TERMINATOR_FRONTEND`)

---

## Fichiers modifiés

### 1. `guardian_api/app.py` — 6 nouveaux endpoints

**AVANT (ligne 500) :**
```python
# ─── KYC Stream ───────────────────────────────────────────────────────────────
```

**APRÈS — ajout entre les blocs existants :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/demo/status` | GET | État courant du contrôleur (IDLE/RUNNING/COMPLETED) |
| `/api/demo/scenarios` | GET | Liste des scénarios disponibles |
| `/api/demo/phases` | GET | Phases de la démo dans l'ordre (4 phases) |
| `/api/demo/start` | POST | Démarre un scénario (query params: scenario_id, first_name, last_name, doc_id, dob) |
| `/api/demo/advance` | POST | Avance à la phase suivante |
| `/api/demo/reset` | POST | Réinitialise le contrôleur (archive conservée) |
| `/api/screenpipe/context` | GET | Contexte Screenpipe live ou fallback offline |

**Import ajouté (ligne 21) :**
```python
# AVANT
from guardian_mcp.instrumentation import GENESIS_HASH

# APRÈS
from guardian_mcp.instrumentation import GENESIS_HASH
from guardian_api.scenario_controller import scenario_controller
```

**Import stdlib ajouté :**
```python
# AVANT
import os

# APRÈS
import os
import time
from fastapi import FastAPI, HTTPException, Query
```

### 2. `guardian_api/kyc_fixture.py` — NOUVEAU (commité)

Fixture KYC synthétique déterministe. Données SIMULATED, aucun PII.
- `KycIdentity` : identité synthétique avec `source=SIMULATED`
- `KycEvent` : événement d'audit (session.open / identity.verify / policy.block / chain.seal)
- `KycFixtureResult` : résultat complet avec score, verdict, chain_hash SHA-256
- `build_kyc_fixture(run_id, ...)` : constructeur

### 3. `guardian_api/scenario_controller.py` — NOUVEAU (commité)

Singleton `ScenarioController` — gestion du cycle de vie des démos.
- `DemoState` : IDLE / RUNNING / COMPLETED / ERROR
- `DemoPhase` : DETECTION → DECISION → CONTAINMENT → RECOVERY
- 3 scénarios : `kyc-attack`, `kyc-prompt-injection`, `kyc-exfiltration`
- `start()`, `advance_phase()`, `reset()`, `status()`, `available_scenarios()`, `phase_labels()`

### 4. `guardian_api/test_app.py` — +16 tests

**AVANT :** 58 tests  
**APRÈS :** 74 tests (+16 nouveaux)

| Test | Endpoint testé | Assertion clé |
|------|---------------|---------------|
| `test_demo_status_idle` | GET /api/demo/status | state=IDLE, certified_100=false |
| `test_demo_scenarios_list` | GET /api/demo/scenarios | ≥3 scénarios, data_source=SIMULATED |
| `test_demo_phases_list` | GET /api/demo/phases | 4 phases dans l'ordre exact |
| `test_demo_start_default_scenario` | POST /api/demo/start | state=RUNNING, kyc_result présent |
| `test_demo_start_custom_scenario` | POST /api/demo/start?scenario_id=... | scenario_id correct |
| `test_demo_start_unknown_scenario_returns_400` | POST /api/demo/start | HTTP 400 |
| `test_demo_advance_through_all_phases` | POST /api/demo/advance ×4 | cycle complet → COMPLETED |
| `test_demo_advance_without_active_run_returns_400` | POST /api/demo/advance | HTTP 400 si IDLE |
| `test_demo_reset_returns_previous_run_id` | POST /api/demo/reset | previous_run_id correct |
| `test_demo_reset_when_idle` | POST /api/demo/reset | previous_run_id=None |
| `test_demo_status_reflects_running_state` | GET /api/demo/status | run_id cohérent avec start |
| `test_demo_kyc_fixture_has_correct_structure` | POST /api/demo/start | identity, score, chain_hash(64) |
| `test_screenpipe_context_offline_fallback` | GET /api/screenpipe/context | source=offline_fallback |
| `test_screenpipe_context_limit_parameter` | GET /api/screenpipe/context?limit=2 | ≤2 events |
| `test_screenpipe_context_limit_out_of_range` | GET /api/screenpipe/context?limit=0 | HTTP 422 |
| `test_screenpipe_context_unreachable_url_falls_back` | GET /api/screenpipe/context | fallback si URL KO |

### 5. `.gitignore` — ajout

```
# Répertoire de build Rust
guardian_core/target/
target/
```

---

## Endpoint Screenpipe — architecture

```
GET /api/screenpipe/context?limit=N
         │
         ├─ SCREENPIPE_API_URL défini ET joignable (timeout=3s)
         │    └─ source="screenpipe_live", available=true
         │       GET {url}/search?limit=N&content_type=all
         │       Normalisation champs (timestamp/app_name/text/event_type)
         │
         └─ SCREENPIPE_API_URL absent OU injoignable
              └─ source="offline_fallback", available=false
                 5 événements démo horodatés (Guardian Console/Terminal)
                 La démo Guardian continue normalement
```

---

## Résultats des tests

```
$ python3 -m pytest guardian_api/test_app.py -q
74 passed in 2.86s

$ python3 -m pytest -q  (suite complète)
185 passed in 6.85s
```

**Aucune régression** sur les 58 tests existants.

---

## Déploiement OVH2

| Paramètre | Valeur |
|-----------|--------|
| Serveur | `151.80.107.29` (node artcb ovh 2) |
| Port | `8001` (port 8000 réservé au nœud ARTCB blockchain) |
| SHA déployé | `8b2db2c` (= origin/main) |
| Venv | `~/ARTCB-TERMINATOR/.venv` |
| Process | `uvicorn guardian_api.app:app --host 0.0.0.0 --port 8001` |

**Vérification live :**

```
GET http://151.80.107.29:8001/api/health
→ {"status":"ok","service":"artcb-terminator-api","engine":"guardian","title":"ARTCB TERMINATOR FORENSIC"}

GET http://151.80.107.29:8001/api/demo/status
→ {"state":"IDLE","run_id":null,...,"certified_100":false,"unique_human_proven":false}

GET http://151.80.107.29:8001/api/screenpipe/context?limit=2
→ source="offline_fallback" | events=2
```

---

## Clone artcb_kyc

| Action | Résultat |
|--------|---------|
| Remote mise à jour | `git@github.com:vgactech/artcb_kyc.git` (SSH via `artcb_terminator` key) |
| PAT révoqué nettoyé | Ancienne URL avec `github_pat_11BUHBAAQ0...` remplacée |
| Push `main` | ✅ `41bfefc` poussé sur `vgactech/artcb_kyc` |
| Contenu | benchmark R580, analyse concurrents (9 participants), nos résultats, pipeline audit |

---

## Alertes GitHub Dependabot (non bloquantes)

3 vulnérabilités signalées sur le dépôt ARTCB-TERMINATOR :
- 1 HIGH — à investiguer (probablement dans les dépendances Python)
- 1 MODERATE
- 1 LOW

⚠️ **Action recommandée** : consulter GitHub → Security → Dependabot alerts avant la soumission finale.

---

## Endpoints totaux après R064

| Route | Méthode | Catégorie |
|-------|---------|-----------|
| `/api/health` | GET | Infra |
| `/api/artcb/status` | GET | ARTCB bridge |
| `/api/simulation/run` | POST | Démo |
| `/api/llm-attack/run` | POST | LLM |
| `/api/llm-attack/stream` | POST | SSE |
| `/api/voice/status` | GET | Voice |
| `/api/kyc/stream` | GET | KYC SSE |
| `/api/scenarios` | GET | Policy |
| `/api/scenarios/{id}/run` | POST | Policy |
| `/api/demo/status` | GET | **NOUVEAU** |
| `/api/demo/scenarios` | GET | **NOUVEAU** |
| `/api/demo/phases` | GET | **NOUVEAU** |
| `/api/demo/start` | POST | **NOUVEAU** |
| `/api/demo/advance` | POST | **NOUVEAU** |
| `/api/demo/reset` | POST | **NOUVEAU** |
| `/api/screenpipe/context` | GET | **NOUVEAU** |

**Total : 16 endpoints** (10 existants + 6 nouveaux)

---

## Avancement global

| Module | Tests | État |
|--------|-------|------|
| guardian_api (Python) | 74/74 PASS | ✅ |
| guardian_mcp (Python) | 111/111 PASS | ✅ |
| guardian_core (Rust) | 45/45 PASS | ✅ (local, cargo requis) |
| OVH2 live | health OK | ✅ |
| artcb_kyc GitHub | push OK | ✅ |

**Avancement hackathon : ~78 %**

Reste à faire :
- Frontend (`artcb_TERMINATOR_FRONTEND`) — vide, à construire
- Service systemd permanent sur OVH2 (actuellement process `nohup` — survivra pas au reboot)
- Rendre le dépôt PUBLIC avant soumission (SUBMISSION_HACKATHON.md §repo)
- Pitch deck (≤8 slides) — structure prête dans SUBMISSION_HACKATHON.md
- Démo video (optionnel)

---

*Rapport généré le 2026-10-17 — Mode DEBUG actif — CERTIFIED_100=false — unique_human_proven=false*
