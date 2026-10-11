# R058 — Full System Audit: Diagnostic complet de tous les modules

**Date**: 2026-10-11  
**Commit référence**: `860265f` (HEAD `feat/artcb-forensic-integration`)  
**Bundle déployé**: `index-C-Cr95KV.js` sur `http://35.90.101.61/`  
**Périmètre**: tous modules Python, Rust, TypeScript/React, infrastructure EC2, secrets Doppler, blockchain ARTCB

---

## 1. Tests automatisés

### Python — 169/169 PASS ✅

```
guardian_mcp/  +  guardian_api/  →  169 passed in 27.91s
```

Couverture confirmée sur :
- `test_demo_scenario.py` — pipeline complet 4 agents
- `test_instrumentation.py` — chaîne R0, hachage SHA-256, parentage
- `test_app.py` — endpoints FastAPI

### TypeScript — 0 erreurs ✅

```
npx tsc --noEmit  →  (no output = pass)
```

### Rust (guardian_core) — NON TESTÉ localement ⚠️

`cargo` absent de la machine locale (clé USB). Les tests Rust (`cargo test`) ne peuvent pas être exécutés ici.  
**Dernier résultat connu** : R017 (`27 tests Rust PASS`).

---

## 2. Infrastructure EC2

### Frontend (`35.90.101.61`)

| Check | Résultat |
|---|---|
| `GET /` | ✅ HTTP 200, `lang="fr"` |
| Bundle JS servi | `index-C-Cr95KV.js` ✅ |
| `VITE_API_URL=http://54.203.22.158:8000` dans bundle | ✅ |
| KYC tab `hidden:true` dans bundle | ✅ |
| nginx conf proxy `/api/` → backend | ✅ `proxy_buffering off` |
| Port 3000 | ✅ Fermé (TCP RST) |

### API backend (`54.203.22.158:8000`)

| Check | Résultat |
|---|---|
| `GET /api/health` | ✅ `{"status":"ok","engine":"guardian"}` |
| `GET /api/scenarios` | ✅ 4 scénarios retournés |
| `POST /api/scenarios/sensitive-exfiltration/run` | ✅ `decision=BLOCK, chain=PASS, agents=4` |
| SSE `/api/kyc/stream` | ✅ 7 events reçus (`session_opened`…`kyc_result`) |
| Processus EC2 | `uvicorn guardian_api.app:app --port 8000` — PID 30226 ✅ |

### AWS credentials (STS)

| Check | Résultat |
|---|---|
| `GetCallerIdentity` | ❌ **ExpiredToken** — token STS hackathon expiré |

**Action requise** : renouveler les credentials STS via AWS CloudShell (`python3 -c "import os,urllib.request..."`) et mettre à jour Doppler `aws/dev`.  
Impact : `GUARDIAN_ATTACKER_ENABLED` et Bedrock sont inopérants jusqu'au renouvellement.

---

## 3. Modules Python — diagnostic par fichier

### `guardian_mcp/instrumentation.py` (1468 lignes) ✅

Cœur du système. Contient :
- `GuardianMCPInstrumentation` — intercepte les appels d'outils MCP, génère les événements R0
- `ChainVerificationResult` / `load_and_verify_jsonl` — replay R0
- `ToolResponseArchive` / `make_recording_sink` — archivage
- `ExternalCallForbiddenError` — barrière replay

État : **stable**, testé à 100% (169 tests PASS).

### `guardian_mcp/defender_agent.py` (329 lignes) ✅

Méthodes clés opérationnelles :
- `evaluate_request()` — applique la politique Guardian
- `verify_chain_r0()` — vérifie intégrité chaîne
- `verify_decisions_r1()` — replay niveau R1
- `get_all_events()` — export pour l'API

### `guardian_mcp/llm_attacker.py` (276 lignes) ⚠️

- **Primaire** : OpenAI `gpt-4o` — `OPENAI_API_KEY` dans Doppler `aws/dev` → **quota $0 épuisé** (confirmé R050)
- **Fallback** : AWS Bedrock `us.anthropic.claude-sonnet-4-5-20250929-v1:0` — token STS **expiré**
- **En production** : l'API utilise un attaquant statique (`guardian-attacker-static`) — les scénarios fonctionnent sans LLM
- `GUARDIAN_ATTACKER_ENABLED=true` non configuré sur EC2 → endpoints `/api/llm-attack/*` désactivés (503)

### `guardian_mcp/voice_commentary.py` (321 lignes) ⚠️

- Requiert `VOICE_1_ELEVENLABS_API` — clé **401 Unauthorized** (R050)
- Mode dégradé textuel actif — voix désactivée, pipeline non bloqué

### `guardian_mcp/artcb_bridge.py` (186 lignes) ⚠️

- `ARTCB_API_URL=http://91.134.45.8:8000` (N4, Doppler `artcb-blockchain/dev`)
- N2/N3/N4 tous **UNREACHABLE** au moment de l'audit
- `is_available()` retourne `False` → `/api/artcb/status` retourne `{"available": false}`
- ForensicPanel affiche "OFFLINE" (correct, pas un bug)

### `guardian_api/kyc_stream.py` (326 lignes) ✅

Pipeline SSE KYC complet fonctionnel :
- `kyc_stream_generator()` — 7 événements SSE + PDF base64
- `_build_pdf()` + `_minimal_pdf()` — génération PDF avec fallback
- Testé live : 7/7 événements reçus sur backend direct

### `guardian_api/app.py` (588 lignes) ✅

Tous les endpoints opérationnels sauf LLM (désactivé par `GUARDIAN_ATTACKER_ENABLED`).

---

## 4. Frontend — diagnostic complet

### Onglets visibles au jury

| Onglet | État | Note |
|---|---|---|
| 🏦 Pitch Jury | ✅ Opérationnel | Présentation complète, architecture, KYC steps |
| 🔍 KYC Forensic | 🚫 Masqué (`hidden:true`) | Code intact, réactivable en 1 ligne |
| ⚡ Scénarios Guardian | ✅ Opérationnel | 4 scénarios, 4 agents, chaîne R0 vérifiée |

### Composants React

| Composant | État | Note |
|---|---|---|
| `App.tsx` | ✅ | Routing, health check, HUD graph, SSE listener |
| `PitchPage.tsx` | ✅ | Hero, architecture, KYC scenario, stats, CTA |
| `AgentFlow.tsx` | ✅ | 4 agents animés, trace d'exécution |
| `ForensicPanel.tsx` | ✅ | Indicateurs phase, ARTCB MCP status |
| `LiveGuardianGraph.tsx` | ✅ | SVG transparent, sémantique corrigée |
| `KycPanel.tsx` | ⚠️ Masqué | SSE fonctionnel côté backend, panel caché |
| `ExecutionGraphOverlay.tsx` | ✅ | Modal graphe, lazy-loaded |
| `SecurityResults.tsx` | ✅ | Décisions Guardian, verdicts |
| `ReplayResults.tsx` | ✅ | Replay R0/R1, tamper detection |
| `OrchestrationProof.tsx` | ✅ | IDs agents, artefacts, propagation |
| `EventTimeline.tsx` | ✅ | Timeline événements Guardian |

### Accessibilité

| Défaut | Statut |
|---|---|
| `text-slate-500/600` (25 instances) | ✅ Tous corrigés → `text-slate-400` |
| `lang="en"` → `lang="fr"` | ✅ Corrigé |
| Header mobile overflow 375px | ✅ Corrigé |
| Form labels inline `#475569` | ✅ Corrigés → `#94a3b8` |
| Navigation clavier / focus rings | ⚠️ Non audité |
| ARIA live regions SSE | ⚠️ Non ajouté |

---

## 5. Secrets Doppler — état

| Projet | Secret | État |
|---|---|---|
| `artcb-terminator/dev` | `GITHUB_API_KEY` | ✅ Valide |
| `artcb-terminator/dev` | `AVA_API_KEY` | ✅ Présent |
| `aws/dev` | `AWS_ACCESS_KEY_ID` (STS) | ❌ **Expiré** |
| `aws/dev` | `OPENAI_API_KEY` | ❌ Quota $0 épuisé |
| `aws/dev` | `VOICE_1_ELEVENLABS_API` | ❌ 401 Unauthorized |
| `artcb-blockchain/dev` | `ARTCB_API_URL=http://91.134.45.8:8000` | ✅ Configuré (N4 offline) |

---

## 6. Blockchain ARTCB

| Nœud | IP | État audit |
|---|---|---|
| N2 | `151.80.107.29` | ❌ Unreachable |
| N3 | `13.38.209.25` | ❌ Unreachable |
| N4 | `91.134.45.8` | ❌ Unreachable |

Dernière hauteur connue : **1142** (R051). PBFT consensus stall depuis ~26 jours.  
Impact sur le démo : nul — Guardian fonctionne en standalone, la blockchain est optionnelle.

---

## 7. Ce qui fonctionne à 100% devant le jury

| Fonctionnalité | Accessible sur `http://35.90.101.61/` |
|---|---|
| Page Pitch Jury complète | ✅ |
| Architecture Guardian visible | ✅ |
| Lancer un scénario (safe-read / prompt-injection / exfiltration / human-approval) | ✅ |
| Décision Guardian BLOCK/ALLOW en temps réel | ✅ |
| Trace 4 agents animés | ✅ |
| Chaîne R0 vérifiée PASS | ✅ |
| Tamper detection FAIL (détection altération) | ✅ |
| Graphe HUD transparent (overlay SVG) | ✅ |
| Panel Forensic Indicators | ✅ |
| Guardian Online badge | ✅ |

## 8. Ce qui ne fonctionne pas

| Fonctionnalité | Cause |
|---|---|
| KYC Forensic panel | Masqué volontairement (R057) — cause réelle: blank page non diagnostiquée |
| Attaque LLM live (Bedrock/OpenAI) | Token STS expiré + quota OpenAI épuisé |
| Voice commentary ElevenLabs | Clé 401 |
| Blockchain ARTCB bridge | Nœuds offline |

---

## 9. Actions prioritaires avant soumission jury

| Priorité | Action | Commande |
|---|---|---|
| **P0** | Renouveler token STS AWS | CloudShell `python3 -c "import os,urllib.request..."` → Doppler `aws/dev` |
| **P1** | Diagnostiquer KYC blank page | Tester `EventSource` dans navigateur, vérifier erreur console |
| **P2** | Ranimer nœuds ARTCB (optionnel) | SSH N4 `systemctl restart artcb` |
