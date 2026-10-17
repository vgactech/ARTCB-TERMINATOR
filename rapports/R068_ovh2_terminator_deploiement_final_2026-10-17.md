# R068 — OVH2 : artcb.service supprimé, TERMINATOR déployé publiquement

**Date :** 2026-10-17T04:25:00Z  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**  

---

## Décisions appliquées cette session

| Décision | Action |
|----------|--------|
| OVH2 = TERMINATOR UNIQUEMENT | `artcb.service` désactivé définitivement |
| OVH4 + AWS3 = nœuds ARTCB blockchain | inchangés, toujours actifs |
| Clé ElevenLabs → Doppler `artcb-terminator/dev` | `ELEVENLABS_API_KEY` stockée |
| Frontend visible publiquement | nginx OVH2 sert `/var/www/terminator/index.html` |

---

## 1. Suppression définitive artcb.service sur OVH2

### AVANT
```
artcb.service : active (running) — enabled
Port :8000 : uvicorn src.api.main (PID 922483)
RAM : 6.7 Go utilisés (OOM)
```

### APRÈS
```
artcb.service : failed — disabled
Port :8000 : LIBRE
sudo systemctl is-enabled artcb.service → disabled
```

**Commandes exécutées :**
```bash
sudo systemctl disable artcb.service   # ne redémarre plus jamais
sudo systemctl stop artcb.service      # arrêté maintenant
```

---

## 2. Clé ElevenLabs stockée dans Doppler

### AVANT
Clé non présente dans `artcb-terminator`.

### APRÈS
```
Projet : artcb-terminator
Config  : dev
Secret  : ELEVENLABS_API_KEY = sk_31dfb53c...3fb3d6
```

---

## 3. Déploiement frontend TERMINATOR sur OVH2

### AVANT
```
http://151.80.107.29/  → nginx default (404 / blockchain)
https://artcb.me/      → proxy vers :8000 blockchain (502 quand OOM)
```

### APRÈS
```
http://151.80.107.29/  → frontend ARTCB-TERMINATOR index.html ✅
https://artcb.me/      → frontend ARTCB-TERMINATOR index.html ✅
```

**Fichier déployé :**  
Source locale : `/Users/deyi/.bob/artcb_TERMINATOR_FRONTEND/index.html` (commit 56b75ca)  
Destination OVH2 : `/var/www/terminator/index.html`

**Config nginx `/etc/nginx/conf.d/artcb-terminator.conf` :**
```nginx
server {
    listen 80 default_server;
    server_name _;
    root /var/www/terminator;
    index index.html;
    location /       { try_files $uri /index.html; }
    location /api/   { proxy_pass http://127.0.0.1:8002; proxy_buffering off; }
}
```

---

## 4. Service Guardian déployé sur OVH2

### AVANT
Guardian tournait uniquement en local sur MacBook (port 8002 local, inaccessible publiquement).

### APRÈS
```
/etc/systemd/system/artcb-guardian.service — enabled + active
Port :8002 : uvicorn guardian_api.app:app (PID 1400161)
```

**Vérification :**
```
curl http://127.0.0.1:8002/api/health
→ {"status":"ok","service":"artcb-terminator-api","engine":"guardian","title":"ARTCB TERMINATOR FORENSIC"}
```

**Script déployé :** `terminator_repo/deploy_terminator_ovh2.sh`

---

## 5. Architecture finale OVH2

```
OVH2 (151.80.107.29)
├── nginx :80/:443  → /var/www/terminator/index.html  (frontend 3D)
│                   → proxy /api/* → :8002             (Guardian SSE)
├── artcb-guardian.service :8002  → Guardian API (actif, enabled)
└── artcb.service   → DÉSACTIVÉ DÉFINITIVEMENT
```

---

## 6. Architecture réseau ARTCB finale

| Nœud | Rôle | Service | État |
|------|------|---------|------|
| OVH2 `151.80.107.29` | TERMINATOR FRONTEND | nginx + Guardian :8002 | ✅ actif |
| OVH4 `91.134.45.8` | Nœud blockchain | artcb.service :8000 | ✅ actif |
| AWS3 `13.38.209.25` | Nœud blockchain | artcb.service :8000 | ✅ actif |

---

## 7. Accès public

| URL | Contenu |
|-----|---------|
| `http://151.80.107.29/` | Interface ARTCB-TERMINATOR 3D ✅ |
| `https://artcb.me/` | Interface ARTCB-TERMINATOR 3D ✅ |
| `https://artcb.me/api/health` | Guardian API health ✅ |

---

## 8. Rapport précédent

`R067_bilan_deploiement_noeud_artcb_me_up_kyc_pipeline_migration_2026-10-17.md` — conservé intégralement.
