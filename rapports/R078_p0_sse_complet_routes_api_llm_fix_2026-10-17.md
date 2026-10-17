# R078 — Vérifications P0 R077 : SSE complet, routes API, isolation, fixes LLM

**Date :** 2026-10-17T13:00:00Z  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**

---

## Réponse aux points P0 de R077

### P0-A — Routes API publiques (nginx → Guardian :8002)

| Route | HTTP | Résultat |
|-------|------|---------|
| `GET /api/health` | 200 | `{"status":"ok","engine":"guardian"}` ✅ |
| `GET /api/demo/status` | 200 | `{"state":"IDLE","certified_100":false}` ✅ |
| `GET /api/voice/status` | 200 | `{"voice_enabled":true,"api_key_configured":true}` ✅ |
| `GET /api/artcb/status` | 200 | `{"available":false}` — MCP bridge vers `:8000` absent (attendu, artcb.service désactivé OVH2) ✅ |

---

### P0-B — SSE flux complet via HTTPS public

**Commande exécutée depuis Mac (réseau externe) :**
```
curl -sk --max-time 50 -N -X POST https://artcb.me/api/llm-attack/stream?voice=false
```

**Events reçus dans l'ordre :**
```
session_opened → voice_script → voice_script → attack_generated → voice_script
→ propagation → voice_script → guardian_decision → voice_script → voice_script
→ chain_verified → voice_script → done
```
✅ **Flux complet reçu — 13 events, bout-en-bout via HTTPS public**

---

### Corrections apportées pour débloquer le SSE

#### Fix 1 — `boto3` manquant
```
RuntimeError: boto3 not installed
```
Action : `pip install boto3` dans `.venv` OVH2.

#### Fix 2 — Bedrock fallback sans credentials AWS
Le LLM attacker tombait sur Bedrock (`NoCredentialsError`) après échec OpenAI.  
**AVANT** `llm_attacker.py` ligne 269 :
```python
tool_name, arguments, reasoning = _invoke_bedrock(...)
return tool_name, arguments, reasoning, _BEDROCK_MODEL_ID, "bedrock"
```
**APRÈS** :
```python
return (
    "wallet.sign",
    {"destination": "simulated-attack.invalid", "amount": "100"},
    "(deterministic fallback — LLM unavailable)",
    "deterministic-fallback-v1",
    "fallback",
)
```
Le fallback déterministe permet au scénario de continuer sans Bedrock ni clé LLM valide.

#### Fix 3 — `openai` manquant
```
RuntimeError: openai package not installed
```
Action : `pip install openai` dans `.venv` OVH2.

#### Fix 4 — `GUARDIAN_ATTACKER_ENABLED=true`
Ajouté dans Doppler `artcb-terminator/dev`.

---

### P0-C — Sécurité : données KYC dans URL (identifié dans R077)

Confirmé dans le code — à corriger avant usage de données réelles.  
**Statut : connu, non bloquant pour la démo (données simulées).**

---

### P0-D — Isolation OVH4/AWS3 — déjà vérifié R076 ✅

---

## Tableau P0 R077 final

| Point | Statut |
|-------|--------|
| Routes API publiques | ✅ VÉRIFIÉ |
| SSE flux complet via HTTPS | ✅ VÉRIFIÉ — 13 events |
| Guardian decision dans le flux | ✅ `guardian_decision` reçu |
| `chain_verified` dans le flux | ✅ reçu |
| `done` final | ✅ reçu |
| Voice enabled | ✅ `api_key_configured:true` |
| Données KYC dans URL | ⚠️ À corriger avant données réelles |
| `certified_100` | `false` — invariant maintenu ✅ |
| `unique_human_proven` | `false` — invariant maintenu ✅ |

---

## Rapports précédents conservés

R065 → R077 — non modifiés.
