#!/usr/bin/env bash
# start_guardian.sh — Lance Guardian API ARTCB-TERMINATOR sur port 8002
# Usage : ./start_guardian.sh
#
# Port 8001 est réservé par le frontend Vite du playground ARTCB blockchain.
# Guardian tourne sur 8002.
#
# MODE DEBUG actif — CERTIFIED_100=false | unique_human_proven=false

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${GUARDIAN_PORT:-8002}"
FRONTEND_DIR="${SCRIPT_DIR}/../artcb_TERMINATOR_FRONTEND"
LOG_FILE="/tmp/guardian_api_${PORT}.log"

# ── Vérifier que le port est libre ──────────────────────────────────────────
if lsof -ti :"${PORT}" >/dev/null 2>&1; then
  echo "⚠  Port ${PORT} déjà occupé. Tentative de connexion au Guardian existant..."
  HEALTH=$(curl -s --max-time 2 "http://localhost:${PORT}/api/health" 2>/dev/null || echo "")
  if echo "$HEALTH" | grep -q '"status".*"ok"'; then
    echo "✅ Guardian déjà actif sur :${PORT}"
  else
    echo "❌ Port ${PORT} occupé par un autre process. Choisir un autre port :"
    echo "   GUARDIAN_PORT=8003 ./start_guardian.sh"
    exit 1
  fi
else
  # ── Lancer Guardian en background ─────────────────────────────────────────
  echo "🚀 Lancement Guardian API sur port ${PORT}..."
  cd "$SCRIPT_DIR"
  python3 -m uvicorn guardian_api.app:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level info \
    > "${LOG_FILE}" 2>&1 &
  GUARDIAN_PID=$!
  echo "   PID: ${GUARDIAN_PID} | log: ${LOG_FILE}"

  # Attendre que l'API soit prête (max 8 secondes)
  echo -n "   En attente..."
  for i in $(seq 1 16); do
    sleep 0.5
    HEALTH=$(curl -s --max-time 1 "http://localhost:${PORT}/api/health" 2>/dev/null || echo "")
    if echo "$HEALTH" | grep -q '"status".*"ok"'; then
      echo " ✅"
      break
    fi
    echo -n "."
    if [ $i -eq 16 ]; then
      echo " ❌ Timeout — vérifier ${LOG_FILE}"
      exit 1
    fi
  done
fi

# ── Afficher l'état ──────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Guardian API  →  http://localhost:${PORT}/api/health"
echo "  Demo start    →  http://localhost:${PORT}/api/demo/start  [POST]"
echo "  Scénarios     →  http://localhost:${PORT}/api/scenarios"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Test démo rapide via POST body (PII hors URL — R083 fix) ─────────────────
# AVANT (R082 P0) : GET /api/kyc/stream?first_name=Alice&last_name=Martin&doc_id=TEST-001&dob=1990-01-01
# APRÈS  (R083)   : POST /api/demo/start avec données synthétiques dans le body JSON
# Raison : les query strings apparaissent dans les logs Nginx/proxy ; le body JSON ne l'est pas.
echo "🔬 Test démo rapide (données synthétiques — body JSON)..."
DEMO_RESPONSE=$(curl -s --max-time 12 \
  -X POST "http://localhost:${PORT}/api/demo/start" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"kyc-attack","first_name":"Demo","last_name":"User","doc_id":"FR-DEMO-000000","dob":"1990-01-01"}' \
  2>/dev/null)
if echo "$DEMO_RESPONSE" | grep -q '"session_id"\|"scenario_id"\|"status"'; then
  echo "   Session démarrée ✅ — connecter le frontend SSE pour les événements."
elif echo "$DEMO_RESPONSE" | grep -q '"detail"'; then
  # L'endpoint peut retourner une erreur si scenario_id est inconnu : afficher sans paniquer
  DETAIL=$(echo "$DEMO_RESPONSE" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('detail','?'))" 2>/dev/null || echo "?")
  echo "   ⚠  Réponse API : ${DETAIL}"
else
  echo "   ⚠  Pas de réponse demo/start — vérifier les logs : ${LOG_FILE}"
fi

# ── Ouvrir le frontend ───────────────────────────────────────────────────────
if [ -f "${FRONTEND_DIR}/index.html" ]; then
  echo ""
  echo "🌐 Ouverture du frontend holographique..."
  open "${FRONTEND_DIR}/index.html" 2>/dev/null || \
    xdg-open "${FRONTEND_DIR}/index.html" 2>/dev/null || \
    echo "   Ouvrir manuellement : ${FRONTEND_DIR}/index.html"
  echo ""
  echo "💡 Le chip 'API ONLINE' s'allume automatiquement."
  echo "   Cliquer sur ▶ Run KYC pour lancer la démo live."
fi
echo ""
echo "Pour arrêter Guardian : kill \$(lsof -ti :${PORT})"
