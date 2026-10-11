# R057 — Graph semantic fix + KYC tab hidden

**Date**: 2026-10-11  
**Commits**: `2d7d949` (graph semantic) · `c62b32f` (KYC tab hidden)  
**Branch**: `feat/artcb-forensic-integration`  
**Bundle deployed**: `index-C-Cr95KV.js`

---

## 1. Fix — buildNodes semantic anomaly (R056 Anomaly A)

### Root cause

In `buildNodes()` ([`LiveGuardianGraph.tsx`](../frontend/src/components/LiveGuardianGraph.tsx)), the `attack_generated` SSE event was setting `attacker = 'blocked'`. This is forensically incorrect: a generation event carries no proof of blocking. The `blocked` state was being displayed before any Guardian decision had occurred.

### What each state must mean

| State | Meaning | Source event |
|---|---|---|
| `idle` | Agent not yet involved | — |
| `active` | Agent acting, outcome unknown | `session_opened` / `attack_generated` / `propagation` |
| `blocked` | Action rejected by Guardian | `guardian_decision { decision: 'BLOCK' }` |
| `done` | Action completed (allowed or verified) | `guardian_decision { decision: 'ALLOW' }` / `chain_verified` |
| `error` | Abnormal termination | (reserved) |

### Fix applied (commit 2d7d949)

```
attack_generated  → attacker = 'active'   (attempt in progress, not yet decided)
propagation       → attacker = 'done', propagator = 'active'
guardian_decision BLOCK  → defender = 'blocked', attacker = 'blocked'  ← source of truth
guardian_decision ALLOW  → defender = 'done',    attacker = 'done'
guardian_decision other  → defender = 'active'   (ESCALATE)
chain_verified / done    → defender = 'done'
```

Each visual state transition now maps to exactly one authenticated SSE event. No state is inferred from a preceding step.

### Bundle verification (index-C-Cr95KV.js, live on EC2)

Extracted from minified bundle:

```
e==='attack_generated'&&(t.orchestrator='done', t.attacker='active', n.attacker++)
e==='guardian_decision': e.decision==='BLOCK'
  ? (t.defender='blocked', t.attacker='blocked')
  : e.decision==='ALLOW'
  ? (t.defender='done', t.attacker='done')
  : t.defender='active'
```

✅ `attacker='active'` on `attack_generated` — confirmed  
✅ `attacker='blocked'` only on `guardian_decision BLOCK` — confirmed  
✅ Old bug (`attacker='blocked'` on generation) — absent from bundle

---

## 2. Change — KYC Forensic tab hidden

**Reason**: The KYC Forensic panel (`tab === 'kyc'`) produces no visible output in the current production build. Presenting a blank panel to the jury during the hackathon demonstration would be penalising.

**Decision**: Hide the tab from the navigation bar without deleting any code.

**Implementation** (commit c62b32f, [`App.tsx`](../frontend/src/App.tsx)):

```typescript
{ id: 'kyc', label: '🔍 KYC Forensic', hidden: true }
```

The tab array is filtered with `.filter(t => !t.hidden)` before rendering. The `tab === 'kyc'` render branch, the `KycPanel` component, and all KYC state are preserved in full — one line change to re-enable.

**To re-enable**: set `hidden: false` on the `kyc` entry, rebuild, redeploy.

**Bundle verification**: `hidden:!0` (minified `true`) confirmed present in `index-C-Cr95KV.js`. `KYC Forensic` string still present (correct — it is in the filtered-out data, not rendered).

---

## 3. Production state post-R057

| Endpoint | Status |
|---|---|
| `http://35.90.101.61/` | ✅ HTTP 200 |
| `http://35.90.101.61/api/health` | ✅ `{"status":"ok"}` |
| Tabs visible to jury | 🏦 Pitch Jury · ⚡ Scénarios Guardian |
| KYC tab | Hidden (code intact) |
| HUD graph | Transparent SVG overlay, `pointer-events-none` |
| Graph state semantic | Corrected — `blocked` only on authenticated Guardian decision |

---

## 4. Open items (from R056, unchanged)

| Item | Severity |
|---|---|
| Keyboard navigation / focus rings not audited | Medium |
| Dynamic ARIA live regions for SSE timeline | Medium |
| Mobile HUD graph no accessible toggle | Low |
| KYC panel blank — root cause not yet diagnosed | High (deferred) |
