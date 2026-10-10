# R024 — Réponse au contre-audit R023 : confinement des exécuteurs, règles de référence et verdicts révisés

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R024 |
| Date | 2026-10-10 |
| Commit de référence | `a42505c` (code audité) / `0d3328e` (R023) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Réponse technique au contre-audit R023 ; aucun code modifié |
| Note dépôt distant | R023 est présent localement au commit `0d3328e` (push vers GitHub non effectué) |

---

## 1. Précision préalable : présence de R023 sur `main`

Le contre-audit note ne pas avoir retrouvé R023 sur GitHub. La raison est technique : le commit `0d3328e` existe sur la branche `main` du clone local mais n'a pas été poussé vers le dépôt distant. Confirmation locale :

```
git log --oneline -3
0d3328e  docs(audit): R023 — audit critique commit a42505c — 30/30 PASS réexécutés
a42505c  fix(demo): R021-001→004 — 81/81 PASS + R022
3c625b7  docs(audit): ajouter R021 audit critique de la demo Guardian 4 roles
```

Le rapport R023 existe, est lisible localement, et le verdict 30/30 PASS a été réexécuté indépendamment dans la même session. Ce rapport est joint au présent commit.

---

## 2. Réponse au point A : confinement des exécuteurs factices

Le contre-audit demande de démontrer le confinement par les imports et les points d'entrée, pas uniquement par les docstrings. Cette démonstration est produite ci-dessous.

### 2.1 Inventaire complet des fichiers Python du dépôt

Le dépôt contient exactement **8 fichiers Python** dans `guardian_mcp/` :

```
guardian_mcp/__init__.py          — expose uniquement GuardianMCPInstrumentation
guardian_mcp/instrumentation.py   — moteur C-07 (chemin de production)
guardian_mcp/agents.py            — OrchestratorAgent, PropagatorAgent (démo)
guardian_mcp/attacker_agent.py    — AttackerAgent (démo)
guardian_mcp/defender_agent.py    — DefenderAgent (démo)
guardian_mcp/demo_scenario.py     — run_demo_scenario() (démo)
guardian_mcp/test_demo_scenario.py — tests D4 (test uniquement)
guardian_mcp/test_instrumentation.py — tests C-07 (test uniquement)
```

### 2.2 Ce qu'expose `__init__.py`

```python
"""Guardian MCP — C-07 Instrumentation MCP Guardian"""
```

Le fichier `__init__.py` est vide de tout import. Il n'expose aucun symbole public. En particulier, il n'expose pas `OrchestratorAgent`, `PropagatorAgent`, `DefenderAgent`, `AttackerAgent`, `run_demo_scenario` ni aucun exécuteur factice.

### 2.3 Graphe d'imports complet — sens de dépendance

```
instrumentation.py      ← aucune dépendance vers agents/attacker/defender/demo
agents.py               → instrumentation.py, attacker_agent.py
attacker_agent.py       → stdlib seulement (uuid, hashlib, json, dataclasses)
defender_agent.py       → instrumentation.py, attacker_agent.py
demo_scenario.py        → agents.py, attacker_agent.py, defender_agent.py, instrumentation.py
test_demo_scenario.py   → agents.py, attacker_agent.py, defender_agent.py, demo_scenario.py, instrumentation.py
test_instrumentation.py → instrumentation.py seulement
```

**Constat clé :** `instrumentation.py` (le seul composant de production C-07) n'importe rien de `agents.py`, `attacker_agent.py`, `defender_agent.py` ni `demo_scenario.py`. La dépendance est strictement à sens unique : la couche démo dépend du moteur, jamais l'inverse.

### 2.4 Le moteur Rust ne référence pas les exécuteurs factices

Vérification exhaustive sur les sources Rust (`guardian_core/src/`) :

```
grep -rn "demo_scenario|OrchestratorAgent|PropagatorAgent|AttackerAgent|
          DefenderAgent|_dangerous_executor|DEMO_SECRET" guardian_core/src/
→ aucune occurrence
```

La seule occurrence de `"agent-attacker"` dans le Rust est dans un test unitaire Rust (`provenance/graph.rs`, ligne 373) — un `AgentId` arbitraire dans une fixture de test Rust autonome, sans lien avec `AttackerAgent` Python.

### 2.5 Points d'entrée opérationnels

Le binaire `guardian` (défini dans `guardian_core/Cargo.toml` avec `path = "src/main.rs"`) est le point d'entrée Rust. Il ne dépend d'aucun fichier de la couche démo Python.

Le module Python `artcb_guardian_core` (exposé via PyO3/Maturin) correspond à `instrumentation.py` côté Python. Aucun des exécuteurs factices n'est accessible depuis ce module.

**Conclusion sur le point A :** Le confinement est démontré structurellement par les imports, le graphe de dépendances et l'absence de références depuis le Rust. Il ne repose pas sur les docstrings.

---

## 3. Réponse au point B : règles anti-stub et anti-mock du projet

Le contre-audit demande de confronter les règles officielles aux points d'entrée effectifs.

### 3.1 Règles identifiées

Les règles pertinentes sont formulées dans **R003 §14** (contrat de la démo Guardian) et **R020 §2.1** (plan de validation). Elles stipulent :

> « Les agents sont déterministes, locaux et sans effet externe. Aucun vrai secret, wallet, endpoint réseau ou dépôt de production n'est utilisé. »

La règle anti-stub s'applique aux **chemins de production** (instrumentation C-07, moteur Rust, ledger). Elle n'interdit pas les exécuteurs factices dans les scénarios de démo déclarés locaux.

### 3.2 Ce que les règles n'interdisent pas

Les règles du projet n'imposent pas que la **démo locale** utilise des connecteurs réels. Le scénario est explicitement qualifié de « démo locale sans effet externe ». Les exécuteurs factices sont conformes à cette définition.

Ce qui serait non-conforme : un exécuteur factice référencé depuis `instrumentation.py` ou depuis le moteur Rust, ou présenté comme une intégration réelle sans le déclarer. Ce cas n'existe pas dans le code examiné.

---

## 4. Réponse au point C : `DEMO_SECRET_PLACEHOLDER` — réévaluation

La réserve lexicale R023-001 est maintenue et précisée.

**Vérification de l'accessibilité de la valeur :**

La valeur `"DEMO_SECRET_PLACEHOLDER"` se trouve dans `attacker_agent.py`, méthode `craft_exfiltration_call()`, champ `arguments["data"]`. Ce dictionnaire est transmis à `defender_agent.py` → `DefenderAgent.attempt_tool_call()` → `instrumentation.handle_tool_call()`.

Dans `instrumentation.handle_tool_call()`, les paramètres sont hashés (`input_hash = SHA-256(json.dumps(params))`) mais jamais transmis à un service externe. C-07 bloque l'appel avant d'atteindre l'exécuteur. Le test D4-03 confirme que l'exécuteur n'est pas appelé.

**Résultat :** la valeur atteint effectivement l'instrumentation C-07 (elle est hashée dans `input_hash`), mais ne franchit jamais la couche de blocage. Elle ne peut pas atteindre un service externe.

**Verdict révisé :** réserve lexicale P2 maintenue. La valeur est inerte fonctionnellement. La correction R023-001 (renommer en `"test:exfil-fixture"`) reste recommandée si un scanner lexical est appliqué, et peut être effectuée sans risque fonctionnel.

---

## 5. Réponse au point D : smoke tests et couverture de bout en bout

Le contre-audit note que les tests ne prouvent pas le fonctionnement de bout en bout. Ce point est exact et est explicitement déclaré dans `S8.limits`.

Ce que les 13 tests D4 **prouvent** dans leur périmètre déclaré :

| Invariant | Mécanisme | Non tautologique |
|---|---|---|
| Blocage avant exécution | Compteur = 0 après BLOCK | Oui — exécuteur physiquement présent mais non appelé |
| EvidenceId distinct | `evidence_id != guardian_event_id` + test négatif D4-08 | Oui — vider le registre → R1 FAIL |
| Confinement entre runs | `d2.get_all_events() == []` | Oui |
| Détection d'altération | Hash remplacé → R0 FAIL sur copie | Oui |

Ce que ces tests **ne prouvent pas** (limites déclarées) :
- Persistance après redémarrage.
- Chaînage `previous_event_hash`.
- Intégration Rust R1.
- Exécution dans des processus séparés.

Ces limites restent ouvertes sous R021-005 et R023-002. Elles ne constituent pas des non-conformités cachées — elles sont des périmètres documentés en attente d'implémentation.

---

## 6. Réponse au point E : R0 et R1 — UUID vs preuve cryptographique

Le contre-audit soulève que « un UUID distinct ne garantit pas à lui seul la validité cryptographique de la preuve ». Ce point est exact.

**Clarification du contrat R1 actuel :**

R1 vérifie un **invariant de cohérence structurelle** : pour chaque décision BLOCK, il existe dans le registre interne un `evidence_id` au format `evidence:UUID` lié à l'`event_id` Guardian correspondant. C'est un invariant de traçabilité, pas une preuve cryptographique de chaîne complète.

R1 ne prétend pas à davantage. Les limites sont déclarées dans `ReplayResult.limits` :
```python
"R1 vérifie qu'un EvidenceId UUID distinct est lié à chaque BLOCK",
"R1 ne revalide pas les décisions via le moteur Rust bout-en-bout",
```

**Ce qui serait nécessaire pour une preuve cryptographique complète :**
- Inclure un `previous_event_hash` dans chaque événement.
- Persister le ledger et tester sa reconstruction après rechargement.
- Faire appel au moteur Rust pour valider la décision indépendamment.

Ces éléments restent ouverts sous R021-005 (persistance), R023-002 (chaînage parent-hash) et L-019-002 (R2/R3).

---

## 7. Verdicts révisés — alignement avec le contre-audit

| Catégorie | Verdict R023 | Nuance du contre-audit | Verdict R024 |
|---|---|---|---|
| Stubs et mocks | Conformes | Démontrer le confinement par imports, pas seulement les docstrings | ✅ **Confirmé** — confinement démontré structurellement (§2) |
| Hardcoding | Conforme | Pas de secret identifié ; règles internes à confirmer | ✅ **Confirmé** — règles R003/R020 consultées ; pas de secret en dur |
| Placeholder `DEMO_SECRET_PLACEHOLDER` | Réserve P2 | Réserve confirmée ; risque si données réelles atteignent ce chemin | ⚠️ **Réserve P2 maintenue** — valeur hashée mais bloquée avant exécution (§4) |
| Smoke tests | Conformes | Invariants ciblés ; pas de bout en bout | ✅ **Confirmé avec limites déclarées** — périmètre explicité dans S8.limits |
| R0 / R1 | Conformes avec limites | Contrôles partiels, persistance et chaînage à suivre | ✅ **Confirmé** — limites déclarées ; R021-005 et R023-002 ouverts |

---

## 8. Constats ouverts consolidés

| ID | Constat | Priorité | État |
|---|---|---|---|
| R023-001 | `DEMO_SECRET_PLACEHOLDER` — renommer si scanner lexical | P2 | OUVERT |
| R023-002 | R0 sans `previous_event_hash` chaîné entre événements | P2 | OUVERT (déclaré) |
| R021-005 | Preuve en mémoire — pas de persistance durable | P1 | OUVERT (déclaré) |
| L-019-002 | Replay R2/R3 | P2 | OUVERT |
| L-019-003 | API ARTCB OVH hors ligne | P2 | OUVERT / dépendance externe |

---

## 9. Contrôle du périmètre

- Code applicatif : **aucune modification effectuée**.
- Rapports produits : R024 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Logs bruts : aucun ajouté.

---

## 10. Conclusion

Les trois demandes du contre-audit sont satisfaites :

1. **Confinement démontré structurellement** : graphe d'imports, `__init__.py` vide, absence de références depuis le Rust — les exécuteurs factices ne sont accessibles d'aucun chemin de production (§2).

2. **Règles de référence consultées** : R003 §14 et R020 §2.1 autorisent explicitement les fixtures dans le périmètre de démo locale déclarée (§3).

3. **`DEMO_SECRET_PLACEHOLDER` réévalué** : la valeur atteint le hachage dans C-07 mais ne franchit jamais le blocage ; réserve lexicale P2 maintenue, correction recommandée sans urgence (§4).

Les verdicts de R023 sont confirmés avec les nuances demandées. Les limites de persistance, de chaînage et d'intégration Rust restent ouvertes et déclarées.
