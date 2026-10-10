# R035 — L-019-002 P0+P1 : manifeste de replay, archive R2, replay_r2 sans effets externes

**Commit** : `c9fda79`
**Date** : 2026-10-10
**Tests** : 93/93 PASS (80 `test_instrumentation.py` + 13 `test_demo_scenario.py`)
**Précédent** : R034 — contre-audit R033 + critères L-019-002 R2/R3
**Base** : R033 — 77/77 PASS (intent/terminal, barrière replay, subprocess, IN_DOUBT)

---

## Anomalies traitées

| ID | Priorité | Constat R034 | Statut |
|---|---|---|---|
| L-019-002 P0 | P0 | Préconditions R0/manifeste non vérifiées avant replay | Clos |
| L-019-002 P1 | P1 | Pas de contrat d'archive des réponses d'outils | Clos |
| L-019-002 P1 | P1 | Pas d'implémentation R2 simulé avec barrière sans effets externes | Clos |

---

## L-019-002 P0 — ReplayManifest et vérification des préconditions

### Constat (R034 §3.2)

`replay_r0` Rust vérifiait uniquement les hashes individuels. Les préconditions
d'archive (nombre d'entrées, pointe de chaîne, version de schéma) n'étaient pas
contrôlées. Un replay pouvait démarrer sur un journal tronqué ou incompatible.

### Correction

Ajout dans `instrumentation.py` :

**`ReplayManifest`** — dataclass décrivant les préconditions d'un replay :
- `run_id` : identifiant du run auditeur
- `original_chain_tip` : hash du dernier événement attendu (ancrage externe)
- `expected_count` : nombre d'entrées attendues
- `schema_version` : version de schéma attendue dans chaque événement
- `requested_level` : niveau de replay demandé ("R0" | "R1" | "R2" | "R3")

**`verify_manifest_preconditions(manifest, path)`** — vérifie :
1. Intégrité de la chaîne (`load_and_verify_jsonl` avec `expected_count` + `expected_last_hash`)
2. Cohérence de la `schema_version` entre le manifeste et chaque entrée JSONL

Retourne `ChainVerificationResult`. Un verdict FAIL bloque tout replay supérieur.

### Tests ajoutés (4)

| Test | Cas couvert |
|---|---|
| `test_l019_p0_manifest_pass_on_valid_journal` | Journal valide → PASS |
| `test_l019_p0_manifest_fail_wrong_count` | expected_count erroné → FAIL |
| `test_l019_p0_manifest_fail_wrong_chain_tip` | pointe de chaîne incorrecte → FAIL |
| `test_l019_p0_manifest_fail_wrong_schema_version` | schema_version incompatible → FAIL |

---

## L-019-002 P1 — Archive R2 et replay sans effets externes

### Constat (R034 §4)

Pas d'archive des réponses d'outils. Impossible de rejouer R2 sans appeler les
vrais outils. Pas de mécanisme pour vérifier qu'une fixture n'a pas été altérée
ni qu'elle correspond au bon appel.

### Correction

**`ArchivedToolResponse`** — réponse archivée liée à un `intent_id` :
- `intent_id` : lien vers l'INTENT de l'appel original
- `input_hash` : SHA-256 des arguments d'entrée (vérification d'appartenance)
- `decision` + `execution_status` : fidélité de la décision Guardian
- `response_payload` + `response_hash` : réponse canonique + intégrité SHA-256
- `verify_response_hash()` : détecte toute altération de la fixture

**`ToolResponseArchive`** — archive indexée par `intent_id` :
- `record()` : lève `ValueError` sur duplication d'`intent_id`
- `get()`, `to_jsonl()`, `from_jsonl()` : lecture, persistance et rechargement

**`make_recording_sink(jsonl_path, archive)`** — remplace `make_file_sink` quand
on veut capturer les réponses pour R2. Archive automatiquement les TERMINAL.

**`R2ReplayResult`** — résultat distinguant :
- `verdict` : "PASS" | "FAIL" | "IN_DOUBT"
- `events_replayed` : nombre de TERMINAL rejoués
- `external_calls_prevented` : sentinelle — toujours 0 dans R2
- `mismatches` : divergences détectées
- `in_doubt` : INTENT orphelins sans TERMINAL

**`replay_r2(journal_path, archive, manifest)`** — rejoue le scénario depuis les fixtures :

1. Vérifie les préconditions du manifeste (P0) → FAIL immédiat si non conformes
2. Pour chaque TERMINAL, récupère la fixture par `intent_id`
3. FAIL si fixture absente, `response_hash` invalide, `input_hash` divergent,
   `decision` ou `execution_status` divergents
4. INTENT sans TERMINAL → IN_DOUBT
5. `external_calls_prevented = 0` confirmé par conception (aucun exécuteur appelé)
6. Ne rétrograde jamais silencieusement vers R0

### Tests ajoutés (12)

| Test | Cas couvert |
|---|---|
| `test_l019_p1_archive_record_and_retrieve` | enregistrement et récupération |
| `test_l019_p1_archive_rejects_duplicate_intent_id` | duplication → ValueError |
| `test_l019_p1_archive_verify_response_hash_detects_tamper` | fixture altérée détectée |
| `test_l019_p1_recording_sink_archives_terminal_events` | sink capture les TERMINAL |
| `test_l019_p1_archive_persist_and_reload` | persistance JSONL + rechargement |
| `test_l019_p1_replay_r2_pass_full_scenario` | scénario complet → PASS, 3 TERMINAL |
| `test_l019_p1_replay_r2_fail_missing_fixture` | fixture absente → FAIL |
| `test_l019_p1_replay_r2_fail_tampered_fixture` | response_hash invalide → FAIL |
| `test_l019_p1_replay_r2_fail_wrong_input_hash` | input_hash divergent → FAIL |
| `test_l019_p1_replay_r2_fail_bad_manifest_preconditions` | manifeste invalide → FAIL, events_replayed=0 |
| `test_l019_p1_replay_r2_in_doubt_orphan_intent` | INTENT orphelin → IN_DOUBT |
| `test_l019_p1_replay_r2_sentinel_external_calls_always_zero` | sentinelle = 0 sur 5 appels |

---

## Résultats observés dans cette session

```
python3 -m pytest test_instrumentation.py test_demo_scenario.py -q
93 passed in 1.08s
```

| Fichier | Collecté | PASS | FAIL |
|---|---|---|---|
| `test_instrumentation.py` | 80 | 80 | 0 |
| `test_demo_scenario.py` | 13 | 13 | 0 |
| **Total** | **93** | **93** | **0** |

---

## Réponses aux critères R034

| Critère R034 §4 | Couvert |
|---|---|
| Fixtures liées aux appels via `intent_id` | ✅ `ArchivedToolResponse.intent_id` |
| Fixtures versionnées | ✅ `schema_version` dans chaque fixture |
| Intégrité des fixtures vérifiable | ✅ `response_hash` + `verify_response_hash()` |
| Fixture absente → FAIL explicite | ✅ `test_l019_p1_replay_r2_fail_missing_fixture` |
| Fixture altérée → FAIL | ✅ `test_l019_p1_replay_r2_fail_tampered_fixture` |
| Mauvais `intent_id` / `input_hash` → FAIL | ✅ `test_l019_p1_replay_r2_fail_wrong_input_hash` |
| Decision Guardian diverge → FAIL | ✅ vérifié dans `replay_r2` |
| INTENT orphelin → IN_DOUBT, pas de relance | ✅ `test_l019_p1_replay_r2_in_doubt_orphan_intent` |
| Archive tronquée sans ancrage → FAIL | ✅ `test_l019_p1_replay_r2_fail_bad_manifest_preconditions` |
| Sentinelle zéro exécuteur externe | ✅ `external_calls_prevented = 0` par conception + test |
| Préconditions P0 bloquent R2 | ✅ `verify_manifest_preconditions` en tête de `replay_r2` |

---

## Limites documentées

- `replay_r2` opère sur le JSONL Python — pas encore connecté au moteur Rust R2/R3.
- Le `response_payload` archivé est le résumé Guardian (decision + execution_status + output_summary), pas le payload brut de l'outil. Un payload brut nécessiterait des modifications de l'interface `handle_tool_call`.
- La vérification de `schema_version` dans `verify_manifest_preconditions` ignore les lignes sans le champ (compatibilité descendante).
- `external_calls_prevented` est toujours 0 par conception dans `replay_r2` — la valeur est une preuve documentaire, pas un compteur dynamique décrémenté par des appels bloqués.

---

## Chantiers restants L-019-002

| ID | Priorité | Constat |
|---|---|---|
| L-019-002 P1 (Rust) | P1 | Exposer `replay_r2` au niveau PyO3 (bindings Rust/Python) |
| L-019-002 P1 (R3) | P1 | Implémenter R3 — exécution déterministe contrôlée dans environnement isolé |
| L-019-002 P2 | P2 | Replay IA R4 avec fidélité qualifiée |
| Chaîne multiprocessus | P2 | Démontrer cohérence globale des séquences entre processus (pas seulement JSON valide) |
