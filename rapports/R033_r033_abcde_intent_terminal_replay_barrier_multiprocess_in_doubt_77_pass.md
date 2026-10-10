# R033 — Intent/Terminal events, barrière replay, multiprocessus, chaîne complète, IN_DOUBT

**Commit** : `2de19ee`
**Date** : 2026-10-10
**Tests** : 77/77 PASS (64 `test_instrumentation.py` + 13 `test_demo_scenario.py`)
**Précédent** : R032 — 58/58 PASS (execution_status, fcntl.flock, is_replay)

---

## Anomalies traitées

| ID | Priorité | Constat | Statut |
|---|---|---|---|
| R033-A | P1 | Gap entre intention et exécution — aucun intent journalisé avant l'effet externe | Clos |
| R033-B | P1 | Mode replay : barrière d'exécution manquante — `is_replay` ignorable par l'appelant | Clos |
| R033-C | P1 | Tests multiprocessus uniquement via threads — pas de vrais sous-processus `subprocess` | Clos |
| R033-D | P2 | Vérification chaîne incomplète — suppression/duplication non toujours détectées | Clos |
| R033-E | P2 | Reprise après incident — events INTENT orphelins non classés IN_DOUBT | Clos |

---

## R033-A — Intent/Terminal events

### Constat

`handle_tool_call` produisait un seul événement TERMINAL après l'exécution. Si le processus crashait entre l'appel à l'exécuteur et la journalisation, aucune trace de l'intention n'existait. L'auditeur ne pouvait pas distinguer « n'a jamais tenté » de « a tenté et échoué silencieusement ».

### Correction

Chaque `handle_tool_call` produit désormais **deux événements enchaînés** :

1. **INTENT** (phase `EventPhase.INTENT`) : journalisé **avant** l'appel à l'exécuteur.
   - `output_summary = "INTENT"`, `execution_status = "NOT_EXECUTED"`, `duration_ms = 0.0`
   - Porte un `intent_id` UUID unique.
2. **TERMINAL** (phase `EventPhase.TERMINAL`) : journalisé **après** l'exécution.
   - Porte le même `intent_id` que l'INTENT correspondant.
   - Porte le vrai `execution_status` (EXECUTED / FAILED / NOT_EXECUTED).

Les deux champs `event_phase` et `intent_id` sont inclus dans le corps canonique → leur modification altère le hash de la chaîne.

### Invariants vérifiés

- `get_events()` retourne uniquement les TERMINAL (rétrocompatibilité).
- `get_all_events()` retourne INTENT + TERMINAL.
- `event_count()` retourne le nombre de TERMINAL (= nombre d'appels métier).
- N appels = 2N entrées JSONL.

### Tests ajoutés (6)

- `test_r033_a_intent_event_emitted_before_terminal`
- `test_r033_a_intent_output_summary_is_intent`
- `test_r033_a_terminal_carries_real_execution_result`
- `test_r033_a_intent_in_canonical_dict`
- `test_r033_a_intent_persisted_in_jsonl`
- `test_r033_a_block_emits_intent_and_terminal`

---

## R033-B — Barrière physique en mode replay

### Constat

Le champ `is_replay` existait dans le corps canonique (R032-C) mais n'avait aucun effet sur l'exécution. L'appelant pouvait passer `is_replay=True` dans un événement tout en laissant l'exécuteur être appelé.

### Correction

`handle_tool_call` accepte maintenant un paramètre keyword-only `is_replay: bool = False`.
Quand `is_replay=True` :
- Le code d'exécution de l'outil est **physiquement court-circuité** (branche `if is_replay:`).
- L'exécuteur réel n'est jamais appelé.
- La réponse indique `"[GUARDIAN] Replay mode — execution suppressed"`.
- Tous les événements produits portent `is_replay=True`.

La barrière vaut pour ALLOW et REDACT. BLOCK et ESCALATE n'appellent jamais l'exécuteur de toute façon.

### Tests ajoutés (5)

- `test_r033_b_replay_never_calls_executor` — sentinelle : compteur reste à 0
- `test_r033_b_replay_events_carry_is_replay_true`
- `test_r033_b_replay_block_also_suppressed`
- `test_r033_b_replay_has_different_hash_than_real`
- `test_r033_b_non_replay_still_calls_executor` — test inverse

---

## R033-C — Tests multiprocessus réels (subprocess)

### Constat

Le test R032-B utilisait `threading` comme proxy pour la concurrence multiprocessus. Les threads partagent le GIL Python et n'exercent pas le verrou `fcntl.flock` dans les mêmes conditions que de vrais processus séparés.

### Correction

Ajout de `test_r033_c_multiprocess_file_lock` qui lance 4 **vrais sous-processus** via `subprocess.Popen`. Chaque processus écrit 3 appels (6 lignes JSONL) de façon concurrente dans le même fichier. 

Vérification : 24 lignes au total, toutes du JSON valide (pas d'entrelacement de caractères entre processus).

### Test ajouté (1)

- `test_r033_c_multiprocess_file_lock`

---

## R033-D — Vérification chaîne complète

### Constat

Les tests précédents (R023-002) couvraient la détection d'altération du `previous_event_hash`. R033-D étend la couverture aux cas : suppression d'un événement INTENT, duplication de ligne, régression de `sequence_no`.

### Tests ajoutés (3)

- `test_r033_d_deletion_of_intent_detected` — suppression d'une ligne rompt le chaînage
- `test_r033_d_duplication_detected_via_expected_count` — doublon détecté via `expected_count`
- `test_r033_d_sequence_regression_detected` — `sequence_no` non-monotone détecté

---

## R033-E — Reprise après incident — IN_DOUBT

### Constat

Après un crash entre la journalisation de l'INTENT et celle du TERMINAL, le journal contient un INTENT orphelin. Sans mécanisme de détection, l'opérateur ne sait pas que l'appel est dans un état indéterminé.

### Correction

Ajout de `find_in_doubt_intents(path)` dans `instrumentation.py` :
- Lit le JSONL, identifie les `intent_id` sans TERMINAL correspondant.
- Retourne une liste de dicts `{intent_id, event_id, tool_name, sequence_no, occurred_at}`.
- Retourne `[]` si le fichier n'existe pas ou si tous les INTENT ont leur TERMINAL.

### Tests ajoutés (4)

- `test_r033_e_no_in_doubt_on_complete_journal`
- `test_r033_e_in_doubt_detected_on_truncated_terminal` — crash simulé : dernier TERMINAL supprimé
- `test_r033_e_in_doubt_multiple_crashes` — 2 TERMINAL supprimés → 2 IN_DOUBT détectés
- `test_r033_e_in_doubt_nonexistent_file`

---

## Adaptations des tests existants

L'introduction des INTENT a doublé le nombre d'entrées JSONL par appel. Les tests suivants ont été mis à jour :

| Test | Avant | Après |
|---|---|---|
| `test_sequence_monotone` | `seqs == [1,2,3,4,5]` | monotonie stricte + séquences globales 1..10 |
| `test_custom_event_sink` | `len(received) == 1` | `len(received) == 2` + vérification INTENT/TERMINAL |
| `test_r021_005_file_sink_persist_and_reload` | 3 lignes / `entries_verified==3` | 6 lignes / `entries_verified==6` |
| `test_r023_002_parent_hash_chained` | 3 lignes | 6 lignes, chaînage sur 6 entrées |
| `test_r028_a_empty_journal_with_expected_count_fails` | `expected_count=3` | `expected_count=6` |
| `test_r028_b_resume_from_existing_journal` | `last_seq==2`, 4 entrées | `last_seq==4`, 8 entrées |
| `test_r030_002_recover_state_accepts_valid_journal` | `last_seq==3` | `last_seq==6` |
| `test_r032_a_execution_status_in_jsonl` | `lines[0]`/`lines[1]` | filtre sur TERMINAL |
| `test_r032_b_file_lock_prevents_interleaving` | 15 lignes | 30 lignes, `initial_seq` ×2 |
| `test_d4_11_two_runs_no_cross_contamination` | `get_all_events()==2` | `get_all_events()==4`, `get_terminal_events()==2` |

`defender_agent.py` : `verify_chain_r0()` utilise désormais `get_all_events()` pour vérifier la chaîne complète INTENT+TERMINAL. `get_all_events()` retourne la chaîne complète ; `get_terminal_events()` retourne les TERMINAL seuls.

---

## Résultats observés dans cette session

```
python3 -m pytest test_instrumentation.py test_demo_scenario.py -q
77 passed in 0.78s
```

| Fichier | Collecté | PASS | FAIL |
|---|---|---|---|
| `test_instrumentation.py` | 64 | 64 | 0 |
| `test_demo_scenario.py` | 13 | 13 | 0 |
| **Total** | **77** | **77** | **0** |

---

## Limites documentées

- `find_in_doubt_intents` ne vérifie pas l'intégrité de la chaîne — un JSONL corrompu peut produire des faux négatifs. Utiliser `load_and_verify_jsonl` en amont.
- Le test R033-C vérifie l'absence d'entrelacement JSON mais pas le chaînage `previous_event_hash` entre processus (les processus écrivent des chaînes indépendantes).
- La barrière replay de R033-B est sur `is_replay` passé à `handle_tool_call` — si l'appelant oublie le flag, la barrière n'est pas activée. Un niveau supérieur (R2/R3) doit contrôler ce paramètre.

---

## Prochaines anomalies ouvertes

| ID | Priorité | Constat |
|---|---|---|
| L-019-002 | P2 | Replay R2/R3 — niveaux supérieurs du moteur Rust |
