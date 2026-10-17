# R069 — Nginx HTTP→HTTPS redirect corrigé + diagnostic PR#1

**Date :** 2026-10-17T04:30:11Z  
**Session :** Anomalies résiduelles R067/R068  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**  

---

## Anomalie 1 — Redirection HTTP→HTTPS (RÉSOLUE)

### AVANT

```
curl http://151.80.107.29/   → 404 Not Found
curl https://artcb.me/       → Service Unavailable (OOM blockchain)
```

**Cause :** Bloc `:80` dans `artcb-me-http.conf` (Certbot) avait retiré le `proxy_pass` et inséré un `return 404`. Le bloc `:443` dans `00-artcb-tls-wildcard.conf` proxifiait vers `:8000` (blockchain désactivée).

### APRÈS

**Fichier modifié :** `/etc/nginx/conf.d/artcb-terminator.conf`  
**Fichier supprimé :** `/etc/nginx/conf.d/00-artcb-tls-wildcard.conf` (remplacé)  
**Fichier supprimé :** `/etc/nginx/conf.d/artcb-me-http.conf` (supprimé session R068)

**Config active (extrait exact) :**
```nginx
# Bloc 1 : HTTP → redirection permanente HTTPS
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}

# Bloc 2 : HTTPS — frontend statique + Guardian API
server {
    listen 443 ssl;
    ...
    root /var/www/terminator;
    location /     { try_files $uri /index.html; }
    location /api/ { proxy_pass http://127.0.0.1:8002; proxy_buffering off; }
}
```

**Vérification :**
```
curl -sI http://151.80.107.29/
→ HTTP/1.1 301 Moved Permanently
→ Location: https://151.80.107.29/

curl https://artcb.me/api/health (depuis serveur)
→ {"status":"ok","service":"artcb-terminator-api","engine":"guardian"}

curl https://151.80.107.29/
→ <!doctype html> (index.html TERMINATOR) ✅
```

**Note DNS split (L-054) :** depuis le Mac local, `artcb.me` peut résoudre vers une IP différente selon le resolver. Tester via IP directe `http://151.80.107.29/` ou `https://151.80.107.29/` confirme le bon fonctionnement. Ce n'est pas un bug nginx.

---

## Anomalie 2 — Fermeture PR#1 `artcb_TERMINATOR_FRONTEND` (NON RÉSOLUE — action utilisateur requise)

### Diagnostic

```
PR#1 : "Harden MediaPipe hologram P0 interactions"
État : open / mergeable: false
Token Doppler artcb-blockchain : fine-grained PAT
Résultat PATCH /pulls/1 : "Resource not accessible by personal access token"
```

**Cause :** Le token fine-grained dans Doppler `artcb-blockchain` n'a pas la permission `pull_requests:write` sur le dépôt `vgactech/artcb_TERMINATOR_FRONTEND`.

### Clé SSH publique à coller sur GitHub

Pour régler ce problème durablement (fermeture de PR + futurs push), voici la clé publique SSH du nœud OVH2 à ajouter dans **GitHub → Settings → SSH Keys** :

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPU7k4AaW/FY0z9dpEbo1fUcWBnFTz3l7c5kHMErKzh5 artcb-ovh-node-2-agent-204
```

### Action manuelle pour fermer PR#1

URL directe : **https://github.com/vgactech/artcb_TERMINATOR_FRONTEND/pull/1**  
→ Cliquer **"Close pull request"** (pas merger — la PR est `mergeable:false`)

---

## État final OVH2 après cette session

```
artcb.service         → disabled / failed  (DÉFINITIVEMENT supprimé)
artcb-guardian.service → enabled / active  (Guardian :8002)
nginx                 → active             (HTTP:80→301 HTTPS:443 frontend+Guardian)
Port :8000            → LIBRE
Port :8002            → Guardian API       ✅
Port :80              → 301 → HTTPS        ✅
Port :443             → Frontend TERMINATOR + /api/ Guardian ✅
```

---

## Rapports précédents conservés intégralement

- R067 — bilan OOM + artcb.me UP
- R068 — OVH2 artcb.service désactivé + TERMINATOR déployé
