# R032 — R032-A execution_status, R032-B verrou multiprocessus, R032-C is_replay — 58/58 PASS

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R032 |
| Date | 2026-10-10 |
| Commit de base | `c1a1d4e` (R031) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Fermeture de R032-A, R032-B et R032-C identifiés dans le contre-audit R031 |
| Exécution | ✅ `pytest guardian_mcp/ -v` — **58/58 PASS observés dans cette session** |
| Fichiers modifiés | `guardian_mcp/instrumentation.py`, `guardian_mcp/test_instrumentation.py` |

---

## 1. Résumé exécutif

| Chantier | État avant | État après |
|---|---|---|
| R032-A — écart exécution/écriture | ⚠️ `output_summary` seul, pas de statut structuré | ✅ Champ `execution_status` : EXECUTED / FAILED / NOT_EXECUTED |
| R032-B — concurrence multiprocessus | ⚠️ `open(…, "a")` sans verrou | ✅ `fcntl.flock(LOCK_EX)` autour de write+flush+fsync |
| R032-C — rejeu vs réel | ⚠️ Aucun marqueur dans les événements | ✅ Champ `is_replay: bool = False` inclus dans le corps canonique |

**Score total Python observé : 58/58 PASS**a (51 existants + 7 nouveaux).

---

## 2. R032-A — Champ `execution_status`

### Ajout dans `MCPToolEvent`

```python
execution_status: str = "NOT_EXECUTED"
# "EXECUTED"     : l'outil a été appelé et a retourné un résultat.
# "FAILED"       : l'outil a été appelé mais a levé une exception.
# "NOT_EXECUTED" : l'outil n'a pas été appelé (BLOCK, ESCALATE).
# "UNKNOWN"      : état indéterminé (crash entre exécution et journalisation).
```

Ce champ est inclus dans `to_canonical_dict()` et donc dans `compute_hash()`. Il est propagé dans `handle_tool_call()` et persisté dans le fichier JSONL.

### Limite R028-C restante

`UNKNOWN` reste théorique : si le processus s'arrête **après** l'exécution de l'outil mais **avant** l'appel au sink, l'événement n'est pas du tout enregistré. Ce gap ne peut pas être détecté sans un mécanisme d'intention préalable (pattern intent/executed), qui reste un chantier distinct.

### Tests

| Test | Vérification |
|---|---|
| `test_r032_a_execution_status_executed_on_allow` | Appel ALLOW → `EXECUTED` |
| `test_r032_a_execution_status_not_executed_on_block` | Appel BLOCK → `NOT_EXECUTED` |
| `test_r032_a_execution_status_failed_on_exception` | Exception dans exécuteur → `FAILED` |
| `test_r032_a_execution_status_in_jsonl` | Champ présent et correct dans le JSONL persisté |

---

## 3. R032-B — Verrou fichier exclusif

### Correction dans `make_file_sink()`

```python
import fcntl
with open(jsonl_path, "a", encoding="utf-8") as f:
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

`fcntl.flock(LOCK_EX)` est un verrou exclusif au niveau du noyau. Il protège contre les écritures concurrentes depuis plusieurs processus sur le même fichier.

### Limite documentée

`fcntl.flock` est POSIX. Sur Windows, ce mécanisme n'est pas disponible (non concerné ici — le projet tourne sur macOS/Linux). Le verrou ne protège pas contre les accès via NFS sans option `lockd`.

Le test `test_r032_b_file_lock_prevents_interleaving` vérifie l'atomicité avec 3 threads concurrents écrivant 5 événements chacun (15 lignes totales, toutes valides).

---

## 4. R032-C — Champ `is_replay`

### Ajout dans `MCPToolEvent`

```python
is_replay: bool = False
# R032-C : True si cet événement est produit lors d'un replay.
# Un événement de replay ne doit pas déclencher d'action externe.
```

Ce champ est inclus dans `to_canonical_dict()`. Un événement de replay produit donc un hash différent de l'événement réel équivalent — les deux ne peuvent pas être confondus dans la chaîne.

### Utilisation attendue

Pour produire un événement de replay, l'appelant crée une instance avec `is_replay=True`. Le test `test_r032_c_is_replay_in_canonical_dict` confirme que les deux hashes diffèrent.

### Limite

Le système ne vérifie pas encore que les événements marqués `is_replay=True` ne déclenchent pas d'actions externes réelles — c'est la responsabilité de l'appelant. Cette vérification relève du niveau L-019-002 R2.

---

## 5. Score

```
58 passed in 0.48s
```

| Suite | Tests | PASS |
|---|---|---|
| Démo 4 agents | 13 | 13 |
| C-07 instrumentation (dont R026→R031) | 38 | 38 |
| **Nouveaux R032** | **7** | **7** |
| **Total Python observé** | **58** | **58** |

---

## 6. État des anomalies après R032

| ID | Constat | État |
|---|---|---|
| R032-A — execution_status structuré | ✅ **FERMÉ** |
| R032-B — verrou multiprocessus | ✅ **FERMÉ** (POSIX) |
| R032-C — marqueur is_replay | ✅ **FERMÉ** |
| R028-C — gap exécution/écriture (pattern intent) | **OUVERT P2** — UNKNOWN reste théorique |
| L-019-002 R2/R3 | **OUVERT P2** — prérequis (is_replay, execution_status) satisfaits |

---

## 7. Contrôle de périmètre

- Fichiers applicatifs modifiés : `instrumentation.py`, `test_instrumentation.py`.
- Rapport : R032 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Projet VLC&ARTCB : aucune migration.
- Logs bruts : aucun ajouté.
