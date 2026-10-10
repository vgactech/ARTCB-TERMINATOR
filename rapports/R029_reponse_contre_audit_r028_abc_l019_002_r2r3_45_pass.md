# R029 — Réponse contre-audit R028 : A/B/C fermés, L-019-002 R2/R3 analysé — 45/45 PASS

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R029 |
| Date | 2026-10-10 |
| Commit de base | `5c66c0e` (R028) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Fermeture des anomalies R028-A, R028-B, R028-C ; analyse L-019-002 R2/R3 |
| Exécution | ✅ `pytest guardian_mcp/ -v` — **45/45 PASS observés dans cette session** |
| Fichiers modifiés | `guardian_mcp/instrumentation.py`, `guardian_mcp/test_instrumentation.py` |

---

## 1. Résumé exécutif

| Anomalie | Priorité | État avant | État après |
|---|---|---|---|
| R028-A — journal vide déclaré PASS | Critique | ⚠️ Aucune garde | ✅ `expected_count` + `expected_last_hash` + 2 tests |
| R028-B — reprise après redémarrage non démontrée | Élevée | ⚠️ Nouvelle instance repart à zéro | ✅ `recover_state_from_jsonl()` + `initial_seq`/`initial_prev_hash` + 3 tests |
| R028-C — gap exécution/écriture | Élevée | ⚠️ Non documenté | ✅ Documenté explicitement dans `limits` + 1 test |
| L-019-002 R2/R3 | P2 | OUVERT | Analysé — périmètre défini dans §3 ci-dessous |

**Score total Python observé : 45/45 PASS** (39 existants + 6 nouveaux).

---

## 2. Corrections applicatives

### R028-A — Journal vide ou tronqué détectable via ancrage externe

`load_and_verify_jsonl()` accepte deux nouveaux paramètres optionnels :

```python
load_and_verify_jsonl(
    path,
    expected_count=3,       # FAIL si nombre d'entrées ≠ 3
    expected_last_hash="…", # FAIL si dernier hash ≠ attendu
)
```

Un journal entièrement vidé avec `expected_count=3` retourne `FAIL` avec `field: "entries_count"`. Un dernier hash falsifié retourne `FAIL` avec `field: "last_event_hash"`. Sans ces paramètres, la limite reste déclarée dans `limits` : la troncature finale n'est pas détectable sans ancrage externe.

**Tests ajoutés :** `test_r028_a_empty_journal_with_expected_count_fails`, `test_r028_a_expected_last_hash_mismatch_fails`.

### R028-B — Reprise après redémarrage

Nouvelle fonction `recover_state_from_jsonl(path) → (last_seq, last_hash)` : relit le journal pour récupérer le numéro de séquence et le hash du dernier événement. Retourne `(0, GENESIS_HASH)` si le fichier est absent ou vide.

`GuardianMCPInstrumentation.__init__()` accepte deux nouveaux paramètres :
- `initial_seq: int = 0`
- `initial_prev_hash: str | None = None`

Patron de reprise documenté :

```python
last_seq, last_hash = recover_state_from_jsonl(ledger)
instr2 = GuardianMCPInstrumentation(
    agent_id="agent:x",
    event_sink=make_file_sink(ledger),
    initial_seq=last_seq,
    initial_prev_hash=last_hash,
)
```

Le test `test_r028_b_resume_from_existing_journal` démontre deux sessions successives écrivant dans le même fichier : les sequence_no sont continus `[1, 2, 3, 4]` et la chaîne `load_and_verify_jsonl(…, expected_count=4)` retourne PASS.

**Tests ajoutés :** `test_r028_b_resume_from_existing_journal`, `test_r028_b_recover_state_empty_file`, `test_r028_b_recover_state_nonexistent`.

### R028-C — Gap exécution/écriture documenté

La limite est désormais explicitement présente dans `ChainVerificationResult.limits` :

```
"R028-C : fsync garantit la durabilité d'une écriture effectuée —
un crash entre exécution et écriture laisse un gap non enregistré"
```

Et dans la docstring de `make_file_sink()`. Le test `test_r028_c_gap_documented_in_limits` vérifie que cette chaîne est présente dans les limites retournées. La correction complète (pattern intent/executed/failed) reste un chantier ouvert — documenter la limite est la première étape.

---

## 3. L-019-002 — Analyse R2/R3

### Définition retrouvée dans R004 §8 et R019

| Niveau | Définition | Ce qui est requis |
|---|---|---|
| R2 — Outils simulés | Rejouer l'orchestration avec des réponses d'outils enregistrées ou simulées. Aucun appel externe imprévu pendant le replay. | Enregistrement des réponses + replay sans appels réseau |
| R3 — Exécution contrôlée | Réexécuter les composants déterministes avec mêmes entrées, versions, paramètres. Comparer les sorties canoniques. | Déterminisme des composants + fixtures d'entrée/sortie |

Le moteur Rust `replay/engine.rs` définit déjà `ReplayLevel::R2SimulatedTools` et `ReplayLevel::R3ControlledExecution` mais ne les implémente pas (R0 et R1 seulement).

### Périmètre R2 pour la couche Python MCP

R2 sur la couche Python nécessite :
1. Un mécanisme pour enregistrer les réponses d'outils lors d'une exécution initiale.
2. Un replay qui réutilise ces réponses enregistrées au lieu d'appeler l'exécuteur réel.
3. Une vérification que les décisions Guardian (ALLOW/BLOCK) sont identiques entre l'original et le replay.

Ce périmètre est distinct du `FileSink` actuel : il s'agit d'enregistrer les **sorties** des outils, pas seulement les événements Guardian.

### Interaction avec R028-A/B/C

Les anomalies R028-A et R028-B sont des prérequis pour R2/R3 : un replay cohérent nécessite un journal persistant et une reprise correcte. Ces deux prérequis sont maintenant satisfaits.

R028-C (gap exécution/écriture) est pertinent pour R2/R3 : si une réponse d'outil n'est pas enregistrée avant un crash, le replay manquera d'une entrée. Le pattern intent/executed/failed est plus important encore pour R2 que pour R1.

### État de L-019-002

Ouvert — périmètre défini. L'implémentation reste un chantier P2 distinct.

---

## 4. Résultats des tests après corrections

```
45 passed in 0.33s
```

| Suite | Tests | PASS |
|---|---|---|
| Démo 4 agents (D4-01→D4-12 + D4-context) | 13 | 13 |
| C-07 instrumentation (existants) | 26 | 26 |
| **Nouveaux R028-A/B/C** | **6** | **6** |
| **Total Python observé** | **45** | **45** |

---

## 5. État des anomalies après R029

| ID | Constat | État |
|---|---|---|
| R028-A — journal vide | ✅ **FERMÉ** — expected_count + expected_last_hash + 2 tests |
| R028-B — reprise redémarrage | ✅ **FERMÉ** — recover_state_from_jsonl + initial_seq/hash + 3 tests |
| R028-C — gap exécution/écriture | ✅ **DOCUMENTÉ** — dans limits ; correction complète (intent/executed) = chantier ouvert |
| L-019-002 R2/R3 | **OUVERT** — périmètre défini dans §3 ; prérequis R028-A/B satisfaits |

---

## 6. Limites maintenues

- **Troncature finale sans ancrage** : sans `expected_count` ou `expected_last_hash`, la troncature de fin de journal reste non détectable. Ces paramètres doivent être fournis par le protocole appelant.
- **Gap exécution/écriture** : un crash entre l'exécution d'un outil et l'écriture de son événement laisse un gap non enregistré. Un pattern intent/executed/failed est nécessaire pour les garanties de niveau R2.
- **Verrous multiprocessus** : plusieurs processus écrivant dans le même journal JSONL peuvent produire des entrées entrelacées. Un mécanisme de verrouillage est requis si ce cas d'usage est nécessaire.

---

## 7. Contrôle de périmètre

- Fichiers applicatifs modifiés : `instrumentation.py`, `test_instrumentation.py`.
- Rapport : R029 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Projet VLC&ARTCB : aucune migration.
- Logs bruts : aucun ajouté.
