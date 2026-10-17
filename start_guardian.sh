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
echo "  KYC stream    →  http://localhost:${PORT}/api/kyc/stream"
echo "  Scénarios     →  http://localhost:${PORT}/api/scenarios"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Test KYC rapide ──────────────────────────────────────────────────────────
echo "🔬 Test KYC rapide (Alice Martin)..."
RESULT=$(curl -s --max-time 12 \
  "http://localhost:${PORT}/api/kyc/stream?first_name=Alice&last_name=Martin&doc_id=TEST-001&dob=1990-01-01" \
  2>/dev/null | grep "^data:" | tail -2)
if echo "$RESULT" | grep -q '"verdict"'; then
  VERDICT=$(echo "$RESULT" | python3 -c "import sys,json; d=json.loads(sys.stdin.readline().replace('data: ','')); print(d.get('verdict','?'))" 2>/dev/null || echo "?")
  echo "   Verdict: ${VERDICT} ✅"
else
  echo "   ⚠  Pas de réponse KYC — vérifier les logs"
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
