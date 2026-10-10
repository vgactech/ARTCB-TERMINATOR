# R027 — Clôture R026-001 et R026-002, R023-001 — corrections applicatives et 34/34 PASS

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R027 |
| Date | 2026-10-10 |
| Commits de base | `74f06ef` (R026), `3ecb673` (R025) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Corrections applicatives ciblées des constats R026-001, R026-002, R023-001 |
| Exécution | ✅ `pytest guardian_mcp/ -v` — 34/34 PASS observés dans cette session |
| Fichiers modifiés | `guardian_mcp/instrumentation.py`, `guardian_mcp/attacker_agent.py`, `guardian_mcp/defender_agent.py`, `guardian_mcp/test_instrumentation.py` |

---

## 1. Résumé exécutif

| Constat | Priorité | État avant | État après |
|---|---|---|---|
| R026-001 — `str(exc)` exposé dans réponse et log ALLOW/REDACT | P2 | ⚠️ Fuite possible par texte d'exception | ✅ Réponse générique + log type seulement |
| R026-002 — Docstring `verify_chain_r0()` trop forte | P2 | ⚠️ Mentionne un parent-hash non implémenté | ✅ Alignée sur le comportement réel |
| R023-001 — `DEMO_SECRET_PLACEHOLDER` | P2 | ⚠️ Marqueur lexical PLACEHOLDER | ✅ Renommé `"test:exfil-fixture"` |

**Score total : 34/34 PASS** (30 existants + 4 nouveaux tests sentinelles R026-001).

---

## 2. R026-001 — Fuite indirecte via exception

### Problème confirmé par les tests

Avant la correction, les deux tests suivants échouaient :

```
FAILED test_r026_allow_exception_sentinel_absent_from_response
  AssertionError: 'SECRET_CANARY_VALUE_42' in 'internal error: SECRET_CANARY_VALUE_42 in context'

FAILED test_r026_redact_exception_sentinel_absent_from_response
  AssertionError: 'SECRET_CANARY_VALUE_42' in 'internal error: SECRET_CANARY_VALUE_42 in context'
```

La sentinelle apparaissait dans la réponse MCP (`str(exc)` dans `content[0]["text"]`) et dans les journaux.

### Correction apportée — `instrumentation.py`

```python
# Avant
logger.error("Erreur outil %s : %s", tool_name, exc)
result = {"isError": True, "content": [{"type": "text", "text": str(exc)}]}

# Après (R026-001)
logger.error("Erreur outil %s : type=%s", tool_name, type(exc).__name__)
result = {"isError": True, "content": [
    {"type": "text", "text": f"[GUARDIAN] Tool execution error (ref: {tool_name})"}
]}
```

Même correction appliquée à la branche REDACT. Seul `type(exc).__name__` est journalisé — aucun message d'exception, aucune valeur potentiellement sensible.

### Quatre tests sentinelles ajoutés — `test_instrumentation.py`

| Test | Vérification |
|---|---|
| `test_r026_allow_exception_sentinel_absent_from_response` | Sentinelle absente du texte de réponse MCP (branche ALLOW) |
| `test_r026_allow_exception_sentinel_not_in_output_summary` | Sentinelle absente de `output_summary` de l'événement |
| `test_r026_redact_exception_sentinel_absent_from_response` | Sentinelle absente de la réponse (branche REDACT/ALLOW selon outil) |
| `test_r026_block_executor_never_receives_arguments` | Exécuteur non appelé pour un outil BLOCK même avec argument sensible |

Tous **PASS** après correction.

---

## 3. R026-002 — Docstring `verify_chain_r0()` alignée

### Avant (trop forte)

```python
def verify_chain_r0(self) -> ReplayResult:
    """Replay R0 — vérifie l'intégrité des hashes ET le chaînage.

    R021-002 : en plus de recalculer chaque hash individuel, vérifie :
    - la monotonie stricte des sequence_no (1, 2, 3, ...)
    - que deux événements consécutifs sont liés (hash du précédent connu)  ← FAUX
    ...
    """
```

### Après (alignée sur le comportement réel)

```python
def verify_chain_r0(self) -> ReplayResult:
    """Replay R0 — vérifie les hashes individuels et la monotonie des séquences.

    R021-002 : deux contrôles effectués :
    1. Recalcul du hash SHA-256 de chaque événement et comparaison au hash stocké.
    2. Vérification que sequence_no augmente strictement (1, 2, 3, …).

    Ces contrôles détectent la modification du contenu d'un événement
    et un réordonnancement si les sequence_no ne sont pas recalculés avec lui.
    Ils ne vérifient pas de lien parent-hash entre événements successifs
    (R023-002 — non implémenté) ...
    """
```

La mention de « deux événements consécutifs sont liés (hash du précédent connu) » est supprimée. La docstring renvoie désormais explicitement à R023-002 pour le chaînage non implémenté.

---

## 4. R023-001 — `DEMO_SECRET_PLACEHOLDER` renommé

```python
# Avant
"data": "DEMO_SECRET_PLACEHOLDER",

# Après (R023-001)
"data": "test:exfil-fixture",   # R023-001 — valeur inerte, pas un vrai secret
```

Aucun test ne référençait littéralement cette chaîne. Les tests D4 (scénario complet) restent PASS.

---

## 5. Résultats complets après corrections

```
34 passed in 0.22s
```

| Suite | Tests | PASS | FAIL |
|---|---|---|---|
| Rust `cargo test` | 45 | 45 (déclarés) | 0 |
| Python C-07 (instrumentation) | 21 | 21 | 0 |
| Tests différentiels PyO3 (D-001→D-006) | 6 | 6 (déclarés) | 0 |
| Démo 4 agents (D4-01→D4-12 + D4-context) | 13 | 13 | 0 |
| **Total Python observé** | **34** | **34** | **0** |

---

## 6. Limites maintenues

Les constats suivants restent ouverts, non affectés par ce commit :

| ID | Constat | Priorité | État |
|---|---|---|---|
| R021-005 | Preuve en mémoire — persistance durable non démontrée | P1 | OUVERT |
| R023-002 | R0 sans `previous_event_hash` chaîné | P2 | OUVERT (référencé dans docstring corrigée) |
| L-019-002 | Replay R2/R3 | P2 | OUVERT |

---

## 7. Distinction docstring vs implémentation (note pour les auditeurs suivants)

R026-002 était une correction documentaire pure. Le comportement de `verify_chain_r0()` n'a pas changé — seule sa description a été mise en conformité avec ce qu'il fait réellement. R023-002 (implémentation du parent-hash) reste un chantier distinct, ouvert.

---

## 8. Contrôle de périmètre

- Fichiers applicatifs modifiés : `instrumentation.py` (correction R026-001), `attacker_agent.py` (correction R023-001), `defender_agent.py` (correction R026-002), `test_instrumentation.py` (4 tests sentinelles ajoutés).
- Rapport : R027 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Projet VLC&ARTCB : aucune migration ni intégration.
- Logs bruts : aucun ajouté.

---

## 9. Formule de présentation pour R026

> « Les trois corrections P2 de R026 sont fermées. La fuite indirecte par exception est corrigée dans `instrumentation.py` et couverte par 4 tests sentinelles. La docstring du replay est alignée sur son comportement réel. Le placeholder lexical est renommé. Score Python observé : 34/34 PASS. »
