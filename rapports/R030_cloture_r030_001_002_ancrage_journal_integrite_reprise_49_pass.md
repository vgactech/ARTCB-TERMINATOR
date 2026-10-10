# R030 — Clôture R030-001 et R030-002 : ancrage journal vide, intégrité avant reprise — 49/49 PASS

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R030 |
| Date | 2026-10-10 |
| Commit de base | `6ec575c` (R029) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Fermeture des anomalies R030-001 et R030-002 identifiées dans le contre-audit R029 |
| Exécution | ✅ `pytest guardian_mcp/ -v` — **49/49 PASS observés dans cette session** |
| Fichiers modifiés | `guardian_mcp/instrumentation.py`, `guardian_mcp/test_instrumentation.py` |

---

## 1. Résumé exécutif

| Anomalie | Priorité | Confirmation | État après |
|---|---|---|---|
| R030-001 — journal vide + `expected_last_hash` → PASS | P1 | ✅ Confirmée par exécution locale | ✅ Garde ajoutée + 2 tests |
| R030-002 — `recover_state_from_jsonl` accepte journal corrompu | P1 | ✅ Confirmée par exécution locale | ✅ Vérification complète avant reprise + 2 tests |

**Score total Python observé : 49/49 PASS** (45 existants + 4 nouveaux).

---

## 2. Confirmation des anomalies avant correction

Les deux anomalies ont été confirmées par exécution directe avant correction :

```
# R030-001 : journal vide + expected_last_hash seulement
load_and_verify_jsonl(p, expected_last_hash='a'*64)
→ verdict=PASS, entries=0   ← BUG CONFIRMÉ

# R030-002 : recover_state_from_jsonl sur journal corrompu (hash altéré)
recover_state_from_jsonl(p)
→ last_seq=3, last_hash=1c57c5d7…  ← retournait silencieusement un état invalide
  load_and_verify_jsonl(p) → verdict=FAIL, mismatches=2
```

---

## 3. R030-001 — Journal vide avec `expected_last_hash`

### Correction

Garde ajoutée dans `load_and_verify_jsonl()` **avant** la boucle de vérification :

```python
# R030-001 : un expected_last_hash non vide sur un journal vide doit aussi FAIL.
if not entries and expected_last_hash:
    return ChainVerificationResult(
        entries_verified=0,
        verdict="FAIL",
        mismatches=[{"error": "Journal vide mais expected_last_hash fourni …", "field": "entries_count"}],
        limits=["R030-001 : journal vide détecté via expected_last_hash"],
    )
```

### Comportement documenté

Un journal vide **sans** ancrage (`expected_count=None`, `expected_last_hash=None`) retourne PASS avec 0 entrées — c'est un journal légitime vide. La limite est documentée dans `limits`. Ce comportement est testé explicitement (`test_r030_001_empty_journal_no_anchor_returns_pass`).

Un journal vide **avec** ancrage externe fourni retourne FAIL — c'est une troncature détectée.

### Tests ajoutés

| Test | Vérification |
|---|---|
| `test_r030_001_empty_journal_with_only_last_hash_fails` | `expected_last_hash` seul sur journal vide → FAIL |
| `test_r030_001_empty_journal_no_anchor_returns_pass` | Aucun ancrage sur journal vide → PASS documenté comme limite |

---

## 4. R030-002 — `recover_state_from_jsonl` vérifie l'intégrité avant reprise

### Correction

`recover_state_from_jsonl()` appelle maintenant `load_and_verify_jsonl()` en premier :

```python
# Vérification complète avant d'extraire l'état
result = load_and_verify_jsonl(jsonl_path)
if result.entries_verified == 0:
    return 0, GENESIS_HASH
if not result.is_pass():
    raise ValueError(
        f"Reprise refusée : le journal contient {len(result.mismatches)} incohérence(s) — R030-002."
    )
```

La reprise est refusée avec `ValueError` si le journal contient des hashes invalides, des séquences non monotones ou un chaînage rompu. L'exception mentionne explicitement `R030-002` et le nombre d'incohérences pour faciliter le diagnostic.

### Tests ajoutés

| Test | Vérification |
|---|---|
| `test_r030_002_recover_state_refuses_corrupted_journal` | Hash corrompu → `ValueError` avec mention R030-002 |
| `test_r030_002_recover_state_accepts_valid_journal` | Journal valide → state correct `(seq=3, hash valide)` |

---

## 5. État des anomalies après R030

| ID | Constat | État |
|---|---|---|
| R030-001 — journal vide + expected_last_hash | ✅ **FERMÉ** |
| R030-002 — reprise sans vérification d'intégrité | ✅ **FERMÉ** |
| R028-C — gap exécution/écriture (pattern intent/executed) | **OUVERT P2** — documenté |
| Verrous multiprocessus | **OUVERT P2** |
| L-019-002 R2/R3 | **OUVERT P2** |

---

## 6. Invariants de persistance désormais couverts

| Invariant | Mécanisme | Test |
|---|---|---|
| Écriture durable | `make_file_sink` + `os.fsync()` | `test_r021_005_file_sink_persist_and_reload` |
| Chaînage cryptographique | `previous_event_hash` dans corps canonique | `test_r023_002_parent_hash_chained` |
| Altération détectée | Hash recomputed ≠ stocké | `test_r023_002_tampered_parent_hash_fails` |
| Réordonnancement détecté | Chaînage + monotonie | `test_r023_002_reordering_detected` |
| Journal vide + ancrage | Garde `not entries and expected_last_hash` | `test_r030_001_empty_journal_with_only_last_hash_fails` |
| Troncature via count | `expected_count` | `test_r028_a_empty_journal_with_expected_count_fails` |
| Reprise sans corrompre la chaîne | `recover_state_from_jsonl` + `initial_seq/hash` | `test_r028_b_resume_from_existing_journal` |
| Reprise refusée si journal corrompu | Vérification complète avant reprise | `test_r030_002_recover_state_refuses_corrupted_journal` |

---

## 7. Contrôle de périmètre

- Fichiers applicatifs modifiés : `instrumentation.py`, `test_instrumentation.py`.
- Rapport : R030 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Projet VLC&ARTCB : aucune migration.
- Logs bruts : aucun ajouté.
