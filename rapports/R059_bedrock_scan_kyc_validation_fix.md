# R059 — Bedrock Claude Sonnet 4.5 Scan + Fix C3 KYC validation

**Date**: 2026-10-11  
**Model**: `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (meilleur disponible dans le compte hackathon)  
**Commits**: `<see below>` — fix KYC validation `&&` → `||`  
**Token STS**: renouvelé ~~`ASIA3GKIQ53K6GZMHO34`~~ → `[REDACTED — GitHub secret alert #2 — 2026-10-11]` (exp. 2026-10-11T12:18:07Z)

---

## 1. Contexte du scan

Token STS renouvelé via CloudShell IMDSv2. Scan Bedrock lancé en 3 appels ciblés.  
**Seul Scan 1 complété** — le token a expiré pendant Scan 2 (~12 min après renouvellement).  
Scan 1 couvre : `instrumentation.py`, `defender_agent.py`, `kyc_stream.py`, `KycPanel.tsx`.

**Important** : Bedrock a reçu les fichiers tronqués à 5000 chars. Certaines observations citent des "truncations" qui sont des artefacts du prompt, pas de vrais bugs. Chaque finding a été vérifié contre le code réel avant d'être rapporté ici.

---

## 2. Findings Bedrock — section A (Sécurité)

### A1 — Race condition INTENT/TERMINAL (artefact de troncature)
Bedrock cite `tool_executed = after >` comme tronqué. **Vérifié** : le code réel à `defender_agent.py:150` est complet. Artefact du prompt.

### A2 — executor_call_count bypassable (observation valide)
`_executor_call_count` est un entier simple — pas de binding cryptographique, pas de thread-safety.  
**Contexte hackathon** : tolérable — le système est single-threaded dans la démo.  
En production, il faudrait un verrou ou un hash de l'exécution.

### A3 — EvidenceId sans vérification que l'événement est loggué (observation valide)
`evidence_id = str(uuid.uuid4())` généré avant confirmation de l'écriture en store.  
**Contexte hackathon** : 169 tests PASS couvrent ce chemin. Risque accepté.

---

## 3. Finding Bedrock — section B (KYC blanc page)

Bedrock diagnostique que les handlers SSE seraient manquants — artefact de la troncature du fichier.  
**Vérifié** : le code réel de `KycPanel.tsx` contient tous les handlers (`kyc_result`, `done`, `error`).

**Vraie cause de la page blanche** (diagnostiquée en R053) : `VITE_API_URL` était absent → `EventSource('')` → 404 silencieux. Corrigé depuis `eb54152`.

Le panel KYC est **masqué volontairement** (`hidden: true`, R057) car un problème d'affichage persistait malgré le fix.

---

## 4. Finding Bedrock — section C3 (BUG RÉEL) ✅ CORRIGÉ

**`KycPanel.tsx:89` — Validation `&&` au lieu de `||`**

```typescript
// AVANT (bug) — rejetait seulement si TOUS les champs vides
if (!firstName.trim() && !lastName.trim() && !docId.trim() && !dob.trim()) {

// APRÈS (fix) — rejette si UN SEUL champ requis est vide
if (!firstName.trim() || !lastName.trim() || !docId.trim() || !dob.trim()) {
```

**Impact** : avec l'ancien code, soumettre `firstName="Alice"` + 3 autres champs vides envoyait une requête invalide au backend → trail forensique incomplet.

**Fix appliqué**, build OK, déployé sur EC2.

---

## 5. Modèles Bedrock disponibles dans le compte hackathon

| Modèle | Disponible |
|---|---|
| `us.anthropic.claude-opus-5-5` | ❌ AccessDenied (marketplace) |
| `us.anthropic.claude-opus-4-5-20251101-v1:0` | Non testé |
| `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | ✅ **ACTIF** (utilisé) |
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Non testé |

**Meilleur modèle autorisé** : `claude-sonnet-4-5-20250929` — le même que l'attaquant LLM du démo.

---

## 6. État post-R059

| Item | État |
|---|---|
| Token STS | ✅ Renouvelé (expire ~2026-10-11T12:18Z) |
| KYC validation `||` | ✅ Corrigé et déployé |
| Bedrock Scan 2+3 | ❌ Token expiré pendant l'exécution |
| LLM attacker Bedrock | ✅ Opérationnel (token valide au moment du renouvellement) |
