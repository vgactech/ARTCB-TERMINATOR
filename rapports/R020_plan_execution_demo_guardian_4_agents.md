# R020 — Plan d'exécution et critères d'acceptation de la démo Guardian à quatre agents

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R020 |
| Date | 2026-10-10 |
| Dépôt | `vgactech/ARTCB-TERMINATOR` |
| Branche examinée | `main` |
| Référence de départ | R019, commit `d698e3489674e535494df11058ebca463f6a67c9` |
| Portée de cette révision | Audit de conception et plan de validation ; aucun code applicatif modifié |
| Priorité | P0 — démonstration Secure Horizons, Track 2 « Defenders Augmented » |

## Expertises activées

- Architecture d'agents IA et orchestration multi-agents ;
- sécurité des outils et défense contre l'injection de prompt ;
- instrumentation MCP et événements d'audit ;
- politiques Guardian ALLOW/BLOCK/REDACT/ESCALATE ;
- intégrité cryptographique, chaîne de preuves et rejeu R0/R1 ;
- tests de scénarios, tests adversariaux et reproductibilité ;
- gouvernance GitHub et contrôle du périmètre des changements.

## 1. Résumé exécutif

R019 identifie la démonstration Guardian à quatre agents comme le livrable P0 encore absent. Les composants C-01 à C-08 sont déclarés implémentés et testés dans R019, pour un total de 68 tests PASS rapportés. Ce résultat constitue la baseline documentaire ; les tests n'ont pas été réexécutés pendant la préparation de ce rapport.

Le dépôt contient déjà `guardian_mcp/instrumentation.py`. Cette couche intercepte les appels d'outils, applique une politique Python élémentaire, émet un `MCPToolEvent`, calcule son hash et renvoie un identifiant d'événement dans la réponse. Elle conserve par défaut les événements en mémoire via `_default_sink`. Le moteur de politique Rust est présent dans `guardian_core/src/policy/engine.rs`, et le moteur de rejeu dans `guardian_core/src/replay/engine.rs`.

**Conclusion critique :** il faut démontrer une chaîne cohérente de bout en bout, et non simplement montrer quatre classes portant le nom d'agents. Le scénario doit prouver qu'une action hostile est détectée, bloquée avant l'exécution de l'outil sensible, associée à une preuve identifiable, intégrée à une chaîne vérifiable, puis détectée comme altérée lorsque l'on modifie une copie de test.

Les quatre fichiers proposés par R019 restent la cible de conception :
- `guardian_mcp/attacker_agent.py`
- `guardian_mcp/defender_agent.py`
- `guardian_mcp/demo_scenario.py`
- `guardian_mcp/test_demo_scenario.py`

Conformément au périmètre de gouvernance actif, ce rapport ne crée ni ne modifie ces fichiers applicatifs. Il fixe les contrats à respecter avant leur implémentation.

## 2. Processus, problème et solution

### 2.1 Processus cible

Le scénario de démonstration devrait présenter quatre rôles logiques :
1. **Agent A — Orchestrateur** : lance l'expérience, attribue un identifiant de session et coordonne les étapes.
2. **Agent B — Source hostile simulée** : transmet une instruction d'injection contrôlée dans une donnée de test. Il ne doit pas disposer d'un accès réseau ou de vrais secrets.
3. **Agent C — Agent de propagation simulée** : reçoit la donnée contaminée et tente d'appeler un outil factice avec une intention d'exfiltration.
4. **Agent D — Défenseur Guardian** : inspecte l'appel, applique la politique, empêche l'exécution interdite et relie la décision aux événements de preuve.

Ces rôles sont des acteurs de démonstration. Ils ne doivent pas être présentés comme quatre processus autonomes isolés tant que l'implémentation ne prouve pas réellement cette séparation.

### 2.2 Problème à résoudre

L'instrumentation actuelle contient une détection Python simple par marqueurs textuels et des listes d'outils sensibles. Elle n'est pas, à elle seule, la preuve d'une intégration complète avec le ledger Rust. Le sink par défaut garde les événements en mémoire, ce qui suffit à certains tests unitaires mais ne prouve ni la persistance durable ni la reconstruction de provenance par le moteur Rust.

Il faut éviter trois faux positifs de démonstration :
- annoncer « propagation » alors que seul un texte est copié entre deux fonctions sans événement causal explicite ;
- annoncer « preuve persistante » alors que l'événement existe uniquement dans une liste Python en mémoire ;
- annoncer « replay R0 » en ne recalculant qu'un hash isolé sans vérifier la chaîne complète attendue.

### 2.3 Solution proposée

La première version doit être **déterministe, locale et sans effet externe**. Les outils d'exfiltration, de lecture de secrets ou d'envoi réseau doivent être des stubs de test qui enregistrent si l'exécuteur a été appelé. Aucun vrai secret, portefeuille, système de production, endpoint externe ou dépôt historique ne doit être utilisé.

L'orchestration doit séparer clairement :
- l'événement d'injection ;
- l'événement de propagation entre agents ;
- la tentative d'appel d'outil ;
- la décision Guardian ;
- l'événement de preuve ;
- le résultat du rejeu ;
- le résultat du test d'altération.

Chaque étape doit avoir un identifiant stable dans le scénario et un lien causal explicite vers l'étape précédente. Les données brutes hostiles peuvent être conservées dans une fixture locale dédiée, mais les événements d'audit ne doivent pas copier inutilement le contenu potentiellement sensible ; un hash et un résumé borné sont préférables.

## 3. Contrat fonctionnel du scénario

| Étape | Action | Preuve observable | Condition de réussite |
|---|---|---|---|
| S0 | Initialiser la session et les quatre rôles | Identifiants de session, run et agents | Tous les identifiants sont présents et cohérents |
| S1 | Injecter une instruction hostile inerte | Événement d'injection et empreinte d'entrée | L'injection est traçable sans être exécutée comme instruction de contrôle |
| S2 | Transmettre la donnée à l'agent suivant | Événement de propagation A→B ou B→C, avec parent/correlation ID | Le lien causal est vérifiable |
| S3 | Simuler une tentative d'exfiltration | Appel à un exécuteur factice instrumenté | La tentative est enregistrée avant la décision finale |
| S4 | Appliquer Guardian | Décision BLOCK et `evidence_id` non nul dans le modèle de preuve retenu | L'exécuteur sensible n'est jamais appelé |
| S5 | Vérifier la chaîne | Résultat R0 PASS sur l'ensemble exact des entrées produites | Tous les hashes attendus correspondent |
| S6 | Vérifier la décision | Résultat R1 PASS pour BLOCK accompagné d'une preuve cohérente | L'invariant BLOCK→EvidenceId est satisfait |
| S7 | Altérer une copie d'une entrée | Résultat R0 FAIL avec divergence localisée | L'archive originale demeure inchangée |
| S8 | Résumer l'expérience | Rapport synthétique de la démo | Le statut distingue PASS, FAIL et NOT_TESTED sans ambiguïté |

**Important :** R019 décrit un invariant R1 où chaque décision BLOCK doit porter un `evidence_id`. Il ne prouve pas que le type d'événement MCP Python actuel possède déjà ce champ ou que les événements C-07 sont automatiquement convertis en `LedgerEntry` Rust. L'adaptateur entre événements MCP et ledger doit être explicitement défini et testé avant de revendiquer le critère S6 comme une intégration de bout en bout.

## 4. Contrats d'interface à stabiliser avant implémentation

### 4.1 Événement

Le scénario doit au minimum exposer : `event_id`, `agent_id`, `session_id`, `run_id`, numéro de séquence, type d'événement, décision, raison, hash d'entrée, hash d'événement et identifiant de corrélation ou de parent.

Le schéma canonique existant de `MCPToolEvent` contient notamment les identifiants, la décision, le hash d'entrée, le résumé de sortie et le hash calculé. Le lien de causalité entre événements inter-agents n'est pas visible dans ce modèle actuel ; il faut donc soit l'ajouter dans un contrat explicitement versionné, soit le porter dans une structure de scénario séparée et la relier sans ambiguïté au ledger. Ne pas modifier silencieusement le schéma existant.

### 4.2 Politique

- Une action explicitement classée interdite doit aboutir à BLOCK.
- L'exécuteur factice associé doit prouver qu'il n'a pas été appelé.
- Le motif interne et la preuve doivent être associés au même événement de décision.
- Une réponse d'erreur seule n'est pas suffisante : elle ne prouve pas que l'action a été empêchée avant son exécution.
- Les tests doivent couvrir également le cas normal ALLOW pour éviter qu'un scénario où tout est bloqué soit présenté comme un succès.

### 4.3 Rejeu

- R0 vérifie l'intégrité structurelle des entrées fournies et doit détecter une altération de hash.
- R1 ajoute la vérification de cohérence des décisions de politique, notamment BLOCK→EvidenceId.
- Un PASS doit indiquer le nombre d'événements rejoués, le niveau atteint et les limites de la vérification.
- Le test d'altération doit modifier une copie isolée, jamais la chaîne d'origine.
- R0 PASS ne prouve pas que la décision métier d'origine était correcte ; R1 ne doit pas être présenté comme une preuve d'exécution réelle de tous les agents.

## 5. Plan de tests d'acceptation

| ID | Test | Résultat attendu |
|---|---|---|
| D4-01 | Exécution nominale d'un outil inoffensif | ALLOW, réponse valide et événement enregistré |
| D4-02 | Injection contenant un marqueur hostile reconnu | BLOCK et événement correspondant |
| D4-03 | Tentative d'exfiltration par outil factice | BLOCK avant exécution ; compteur d'appels égal à zéro |
| D4-04 | Propagation entre agents | Événements de départ et d'arrivée reliés par un identifiant causal |
| D4-05 | Preuve de blocage | EvidenceId non vide, lié à la même décision BLOCK |
| D4-06 | Replay de la chaîne intacte | R0 PASS sur toutes les entrées du run |
| D4-07 | Replay de la décision | R1 PASS si la décision et la preuve sont cohérentes |
| D4-08 | Suppression de l'EvidenceId sur une copie | R1 FAIL |
| D4-09 | Altération d'un champ couvert par le hash | R0 FAIL et divergence localisée |
| D4-10 | Erreur de l'exécuteur factice | Événement d'erreur produit, aucune fuite de données brutes |
| D4-11 | Deux runs consécutifs | Aucun mélange de séquences ou d'identifiants entre runs |
| D4-12 | Rapport de fin incomplet | Les étapes non exécutées apparaissent NOT_TESTED, pas PASS |

Les tests doivent rester indépendants de l'API ARTCB OVH et d'un réseau externe. L'API hors ligne mentionnée par R019 ne doit pas bloquer cette démonstration locale.

## 6. Menaces et protections requises

### T1 — Injection de prompt
**Processus :** une chaîne hostile est transmise comme donnée à un agent.  
**Problème :** le contenu pourrait être traité comme une instruction privilégiée.  
**Solution :** le traiter comme donnée non fiable, le marquer dans la provenance et vérifier que la politique le bloque avant tout appel interdit.

### T2 — Faux positif de blocage
**Processus :** Guardian renvoie une réponse BLOCK.  
**Problème :** l'exécuteur pourrait avoir été appelé auparavant ou parallèlement.  
**Solution :** utiliser un exécuteur factice avec compteur et exiger zéro appel pour le chemin bloqué.

### T3 — Perte de provenance
**Processus :** plusieurs agents transmettent une donnée.  
**Problème :** un simple hash global ne démontre pas quel agent a transmis quoi à qui.  
**Solution :** produire des événements par étape, avec agent source, agent destinataire, parent/correlation ID et empreintes d'entrée/sortie bornées.

### T4 — Preuve seulement en mémoire
**Processus :** C-07 stocke par défaut ses événements dans une liste Python.  
**Problème :** la fermeture du processus fait perdre cette liste ; elle ne prouve pas une persistance durable.  
**Solution :** pour la première démo, annoncer explicitement « preuve en mémoire » si aucun sink durable n'est relié. Pour revendiquer la persistance Rust, tester l'adaptateur et le store durable réellement.

### T5 — Rejeu artificiellement positif
**Processus :** un seul hash est recalculé ou les entrées sont reconstruites après altération.  
**Problème :** le résultat ne prouve pas l'intégrité de la chaîne d'origine.  
**Solution :** figer la séquence d'origine, calculer son tip, rejouer cette séquence et altérer uniquement une copie de test.

### T6 — Fuite de données de test
**Processus :** les paramètres ou exceptions sont consignés dans les logs.  
**Problème :** une donnée sensible ou une chaîne hostile peut être recopiée dans les journaux.  
**Solution :** ne pas utiliser de vrais secrets ; préférer hash et résumé borné ; ne pas ajouter de logs bruts au dépôt.

## 7. Séquence de réalisation recommandée

1. **Geler la baseline** : relever le SHA du commit, exécuter les suites existantes et conserver les résultats de test hors du dépôt.
2. **Définir les contrats** : types d'événements, causalité, EvidenceId et adaptateur MCP→ledger.
3. **Construire les rôles simulés** : agents déterministes sans accès réseau, fichiers sensibles ou outils de production.
4. **Assembler le scénario** : orchestration explicite des étapes S0 à S8 et rapport de résultat.
5. **Écrire les tests d'acceptation** : les 12 tests D4-01 à D4-12, avec tests négatifs obligatoires.
6. **Exécuter les tests** : suites Guardian existantes puis nouvelle suite de scénario ; documenter les commandes et résultats effectivement observés.
7. **Vérifier le périmètre** : seuls les chemins autorisés sont modifiés ; aucun log brut ni changement dans le dépôt historique `vgactech/artcb`.
8. **Produire le rapport suivant** : ne fermer L-019-001 que si tous les critères bloquants ont une preuve reproductible.

## 8. Critère Go/No-Go pour la compétition

La démo est **GO** seulement si :
- la tentative hostile et sa propagation sont observables ;
- l'action interdite n'est pas exécutée ;
- BLOCK est associé à une preuve non vide ;
- le rejeu intact passe ;
- le rejeu altéré échoue ;
- les résultats sont reproductibles ;
- les limites (mémoire vs stockage durable, simulation vs agents séparés, R0/R1 vs niveaux supérieurs) sont présentées honnêtement.

Sinon, le statut reste **NO-GO** ou **PARTIEL**, avec la liste des critères non satisfaits. Le simple succès des 68 tests Guardian existants ne ferme pas automatiquement le scénario à quatre agents.

## 9. Registre des tâches

| ID | Tâche | Priorité | Statut après ce rapport |
|---|---|---|---|
| L-019-001 | Démo Guardian quatre agents | P0 | OUVERTE — spécification et critères détaillés |
| I-019-004 | Vérifier la présence éventuelle d'un PAT dans la configuration locale référencée par R019 | P1 sécurité | NON VÉRIFIÉE dans cette session |
| L-019-002 | Replay R2/R3 | P2 | OUVERTE |
| L-019-003 | API ARTCB OVH hors ligne | P2 | OUVERTE / dépendance externe |
| L-019-004 | Attestation TPM distante | P1 futur | OUVERTE |
| L-019-005 | Fixtures Python natives C-10 | P2 | OUVERTE |
| L-019-006 | Espace de test local SPECIal | P2 | OUVERTE |

## 10. Contrôle de périmètre

- Dépôt historique `vgactech/artcb` : lecture seule ; aucune écriture.
- Code applicatif de `ARTCB-TERMINATOR` : aucun changement effectué dans cette révision.
- Fichiers modifiés : rapport R020 uniquement.
- Logs bruts : aucun ajouté.
- Intégration dans VLC&ARTCB : aucune.
- État des tests : 68/68 PASS est repris comme résultat documenté de R019 ; aucune nouvelle exécution n'est revendiquée ici.

## 11. Conclusion

Le chemin le plus court vers la démo n'est pas de multiplier les agents avant d'avoir figé le contrat de preuve. Il faut d'abord garantir qu'une chaîne d'événements lisible et corrélée relie l'injection, la propagation, la décision, l'EvidenceId et le rejeu. Les agents peuvent ensuite orchestrer ce chemin de façon visible.

**Prochaine action P0 :** implémentation contrôlée des quatre fichiers du scénario après autorisation explicite de modifier le code applicatif, puis exécution des tests D4-01 à D4-12. Jusqu'à cette implémentation, L-019-001 reste ouverte.
