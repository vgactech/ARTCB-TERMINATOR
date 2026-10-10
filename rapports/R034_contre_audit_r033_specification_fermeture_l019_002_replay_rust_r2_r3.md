# R034 — Contre-audit R033 et spécification de fermeture L-019-002 (Replay Rust R2/R3)

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R034 |
| Date | 2026-10-10 |
| Dépôt audité | `vgactech/ARTCB-TERMINATOR` |
| Branche observée | `main` |
| Dernier commit observé | `6bc9db9757cba4c3e1f38e6e2664e72a9dd199d8` |
| Base code R033 | `2de19eee7d6c2c1ee44a113e72c454a3acaa1046` |
| Portée | Vérification distante en lecture seule ; analyse R033 ; définition des critères de fermeture de L-019-002 |
| Écriture | Ce rapport uniquement dans `rapports/` ; aucun code applicatif modifié |
| Dépôt historique `vgactech/artcb` | Aucune écriture |
| Logs bruts | Aucun ajouté au dépôt |

## Expertises activées

- Audit GitHub et vérification de commits
- Architecture Rust/Python et bindings PyO3
- Replay déterministe et sécurité des outils
- Event sourcing, journaux durables et intégrité cryptographique
- Concurrence multiprocessus
- Forensic et classification IN_DOUBT
- Tests adversariaux et validation de contrats

## 1. Résumé exécutif

La synchronisation GitHub confirme que les commits R033 annoncés existent sur `main` :

- Code : [2de19ee](https://github.com/vgactech/ARTCB-TERMINATOR/commit/2de19eee7d6c2c1ee44a113e72c454a3acaa1046)
- Rapport : [6bc9db9](https://github.com/vgactech/ARTCB-TERMINATOR/commit/6bc9db9757cba4c3e1f38e6e2664e72a9dd199d8)

Le rapport R033 consigne 77 tests réussis (64 instrumentation + 13 scénario). Le statut combiné CI consulté pour le commit de code ne renvoie aucun statut : ce résultat ne constitue donc pas une confirmation indépendante d'une exécution GitHub Actions.

**Verdict : R033 apporte des améliorations réelles de traçabilité, mais L-019-002 demeure ouvert.** L'analyse directe du code Rust montre que `ReplayLevel` déclare R0 à R4, tandis que `ReplayEngine` n'implémente que R0 et R1. Les fonctions de replay ne sont pas exposées dans le module PyO3 actuellement inspecté. R2/R3 ne doivent donc pas être considérés comme opérationnels au seul motif que leurs variantes d'énumération existent.

## 2. R033 — bénéfices confirmés et limites restantes

### 2.1 INTENT / TERMINAL

**Processus :** chaque appel Python instrumenté émet une intention avant l'exécuteur, puis un événement terminal lié par `intent_id`. Ces champs font partie du corps canonique hashé.

**Problème :** l'écriture d'un INTENT ne rend pas atomiques une action externe et sa trace terminale. Un outil peut avoir produit son effet puis le processus peut crasher avant l'écriture du TERMINAL. L'état est réellement indéterminé.

**Solution :** garder l'appel en IN_DOUBT, ne pas le relancer automatiquement, réconcilier l'état auprès de l'outil externe et utiliser une clé d'idempotence quand elle est prise en charge. L'absence de TERMINAL ne prouve ni succès ni échec.

### 2.2 Barrière de replay Python

**Processus :** `handle_tool_call(..., is_replay=True)` supprime les branches d'exécution pour les décisions ALLOW et REDACT.

**Problème :** `is_replay` est optionnel et vaut `False` par défaut. La garantie est donc locale à cette méthode et dépend encore de la bonne transmission du drapeau. Elle n'est pas une garantie globale du système.

**Solution :** faire du mode replay un contexte d'exécution explicite et fermé par défaut, dans lequel aucun exécuteur externe n'est accessible. Le niveau supérieur doit refuser un replay si ce contexte ne peut pas être garanti. Les tests doivent vérifier qu'aucun appel réseau, processus, écriture métier ou autre effet externe n'est déclenché.

### 2.3 Multiprocessus

**Processus :** le test annoncé démarre quatre processus et valide 24 lignes JSONL syntaxiquement correctes.

**Problème :** la validité JSON ne prouve pas une chaîne globale cohérente. Le rapport R033 indique lui-même que le test ne valide pas le chaînage `previous_event_hash` entre processus.

**Solution :** séparer les propriétés testées : absence d'entrelacement, verrouillage exclusif, séquence unique, chaînage global, reprise après crash et validation après redémarrage. Si les processus émettent des chaînes indépendantes, le modèle de données doit le dire explicitement au lieu de présenter le fichier comme une seule chaîne.

### 2.4 IN_DOUBT

**Processus :** `find_in_doubt_intents` détecte les identifiants INTENT sans TERMINAL associé.

**Problème :** la fonction ne valide pas à elle seule l'intégrité du journal. Une archive tronquée ou altérée peut produire une vue incomplète.

**Solution :** vérifier d'abord l'intégrité, la continuité et les ancrages du journal ; classer ensuite les intentions orphelines. Une erreur de vérification du journal doit être distincte du statut IN_DOUBT d'un appel.

## 3. L-019-002 — constat Rust observé

Fichiers consultés en lecture seule :

- `guardian_core/src/replay/engine.rs`
- `guardian_core/src/python_bindings.rs`
- `guardian_core/src/event/ledger.rs`
- `guardian_core/src/lib.rs`
- `guardian_core/Cargo.toml`
- `guardian_mcp/defender_agent.py`
- rapports historiques R018 et R029, puis rapport R033

### 3.1 Écart entre déclaration et implémentation

**Processus :** `ReplayLevel` déclare `R0Structural`, `R1PolicyDecisions`, `R2SimulatedTools`, `R3ControlledExecution` et `R4AIQualified`.

**Problème :** dans `ReplayEngine`, seules les méthodes `replay_r0` et `replay_r1_policy` sont présentes. Les variantes R2/R3/R4 ne constituent pas des implémentations. Le module PyO3 consulté expose la construction d'événement, la canonicalisation, le hash, la validation, la politique et des utilitaires, mais pas de fonction de replay R2/R3.

**Solution :** implémenter les niveaux comme contrats séparés et les exposer explicitement après validation des interfaces. Tant que cette étape n'est pas réalisée et testée, le statut doit rester « non implémenté ».

### 3.2 Contrôles supplémentaires nécessaires en R0

La méthode R0 consultée recalcule le hash du corps de chaque événement et le compare à `event_hash`. Elle ne semble pas, dans cette méthode, vérifier elle-même l'ensemble des invariants d'enveloppe et de manifeste.

Avant de prendre R0 comme précondition sûre pour R2/R3, vérifier aussi :

- le nombre d'entrées par rapport à `manifest.entries_count` ;
- l'identité du flux et l'ordre de `stream_sequence` ;
- la relation entre `previous_event_hash`, `event_hash` et `chain_hash` ;
- le `original_chain_tip` annoncé par le manifeste ;
- le run, les versions de schéma et de politique attendues ;
- les entrées dupliquées, manquantes, réordonnées ou étrangères au flux ;
- l'ancrage externe attendu pour détecter la troncature de fin.

Un hash de corps valide, pris isolément, ne prouve pas que l'enveloppe, le chaînage, le manifeste et la complétude du flux sont valides.

### 3.3 Limite de R1

La méthode R1 consultée vérifie notamment qu'une décision BLOCK possède un `evidence_id`. Cette vérification est utile, mais elle ne réexécute pas le moteur de politique à partir des mêmes entrées et de la même version de règles. Elle ne suffit donc pas à démontrer la reproductibilité d'une décision.

Le rapport R018 avait déjà distingué cette exigence d'une simple vérification d'intégrité. Cette tâche historique reste pertinente pour la qualité du socle R2/R3.

## 4. Contrat proposé pour R2 — outils simulés

### Processus

R2 rejoue le scénario à partir des événements et des réponses d'outils archivées. Les outils sont remplacés par des fixtures déterministes : aucun service externe réel ne doit être appelé.

### Problème à résoudre

Le journal d'événements ne garantit pas à lui seul que les réponses d'outils ont été conservées intégralement, reliées au bon appel et versionnées. Une réponse manquante ou associée au mauvais événement peut fabriquer un replay trompeur.

### Critères d'implémentation

1. Associer chaque invocation à un identifiant stable et à son `intent_id`.
2. Archiver l'identité de l'outil, le hash des entrées, la réponse canonique ou une référence vérifiable à cette réponse, ainsi que son statut.
3. Relier la réponse au run, à l'événement terminal et à la version du contrat de l'outil.
4. Refuser le replay en cas de fixture manquante, dupliquée, invalide ou incompatible ; ne pas appeler silencieusement l'outil réel comme solution de repli.
5. Vérifier les décisions Guardian et les sorties canoniques attendues.
6. Produire un rapport indiquant les événements rejoués, les divergences, les données manquantes et les limites.
7. Réutiliser les preuves de R0 et vérifier la complétude de l'archive avant le replay.

### Tests d'acceptation R2

- Toutes les fixtures sont utilisées dans le bon ordre et le résultat correspond à l'original.
- Un compteur sentinelle prouve que zéro exécuteur externe a été appelé.
- Une fixture absente entraîne un FAIL explicite.
- Une fixture altérée, réordonnée ou dupliquée entraîne un FAIL.
- Une réponse associée au mauvais `intent_id` entraîne un FAIL.
- Une décision Guardian modifiée entraîne un FAIL.
- Un INTENT orphelin conduit à IN_DOUBT et n'est jamais relancé automatiquement.
- Une archive tronquée sans ancrage suffisant ne peut pas obtenir PASS.

## 5. Contrat proposé pour R3 — exécution déterministe contrôlée

### Processus

R3 réexécute uniquement des composants autorisés et déterministes, dans un environnement isolé, avec les mêmes entrées, versions et paramètres. Il compare les sorties canoniques à celles de l'exécution initiale.

### Problème à résoudre

Une réexécution contrôlée n'est pas équivalente à R2 : elle exécute du code et peut produire des effets secondaires. De plus, certaines dépendances — horloge, aléa, concurrence, environnement, modèle distant — peuvent empêcher une reproduction bit à bit.

### Critères d'implémentation

1. Définir une liste explicite de composants admissibles à R3.
2. Exécuter dans un environnement isolé sans accès aux effets externes non autorisés.
3. Fixer ou injecter les sources de temps et d'aléa lorsque cela est nécessaire.
4. Enregistrer les versions de code, configuration, dépendances, politique et schéma.
5. Utiliser les mêmes entrées canoniques et comparer les sorties canoniques.
6. En cas de non-déterminisme documenté, déclarer le niveau de fidélité réellement obtenu ; ne pas annoncer une reproduction exacte.
7. Toute tentative d'effet externe non autorisé doit échouer fermement et apparaître dans le rapport.

### Tests d'acceptation R3

- Un composant déterministe produit les mêmes sorties canoniques avec les mêmes entrées.
- Une modification de version, de configuration ou d'entrée est détectée.
- Un effet secondaire externe est bloqué et comptabilisé comme tentative.
- Une dépendance non contrôlée empêche le verdict PASS au niveau R3 exact.
- Les divergences indiquent l'identifiant d'événement, le champ, la valeur originale et la valeur rejouée.
- Le niveau atteint ne peut jamais être supérieur au niveau effectivement validé.

## 6. Contrat commun du manifeste et du verdict

Le manifeste doit être vérifié, et non simplement transporté dans le rapport. Le moteur doit comparer le run demandé, le nombre d'entrées, la pointe de chaîne, les versions de schéma/politique et le niveau demandé aux données réellement chargées.

Règles de verdict :

- **PASS** : tous les invariants requis pour le niveau demandé sont vérifiés.
- **FAIL** : une divergence ou violation d'invariant est observée.
- **IN_DOUBT** : une opération est potentiellement exécutée, mais son résultat terminal n'est pas établi.
- **NOT_SUPPORTED / niveau non atteint** : l'implémentation ne prend pas en charge le niveau demandé ; ne jamais rétrograder silencieusement vers R0/R1 tout en affichant un PASS pour R2/R3.

Le rapport doit distinguer intégrité des traces, fidélité de simulation, déterminisme de l'exécution et exactitude métier. Ce sont des propriétés différentes.

## 7. Ordre de travail recommandé

| Ordre | Chantier | Critère de sortie |
|---|---|---|
| P0 | Durcir les préconditions R0/manifeste et la validation de chaîne | Archive complète et enveloppe vérifiées avant tout replay supérieur |
| P1 | Formaliser le contrat d'archive des réponses d'outils | Fixtures liées aux appels, versionnées et vérifiables |
| P1 | Implémenter R2 simulé et sa barrière sans effets externes | Tests négatifs et sentinelles démontrent zéro exécution externe |
| P1 | Implémenter R3 contrôlé dans un environnement isolé | Parité canonique pour les composants explicitement déterministes |
| P1 | Exposer les fonctions validées à Python via PyO3 | Tests de contrat Rust/Python |
| P2 | Traiter le replay IA R4 avec fidélité qualifiée | Fidélité documentée, sans prétendre au déterminisme exact du LLM |

## 8. Réconciliation des tâches antérieures

- **R018 :** l'analyse du moteur de replay avait déjà établi que R1 et les niveaux supérieurs restaient à implémenter. Ce point ne doit pas être considéré comme clos.
- **R029 :** L-019-002 a été analysé et son périmètre R2/R3 défini, mais il était explicitement encore ouvert.
- **R033 :** le journal INTENT/TERMINAL et la barrière locale de replay ont progressé ; ils ne remplacent pas le moteur de replay R2/R3.
- **L-019-002 :** reste **OUVERT** jusqu'à ce que les critères d'acceptation soient implémentés et validés par tests.

Les tâches antérieures non liées au replay ne sont pas déclarées closes par ce rapport. Elles doivent rester suivies dans leurs rapports de référence.

## 9. Contrôle de périmètre et conclusion

Cette itération a été une inspection distante en lecture seule suivie de la création de ce rapport. Aucun fichier applicatif n'a été modifié. Aucun changement n'a été effectué dans `vgactech/artcb`, aucun contenu n'a été migré vers VLC&ARTCB et aucun log brut n'a été ajouté.

**Conclusion :** R033 est une avancée utile, mais le point de contrôle principal suivant est la fermeture réelle de L-019-002. L'existence des types R2/R3 n'est pas une preuve d'implémentation. Il faut un contrat d'archive vérifiable, une barrière globale sans effets externes pour R2, une exécution contrôlée pour R3, des tests adversariaux, et une exposition Rust/Python validée avant de déclarer le chantier terminé.
