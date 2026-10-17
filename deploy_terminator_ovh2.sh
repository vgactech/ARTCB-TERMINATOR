#!/usr/bin/env bash
# deploy_terminator_ovh2.sh — Déploie ARTCB-TERMINATOR sur OVH2
# OVH2 = FRONTEND + GUARDIAN UNIQUEMENT (artcb.service désactivé définitivement)
# Usage: bash deploy_terminator_ovh2.sh
set -e

OVH2_IP="151.80.107.29"
OVH2_USER="ubuntu"
SSH_KEY="/tmp/artcb_ssh/ovh2_key"
REMOTE_DIR="/home/ubuntu/ARTCB-TERMINATOR"
FRONTEND_SRC="/Users/deyi/.bob/artcb_TERMINATOR_FRONTEND/index.html"
GUARDIAN_SRC="/Users/deyi/.bob/terminator_repo"

echo "[1/6] Vérification clé SSH..."
test -f "$SSH_KEY" || { echo "ERREUR: $SSH_KEY absent"; exit 1; }
chmod 600 "$SSH_KEY"

echo "[2/6] Copie index.html → OVH2:/var/www/html/..."
scp -o StrictHostKeyChecking=accept-new -i "$SSH_KEY" \
    "$FRONTEND_SRC" \
    "${OVH2_USER}@${OVH2_IP}:/tmp/index_terminator.html"

ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -i "$SSH_KEY" \
    "${OVH2_USER}@${OVH2_IP}" \
    'sudo mkdir -p /var/www/terminator && sudo cp /tmp/index_terminator.html /var/www/terminator/index.html && sudo chmod 644 /var/www/terminator/index.html && echo "frontend copié"'

echo "[3/6] Copie guardian_api + requirements → OVH2..."
scp -o StrictHostKeyChecking=accept-new -i "$SSH_KEY" -r \
    "$GUARDIAN_SRC/guardian_api" \
    "${OVH2_USER}@${OVH2_IP}:${REMOTE_DIR}/"

scp -o StrictHostKeyChecking=accept-new -i "$SSH_KEY" \
    "$GUARDIAN_SRC/start_guardian.sh" \
    "${OVH2_USER}@${OVH2_IP}:${REMOTE_DIR}/"

echo "[4/6] Install dépendances Python sur OVH2..."
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -i "$SSH_KEY" \
    "${OVH2_USER}@${OVH2_IP}" \
    "cd ${REMOTE_DIR} && python3 -m venv .venv 2>/dev/null || true && .venv/bin/pip install -q -r guardian_api/requirements.txt && echo 'deps OK'"

echo "[5/6] Configurer nginx pour TERMINATOR..."
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -i "$SSH_KEY" \
    "${OVH2_USER}@${OVH2_IP}" 'bash -s' <<'NGINX_CONF'
sudo tee /etc/nginx/conf.d/artcb-terminator.conf > /dev/null <<'EOF'
# ARTCB-TERMINATOR frontend — OVH2 dédié
# artcb.service DÉSACTIVÉ définitivement sur ce nœud
server {
    listen 80;
    listen [::]:80;
    server_name terminator.artcb.me artcb.me www.artcb.me _;

    # Frontend statique
    root /var/www/terminator;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Guardian API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Connection "";
        proxy_read_timeout 300s;
        # SSE support
        proxy_buffering off;
        proxy_cache off;
    }

    # SSE stream
    location /api/v1/demo/kyc/stream {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        add_header X-Accel-Buffering no;
    }
}
EOF
echo "nginx conf écrite"
NGINX_CONF

echo "[6/6] Reload nginx + vérification..."
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -i "$SSH_KEY" \
    "${OVH2_USER}@${OVH2_IP}" \
    'sudo nginx -t 2>&1 && sudo systemctl reload nginx && echo "nginx reloaded"'

echo ""
echo "✅ Déploiement terminé"
echo "   Frontend : http://151.80.107.29/"
echo "   Guardian : démarrer manuellement via systemd (voir étape suivante)"
