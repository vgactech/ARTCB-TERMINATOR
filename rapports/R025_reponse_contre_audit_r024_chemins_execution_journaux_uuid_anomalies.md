# R025 — Réponse au contre-audit R024 : chemins d'exécution, journaux, UUID et anomalies

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R025 |
| Date | 2026-10-10 |
| Commits audités | `a42505c` (code), `0d3328e` (R023), `d5af449` (R024) |
| Dépôt | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| Portée | Réponse technique aux trois points du contre-audit R024 ; aucun code modifié |
| Exécution indépendante | ✅ 30/30 PASS observés dans cette session (`pytest guardian_mcp/ -v`) |
| Push distant | ✅ R023 et R024 poussés vers `origin/main` — disponibles sur GitHub |

---

## 1. Précision préliminaire : synchronisation distante

Le contre-audit note que R023 et R024 n'étaient pas visibles sur GitHub. Ils ont été poussés au début de cette session :

```
git push origin main
→ a42505c..d5af449  main -> main
```

Les deux rapports sont désormais sur `origin/main`. Le décalage constaté était un retard de push local, non une incohérence de contenu.

---

## 2. Point A — Chemins d'exécution indirects

Le contre-audit demande de compléter la preuve de confinement par :
- l'absence d'imports dynamiques ;
- la vérification des points d'entrée ;
- l'isolation à l'exécution.

### 2.1 Analyse AST — imports dynamiques

Une analyse AST complète (`ast.walk` sur les 8 fichiers Python) a été exécutée, recherchant les appels à `__import__`, `eval`, `exec`, `compile`, `importlib.import_module`. Résultat :

```
__init__.py:        OK
agents.py:          OK
attacker_agent.py:  OK
defender_agent.py:  OK
demo_scenario.py:   OK
instrumentation.py: OK
test_demo_scenario.py: OK
test_instrumentation.py: OK
```

**Aucun import dynamique, `eval`, `exec` ni `subprocess` n'est présent dans le code source.** Les occurrences textuelles de `exec`/`eval` trouvées par `grep` dans le rapport R024 étaient des sous-chaînes dans des noms de variables (`_executor_call_count`, `_evaluate_policy`, `execute_tool`) ou des commentaires — confirmé par l'analyse AST.

### 2.2 Graphe d'imports statiques (produit par analyse AST)

```
instrumentation.py → hashlib, json, logging, time, uuid, dataclasses, enum, typing, datetime
agents.py          → guardian_mcp.attacker_agent, guardian_mcp.instrumentation
attacker_agent.py  → hashlib, json, uuid, dataclasses  [stdlib seulement]
defender_agent.py  → guardian_mcp.attacker_agent, guardian_mcp.instrumentation
demo_scenario.py   → guardian_mcp.agents, guardian_mcp.attacker_agent,
                     guardian_mcp.defender_agent, guardian_mcp.instrumentation, copy, sys
test_*.py          → couche démo + instrumentation + pytest
```

`instrumentation.py` n'importe aucun module de la couche démo. Le graphe est acyclique et à sens unique.

### 2.3 Points d'entrée opérationnels

- **Binaire Rust `guardian`** (`guardian_core/Cargo.toml`, `src/main.rs`) : zéro référence aux classes Python démo, confirmé par `grep -rn` exhaustif sur `guardian_core/src/`.
- **Module PyO3 `artcb_guardian_core`** : exposé via Maturin, correspond à `instrumentation.py` côté Python. Aucun exécuteur factice accessible.
- **`__init__.py`** : vide — n'expose aucun symbole public.

### 2.4 Isolation à l'exécution

L'isolation à l'exécution repose sur la structure du code, vérifiable par les tests :

- `test_d4_11_two_runs_no_cross_contamination` : deux instances `DefenderAgent` indépendantes ne partagent aucun événement — **PASS**.
- `test_d4_03_exfiltration_executor_never_called` : le compteur d'exécution reste à zéro après BLOCK — **PASS**. Cela n'est possible que si aucun chemin indirect n'appelle l'exécuteur.

### 2.5 Niveau de preuve — nuance maintenue

Le contre-audit demande de distinguer :

| Niveau | État |
|---|---|
| Séparation statique des imports | ✅ Démontrée par AST |
| Absence de références Rust aux classes démo | ✅ Démontrée par grep exhaustif |
| Absence d'imports dynamiques | ✅ Démontrée par AST |
| Isolation à l'exécution | ✅ Démontrée par les tests D4-03 et D4-11 |
| Absence absolue de tout chemin indirect possible | ⚠️ Non démontrable de façon universelle — limite inhérente à toute analyse statique |

La limite universelle signalée par le contre-audit est exacte et est maintenue. Elle s'applique à tout système Python — un programme pourrait théoriquement utiliser des canaux non analysés (fichiers, sockets, variables d'environnement). Dans ce code, aucun tel mécanisme n'est présent ; la preuve est forte mais non absolue.

---

## 3. Point B — `DEMO_SECRET_PLACEHOLDER` : chemin complet et journaux

Le contre-audit demande de vérifier trois sous-points :
1. Que le blocage précède effectivement tout effet de bord de l'exécuteur.
2. Que le compteur d'exécution reste à zéro.
3. Que les journaux ne contiennent pas les paramètres sensibles en clair.

### 3.1 Ordre des opérations dans `handle_tool_call()`

Le code source de `instrumentation.py` montre l'ordre suivant :

```python
# 1. Évaluation de politique — AVANT tout appel à executor
decision, reason = _evaluate_policy(tool_name, arguments)

# 2. Branche BLOCK — executor n'est jamais appelé
elif decision == GuardianDecision.BLOCK:
    result = {"isError": True, "content": [...]}
    output_summary = f"BLOCKED:{reason}"
    # → executor n'est pas dans cette branche

# 3. Enregistrement de l'événement
event = MCPToolEvent(
    input_hash=_sha256_hex(json.dumps(arguments, sort_keys=True).encode()),
    ...
)
```

**`wallet.sign` est dans `_SENSITIVE_TOOLS` → décision BLOCK retournée immédiatement → la branche `executor` n'est jamais atteinte.** La valeur `DEMO_SECRET_PLACEHOLDER` est présente dans `arguments` au moment du hachage, mais l'exécuteur n'est jamais invoqué.

### 3.2 Compteur d'exécution

Test D4-03 : `defender.executor_call_count == 0` après `attempt_tool_call(exfil_call)` — **PASS observé**. Ce test prouve l'invariant au niveau du code Python de démonstration.

### 3.3 Journaux — paramètres sensibles en clair

Analyse complète des appels `logger.*` dans `instrumentation.py` :

```python
logger.error("Erreur outil %s : %s", tool_name, exc)          # aucun argument
logger.error("Erreur outil %s (REDACT) : %s", tool_name, exc) # aucun argument
logger.info(
    "GuardianMCP [%s] tool=%s decision=%s hash=%s…",
    event.event_id[:8],
    event.tool_name,
    event.decision.value,
    event_hash[:12],                                           # 12 premiers chars du hash
)
```

**Aucun appel `logger` ne logue les `arguments` en clair.** Le seul champ dérivé des arguments dans les journaux est `event_hash[:12]` — les 12 premiers caractères du SHA-256 de l'événement complet, non les arguments eux-mêmes.

### 3.4 Verdict révisé sur `DEMO_SECRET_PLACEHOLDER`

| Sous-point | Résultat |
|---|---|
| Blocage avant exécuteur | ✅ Démontré par le code source (`_evaluate_policy` avant `executor`) |
| Compteur exécution = 0 | ✅ Démontré par test D4-03 PASS |
| Arguments non loggés en clair | ✅ Démontré par analyse des appels `logger.*` |
| Valeur hashée dans `input_hash` | ✅ Confirmé — SHA-256(arguments), non transmis à l'extérieur |
| Réserve lexicale | ⚠️ P2 maintenue — correction R023-001 recommandée si scanner actif |

La correction lexicale (renommer en `"test:exfil-fixture"`) reste distincte et indépendante de la correction fonctionnelle. Comme le note le contre-audit, renommer ne remplace pas les tests d'isolation — et ces tests existent (D4-03, D4-11).

---

## 4. Point C — UUID et preuves cryptographiques : clarification du contrat

Le contre-audit énonce que « un UUID ne prouve ni l'authenticité de l'auteur, ni l'intégrité du contenu, ni l'exécution effective d'une opération ». Ce point est exact.

### 4.1 Ce que l'UUID EvidenceId prouve réellement

L'`evidence_id` de format `evidence:UUID` est un **identifiant de traçabilité structurelle**, pas une signature cryptographique. Il prouve :

- Qu'un identifiant distinct a été créé pour chaque décision BLOCK.
- Qu'il est enregistré dans le registre interne avec le lien `evidence_id → guardian_event_id`.
- Qu'un test négatif (D4-08, vider le registre) entraîne un échec R1 — la vérification n'est pas tautologique.

Il ne prouve pas :
- L'authenticité de l'auteur (pas de signature asymétrique).
- L'intégrité du contenu au-delà du hash SHA-256 de l'événement.
- L'exécution effective d'une opération par un service réel.

### 4.2 Ce que le hash SHA-256 de l'événement (`MCPToolEvent.compute_hash()`) prouve réellement

Le hash de l'événement couvre l'ensemble des champs canoniques de `MCPToolEvent` (sérialisés en JSON trié, avec préfixe domaine `ARTCB-GUARDIAN-EVENT-V1`). Il prouve :
- L'intégrité du contenu de l'événement individuel en mémoire.
- La détection d'une modification post-enregistrement (D4-09 PASS).

Il ne prouve pas :
- Un chaînage `previous_event_hash` entre événements consécutifs.
- La persistance après redémarrage.

### 4.3 Hiérarchie de preuves — état actuel

| Niveau | Mécanisme actuel | Prouve | Ne prouve pas |
|---|---|---|---|
| Hash individuel (R0) | SHA-256 avec préfixe domaine | Intégrité d'un événement | Ordre global, persistance |
| Séquence (R0) | `sequence_no` monotone | Ordre d'enregistrement en mémoire | Résistance à la suppression |
| EvidenceId (R1) | UUID + registre interne | Traçabilité BLOCK→preuve | Authenticité, intégration Rust |
| Parent-hash (absent) | Non implémenté | — | Chaîne résistante à la suppression |
| Persistance (absent) | Non implémenté | — | Reconstruction après redémarrage |

Ces limites sont déclarées et documentées. Elles restent ouvertes sous R021-005 (persistance) et R023-002 (parent-hash).

---

## 5. État des anomalies ouvertes — vérification de non-régression

Les quatre anomalies citées dans le contre-audit sont relues dans leurs rapports sources et confirmées dans leur état :

| ID | Origine | Constat | Critère de clôture | État |
|---|---|---|---|---|
| R021-005 | R021 §2.6 | Preuve en mémoire — persistance durable non démontrée | Test qui écrit, ferme/recharge le stockage Rust et rejoue l'archive rechargée | **OUVERT** |
| R023-001 | R023 §2.3 | `DEMO_SECRET_PLACEHOLDER` — réserve lexicale | Renommer la fixture ; aucun scanner actif ne signale de violation | **OUVERT (P2)** |
| R023-002 | R023 §2.5 | R0 sans `previous_event_hash` chaîné entre événements | Implémenter le champ et tester la détection de réordonnancement | **OUVERT (P2)** |
| L-019-002 | R019 | Replay R2/R3 non implémentés | Définir les invariants R2/R3 et les tests correspondants | **OUVERT (P2)** |

Aucune de ces anomalies n'a régressé ni été clôturée par R024 ou R025. Leur historique est intact.

---

## 6. Ce que R025 modifie par rapport à R023 et R024

R025 précise trois points non couverts par R024 :

1. **Import dynamiques** : vérification AST complète confirme l'absence de `__import__`, `eval`, `exec`, `importlib.import_module` (R024 avait seulement exclu les références Rust).

2. **Journaux** : analyse exhaustive des appels `logger.*` confirme que les `arguments` ne sont jamais loggés en clair.

3. **Hiérarchie de preuves** : tableau explicite distinguant ce que prouve chaque mécanisme (hash individuel, séquence, EvidenceId, parent-hash absent).

---

## 7. Contrôle de périmètre

- Code applicatif : **aucune modification effectuée**.
- Rapports produits : R025 uniquement.
- Dépôt `vgactech/artcb` : aucune écriture.
- Projet VLC&ARTCB : aucune migration ni intégration.
- Logs bruts : aucun ajouté.
- Push : R023 + R024 poussés vers `origin/main` en début de session ; R025 sera poussé avec ce fichier.

---

## 8. Conclusion

| Point du contre-audit | Réponse apportée |
|---|---|
| Confinement par imports statiques seulement ? | ✅ Complété par AST (imports dynamiques), grep Rust, tests D4-03/D4-11 |
| `DEMO_SECRET_PLACEHOLDER` atteint-il un chemin dangereux ? | ✅ Hashé mais pas loggé en clair ; blocage avant exécuteur démontré |
| UUID = preuve cryptographique ? | ✅ Clarifié : traçabilité structurelle, pas authenticité ni résistance à la suppression |
| Anomalies R021-005, R023-001, R023-002, L-019-002 | ✅ Relues, non régressées, toutes maintenues ouvertes avec leurs critères de clôture |

La limite universelle de l'analyse statique (impossibilité de prouver l'absence absolue de tout chemin indirect) est maintenue — elle est inhérente à tout audit logiciel. Dans ce code, les mécanismes d'exécution indirecte attendus (imports dynamiques, sous-processus, plugins) sont absents, ce qui constitue une preuve forte mais non absolue.
