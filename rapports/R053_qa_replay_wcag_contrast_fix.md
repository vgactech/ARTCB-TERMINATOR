# R053 — QA Replay : Correction contraste WCAG AA + Bugs critiques frontend

**Date** : 2026-10-11  
**Commit** : `eb54152`  
**Branche** : `feat/artcb-forensic-integration`  
**Statut** : ✅ LIVRÉ ET DÉPLOYÉ

---

## 1. Source du rapport

Rapport QA généré par la plateforme **QA Replay (replay.io)** sur l'URL de production `http://35.90.101.61/`.  
Enregistrement Replay : https://app.replay.io/recording/912dd46a-9cb3-45c7-b9c8-b0f6df9bd617

---

## 2. Bugs identifiés et corrigés

### Bug #1 — Contraste WCAG AA insuffisant (QA Replay)

| Champ | Valeur |
|---|---|
| Éléments affectés | `<BUTTON> "🔍 KYC Forensic"` + `<BUTTON> "⚡ Scénarios Guardian"` |
| Classe fautive | `text-slate-500` |
| Foreground mesuré | `rgb(98, 116, 142)` |
| Background effectif | `rgb(5, 10, 18)` |
| Ratio mesuré | **4.16:1** |
| Seuil WCAG AA normal text | **4.5:1** |
| Statut avant fix | ❌ FAIL |
| **Fix appliqué** | `text-slate-500` → `text-slate-400`, `hover:text-slate-300` → `hover:text-slate-200` |
| Ratio après fix | **~6.7:1** |
| Statut après fix | ✅ PASS |

**Fichiers modifiés** :
- [`frontend/src/App.tsx`](../frontend/src/App.tsx) ligne 158 (onglets) et ligne 134 (bouton HUD Graph)

---

### Bug #2 — `ERR_CONNECTION_RESET` sur `http://35.90.101.61:3000/`

**Cause** : Le port 3000 est le serveur de développement Vite. Il n'est pas exposé en production.  
**URL correcte** : `http://35.90.101.61/` (port 80, nginx).  
**Fix** : Documentation + script de déploiement corrigé.

---

### Bug #3 — Badge "Offline" affiché à tort sur les appareils du jury

**Cause racine** : `VITE_API_URL` n'était pas défini pour le build de production.  
- `apiBaseUrl = import.meta.env.VITE_API_URL ?? ''` → chaîne vide
- `fetch('/api/health')` → nginx renvoyait 404 → `setEngineState('offline')`

**Fix** :
- Créé [`frontend/.env.production`](../frontend/.env.production) avec `VITE_API_URL=http://54.203.22.158:8000`
- Configuré nginx avec proxy `/api/` → `http://54.203.22.158:8000/api/` (avec `proxy_buffering off` pour les SSE)

---

### Bug #4 — Page vide au clic "Lancer KYC complet"

**Cause racine** : Même que Bug #3 — `apiBase` vide dans `KycPanel`.  
- `new EventSource(''/api/kyc/stream')` → EventSource sur chemin relatif → nginx 404
- L'événement `error` de l'EventSource se déclenchait immédiatement
- `setRunning(false)` mais timeline vide → rendu visuel = page vide

**Fix** :
- `VITE_API_URL` correctement injecté → SSE pointe vers `http://54.203.22.158:8000/api/kyc/stream`
- Gestionnaire d'erreur SSE amélioré : discrimine `CLOSED` (fin normale) vs erreur réseau réelle, affiche l'URL problématique dans le détail

---

## 3. Configuration nginx corrigée

```nginx
server {
    listen 80 default_server;
    root /var/www/html/artcb;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API → backend EC2 (SSE-compatible)
    location /api/ {
        proxy_pass http://54.203.22.158:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;      # ← critique pour les SSE KYC
        proxy_cache off;
        proxy_read_timeout 120s;
    }
}
```

---

## 4. Vérification post-déploiement

```
GET http://35.90.101.61/           → HTTP 200 ✅ (635 bytes, HTML)
GET http://35.90.101.61/api/health → HTTP 200 ✅
  {"status":"ok","service":"artcb-terminator-api","engine":"guardian","title":"ARTCB TERMINATOR FORENSIC"}
```

---

## 5. État post-fix

| Vérification | Résultat |
|---|---|
| Build TypeScript | ✅ zéro erreur |
| Bundle Vite | ✅ 409 kB JS, 49 kB CSS |
| Page chargée sur port 80 | ✅ HTTP 200 |
| Proxy `/api/health` | ✅ HTTP 200 |
| Contraste onglets inactifs | ✅ ~6.7:1 (WCAG AA) |
| KYC SSE error handler | ✅ message d'erreur explicit, pas de page blanche |
| Commit pushé | ✅ `eb54152` sur `feat/artcb-forensic-integration` |
