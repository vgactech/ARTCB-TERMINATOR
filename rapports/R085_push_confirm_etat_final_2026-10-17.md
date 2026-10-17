# R085 — Confirmation push R084 + état final session

**Date :** 2026-10-17T14:30:00Z  
**Commit R084 :** `5cd85cf`  
**Push :** `88f1029..5cd85cf HEAD -> main` ✅  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**  
**Dépôt :** `vgactech/ARTCB-TERMINATOR` (espace R001–R085 — D-091)

---

## Résumé de la session

Cette session a repris après le push R083 (`88f1029`) et a exécuté l'ensemble des tâches P1 identifiées.

### Travaux réalisés

| Réf | Fichier | Description | Statut |
|-----|---------|-------------|--------|
| C1 | `frontend/src/components/KycPanel.tsx` | PII hors URL : `EventSource` GET → `fetch` POST SSE manuel | ✅ `5cd85cf` |
| C2 | `guardian_api/app.py` | Nouveau endpoint `POST /api/kyc/stream` + `KycStreamBody` (BaseModel) — GET conservé pour compat | ✅ `5cd85cf` |
| C3 | `frontend/src/App.tsx` | Onglet `🔍 KYC Forensic` activé (`hidden: true → false`) | ✅ `5cd85cf` |
| C4 | Documentation | Config OpenRouter/Bob : `OPENAI_BASE_URL=https://openrouter.ai/api/v1` + `OPENAI_API_KEY=<BOB_API_KEY>` | ✅ R084 |

### Findings P1 analysés

| Tâche | Résultat |
|-------|----------|
| `BOOTSTRAP_NODES 151.80.107.29` | Non applicable — ciblait ARTCB principal, pas TERMINATOR |
| Dependabot (1 HIGH, 1 moderate, 1 low) | Confirmé GitHub — accepter les PRs auto depuis l'UI |
| LLM `llm_mode: "openai"` | Documenté — clé absente localement → fallback conservé |
| Audit frontend boutons | Exécuté — seul défaut : onglet KYC masqué (corrigé C3) |

---

## Avant / Après — récapitulatif technique

### `KycPanel.tsx` — ligne 97

**AVANT :**
```typescript
// PII dans l'URL → logs Nginx
const url = `${apiBase}/api/kyc/stream?first_name=${encodeURIComponent(firstName)}&...`
const es = new EventSource(url)
esRef.current = es  // ref: EventSource
```

**APRÈS :**
```typescript
// PII dans le body JSON → invisible dans les logs
const ctrl = new AbortController()
esRef.current = ctrl  // ref: AbortController
const resp = await fetch(`${apiBase}/api/kyc/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
  body: JSON.stringify({ first_name: firstName, last_name: lastName, doc_id: docId, dob }),
  signal: ctrl.signal,
})
// parseur SSE manuel via ReadableStream
```

### `guardian_api/app.py` — lignes 716–741

**AVANT :**
```python
@app.get("/api/kyc/stream")
def kyc_stream(first_name: str = "Alice", ...):  # GET unique
```

**APRÈS :**
```python
class KycStreamBody(BaseModel): ...     # body pour POST

def _kyc_stream_response(...):          # helper partagé

@app.post("/api/kyc/stream")            # préféré depuis R084
@limiter.limit("6/minute")
def kyc_stream_post(request, body: KycStreamBody): ...

@app.get("/api/kyc/stream")             # compat backward — start_guardian.sh
def kyc_stream_get(first_name="Demo", ...): ...
```

### `App.tsx` — ligne 160

**AVANT :**
```typescript
{ id: 'kyc', label: '🔍 KYC Forensic', hidden: true  },
```

**APRÈS :**
```typescript
{ id: 'kyc', label: '🔍 KYC Forensic', hidden: false },
```

---

## Action requise côté utilisateur

**Dependabot** : ouvrir https://github.com/vgactech/ARTCB-TERMINATOR/security/dependabot et accepter les PRs automatiques (1 HIGH npm, 1 moderate, 1 low).

---

## État infra live consolidé (R082 → R085)

| Domaine | État | Commit |
|---------|------|--------|
| DNS `artcb.me → 151.80.107.29` | ✅ propagé | DNS OVH |
| HTTPS frontend public | ✅ | nginx OVH2 |
| SSE 13 events bout-en-bout | ✅ live | `f2e1c85` |
| Rate limit 429 (6 req/min SSE) | ✅ live | `f2e1c85` |
| `llm_mode` dans SSE | ✅ `"fallback"` | `f2e1c85` |
| KYC POST body `/api/demo/start` | ✅ | `f2e1c85` |
| KYC hors URL `start_guardian.sh` | ✅ | `88f1029` |
| KYC hors URL `KycPanel.tsx` | ✅ | `5cd85cf` |
| POST `/api/kyc/stream` backend | ✅ | `5cd85cf` |
| Onglet KYC Forensic visible | ✅ | `5cd85cf` |
| Voice SSE isolation Guardian | ✅ déjà correct | existant |
| SSH `accept-new` | ✅ | `f2e1c85` |
| ElevenLabs `voice_enabled=true` | ✅ | Doppler |
| OVH4 + AWS3 blockchain | ✅ healthy | — |
| Isolation `artcb.me` OVH2 seul | ✅ | DNS + nginx 444 |
| `certified_100=false` | ✅ invariant | — |
| `unique_human_proven=false` | ✅ invariant | — |

---

## Rapports précédents

R065 → R084 — **non modifiés, non écrasés** (règle PROTOCOLE_ARTCB).
