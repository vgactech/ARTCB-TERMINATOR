# R092 — Rejet dates de naissance futures + cycle de vie Blob URL React

**Projet :** ARTCB-TERMINATOR  
**Espace de numérotation :** TERMINATOR (R001–R061+, indépendant de l'espace ARTCB)  
**Date :** 2026-10-17  
**Horodatage log :** 2026-10-17T17:47:35.716842Z  
**CERTIFIED_100=false** | **unique_human_proven=false** | **Mode DEBUG actif**

---

## Résumé exécutif

Ce rapport documente deux corrections appliquées dans le cadre de R092 :

| Fix | Composant | Sévérité | Statut |
|-----|-----------|----------|--------|
| **P1** — Rejet des dates de naissance dans le futur | `guardian_api/kyc_stream.py` | 🔴 P1 — Validation KYC incorrecte | ✅ CORRIGÉ |
| **P2** — Cycle de vie des Blob URLs via `pdfUrlRef` | `frontend/src/components/KycPanel.tsx` | 🟡 P2 — Anti-pattern React / fuite mémoire | ✅ CORRIGÉ |

---

## Résultats pytest

```
80 passed in 8.14s
Platform : darwin — Python 3.11.9 — pytest 9.1.1
```

| Métrique | Valeur |
|----------|--------|
| Total tests | **80** |
| Passed | **80** ✅ |
| Failed | **0** |
| Skipped | **0** |
| Durée | **8.14s** |
| Nouveaux tests R092 | **6** |

### 6 nouveaux tests R092

| Test | Résultat |
|------|----------|
| `test_kyc_stream_dob_future_is_rejected` | ✅ PASS |
| `test_kyc_stream_dob_today_is_rejected` | ✅ PASS |
| `test_kyc_stream_valid_dob_passes_validation` | ✅ PASS |
| `test_kyc_stream_done_event_pdf_b64_absent_on_rejected` | ✅ PASS |
| `test_kyc_stream_done_event_present_for_valid_flow` | ✅ PASS |
| `test_kyc_stream_get_endpoint_also_rejects_future_dob` | ✅ PASS |

---

## P1 — Rejet des dates de naissance dans le futur

**Fichier :** `guardian_api/kyc_stream.py`

### Problème

La validation KYC acceptait des dates de naissance dans le futur (ex. `2029-01-01`). Une date de naissance future est ontologiquement impossible — la personne n'est pas encore née. Le flux SSE renvoyait `validation_status: "PASS"` pour ces cas, produisant des identités KYC invalides.

### Avant (état avant R092)

```python
# guardian_api/kyc_stream.py — état avant R092
# Ligne 20 : pas d'import de date
from datetime import datetime

# Lignes 263–272 : validation sans garde future
try:
    parsed_dob = datetime.strptime(dob.strip(), "%Y-%m-%d")
    year = parsed_dob.year
    if year < 1900 or year > 2100:
        dob_fail_reason = f"dob year {year} out of plausible range [1900-2100]"
    else:
        dob_ok = True   # ← acceptait 2029-01-01, 2035-12-31, etc.
except ValueError as exc:
    dob_fail_reason = f"dob not a valid calendar date: {exc}"
```

### Après (état après R092)

```python
# guardian_api/kyc_stream.py — état après R092
# Ligne 20 : import étendu avec date
from datetime import date, datetime

# Lignes 263–274 : garde future ajoutée (lignes 268–270)
try:
    parsed_dob = datetime.strptime(dob.strip(), "%Y-%m-%d")
    year = parsed_dob.year
    if year < 1900 or year > 2100:
        dob_fail_reason = f"dob year {year} out of plausible range [1900-2100]"
    elif parsed_dob.date() >= date.today():
        # R092 — P1 : reject future birth dates (e.g. 2029-01-01 is not a valid dob)
        dob_fail_reason = f"dob {dob.strip()} is in the future — birth date must be before today"
    else:
        dob_ok = True
except ValueError as exc:
    dob_fail_reason = f"dob not a valid calendar date: {exc}"
```

### Lignes exactes modifiées

| Ligne | Avant | Après |
|-------|-------|-------|
| 20 | `from datetime import datetime` | `from datetime import date, datetime` |
| 268 | `else:` | `elif parsed_dob.date() >= date.today():` |
| 269 | `    dob_ok = True` | `    # R092 — P1 : reject future birth dates` |
| 270 | *(absent)* | `    dob_fail_reason = f"dob {dob.strip()} is in the future — birth date must be before today"` |
| 271 | *(absent)* | `else:` |
| 272 | *(absent)* | `    dob_ok = True` |

### Cas couverts

| Date testée | Comportement attendu | Résultat |
|-------------|---------------------|----------|
| `2029-01-01` (futur) | FAIL — `dob is in the future` | ✅ REJETÉ |
| `{today}` (aujourd'hui) | FAIL — `dob is in the future` | ✅ REJETÉ |
| `1990-06-15` (passé valide) | PASS | ✅ ACCEPTÉ |
| `pdf_b64` sur KYC FAIL | absent de l'événement `done` | ✅ ABSENT |
| flux complet KYC valide | événement `done` présent | ✅ PRÉSENT |
| endpoint GET avec dob future | FAIL | ✅ REJETÉ |

---

## P2 — Cycle de vie des Blob URLs via `pdfUrlRef`

**Fichier :** `frontend/src/components/KycPanel.tsx`

### Problème

`URL.revokeObjectURL()` était appelé à l'intérieur d'un setState updater (anti-pattern React). En mode React StrictMode, les updaters peuvent être exécutés plusieurs fois en développement. Appeler un effet de bord destructif (revoke) dans un updater provoque :

1. **Revoke prématuré** : l'URL peut être révoquée avant que le composant ait fini de la rendre (image/PDF devient inaccessible).
2. **Double-revoke** : en StrictMode, le revoke est appelé deux fois, produisant des erreurs silencieuses.
3. **Fuite mémoire** : à l'unmount du composant, aucun cleanup systématique n'existait.

### Avant (anti-pattern)

```typescript
// KycPanel.tsx — AVANT R092 (anti-pattern)
// Revoke dans un setState updater — FAUX
setPdfUrl(prev => {
  if (prev) URL.revokeObjectURL(prev)  // ← effet de bord dans setState = violation React
  return newUrl
})
```

### Après (pattern corrigé)

```typescript
// KycPanel.tsx — APRÈS R092 (pattern correct)

// 1. Déclaration du ref dédié (ligne 88)
const pdfUrlRef = useRef<string | null>(null)

// 2. Cleanup à l'unmount via useEffect (lignes 97–104)
useEffect(() => {
  return () => {
    if (pdfUrlRef.current) {
      URL.revokeObjectURL(pdfUrlRef.current)
      pdfUrlRef.current = null
    }
  }
}, [])

// 3. Reset de la session — revoke via ref (lignes 119–122)
function reset() {
  esRef.current?.abort()
  // ...
  if (pdfUrlRef.current) {         // ← effet de bord pur, pas dans setState
    URL.revokeObjectURL(pdfUrlRef.current)
    pdfUrlRef.current = null
  }
  setPdfUrl(null)
  // ...
}

// 4. Création d'une nouvelle URL — revoke avant assignation (lignes 218–223)
if (pdfUrlRef.current) {
  URL.revokeObjectURL(pdfUrlRef.current)  // ← revoke de l'ancienne avant création
}
const newUrl = URL.createObjectURL(blob)
pdfUrlRef.current = newUrl               // ← ref toujours synchronisé
setPdfUrl(newUrl)
```

### Sites de modification dans `KycPanel.tsx`

| Ligne | Nature | Description |
|-------|--------|-------------|
| 20–23 | Commentaire en-tête | Documentation R092 P2 |
| 25 | Import | `useRef` ajouté à l'import React |
| 88 | Déclaration | `const pdfUrlRef = useRef<string \| null>(null)` |
| 95–104 | Nouveau `useEffect` | Cleanup revoke à l'unmount |
| 118–122 | Fonction `reset()` | Revoke via ref avant `setPdfUrl(null)` |
| 216–222 | Handler SSE `done` | Revoke ancien + assignation ref + `setPdfUrl(newUrl)` |

---

## Fichiers modifiés

| Fichier | Lignes ajoutées | Lignes supprimées | Nature |
|---------|-----------------|-------------------|--------|
| `guardian_api/kyc_stream.py` | +5 | 0 | Import + garde P1 |
| `frontend/src/components/KycPanel.tsx` | +37 | -9 | Ref + 3 sites revoke P2 |
| `guardian_api/test_app.py` | +221 | 0 | Helper `_parse_sse` + 6 tests R092 |

---

## Log JSON généré

```
logs/20261017_R092_dob_future_blob_url_lifecycle.json
```

Vérifié présent sur disque après exécution ✅

---

## Invariants

| Invariant | Valeur |
|-----------|--------|
| `CERTIFIED_100` | `false` |
| `unique_human_proven` | `false` |
| Mode DEBUG | actif |

---

*Rapport généré automatiquement — R092 — ARTCB-TERMINATOR — 2026-10-17*
