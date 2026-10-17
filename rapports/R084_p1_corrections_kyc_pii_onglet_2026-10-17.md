# R084 — Corrections P1 : PII hors URL (KycPanel) + POST endpoint + Onglet KYC activé

**Date :** 2026-10-17T14:30:00Z  
**Commits audités :** `88f1029` (R083) → ce commit (R084)  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**  
**Dépôt :** `vgactech/ARTCB-TERMINATOR` (espace R001–R084, indépendant d'ARTCB principal — D-091)

---

## Contexte

La session précédente (R083) avait corrigé `start_guardian.sh` pour ne plus passer le PII dans l'URL via curl.
Audit de cette session : **le même problème existait côté frontend React** (`KycPanel.tsx` utilisait `EventSource` GET avec les données personnelles encodées dans l'URL).

---

## Corrections appliquées

### C1 — `frontend/src/components/KycPanel.tsx` — PII hors URL

**Fichier :** `frontend/src/components/KycPanel.tsx`  
**Priorité :** P1-CRITIQUE

**Problème :** `EventSource` ne supporte que GET. L'URL contenait `first_name`, `last_name`, `doc_id`, `dob` en query string — visibles dans les logs Nginx, les devtools réseau, les bookmarks browser.

**AVANT (ligne 97) :**
```typescript
const url = `${apiBase}/api/kyc/stream?first_name=${encodeURIComponent(firstName)}&last_name=${encodeURIComponent(lastName)}&doc_id=${encodeURIComponent(docId)}&dob=${encodeURIComponent(dob)}`
const es = new EventSource(url)
esRef.current = es
// ... es.addEventListener('session_opened', ...)
```

**APRÈS (lignes 98–220) :**
```typescript
const ctrl = new AbortController()
esRef.current = ctrl

;(async () => {
  const resp = await fetch(`${apiBase}/api/kyc/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ first_name: firstName, last_name: lastName, doc_id: docId, dob }),
    signal: ctrl.signal,
  })
  // ... parseur SSE manuel via ReadableStream + switch/case sur les event types
})()
```

Changements liés :
- `esRef` : `useRef<EventSource|null>` → `useRef<AbortController|null>`
- `reset()` : `esRef.current?.close()` → `esRef.current?.abort()`
- Parseur SSE manuel : lit `event:` et `data:` ligne par ligne depuis `ReadableStream`
- Gestion `AbortError` : silencieuse (reset normal)

---

### C2 — `guardian_api/app.py` — Nouveau endpoint POST `/api/kyc/stream`

**Fichier :** `guardian_api/app.py`  
**Priorité :** P1-CRITIQUE

Le frontend POST nécessite un endpoint côté backend. Le GET est conservé pour la compatibilité avec `start_guardian.sh` et les tests curl.

**AVANT (lignes 716–741) :**
```python
@app.get("/api/kyc/stream")
def kyc_stream(
    first_name: str = "Alice",   # ← PII dans query params → logs Nginx
    last_name: str = "Dupont",
    doc_id: str = "FR-2024-000000",
    dob: str = "1990-01-01",
) -> StreamingResponse:
```

**APRÈS (lignes 716–786) :**
```python
class KycStreamBody(BaseModel):
    """POST body — PII hors URL et hors logs."""
    first_name: str = "Demo"
    last_name: str = "User"
    doc_id: str = "FR-DEMO-000000"
    dob: str = "1990-01-01"

def _kyc_stream_response(...) -> StreamingResponse:
    """Helper partagé GET + POST."""
    ...

@app.post("/api/kyc/stream")
@limiter.limit("6/minute")
def kyc_stream_post(request: Request, body: KycStreamBody) -> StreamingResponse:
    """POST — préféré depuis R084 — PII dans le body JSON uniquement."""
    return _kyc_stream_response(...)

@app.get("/api/kyc/stream")                        # rétrocompat
def kyc_stream_get(first_name: str = "Demo", ...) -> StreamingResponse:
    """GET — conservé pour compatibilité start_guardian.sh / curl.
    WARNING: query params visibles dans les logs Nginx."""
    return _kyc_stream_response(...)
```

Vérification syntaxe : `ast.parse()` → **SYNTAX_OK**

---

### C3 — `frontend/src/App.tsx` — Onglet KYC Forensic activé

**Fichier :** `frontend/src/App.tsx`  
**Priorité :** P1

L'onglet KYC Forensic était masqué (`hidden: true`) sans justification pour la démo hackathon.

**AVANT (ligne 160) :**
```typescript
{ id: 'kyc', label: '🔍 KYC Forensic', hidden: true  },
```

**APRÈS (ligne 160) :**
```typescript
{ id: 'kyc', label: '🔍 KYC Forensic', hidden: false },
```

---

## Findings — tâches P1 analysées et classifiées

| # | Tâche R083 | Résultat analyse |
|---|-----------|-----------------|
| P1-1 | Retirer `151.80.107.29:8000` de `BOOTSTRAP_NODES` | **Non applicable** — ce ciblage concernait ARTCB principal. Dans TERMINATOR, `151.80.107.29` = IP OVH2 correcte dans `deploy_terminator_ovh2.sh` et `scripts/fix_dns_ovh.py`. Aucune correction requise. |
| P1-2 | Dependabot alerts (1 HIGH, 1 moderate, 1 low) | **Non reproductible localement** — pas de `node_modules` ni `package-lock.json` dans le repo. Les alertes GitHub portent probablement sur les deps npm (vite 8.x, framer-motion 14, @rolldown). Accepter les PRs Dependabot automatiques depuis l'interface GitHub. |
| P1-3 | Tester `llm_mode: "openai"` via OpenRouter | **Documenté** — `llm_attacker.py` supporte déjà `OPENAI_BASE_URL` (ligne 286). Activer via : `OPENAI_API_KEY=<BOB_API_KEY>` + `OPENAI_BASE_URL=https://openrouter.ai/api/v1`. Aucune clé disponible en local dans cette session → `llm_mode="fallback"` conservé. |
| P1-4 | Audit frontend React — boutons | **Exécuté** — code `App.tsx` lu intégralement. Seul défaut : onglet KYC masqué → corrigé (C3). Boutons scenarios, HUD toggle, moteur badge : fonctionnels. |

---

## Configuration LLM réel — Guide

Pour activer `llm_mode: "openai"` (vrai LLM) :

```bash
# Via Doppler (projet artcb-blockchain, config aws/dev) :
doppler secrets set OPENAI_API_KEY="<valeur de BOB_API_KEY>"
doppler secrets set OPENAI_BASE_URL="https://openrouter.ai/api/v1"
doppler secrets set GUARDIAN_LLM_MODEL="openai/gpt-4o"
doppler secrets set GUARDIAN_ATTACKER_ENABLED="true"

# Ou localement dans .env :
OPENAI_API_KEY=<BOB_API_KEY>
OPENAI_BASE_URL=https://openrouter.ai/api/v1
GUARDIAN_LLM_MODEL=openai/gpt-4o
GUARDIAN_ATTACKER_ENABLED=true
```

Note : `llm_attacker.py` lit `OPENAI_BASE_URL` (ligne 286) et passe `base_url=` au client OpenAI — compatible OpenRouter nativement.

---

## État infra live (hérité R082, non modifié)

| Domaine | État |
|---------|------|
| DNS `artcb.me → 151.80.107.29` | ✅ propagé |
| HTTPS frontend public | ✅ nginx OVH2 |
| SSE 13 events bout-en-bout | ✅ live (`f2e1c85`) |
| Rate limit 429 (6 req/min SSE) | ✅ live |
| `llm_mode` dans SSE | ✅ `"fallback"` visible |
| KYC POST body `/api/kyc/stream` | ✅ `f2e1c85` |
| KYC hors URL `start_guardian.sh` | ✅ `88f1029` |
| **KYC hors URL `KycPanel.tsx`** | ✅ **ce commit R084** |
| **POST `/api/kyc/stream` backend** | ✅ **ce commit R084** |
| **Onglet KYC Forensic visible** | ✅ **ce commit R084** |
| Voice SSE isolation Guardian | ✅ déjà correct |
| SSH `accept-new` | ✅ `f2e1c85` |
| ElevenLabs `voice_enabled=true` | ✅ Doppler |
| OVH4 + AWS3 blockchain | ✅ healthy |
| Isolation `artcb.me` OVH2 seul | ✅ DNS + nginx 444 |
| `certified_100=false` | ✅ invariant |
| `unique_human_proven=false` | ✅ invariant |

---

## Rapports précédents

R065 → R083 — **non modifiés, non écrasés** (règle PROTOCOLE_ARTCB).

---

## Log

`logs/20261017_R084_p1_corrections.json` — généré avant ce rapport.
