#!/bin/bash
# ARTCB-TERMINATOR — EC2 Deployment Script
# Deploys Guardian API + Frontend to AWS hackathon servers
# Usage: bash scripts/deploy_ec2.sh
# Requires: doppler CLI authenticated, artcb-terminator-key.pem in $TEMP

set -e

KEY_FILE="${TEMP:-/tmp}/artcb-terminator-key.pem"
chmod 400 "$KEY_FILE" 2>/dev/null || true

API_IP="54.203.22.158"
FRONTEND_IP="35.90.101.61"
REPO="https://github.com/vgactech/ARTCB-TERMINATOR.git"
BRANCH="feat/artcb-forensic-integration"

echo "=== [1/4] Deploy Guardian API to $API_IP ==="
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ec2-user@$API_IP bash <<'REMOTE'
  set -e
  sudo yum install -y git python3.11 python3.11-pip 2>/dev/null || true
  [ -d ~/ARTCB-TERMINATOR ] || git clone https://github.com/vgactech/ARTCB-TERMINATOR.git ~/ARTCB-TERMINATOR
  cd ~/ARTCB-TERMINATOR
  git fetch origin feat/artcb-forensic-integration
  git checkout feat/artcb-forensic-integration
  git pull origin feat/artcb-forensic-integration
  pip3.11 install -r requirements.txt -q
  pip3.11 install boto3 -q
  # Install doppler
  curl -sLf --retry 3 --tlsv1.2 -o /tmp/doppler.rpm \
    "https://cli.doppler.com/download?format=rpm&arch=amd64" && \
    sudo rpm -i /tmp/doppler.rpm 2>/dev/null || true
  echo "API node ready: $(python3.11 --version)"
REMOTE
echo "✅ API node prepared"

echo "=== [2/4] Deploy Frontend to $FRONTEND_IP ==="
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ec2-user@$FRONTEND_IP bash <<'REMOTE'
  set -e
  sudo yum install -y git nodejs npm 2>/dev/null || true
  sudo npm install -g pm2 -q
  [ -d ~/ARTCB-TERMINATOR ] || git clone https://github.com/vgactech/ARTCB-TERMINATOR.git ~/ARTCB-TERMINATOR
  cd ~/ARTCB-TERMINATOR
  git fetch origin feat/artcb-forensic-integration
  git checkout feat/artcb-forensic-integration
  git pull origin feat/artcb-forensic-integration
  cd frontend
  npm install -q
  npm run build
  echo "Frontend built: $(ls -la dist/ | head -5)"
REMOTE
echo "✅ Frontend node prepared"

echo "=== [3/4] Start API service ==="
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ec2-user@$API_IP bash <<'REMOTE'
  cd ~/ARTCB-TERMINATOR
  # Set env vars from Doppler (must have doppler token)
  export DOPPLER_TOKEN="${DOPPLER_TOKEN:-}"
  pkill -f uvicorn 2>/dev/null || true
  nohup doppler run --project aws --config dev -- \
    python3.11 -m uvicorn guardian_api.app:app \
    --host 0.0.0.0 --port 8000 \
    > /tmp/guardian_api.log 2>&1 &
  sleep 3
  curl -sf http://localhost:8000/healthz && echo "API healthy" || echo "API starting..."
REMOTE

echo "=== [4/4] Start Frontend service ==="
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ec2-user@$FRONTEND_IP bash <<'REMOTE'
  cd ~/ARTCB-TERMINATOR/frontend
  pm2 delete artcb-frontend 2>/dev/null || true
  pm2 serve dist 3000 --name artcb-frontend --spa
  pm2 save
  echo "Frontend serving on :3000"
REMOTE

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "Guardian API : http://$API_IP:8000"
echo "Frontend     : http://$FRONTEND_IP:3000"
echo ""
echo "Next: configure DNS terminator.artcb.me -> $FRONTEND_IP"
