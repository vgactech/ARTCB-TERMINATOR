# R031 — Correction faille résiduelle R030-002 : ordre FAIL/count inversé — 51/51 PASS

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R031 |
| Date | 2026-10-10 |
| Commit de base | `c9e9cf8` (R030) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Correction de la faille résiduelle dans `recover_state_from_jsonl()` identifiée dans le contre-audit R030 |
| Exécution | ✅ `pytest guardian_mcp/ -v` — **51/51 PASS observés dans cette session** |
| Fichiers modifiés | `guardian_mcp/instrumentation.py`, `guardian_mcp/test_instrumentation.py` |

---

## 1. Confirmation du bug avant correction

Le contre-audit R030 avait identifié par inspection statique un chemin potentiel où `recover_state_from_jsonl()` pouvait retourner silencieusement `(0, GENESIS_HASH)` sur un journal non vide mais corrompu. Ce chemin a été **confirmé par exécution locale** avant correction :

```python
# Journal contenant une ligne JSON invalide
p.write_text("NOT_JSON\n")
recover_state_from_jsonl(p)
→ (0, '000...000')   # BUG : retour silencieux au lieu de ValueError
```

### Cause exacte

Dans `recover_state_from_jsonl()`, l'ordre des vérifications était :

```python
result = load_and_verify_jsonl(jsonl_path)
if result.entries_verified == 0:   # ← évalué EN PREMIER
    return 0, GENESIS_HASH          # ← court-circuit silencieux
if not result.is_pass():           # ← jamais atteint si entries_verified == 0
    raise ValueError(...)
```

Quand la première ligne est du JSON invalide, `load_and_verify_jsonl()` retourne `entries_verified=0` avec `verdict="FAIL"`. La branche `entries_verified == 0` était évaluée avant le verdict, masquant le FAIL.

---

## 2. Correction — inversion de l'ordre des deux vérifications

```python
# Après correction
result = load_and_verify_jsonl(jsonl_path)
if not result.is_pass():           # ← verdict EN PREMIER
    raise ValueError(...)
if result.entries_verified == 0:   # ← count ENSUITE (uniquement si PASS)
    return 0, GENESIS_HASH
```

Un seul déplacement de bloc. Le verdict est désormais toujours vérifié avant le compte d'entrées. Un FAIL avec `entries_verified=0` lève maintenant `ValueError` comme attendu.

---

## 3. Comportements vérifiés après correction

| Scénario | Comportement avant | Comportement après |
|---|---|---|
| Première ligne JSON invalide | `(0, GENESIS_HASH)` silencieux | `ValueError` avec mention R030-002 |
| Journal vide légitime (PASS, 0 entrées) | `(0, GENESIS_HASH)` | `(0, GENESIS_HASH)` — inchangé |
| Fichier absent | `(0, GENESIS_HASH)` | `(0, GENESIS_HASH)` — inchangé |
| Journal corrompu (hash altéré, FAIL) | `ValueError` | `ValueError` — inchangé |
| Journal valide | State correct | State correct — inchangé |

---

## 4. Tests ajoutés

| Test | Vérification |
|---|---|
| `test_r030_002_invalid_first_line_raises_not_silent` | JSON invalide ligne 1 → `ValueError` avec mention R030-002 |
| `test_r030_002_invalid_first_line_load_verify_returns_fail` | `load_and_verify_jsonl` retourne FAIL avec `entries_verified=0` sur JSON invalide |

---

## 5. Score

```
51 passed in 0.42s
```

| Suite | Tests | PASS |
|---|---|---|
| Démo 4 agents | 13 | 13 |
| C-07 instrumentation (dont R026/R028/R030) | 36 | 36 |
| **Nouveaux R031** | **2** | **2** |
| **Total Python observé** | **51** | **51** |

---

## 6. État des anomalies après R031

| ID | Constat | État |
|---|---|---|
| R030-002 faille résiduelle (ordre FAIL/count) | ✅ **FERMÉ** |
| R028-C — gap exécution/écriture | **OUVERT P2** — documenté dans limits |
| Verrous multiprocessus | **OUVERT P2** |
| L-019-002 R2/R3 | **OUVERT P2** |

---

## 7. Contrôle de périmètre

- Fichiers applicatifs modifiés : `instrumentation.py`, `test_instrumentation.py`.
- Rapport : R031 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Projet VLC&ARTCB : aucune migration.
- Logs bruts : aucun ajouté.
