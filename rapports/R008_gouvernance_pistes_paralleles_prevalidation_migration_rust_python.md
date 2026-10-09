# R008 — Gouvernance des deux pistes parallèles et portes de validation avant migration Rust/Python

**Date :** 2026-10-09  
**Dépôt cible du rapport :** `vgactech/ARTCB-TERMINATOR`  
**Emplacement autorisé :** `rapports/` uniquement  
**Sources examinées en lecture seule :** `vgactech/artcb`, révision observée `7304d493018995d851ed5c13107c5e9d5bd79268`  
**Dépendances documentaires :** R006 et R007 du dépôt ARTCB-TERMINATOR ; rapports historiques R460 et R462 consultés pour constater des garanties déclarées et leurs limites  
**Statut :** plan de gouvernance et questions à trancher ; aucune migration ni exécution de campagne complète n'est revendiquée.

## Expertises mobilisées

- Gouvernance de migration et gestion de versions parallèles ;
- audit de dépôt Git et traçabilité des sources ;
- stratégie de tests de caractérisation, de non-régression et de différentiel ;
- ingénierie de migration Python vers Rust et coexistence inter-langages ;
- sécurité logicielle, cryptographie appliquée et gestion des preuves ;
- intégration continue, reproductibilité des builds et chaîne d'approvisionnement ;
- gestion de risques, critères d'acceptation et certification technique.

## 1. Décision proposée

Le projet doit fonctionner avec **deux pistes de travail parallèles, isolées et reliées par des contrats de compatibilité**, sans commencer à coder l'implémentation Rust/Python dans `ARTCB-TERMINATOR` avant que l'inventaire, les tests de référence et les critères de sortie soient établis.

### Piste A — référence Python historique ARTCB

Dépôt de référence : https://github.com/vgactech/artcb

Objectif : comprendre ce qui existe réellement, établir l'inventaire des capacités, figer la révision source, exécuter les tests dans un environnement isolé et distinguer les garanties prouvées des affirmations documentaires.

**Contrainte impérative :** le dépôt historique `vgactech/artcb` demeure en lecture seule pour cette mission. Aucune écriture, modification de fichier, branche, commit, issue, configuration ou push ne doit y être effectué. Si des tests nécessitent un espace de travail modifiable, ils doivent tourner dans une copie de travail temporaire isolée ou dans un clone/fork de validation distinct explicitement autorisé, jamais dans le dépôt historique lui-même. Les journaux bruts et artefacts sensibles restent hors des dépôts Git.

### Piste B — destination de migration ARTCB-TERMINATOR

Dépôt cible : https://github.com/vgactech/ARTCB-TERMINATOR

Objectif : préparer les contrats, spécifications, matrice de correspondance, décisions d'architecture, critères d'acceptation et rapports de preuve qui guideront la migration.

**Périmètre actuel d'écriture :** uniquement `rapports/`, en conservant la numérotation existante. Jusqu'à l'approbation explicite d'une étape d'implémentation distincte, aucun code Rust ou Python applicatif, fichier de configuration, dépendance, workflow CI ou secret ne doit être ajouté ou modifié dans ce dépôt.

### Comment les deux pistes travaillent en parallèle

La piste A produit des constats et des résultats reproductibles ; la piste B transforme ces résultats en contrats, décisions de migration et critères de validation. Les rapports et les références de commits relient les pistes. Une conclusion non vérifiée dans A ne devient jamais automatiquement une exigence certifiée dans B.

## 2. Processus, problème et solution

### Processus — le déroulement recherché

1. Identifier la révision exacte du dépôt historique et inventorier ses modules, API, formats de données, dépendances, tests, scripts de déploiement et fonctionnalités.
2. Reproduire les tests existants dans un environnement isolé et mesurer la couverture réellement obtenue.
3. Créer des tests de caractérisation qui enregistrent le comportement existant, y compris les comportements historiques à corriger.
4. Classer chaque capacité : à conserver, corriger avant migration, réécrire, remplacer, déprécier ou exclure.
5. Définir les contrats indépendants du langage : schémas, formats d'entrée/sortie, codes d'erreur, règles cryptographiques, invariants et comportement en cas de panne.
6. Évaluer et tester les bibliothèques candidates Rust et Python sans les intégrer prématurément au projet cible.
7. Préparer une matrice de traçabilité reliant chaque capacité source à un contrat, à des tests, à une future unité d'implémentation et à une preuve d'acceptation.
8. Lorsque toutes les portes obligatoires sont satisfaites, présenter un rapport de décision autorisant ou refusant le démarrage de l'implémentation.
9. Après autorisation explicite, migrer par unités cohérentes, exécuter les tests de conformité et de non-régression, comparer les résultats Rust/Python, puis vérifier la parité avec les comportements attendus.
10. Ne déclarer une unité terminée qu'après collecte de preuves et revue des risques résiduels.

### Problème — pourquoi coder trop tôt augmente le risque

Sans inventaire ni comportement de référence, une migration peut omettre une fonctionnalité existante, reproduire un défaut historique, modifier silencieusement un format, changer une décision de sécurité ou créer deux implémentations qui ne produisent pas les mêmes résultats.

Le simple fait que Rust compile ou que les tests unitaires passent ne prouve pas la parité fonctionnelle, la sécurité, la compatibilité des données, la performance en production ni la capacité de reprise après panne. De même, deux sorties identiques ne suffisent pas à certifier une propriété si les deux implémentations partagent le même défaut.

### Solution — règle de gouvernance

Aucune implémentation applicative dans `ARTCB-TERMINATOR` avant le **Go/No-Go de préparation à la migration**. Cette décision doit s'appuyer sur des résultats exécutés, un corpus de tests versionné, des contrats approuvés, une matrice de correspondance complète et une liste explicite des écarts non résolus. Les éléments encore inconnus restent marqués `NOT_TESTED`, `INCONCLUSIVE` ou `BLOCKED`, sans être transformés en succès supposés.

## 3. Portes obligatoires avant toute migration

| Porte | Preuve exigée | Critère de passage |
|---|---|---|
| G0 — Source figée | URL, commit SHA, date, branche observée et empreintes des artefacts de référence | Révision source non ambiguë |
| G1 — Inventaire | Modules, points d'entrée, API, modèles, stockage, tâches planifiées, intégrations et dépendances | Chaque zone connue est recensée ou explicitement marquée inconnue |
| G2 — Baseline | Tests existants exécutés dans un environnement isolé, commandes, versions, résultats et limites | Les résultats sont observés et reproductibles ; les échecs sont classés |
| G3 — Caractérisation | Tests de comportement pour les parcours importants et les cas limites | Les comportements actuels sont enregistrés, sans présumer qu'ils sont tous souhaitables |
| G4 — Risques et défauts | Registre de vulnérabilités, dettes techniques, écarts fonctionnels et défauts à corriger | Les bloqueurs critiques ont une décision et un plan de traitement |
| G5 — Contrats communs | Schémas, formats canoniques, erreurs, invariants, versionnage et compatibilité | Les contrats sont suffisamment précis pour être testés indépendamment du langage |
| G6 — Bibliothèques | Évaluation de conformité, maintenance, licence, sécurité, versions et comportement sur corpus | Les choix sont documentés et justifiés ; aucune dépendance n'est présumée validée |
| G7 — Stratégie Rust/Python | Répartition des responsabilités, API inter-langages, frontières de processus et règles de parité | Chaque composant a un propriétaire logique et un contrat d'échange défini |
| G8 — Banc différentiel | Corpus partagé, exécution des deux implémentations et comparateur automatique prévu | Les critères de comparaison sont définis avant d'écrire l'implémentation |
| G9 — Sécurité et exploitation | Threat model, gestion des clés, permissions, secrets, observabilité, reprise, sauvegarde et mise à jour | Les exigences opérationnelles et les scénarios de défaillance sont testables |
| G10 — Go/No-Go | Rapport de synthèse et revue des preuves | Décision explicite et limites résiduelles acceptées avant le début du code cible |

Une porte ne peut pas être déclarée franchie sur la base d'une intention, d'un plan de test ou d'une case cochée sans preuve.

## 4. Matrice de traçabilité à constituer

Pour chaque capacité du dépôt source, enregistrer les champs suivants :

- identifiant stable et nom de la capacité ;
- chemin source et symboles concernés ;
- révision source exacte ;
- description du comportement observé ;
- appelants, dépendances et effets de bord ;
- entrées, sorties, erreurs et invariants ;
- données persistées et contraintes de compatibilité ;
- tests existants, résultat réellement observé et couverture connue ;
- défauts, vulnérabilités et cas non couverts ;
- décision de migration : conserver, corriger, réécrire, remplacer, déprécier ou exclure ;
- cible prévue : Rust, Python, contrat partagé ou service externe ;
- test de parité et test de non-régression requis ;
- statut, preuve associée, réviseur et décision d'acceptation.

Les fonctionnalités sans preuve suffisante doivent rester visibles dans le registre. Une absence de test ne signifie ni que la fonction est correcte, ni qu'elle est inutile.

## 5. Architecture de migration à évaluer, sans la présumer

Il faut déterminer quelles responsabilités appartiennent à Rust, lesquelles doivent rester en Python, et si une partie doit être définie dans un contrat indépendant des deux langages. Il ne faut pas décider que « tout doit être réécrit » avant d'avoir mesuré les exigences et les coûts.

Options à comparer pour chaque composant :

- **Rust** : candidats possibles pour les composants nécessitant des invariants de type forts, une gestion explicite des erreurs, des performances prévisibles ou une surface de confiance réduite.
- **Python** : candidat possible pour l'orchestration, les intégrations, les outils d'administration et les composants où l'écosystème existant est déterminant.
- **Contrat neutre** : JSON versionné ou autre format justifié pour les échanges, accompagné de règles strictes de validation, de canonicalisation et de compatibilité.
- **Frontière d'exécution** : bibliothèque native, processus séparés ou API réseau ; décision fondée sur la sécurité, le coût opérationnel, la latence et la facilité de test.

Ces options sont des hypothèses d'architecture à évaluer, pas des décisions déjà validées. Une même logique de sécurité ne doit pas être dupliquée sans raison dans deux langages : si la duplication est nécessaire, les tests différentiels et les invariants communs sont obligatoires.

## 6. Tests à prévoir avant de qualifier une migration de validée

1. **Tests de caractérisation** : capturent les comportements de la version de référence.
2. **Tests unitaires** : vérifient chaque fonction ou module.
3. **Tests de contrat** : valident les formats, schémas, erreurs et règles de versionnage.
4. **Tests différentiels Rust/Python** : comparent les décisions, octets, valeurs et codes d'erreur pertinents sur le même corpus.
5. **Tests de non-régression** : s'assurent que les corrections n'ont pas réintroduit les défauts connus.
6. **Tests adversariaux et de sécurité** : entrées malformées, altérations, rejeu, ambiguïtés, erreurs de permission, fuite d'informations et échec fermé lorsque requis.
7. **Tests de persistance et de panne** : arrêt brutal, reprise, écritures partielles, répétition d'une requête et cohérence après redémarrage.
8. **Tests d'intégration** : stockage, API, réseau, identités, TPM et autres équipements lorsque le composant les utilise.
9. **Tests de performance** : charge représentative, latence, mémoire, concurrence et dégradation.
10. **Tests de build et de chaîne d'approvisionnement** : builds reproductibles, verrouillage des versions, licences, vulnérabilités de dépendances et provenance des artefacts.
11. **Tests de compatibilité** : données anciennes, versions de protocoles, migration et retour arrière.
12. **Tests en environnement réel** : seulement lorsqu'ils sont nécessaires, avec environnement, autorisation, critères d'arrêt et données de test clairement définis.

Tous les tests ne s'appliquent pas forcément à tous les composants. Chaque exclusion doit être justifiée et consignée ; aucun test pertinent ne doit être omis simplement parce qu'il est coûteux.

## 7. Critères de preuve et sens du mot « certifié »

Le rapport de migration devra distinguer :

- **Conforme aux tests exécutés** : les tests identifiés ont été réellement lancés et leurs résultats sont disponibles.
- **Validation interne** : les critères internes définis par le projet ont été satisfaits, avec limites et périmètre explicités.
- **Audit indépendant** : une partie indépendante a examiné les preuves selon un périmètre documenté.
- **Certification formelle** : uniquement si un référentiel, une autorité ou un organisme compétent et un processus formel existent réellement.

Le projet ne doit pas employer « certifié » comme synonyme de « compile », « tests unitaires verts » ou « rapport écrit ». La déclaration doit indiquer exactement ce qui a été vérifié, sur quelle révision, dans quel environnement, avec quelles exclusions et par qui.

## 8. Questions à poser et décisions nécessaires

Les questions ci-dessous doivent être résolues avant le Go/No-Go. Lorsqu'une réponse n'est pas disponible, la décision correspondante reste bloquée ou explicitement provisoire.

### Q1 — Quel est le périmètre exact de la migration ?

Faut-il migrer l'intégralité du dépôt historique, uniquement les capacités ARTCB retenues, ou un sous-ensemble prioritaire ? Chaque répertoire, service et outil doit être classé.

### Q2 — Quelle révision du dépôt historique fait foi ?

Le plan doit-il figer la révision observée `7304d493018995d851ed5c13107c5e9d5bd79268` comme baseline initiale, ou une autre révision précise doit-elle être retenue ? Toute évolution ultérieure de la source doit créer une nouvelle baseline et une analyse de delta.

### Q3 — Où exécuter les tests qui ont besoin d'écrire ?

La règle actuelle interdit toute modification de `vgactech/artcb`. Confirmer que les tests seront exécutés dans un clone/copie isolée et jetable, ou préciser le dépôt de validation séparé autorisé. Aucun push ne doit être effectué vers le dépôt historique.

### Q4 — Quelle est la répartition attendue entre Rust et Python ?

Quels composants doivent impérativement être en Rust, lesquels doivent rester en Python, et lesquels peuvent être remplacés par un service ou une bibliothèque ? Si l'objectif est « tout migrer », faut-il conserver une couche Python d'orchestration et d'intégration ?

### Q5 — Quels systèmes et environnements sont obligatoires ?

Quelles distributions Linux, architectures CPU, versions de Python et de Rust, environnements conteneurisés, systèmes de stockage et plateformes de déploiement doivent être supportés ?

### Q6 — Quels niveaux de preuve sont requis pour chaque fonctionnalité ?

Quels critères rendent une fonctionnalité acceptable : tests unitaires, tests différentiels, fuzzing, revue de sécurité, tests matériels réels, audit indépendant ou certification externe ? Qui approuve chaque résultat ?

### Q7 — Quels composants nécessitent du matériel réel ?

Pour les fonctionnalités TPM, HSM, TEE, biométriques ou autres, quels équipements sont disponibles pour les essais ? Quels tests synthétiques peuvent être exécutés en CI, et lesquels doivent rester explicitement non validés sans matériel réel ?

### Q8 — Quelle compatibilité doit être maintenue ?

Les données persistées, événements, API, protocoles réseau, identifiants, formats cryptographiques et versions déjà en service doivent-ils être rétrocompatibles ? Quelle stratégie de migration de données et de retour arrière est exigée ?

### Q9 — Quels objectifs de performance et de disponibilité sont attendus ?

Définir, si nécessaire, des objectifs mesurables de latence, débit, mémoire, temps de démarrage, disponibilité, durée de reprise et taille maximale des charges.

### Q10 — Quel modèle de menace doit guider les tests ?

Quels adversaires, privilèges, capacités de rejeu, compromissions de nœud, risques de supply chain, scénarios d'exfiltration et conséquences d'une panne sont dans le périmètre ? Quels éléments sont hors périmètre et pourquoi ?

### Q11 — Quelles règles encadrent les clés et les secrets ?

Confirmer où résident les secrets, comment ils sont injectés dans les environnements de test, quelles clés sont synthétiques, et comment prévenir toute publication dans Git, les logs, les artefacts CI ou les rapports.

### Q12 — Quelle définition de « certification » est attendue ?

S'agit-il d'une validation technique interne avec preuves reproductibles, d'un audit indépendant, ou d'une certification conforme à un référentiel externe précis ? Sans référentiel et autorité identifiés, seul un statut de validation borné peut être déclaré.

### Q13 — Qui décide du démarrage du code dans ARTCB-TERMINATOR ?

Confirmer le mécanisme d'autorisation explicite et les critères qui doivent être satisfaits avant de sortir du périmètre documentaire `rapports/`.

### Q14 — Comment prioriser les défauts historiques ?

Quels défauts doivent être corrigés avant migration, lesquels peuvent être traités pendant une unité de migration, et lesquels doivent bloquer la sortie ? La priorité doit dépendre du risque et des dépendances, pas seulement de l'ordre des fichiers.

### Q15 — Comment gérer les chantiers et rapports précédents incomplets ?

Maintenir un registre vivant des travaux ouverts, avec identifiant, priorité, état, blocage, prochaine action et lien vers la preuve. Chaque rapport suivant doit actualiser ce registre sans effacer les tâches encore ouvertes.

## 9. Risques spécifiques et mesures de réduction

| Risque | Processus / problème | Mesure |
|---|---|---|
| Source qui change pendant l'audit | Les résultats ne correspondent plus à la même révision | Figer le commit source et tracer tout changement |
| Test exécuté dans le mauvais dépôt | Violation de la règle de lecture seule | Copie de travail isolée ; contrôle explicite du dépôt et du chemin |
| Migration prématurée | Réécriture avant connaissance des comportements et dépendances | Portes G0–G10 et Go/No-Go formel |
| Régression silencieuse | Les tests ne couvrent pas les parcours existants | Tests de caractérisation et matrice de traçabilité |
| Faux sentiment de certification | Des tests limités sont présentés comme une garantie générale | Énoncer le périmètre exact, les exclusions et les limites |
| Divergence Rust/Python | Sémantique, erreurs, dates, nombres ou encodage diffèrent | Corpus commun et comparaison automatisée des résultats normatifs |
| Double implémentation de sécurité incohérente | Deux chemins de code appliquent des règles différentes | Contrat unique, vecteurs partagés, tests différentiels et revue |
| Dépendance vulnérable ou non maintenue | Un composant tiers affaiblit le résultat | Vérification de licence, maintenance, versions et vulnérabilités |
| Fuite de secret dans les preuves | Les rapports ou logs rendent une clé publique | Données synthétiques, expurgation et logs bruts hors Git |
| Oubli d'un chantier antérieur | Un nouveau sujet remplace un ancien blocage | Registre cumulatif et revue systématique des tâches ouvertes |

## 10. Lien avec R006 et R007

R006/R007 couvrent le contrat d'événement JSON, le profil JCS, les empreintes et le protocole de validation Rust/Python. Ce travail devient un **lot technique candidat** dans la migration, mais ne prouve pas à lui seul que les validateurs existent, que les bibliothèques sont conformes ou que les tests ont été exécutés.

Avant de faire de ce lot une implémentation, il faut :
- vérifier le schéma et le corpus de fixtures exacts ;
- confirmer les vecteurs JCS et le digest par une implémentation conforme ;
- décider des bibliothèques et versions candidates ;
- exécuter les tests Rust/Python dans un environnement de validation ;
- conserver séparément les résultats de parsing, schéma, canonicalisation, hash et protocole ;
- publier uniquement un résumé expurgé dans `rapports/`.

Les rapports historiques R460/R462 consultés décrivent des tests de liaison TPM et leurs limites, dont l'absence d'attestation distante complète dans le périmètre documenté. Ces déclarations sont des pistes de traçabilité à vérifier dans une baseline reproductible ; elles ne sont pas assimilées ici à une certification indépendante.

## 11. État initial et prochaines actions

| Action | Piste | État dans ce rapport |
|---|---|---|
| Figer et documenter la baseline source | A | PARTIEL : une révision a été observée ; la baseline complète doit être validée |
| Inventorier toutes les capacités | A | NOT_TESTED |
| Exécuter la suite existante dans un environnement isolé | A | NOT_TESTED |
| Construire les tests de caractérisation | A | NOT_TESTED |
| Créer la matrice source → contrat → cible → tests | A + B | À CONSTRUIRE |
| Définir la répartition Rust/Python | B | BLOQUÉ par les questions Q1/Q4 |
| Sélectionner les bibliothèques et versions | B | NOT_TESTED |
| Valider R006/R007 par exécution | B | NOT_TESTED selon R007 |
| Traiter les questions Q1–Q15 | Gouvernance | À CONFIRMER |
| Autoriser le code applicatif dans ARTCB-TERMINATOR | B | NON AUTORISÉ par ce rapport |
| Écrire ce rapport dans `rapports/` | B | Seul changement permis par la mission actuelle |

## Conclusion

La demande de deux pistes parallèles est retenue comme modèle de gouvernance : la version historique sert de référence testée en lecture seule, tandis qu'ARTCB-TERMINATOR reçoit les contrats, plans, matrices et preuves de migration dans `rapports/`. Les essais qui nécessitent des écritures doivent être isolés dans une copie de travail séparée, sans modifier ni pousser vers le dépôt historique.

Le principe de minimisation des problèmes est de **comprendre et tester d'abord, contractualiser ensuite, coder après le Go/No-Go, puis valider chaque unité de migration contre des preuves reproductibles**. Les questions Q1–Q15 sont consignées pour éviter que les décisions manquantes soient remplacées par des hypothèses silencieuses.

**Limite de ce rapport :** il formalise l'organisation et les portes de validation. Il ne prétend pas que l'inventaire, les tests, la migration, la certification ou les corrections applicatives ont déjà été exécutés.
