# R070 — Guardian OVH2 : guardian_mcp déployé, ElevenLabs actif, Doppler injecté

**Date :** 2026-10-17T10:05:00Z  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**  

---

## Problèmes résolus cette session

| # | Problème | Résolution |
|---|----------|-----------|
| 1 | `guardian_mcp` absent sur OVH2 | Copié via scp depuis local |
| 2 | `VOICE_1_ELEVENLABS_API` nom variable manquant dans Doppler | Ajouté dans `artcb-terminator/dev` |
| 3 | Doppler non authentifié sur OVH2 pour `artcb-terminator` | Service token créé + stocké `/etc/doppler-artcb-terminator.token` |
| 4 | Secrets non injectés dans `artcb-guardian.service` | `EnvironmentFile` + `ExecStartPre` doppler download |

---

## 1. Déploiement guardian_mcp

### AVANT
```
ssh OVH2: python3 -c "from guardian_mcp.demo_scenario import DemoReport"
→ ModuleNotFoundError: No module named 'guardian_mcp'
```

### APRÈS
```
scp -r /Users/deyi/.bob/terminator_repo/guardian_mcp ubuntu@151.80.107.29:/home/ubuntu/ARTCB-TERMINATOR/
→ python3 -c "from guardian_mcp.demo_scenario import DemoReport; print('OK')"
→ guardian_mcp OK ✅
```

---

## 2. Secrets ElevenLabs dans Doppler artcb-terminator

### AVANT
```
Doppler artcb-terminator/dev : ELEVENLABS_API_KEY présente
Variable attendue par app.py  : VOICE_1_ELEVENLABS_API → absente
```

### APRÈS
```
Doppler artcb-terminator/dev :
  ELEVENLABS_API_KEY      = sk_31dfb53c...  ✅
  VOICE_1_ELEVENLABS_API  = sk_31dfb53c...  ✅ (ajouté)
```

---

## 3. Service token Doppler sur OVH2

### AVANT
```
ssh OVH2: doppler secrets get VOICE_1_ELEVENLABS_API --project artcb-terminator
→ Doppler Error: you must provide a token
```

### APRÈS
```
Token créé : dp.st.dev.[REDACTED — révoqué, ne plus utiliser]
Stocké     : /etc/doppler-artcb-terminator.token (perms 644)
Test       : doppler secrets get VOICE_1_ELEVENLABS_API --token $(cat /etc/...) --plain
→ sk_31dfb53c... ✅
```

---

## 4. artcb-guardian.service — injection des secrets

**Fichier :** `/etc/systemd/system/artcb-guardian.service`

**AVANT (service sans secrets) :**
```ini
ExecStart=.venv/bin/python -m uvicorn guardian_api.app:app --port 8002
# Aucun EnvironmentFile — VOICE_1_ELEVENLABS_API non injecté
```

**APRÈS :**
```ini
ExecStartPre=/bin/sh -c 'doppler secrets download --no-file --format env \
  --token $(cat /etc/doppler-artcb-terminator.token) \
  --project artcb-terminator --config dev \
  > /home/ubuntu/ARTCB-TERMINATOR/.guardian.env'
EnvironmentFile=-/home/ubuntu/ARTCB-TERMINATOR/.guardian.env
ExecStart=/home/ubuntu/ARTCB-TERMINATOR/.venv/bin/python -m uvicorn guardian_api.app:app --host 0.0.0.0 --port 8002
```

---

## 5. Vérifications finales

```bash
# Guardian actif
sudo systemctl is-active artcb-guardian → active ✅

# Health
curl http://127.0.0.1:8002/api/health
→ {"status":"ok","service":"artcb-terminator-api","engine":"guardian"} ✅

# ElevenLabs
curl http://127.0.0.1:8002/api/voice/status
→ {
    "voice_enabled": true,
    "api_key_configured": true,
    "voices": {
      "commentator":  "nPczCjzI2devNBz1zQrb",
      "orchestrator": "pNInz6obpgDQGcFmaJgB",
      "propagator":   "IKne3meq5aSn9XLyUdCD",
      "defender":     "jsCqWAovK2LkecY7zXl4",
      "attacker":     "SILENT"
    }
  } ✅
```

---

## 6. Architecture OVH2 finale

```
OVH2 (151.80.107.29)
├── nginx :80          → 301 HTTPS ✅
├── nginx :443         → /var/www/terminator/index.html (frontend) ✅
│                      → proxy /api/ → :8002 (Guardian) ✅
├── artcb-guardian.service :8002
│   ├── guardian_api/  ✅
│   ├── guardian_mcp/  ✅ (déployé cette session)
│   ├── VOICE_1_ELEVENLABS_API injecté via Doppler ✅
│   └── ElevenLabs voice_enabled=true ✅
└── artcb.service      → DÉSACTIVÉ définitivement ✅
```

---

## Rapports précédents conservés

R065 → R069 — intacts, non modifiés.
