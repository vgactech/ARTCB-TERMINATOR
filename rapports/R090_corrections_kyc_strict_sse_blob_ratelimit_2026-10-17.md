# R090 — Corrections KYC validation stricte, SSE spec, Blob URL, rate_limiter

**Date :** 2026-10-17  
**Dépôt :** `vgactech/ARTCB-TERMINATOR`  
**HEAD avant :** `47e1f88` (docs(R089): audit Dependabot)  
**CERTIFIED_100=false** | **unique_human_proven=false** | **Mode DEBUG actif**

---

## Résumé des corrections

| # | Fichier | Problème | Statut |
|---|---------|---------|--------|
| C1 | `guardian_api/kyc_stream.py` | Validation date non calendaire — `31-02`, `9999` → APPROVED 95% | ✅ Corrigé |
| C2 | `guardian_api/kyc_stream.py` | `kyc_validation_check` WARN mais pipeline continue — pas bloquant | ✅ Corrigé |
| C3 | `frontend/src/components/KycPanel.tsx` | `setPdfUrl(URL.createObjectURL(...))` sans révoquer l'ancienne URL | ✅ Corrigé |
| C4 | `frontend/src/components/KycPanel.tsx` | `.trim()` sur `data:` SSE — supprime espaces significatifs (non-conformité §6.3) | ✅ Corrigé |
| C5 | `guardian_api/conftest.py` | Rate_limiter partagé entre tests → 3 FAIL (`slowapi` 6/min) | ✅ Corrigé |
| C6 | `.gitignore` | `logs/` non ignoré — 6 fichiers commités par erreur | ✅ Corrigé |

---

## C1+C2 — `guardian_api/kyc_stream.py`

### Problème

La validation S1b utilisait une vérification superficielle :

```python
# AVANT (ligne 254) — NON CALENDAIRE
dob_plausible = bool(dob and len(dob) == 10 and dob[4] == "-" and dob[7] == "-")
```

- `"2999-02-31"` → `dob_plausible=True` (longueur OK, `-` aux bons endroits)
- `"1900-13-01"` → `dob_plausible=True` (mois 13 non détecté)
- Résultat : `validation_status="WARN"` mais le pipeline continuait → APPROVED 95%

### Correction

```python
# APRÈS (R090) — CALENDAIRE STRICTE
doc_format_ok = bool(doc_id and doc_id.strip() and len(doc_id.strip()) >= 6)

dob_ok = False
dob_fail_reason = ""
if not dob or not dob.strip():
    dob_fail_reason = "dob is empty or blank"
else:
    try:
        parsed_dob = datetime.strptime(dob.strip(), "%Y-%m-%d")
        year = parsed_dob.year
        if year < 1900 or year > 2100:
            dob_fail_reason = f"dob year {year} out of plausible range [1900-2100]"
        else:
            dob_ok = True
    except ValueError as exc:
        dob_fail_reason = f"dob not a valid calendar date: {exc}"

validation_status = "PASS" if (doc_format_ok and dob_ok) else "FAIL"

# R090 — tout FAIL bloque le pipeline immédiatement
if validation_status == "FAIL":
    yield _sse("kyc_result", {"verdict": "REJECTED", "score": 0, ...})
    yield _sse("done", {"pdf_b64": None})
    return
```

**Comportement post-correction :**

| Entrée | Résultat avant | Résultat après |
|--------|---------------|----------------|
| `1990-05-14` | PASS | PASS ✅ |
| `2999-02-31` | WARN → pipeline continue → APPROVED | FAIL → REJECTED ✅ |
| `1900-02-31` | WARN → pipeline continue → APPROVED | FAIL → REJECTED ✅ |
| `not-a-date` | WARN → pipeline continue → APPROVED | FAIL → REJECTED ✅ |
| `` (vide) | WARN → pipeline continue → APPROVED | FAIL → REJECTED ✅ |
| `2026-13-01` | WARN (mois 13 non détecté) | FAIL → REJECTED ✅ |

---

## C3 — `frontend/src/components/KycPanel.tsx` — Blob URL revoke

### Problème

```typescript
// AVANT (ligne 200) — fuite mémoire si runKyc() appelé N fois
setPdfUrl(URL.createObjectURL(blob))
```

L'ancienne URL n'était pas révoquée avant d'en créer une nouvelle.

### Correction

```typescript
// APRÈS (R090)
setPdfUrl(prev => { if (prev) URL.revokeObjectURL(prev); return URL.createObjectURL(blob) })
```

La révocation se fait **dans la même mise à jour de state**, garantissant l'ordre même en mode Strict.

---

## C4 — `frontend/src/components/KycPanel.tsx` — SSE `data:` sans `.trim()`

### Problème

```typescript
// AVANT (ligne 229) — non-conforme SSE §6.3
curData = curData ? curData + '\n' + line.slice(5).trim() : line.slice(5).trim()
```

`.trim()` supprime les espaces significatifs en début ET en fin de valeur JSON.

### Correction

```typescript
// APRÈS (R090) — spec SSE §6.3 : UN seul espace optionnel après 'data:'
const raw = line.slice(5)
const dataValue = raw.startsWith(' ') ? raw.slice(1) : raw
curData = curData ? curData + '\n' + dataValue : dataValue
```

---

## C5 — `guardian_api/conftest.py` — rate_limiter autouse

### Problème

`slowapi` maintient un compteur en mémoire par clé (IP `testclient`).  
Les tests 780, 819, 876 dépassaient la limite 6/min car les tests précédents avaient consommé le quota.

```
FAILED test_stream_route_speed_clamping        — assert 429 == 200
FAILED test_stream_route_isolation_guardian_before_voice
FAILED test_stream_done_event_has_chain_scope
```

### Correction

Nouveau fichier `guardian_api/conftest.py` :

```python
@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    from guardian_api.app import limiter
    limiter.reset()
```

**Résultat :** 182 PASS / 3 FAIL → **185 PASS / 0 FAIL**

---

## C6 — `.gitignore` — `logs/` ignoré + untrack

### Avant

`logs/` n'était pas dans `.gitignore`. 6 fichiers JSON de log avaient été commités par erreur (R083→R089).

### Après

```
# Logs d'exécution — ne jamais committer (R090)
logs/
```

```bash
git rm --cached logs/ -r  # 6 fichiers sortis du suivi
```

---

## Résultats des tests

```
185 passed in 3.59s
```

**Log JSON :** `logs/20261017_R090_corrections_kyc_sse_ratelimit.json`

---

## Fichiers modifiés

| Fichier | Type | Action |
|---------|------|--------|
| `guardian_api/kyc_stream.py` | Python | Validation calendaire + bloc pipeline |
| `frontend/src/components/KycPanel.tsx` | TypeScript | Blob URL revoke + SSE spec §6.3 |
| `guardian_api/conftest.py` | Python | CRÉÉ — fixture autouse reset_rate_limiter |
| `.gitignore` | Config | Ajout `logs/` |

---

*CERTIFIED_100=false — unique_human_proven=false — Mode DEBUG actif*
