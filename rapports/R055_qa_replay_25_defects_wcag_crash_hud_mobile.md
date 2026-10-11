# R055 — QA Replay: 25 defects resolved — WCAG AA, lang=fr, KYC crash, HUD Graph, mobile header

**Date**: 2026-10-11  
**Commit**: `d7f04c4`  
**Branch**: `feat/artcb-forensic-integration`  
**Bundle deployed**: `index-CSDRKQni.js` (replaces `index-CKMoyo0V.js`)  
**QA Replay recordings**: #912dd46a · #a5a1337e · #571a3034 · #aa69e4ae · #106788b6 · #2341ca11 · #95631434 · #eead1b5c

---

## Defect families and fixes

### Family 1 — WCAG AA contrast: `text-slate-500` on dark surface (4.16:1 → ~6.7:1)

**Affected elements** (12 instances across 8 recordings):  
Tab buttons, Stat sub-labels, Step details, architecture section labels, "Sans/Avec Guardian" labels, KYC scenario steps, "Cas d'usage", "Réglementations couvertes", CTA tags, ForensicPanel subtitle, ARTCB MCP Bridge label, "Guardian decision:" label, scenario card descriptions, metric labels, "Chemin d'orchestration" text, AGENT A/B/C/D badges, "100% PASS"/"Guardian Core"/"N2/N3/N4" stat sub-labels, "Sans Guardian"/"Avec Guardian" section headers.

**Fix**: `text-slate-500` → `text-slate-400` in all occurrences across:
- [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- [`frontend/src/components/PitchPage.tsx`](../frontend/src/components/PitchPage.tsx)
- [`frontend/src/components/ForensicPanel.tsx`](../frontend/src/components/ForensicPanel.tsx)
- [`frontend/src/components/AgentFlow.tsx`](../frontend/src/components/AgentFlow.tsx)
- [`frontend/src/components/SecurityResults.tsx`](../frontend/src/components/SecurityResults.tsx)
- [`frontend/src/components/ReplayResults.tsx`](../frontend/src/components/ReplayResults.tsx)
- [`frontend/src/components/OrchestrationProof.tsx`](../frontend/src/components/OrchestrationProof.tsx)
- [`frontend/src/components/EventTimeline.tsx`](../frontend/src/components/EventTimeline.tsx)
- [`frontend/src/components/LiveGuardianGraph.tsx`](../frontend/src/components/LiveGuardianGraph.tsx)

---

### Family 2 — WCAG AA contrast: `text-slate-600` on dark surface (2.14:1–2.62:1 → ~6.7:1)

**Affected elements**: "4 DISPONIBLES" counter (2.27:1), "→" arrows in architecture diagram (2.62:1), "OFFLINE" badge in ForensicPanel, footer text (2.14:1), "EXPECTED FAILURE" label in ReplayResults.

**Fix**: `text-slate-600` → `text-slate-400` across same files.

---

### Family 3 — WCAG AA contrast: KYC form labels inline `#475569` (2.45:1 → ~6.7:1)

**Affected elements**: "PRÉNOM", "NOM", "N° DOCUMENT", "DATE NAISSANCE" field labels — inline style `color: #475569`.

**Fix** in [`frontend/src/components/KycPanel.tsx`](../frontend/src/components/KycPanel.tsx):  
`color: '#475569'` → `color: '#94a3b8'` (slate-400)

---

### Family 4 — WCAG AA contrast: KYC stat box labels `#64748b` (3.83–3.91:1 → ~6.7:1)

**Affected elements**: "Attaques", "Bloquées", "Taux" — inline style `color: '#64748b'`.

**Fix** in `KycPanel.tsx`: `color: '#64748b'` → `color: '#94a3b8'`

---

### Family 5 — WCAG 3.1.1 Language of Page

**Defect**: `<html lang="en">` while all content is French.

**Fix** in [`frontend/index.html`](../frontend/index.html): `lang="en"` → `lang="fr"`

---

### Bug 6 — KYC crash on empty fields (`crypto.randomUUID TypeError`)

**Defect**: Submitting with all four fields empty threw an uncaught TypeError and unmounted the entire app root, leaving a blank page.

**Fix** in `KycPanel.tsx` — validation guard before `runKyc()`:
```typescript
if (!firstName.trim() && !lastName.trim() && !docId.trim() && !dob.trim()) {
  addEntry({ type: 'error', label: 'Formulaire vide', detail: '…', status: 'fail' })
  return  // ← console stays rendered, no crash
}
```

---

### Bug 7 — HUD Graph button shows nothing when clicked

**Defect**: `showHudGraph && (kycRunning || kycEvents.length > 0)` — the graph only appeared after starting a KYC run. Clicking the button on the Pitch tab had no visible effect.

**Fix** in `App.tsx`: removed the `kycRunning || kycEvents.length > 0` gate.  
The graph now renders immediately when toggled, showing all 4 nodes in `idle` state — giving the jury an instant visual of the architecture before any run.

---

### Bug 8 — Header clips "Guardian Online" at 375px viewport

**Defect**: Right-side header group overflowed by 17px on 375px mobile, cutting off the status pill.

**Fix** in `App.tsx`:
- Left group: `min-w-0 shrink`, icon `shrink-0`, title/subtitle `truncate`
- Right group: `shrink-0`, reduced `gap-3→gap-2`, `px-5→px-3`
- Status pill: `whitespace-nowrap`, abbreviated text on `<sm` (`hidden sm:inline` / `sm:hidden`)

---

## Production verification

| Check | Result |
|---|---|
| `lang="fr"` in served HTML | ✅ confirmed |
| New bundle deployed (`CSDRKQni`) | ✅ replaces `CKMoyo0V` |
| `text-slate-400 hover:text-slate-200` in bundle | ✅ found |
| `AGENT A/B/C/D` badge `text-slate-400` | ✅ found |
| Crash guard "Formulaire vide" | ✅ found in bundle |
| "GUARDIAN GRAPH" (HUD always visible) | ✅ found |
| HTTP 200 on `/` and `/api/health` | ✅ |
| Build TypeScript | ✅ zero errors, built in 20.67s |
