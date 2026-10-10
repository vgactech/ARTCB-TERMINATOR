# R036 — Sentinelle dynamique, ancrage archive, fidélité données, R3 déterministe

**Commit** : `4126ec6`
**Date** : 2026-10-10
**Tests** : 113/113 PASS
**Détail** : 98 `test_instrumentation.py` + 13 `test_demo_scenario.py` + 2 `test_app.py`
**Précédent** : R035 — L-019-002 P0+P1, 93/93 PASS

---

## Contexte

Le contre-audit R035 identifiait quatre insuffisances dans la couche replay :

1. **R036-A** — `external_calls_prevented = 0` était une garantie documentaire, pas une propriété testée du chemin d'exécution.
2. **R036-B** — Pas d'ancrage cryptographique global de l'archive (détection d'une substitution cohérente journal+archive).
3. **R036-C** — `response_payload` n'était pas distingué du payload brut ; pas de version de canonicalisation.
4. **R036-D** — R3 (exécution déterministe contrôlée) n'était pas implémenté.

---

## R036-A — Sentinelle dynamique

### Constat (R035 §4)

`external_calls_prevented = 0` était une constante documentaire. Zéro appels effectués ≠ zéro appels empêchés. La différence est fondamentale pour prouver une propriété du chemin d'exécution.

### Correction

Ajout de `make_failfast_executor(violations)` et `ExternalCallForbiddenError` dans `instrumentation.py`.

**`make_failfast_executor(violations)`** retourne un exécuteur qui :
- Enregistre immédiatement la violation dans `violations` (liste mutable partagée)
- Lève `ExternalCallForbiddenError` (absorbée par l'instrumentation comme FAILED)

En mode `is_replay=True`, l'exécuteur n'est jamais appelé → `violations` reste vide.  
Sans replay, l'exécuteur est appelé → violation enregistrée + `execution_status=FAILED`.

**Usage dans les tests :**
```python
violations = []
executor = make_failfast_executor(violations)
instr.handle_tool_call(params, executor=executor, is_replay=True)
assert len(violations) == 0  # propriété testée, pas documentée
```

### Tests ajoutés (4)

| Test | Cas couvert |
|---|---|
| `test_r036_a_failfast_executor_never_called_in_replay` | replay → 0 violations |
| `test_r036_a_failfast_executor_raises_if_called_without_replay` | sans replay → violation enregistrée + FAILED |
| `test_r036_a_failfast_block_never_reaches_executor` | BLOCK → 0 violations (outil jamais appelé) |
| `test_r036_a_multiple_replay_calls_zero_violations` | 10 appels replay → 0 violations |

---

## R036-B — Ancrage cryptographique de l'archive

### Constat (R035 §3)

Un hash individuel de fixture ne détecte pas la substitution cohérente de l'ensemble journal+archive+manifeste. Sans ancrage global, un attaquant contrôlant les trois fichiers peut recalculer tous les hashes de façon cohérente.

### Correction

Ajout dans `instrumentation.py` :

**`ArchiveAnchor`** — dataclass avec `archive_hash`, `entry_count`, `created_at`, `run_id`. Sérialisable via `to_dict()` / `from_dict()`.

**`compute_archive_hash(archive)`** — SHA-256 de la concaténation triée `intent_id:response_hash` de toutes les fixtures. Déterministe.

**`create_archive_anchor(archive, run_id)`** — à appeler après la session d'enregistrement.

**`verify_archive_anchor(archive, anchor)`** — retourne `(bool, str)`. FAIL si entry_count diverge ou si le hash global diffère.

**Limite documentée :** si l'attaquant contrôle aussi l'ancrage, il peut recalculer les deux de façon cohérente. L'ancrage doit être stocké dans un système tiers pour être probant.

### Tests ajoutés (5)

| Test | Cas couvert |
|---|---|
| `test_r036_b_anchor_created_and_verified` | archive valide → ancrage PASS |
| `test_r036_b_anchor_detects_tampered_fixture` | modification d'une fixture après ancrage → FAIL |
| `test_r036_b_anchor_detects_added_fixture` | ajout d'une fixture après ancrage → FAIL |
| `test_r036_b_anchor_serialization` | sérialisation / désérialisation |
| `test_r036_b_archive_hash_deterministic` | même archive → même hash |

---

## R036-C — Fidélité des données archivées

### Constat (R035 §3)

`response_payload` contenait un résumé Guardian sans que cela soit explicitement distingué du payload brut de l'outil. Un changement de format de sérialisation invalidait les anciens hashes sans avertissement.

### Correction

Ajout dans `ArchivedToolResponse` :

- **`raw_response_hash: str = ""`** — SHA-256 du payload brut de l'outil (vide si non capturé). Documente explicitement ce qui n'est pas archivé.
- **`canonicalization_version: str = "jcs-v1"`** — version du format de sérialisation. Tout changement de sérialisation doit incrémenter cette version pour invalider les fixtures incompatibles.

Ces champs sont persistés dans le JSONL de l'archive via `to_dict()` / `from_dict()`.

**Distinction documentée :**
| Niveau | Champ | Contenu |
|---|---|---|
| Résumé Guardian | `response_payload` + `response_hash` | decision + execution_status + output_summary |
| Payload brut | `raw_response_hash` (si capturé) | réponse complète de l'outil |
| Version canon. | `canonicalization_version` | format de sérialisation utilisé |

### Tests ajoutés (4)

| Test | Cas couvert |
|---|---|
| `test_r036_c_archived_response_has_canonicalization_version` | fixtures portent `jcs-v1` |
| `test_r036_c_raw_response_hash_empty_by_default` | `raw_response_hash=""` par défaut |
| `test_r036_c_response_payload_is_guardian_summary_not_raw` | payload = résumé, pas `isError`/`content` |
| `test_r036_c_canonicalization_version_persisted_in_jsonl` | `canonicalization_version` dans le JSONL |

---

## R036-D — Replay R3 déterministe contrôlé

### Constat (R034 §5, R035 chantiers restants)

R3 n'était pas implémenté. Les niveaux supérieurs à R2 n'existaient que comme variantes d'énumération Rust.

### Correction

Ajout dans `instrumentation.py` :

**`DeterministicContext`** — neutralise les sources de non-déterminisme :
- `fixed_now` : horodatage fixe pour tous les événements reconstruits
- `next_uuid()` : UUID déterministe depuis un compteur séquentiel (`00000000-0000-4000-8000-NNNNNNNNNNNN`)

**`R3ReplayResult`** — distingue :
- `decisions_match` : décisions Guardian identiques aux fixtures
- `execution_statuses_match` : statuts d'exécution identiques
- `hashes_match` : reproductibilité du hash canonique (nécessite `fixed_now`)
- `external_calls_blocked` : toujours 0 (aucun exécuteur appelé)

**`replay_r3(original_events, archive, manifest, ctx)`** :
1. Filtre TERMINAL et INTENT de la session originale
2. Compare chaque TERMINAL à sa fixture archivée (décision + statut + intégrité fixture)
3. Avec `DeterministicContext`, vérifie la reproductibilité interne du hash
4. Signale IN_DOUBT sur INTENT orphelin
5. `external_calls_blocked = 0` confirmé par construction

**Limite documentée :** les hashes originaux incluent l'horodatage réel — non reproductibles sans contexte fixé. Un PASS R3 sur les décisions ≠ PASS R3 sur les hashes sans neutralisation complète du non-déterminisme.

### Tests ajoutés (6)

| Test | Cas couvert |
|---|---|
| `test_r036_d_replay_r3_pass_complete_scenario` | PASS, 3 appels, toutes propriétés |
| `test_r036_d_replay_r3_fail_missing_fixture` | FAIL sans fixture, `decisions_match=False` |
| `test_r036_d_deterministic_context_reproducible_uuid` | même contexte → mêmes UUIDs |
| `test_r036_d_replay_r3_in_doubt_orphan_intent` | INTENT orphelin → IN_DOUBT |
| `test_r036_d_replay_r3_external_calls_blocked_always_zero` | `external_calls_blocked=0` sur 4 appels |

---

## Résultats observés dans cette session

```
python3 -m pytest guardian_mcp/test_instrumentation.py guardian_mcp/test_demo_scenario.py guardian_api/test_app.py -q
113 passed in 3.42s
```

| Fichier | Collecté | PASS | FAIL |
|---|---|---|---|
| `test_instrumentation.py` | 98 | 98 | 0 |
| `test_demo_scenario.py` | 13 | 13 | 0 |
| `test_app.py` | 2 | 2 | 0 |
| **Total** | **113** | **113** | **0** |

---

## Infrastructure AWS — Constat

Projet Doppler `aws` — compte `769488121557`, rôle `WSParticipantRole` (AWS Workshop).  
Région primaire : `us-west-2`.

**Inventaire complet :**
- Aucune instance EC2 active dans aucune région
- Aucun cluster ECS, aucune fonction Lambda applicative (seul `WSConcurrencyCurtailer-DO-NOT-USE`)
- Aucun Load Balancer, Elastic Beanstalk, API Gateway, RDS, S3
- Un seul VPC par défaut (`172.31.0.0/16`)

**Conclusion :** le compte est un environnement Workshop préconfiguré, sans infrastructure applicative déployée. L'API `guardian_api` tourne localement uniquement. Aucun déploiement AWS n'est actif.

---

## Réponses aux critères R035

| Critère R035 | Couvert |
|---|---|
| Sentinelle dynamique (pas documentaire) | ✅ `make_failfast_executor` + tests |
| Ancrage global de l'archive | ✅ `ArchiveAnchor` + `compute_archive_hash` |
| Détection altération cohérente journal+archive | ⚠️ Partiel — détecte si ancrage indépendant ; limite documentée |
| Fidélité : résumé vs payload brut | ✅ `raw_response_hash` + `canonicalization_version` |
| R3 déterministe contrôlé | ✅ `replay_r3` + `DeterministicContext` |
| Aucun exécuteur externe en R3 | ✅ `external_calls_blocked=0` par construction + test |
| IN_DOUBT en R3 | ✅ INTENT orphelin détecté |

---

## Chantiers restants

| ID | Priorité | Constat |
|---|---|---|
| L-019-002 PyO3 | P1 | Bindings Rust/Python — exposer R2/R3 au moteur Rust |
| Chaîne multiprocessus | P2 | Cohérence globale séquences entre processus |
| R4 | P2 | Replay IA avec fidélité qualifiée |
| Ancrage externe | P2 | Stocker l'ancrage dans un système tiers pour preuve d'origine |
| Déploiement AWS | — | Aucune infrastructure active — à déployer si requis |
