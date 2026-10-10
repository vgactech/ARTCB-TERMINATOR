# R028 — Clôture R021-005 et R023-002 : persistance durable JSONL, chaînage parent-hash — 39/39 PASS

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R028 |
| Date | 2026-10-10 |
| Commit de base | `566f1b3` (R027) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Fermeture de R021-005 (persistance durable) et R023-002 (chaînage parent-hash) |
| Exécution | ✅ `pytest guardian_mcp/ -v` — **39/39 PASS observés dans cette session** |
| Fichiers modifiés | `guardian_mcp/instrumentation.py`, `guardian_mcp/defender_agent.py`, `guardian_mcp/test_instrumentation.py` |

---

## 1. Résumé exécutif

| Constat | Priorité | État avant | État après |
|---|---|---|---|
| R021-005 — persistance durable après redémarrage | P1 | ⚠️ Mémoire seulement | ✅ `make_file_sink()` + `load_and_verify_jsonl()` + fsync + tests |
| R023-002 — chaînage `previous_event_hash` | P2 | ⚠️ Non implémenté | ✅ Champ dans `MCPToolEvent`, propagé dans la chaîne, vérifié en R0 et en JSONL |

**Score total Python observé : 39/39 PASS** (34 existants + 5 nouveaux).

Constats restants ouverts : L-019-002 (R2/R3).

---

## 2. R021-005 — Persistance durable

### Contexte

Le contre-audit R026 avait confirmé que les preuves conservées uniquement en mémoire disparaissent à l'arrêt du processus. Un test réussi avant redémarrage ne prouve pas la durabilité.

### Ce qui a été implémenté

#### `make_file_sink(path)` — `instrumentation.py`

Retourne un sink qui :
- Persiste chaque événement en format **JSONL** (une ligne JSON par événement, trié par clés).
- Appelle `os.fsync()` après chaque écriture — garantie de durabilité au niveau du système d'exploitation.
- Crée le répertoire parent si nécessaire.
- Inclut tous les champs de `MCPToolEvent` : `event_id`, `event_hash`, `previous_event_hash`, `decision`, etc.

#### `load_and_verify_jsonl(path)` — `instrumentation.py`

Fonction de rechargement et de vérification indépendante :
- Relit le fichier JSONL depuis le disque (simule un redémarrage).
- Recalcule le `event_hash` de chaque entrée depuis ses champs canoniques.
- Vérifie le chaînage `previous_event_hash` entre chaque entrée.
- Vérifie la monotonie des `sequence_no`.
- Retourne un `ChainVerificationResult` avec verdict `PASS`/`FAIL`, liste des anomalies et limites documentées.

#### Alimentation systématique de `self._events`

Correction interne : `self._events.append((event, event_hash))` est maintenant appelé dans `handle_tool_call()` **avant** l'appel au sink, pour tous les sinks (défaut ou externe). Cela garantit que `prev_hash` est toujours correct et que l'introspection (`get_events()`, `last_event_hash()`) fonctionne même avec un sink fichier.

### Tests ajoutés

| Test | Vérification |
|---|---|
| `test_r021_005_file_sink_persist_and_reload` | 3 événements écrits, lus depuis un nouveau processus simulé, chaîne PASS |
| `test_r021_005_file_not_found_returns_fail` | Fichier absent → FAIL sans exception |

### Limite déclarée

La troncature de fin de fichier n'est pas détectable sans un point d'ancrage externe du dernier hash attendu. Cette limite est documentée dans `limits` du résultat de vérification.

---

## 3. R023-002 — Chaînage `previous_event_hash`

### Contexte

Le contre-audit R026 avait montré que la vérification de `sequence_no` monotone ne constitue pas un chaînage cryptographique : un réordonnancement d'événements non altérés peut ne pas être détecté si les numéros de séquence sont également réordonnés.

### Ce qui a été implémenté

#### Champ `previous_event_hash` dans `MCPToolEvent`

- Nouveau champ avec valeur par défaut `GENESIS_HASH` (`"0" * 64`).
- **Inclus dans le corps canonique** utilisé par `compute_hash()` : tout changement du prédécesseur modifie le hash de l'événement suivant dans la chaîne.
- Propagé automatiquement dans `handle_tool_call()` : `prev_hash = self._events[-1][1] if self._events else GENESIS_HASH`.

#### Vérification 3 dans `verify_chain_r0()` — `defender_agent.py`

```python
# Vérification 3 : chaînage parent-hash (R023-002)
prev_hash = GENESIS_HASH
for event, stored_hash in events:
    if event.previous_event_hash != prev_hash:
        mismatches.append({"field": "previous_event_hash", ...})
    prev_hash = stored_hash
```

#### Chaîne cryptographique explicite

Le premier événement pointe vers `GENESIS_HASH`. Chaque événement suivant pointe vers le `event_hash` du précédent. Toute modification du contenu d'un événement intermédiaire change son hash, ce qui invalide le `previous_event_hash` de tous les événements suivants.

### Tests ajoutés

| Test | Vérification |
|---|---|
| `test_r023_002_parent_hash_chained` | Chaînage GENESIS→E1→E2→E3 vérifié explicitement |
| `test_r023_002_tampered_parent_hash_fails` | Altération du `previous_event_hash` → détection |
| `test_r023_002_reordering_detected` | Inversion de l'ordre des lignes JSONL → détection |

### Limite maintenue (déclarée)

La troncature de fin de chaîne n'est pas détectable sans point d'ancrage externe. Un historique chaîné peut encore être tronqué à sa fin si aucun mécanisme indépendant ne permet de connaître son dernier état attendu — exactement comme le notait le contre-audit R026.

---

## 4. Cohérence avec le store Rust

Le moteur Rust (`guardian_core/src/store/durable.rs`) implémente déjà `DurableEventStore` avec :
- `previous_event_hash` dans `LedgerEntry`
- `chain_hash` (double hash cryptographique)
- `recover_state()` et `read_all()` pour la persistance
- `verify_chain()` pour le replay

L'implémentation Python est **structurellement alignée** sur le modèle Rust : même champ `previous_event_hash`, même constante genesis, même schéma de vérification. La transition vers le store Rust via PyO3 (C-08) reste ouverte mais ne nécessite pas de redesign.

---

## 5. Résultats des tests après corrections

```
39 passed in 0.19s
```

| Suite | Tests | PASS | FAIL |
|---|---|---|---|
| Rust `cargo test` | 45 | 45 (déclarés) | 0 |
| Python C-07 instrumentation | 26 | 26 | 0 |
| Tests différentiels PyO3 | 6 | 6 (déclarés) | 0 |
| Démo 4 agents | 13 | 13 | 0 |
| **Total Python observé** | **39** | **39** | **0** |

---

## 6. État des anomalies après R028

| ID | Constat | Priorité | État |
|---|---|---|---|
| R021-005 — persistance durable | P1 | ✅ **FERMÉ** — `make_file_sink` + `load_and_verify_jsonl` + 2 tests |
| R023-002 — parent-hash | P2 | ✅ **FERMÉ** — champ implémenté + propagé + R0 étendu + 3 tests |
| L-019-002 — replay R2/R3 | P2 | **OUVERT** — invariants à définir |

---

## 7. Limite déclarée commune aux deux constats

> Un historique chaîné (en mémoire ou en JSONL) peut encore être tronqué à sa fin si aucun mécanisme indépendant ne permet de connaître son dernier hash attendu.

Cette limite est documentée dans `ChainVerificationResult.limits` et dans les docstrings de `verify_chain_r0()` et `load_and_verify_jsonl()`. Elle n'invalide pas les garanties fournies — elle les borne précisément.

---

## 8. Contrôle de périmètre

- Fichiers applicatifs modifiés : `instrumentation.py`, `defender_agent.py`, `test_instrumentation.py`.
- Rapport : R028 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Projet VLC&ARTCB : aucune migration ni intégration.
- Logs bruts : aucun ajouté.

---

## 9. Formule de présentation pour les auditeurs suivants

> « R021-005 et R023-002 sont fermés. Chaque événement Guardian référence cryptographiquement son prédécesseur via `previous_event_hash` inclus dans son hash. Les événements peuvent être persistés en JSONL avec fsync et rechargés après redémarrage ; la chaîne est vérifiée de bout en bout. Trois tests négatifs confirment que la modification du parent-hash, l'altération d'une entrée et le réordonnancement des lignes sont tous détectés. Score Python observé : 39/39 PASS. »
