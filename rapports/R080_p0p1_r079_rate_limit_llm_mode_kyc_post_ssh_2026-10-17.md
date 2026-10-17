# R080 — Corrections P0/P1 R079 : rate-limit, llm_mode, KYC POST body, SSH hardening

**Date :** 2026-10-17T14:00:00Z  
**Commit :** `f2e1c85`  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**

---

## Corrections appliquées

### P0-A — Rate limiting sur les routes d'exécution

**Avant :** aucune limitation — routes `/api/llm-attack/stream` et `/api/demo/start` consommables sans limite.

**Après :**
```python
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
@limiter.limit("6/minute")   # /api/llm-attack/stream
@limiter.limit("10/minute")  # /api/demo/start
```

**Preuve live :**
```
req 1-6 : HTTP 200
req 7   : HTTP 429 Too Many Requests  ✅
```

---

### P0-B — KYC données hors URL

**Avant :** `POST /api/demo/start?first_name=Alice&last_name=Martin&doc_id=TEST-001&dob=1990-01-01`  
→ données dans URL → journaux nginx/serveur

**Après :** corps POST `KYCStartBody` (Pydantic) — query params conservés pour rétrocompatibilité mais dépréciés.

```python
class KYCStartBody(BaseModel):
    scenario_id: str = "kyc-attack"
    first_name: str = "Alice"   # données synthétiques uniquement
    doc_id: str = "FR-DEMO-000000"
    dob: str = "1990-01-01"
```

---

### P1-A — `llm_mode` label dans l'event SSE `attack_generated`

**Avant :** impossible de distinguer attaque LLM réelle vs fallback déterministe.

**Après :**
```json
{
  "model": "deterministic-fallback-v1",
  "llm_mode": "fallback"
}
```
Valeurs possibles : `"openai"` | `"bedrock"` | `"fallback"` | `"unknown"`

**Preuve live :**
```
event: attack_generated
data: {..., "llm_mode": "fallback"}  ✅
```

---

### P1-B — `StrictHostKeyChecking=accept-new` dans deploy script

**Avant :** `StrictHostKeyChecking=no` — aucune vérification du serveur distant.  
**Après :** `StrictHostKeyChecking=accept-new` — accepte les nouveaux hôtes mais rejette les clés modifiées.

---

### Dépendance ajoutée

`guardian_api/requirements.txt` : `slowapi>=0.1.9`

---

## État d'avancement global ARTCB-TERMINATOR

| Domaine | État |
|---------|------|
| DNS `artcb.me → 151.80.107.29` | ✅ propagé tous résolveurs |
| HTTPS frontend public | ✅ `https://artcb.me/` |
| Guardian API publique | ✅ `/api/health` `200 ok` |
| SSE flux complet 13 events | ✅ `session_opened → done` |
| Rate limiting SSE (6/min) | ✅ `429` à req 7 |
| `llm_mode` label dans SSE | ✅ `"fallback"` visible |
| KYC POST body (PII hors URL) | ✅ `KYCStartBody` |
| ElevenLabs voice | ✅ `api_key_configured:true` |
| OVH4 + AWS3 blockchain | ✅ `healthy` |
| Isolation `artcb.me` → seul OVH2 | ✅ `444` sur OVH4/AWS3 |
| SSH `accept-new` deploy script | ✅ |
| `certified_100=false` | ✅ invariant maintenu |
| `unique_human_proven=false` | ✅ invariant maintenu |

## Ce qui reste à faire

| # | Tâche | Priorité |
|---|-------|---------|
| 1 | Voice SSE asynchrone (ne bloque pas Guardian decision) | P0 |
| 2 | Test scénario LLM réel (OpenRouter avec clé BOB) | P1 |
| 3 | `bootstrap_nodes` — retirer OVH2 dans `config.py` + redéployer OVH4/AWS3 | P1 |
| 4 | Dependabot alerts (1 high, 1 moderate, 1 low) | P1 |
| 5 | Frontend React — tester chaque bouton via HTTPS public | P1 |
| 6 | KYC `start_guardian.sh` — remplacer URL params par POST body | P1 |

---

## Rapports précédents conservés

R065 → R079 — non modifiés.
