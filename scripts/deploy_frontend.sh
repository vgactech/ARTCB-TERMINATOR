#!/usr/bin/env bash
# deploy_frontend.sh — Build et déploie le frontend sur EC2 via SSH
# Usage: bash scripts/deploy_frontend.sh
# Prérequis: artcb-terminator-key.pem dans %TEMP% (Windows) ou /tmp (Linux)
set -euo pipefail

EC2_FRONTEND="35.90.101.61"
EC2_API="54.203.22.158"
KEY="${TEMP:-/tmp}/artcb-terminator-key.pem"
SSH_USER="ec2-user"

echo "=== [1/4] Build frontend ==="
cd frontend
npm ci --silent
npm run build
cd ..

echo "=== [2/4] Upload dist/ vers EC2 frontend ==="
rsync -avz --delete \
  -e "ssh -i \"$KEY\" -o StrictHostKeyChecking=no" \
  frontend/dist/ \
  ${SSH_USER}@${EC2_FRONTEND}:/home/${SSH_USER}/dist/

echo "=== [3/4] Configurer nginx ==="
ssh -i "$KEY" -o StrictHostKeyChecking=no ${SSH_USER}@${EC2_FRONTEND} bash <<'ENDSSH'
set -e

# Copier le build static vers /var/www/html
sudo rm -rf /var/www/html/artcb
sudo mkdir -p /var/www/html/artcb
sudo cp -r /home/ec2-user/dist/* /var/www/html/artcb/

# Écrire la config nginx avec proxy /api/
sudo tee /etc/nginx/conf.d/artcb.conf > /dev/null <<'NGINX'
server {
    listen 80 default_server;
    server_name _;

    root /var/www/html/artcb;
    index index.html;

    # SPA fallback — toutes les routes non-fichier → index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy /api/ → API EC2 sur port 8000
    location /api/ {
        proxy_pass http://54.203.22.158:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # SSE — désactiver le buffering nginx
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
        proxy_read_timeout 120s;
    }
}
NGINX

sudo nginx -t && sudo systemctl reload nginx
echo "nginx rechargé OK"
ENDSSH

echo "=== [4/4] Test sanity ==="
sleep 2
curl -sf "http://${EC2_FRONTEND}/api/health" | python3 -m json.tool || echo "WARN: API health check failed"
curl -sf "http://${EC2_FRONTEND}/" | head -c 200

echo ""
echo "✅ Déploiement terminé → http://${EC2_FRONTEND}/"
echo "   API backend → http://${EC2_API}:8000/api/health"
