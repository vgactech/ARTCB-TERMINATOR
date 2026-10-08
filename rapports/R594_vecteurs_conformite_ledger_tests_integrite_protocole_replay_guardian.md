# R594 — Vecteurs de conformité du ledger, tests d’intégrité et protocole de replay Guardian

**Date :** 2026-10-09  
**Dépôt de travail :** `vgactech/ARTCB-TERMINATOR`  
**Branche cible :** `main`  
**Dossier autorisé :** `rapports/` uniquement  
**Dépôt source audité :** `vgactech/artcb`  
**Référence source synchronisée :** branche `main`, README.md blob `37c554bddcf2dc07af977a5d93a9cfe374a848ed`  
**Rapport précédent :** R593 — spécification normative de traçabilité atomique des exécutions ARTCB Guardian  
**Objet :** définir des vecteurs de conformité exécutables conceptuellement, des critères d’acceptation, des tests adversariaux d’intégrité et un protocole de replay vérifiable pour le futur ledger Guardian.  
**Statut :** spécification de tests et protocole proposé. Aucun code applicatif, test automatisé ni benchmark n’a été exécuté dans cette étape.

---

## 1. Expertises mobilisées

- Audit de dépôt GitHub et traçabilité des changements ;
- ingénierie des tests et critères de conformité ;
- event sourcing, journaux append-only et transactions durables ;
- cryptographie appliquée : hash chaining, signatures, engagements et racines de Merkle ;
- forensic computing et reconstruction d’incidents ;
- replay déterministe et reproductibilité expérimentale ;
- sécurité des agents IA et systèmes multi-agents ;
- sécurité MCP/API et contrôle des outils ;
- contrats de données Rust/Python et interopérabilité ;
- stockage durable, reprise après panne et gestion des versions ;
- protection des données sensibles, redaction et contrôle d’accès ;
- préparation de démonstration Secure Horizons — Track 2, Defenders Augmented.

## 2. Résumé exécutif

R593 définit la traçabilité atomique et causale des exécutions instrumentées. R594 transforme ces exigences en un protocole de validation vérifiable : chaque garantie revendiquée doit correspondre à un test, un résultat attendu, une preuve conservée et une limite explicitement déclarée.

Le système ne doit pas confondre les notions suivantes :

1. **Intégrité** : les octets contrôlés correspondent à l’empreinte ou à la signature attendue.
2. **Ordre causal** : les dépendances entre événements sont représentées et cohérentes.
3. **Complétude observée** : les événements attendus par les points d’instrumentation sont présents ; cela ne prouve pas que les zones non instrumentées ont été observées.
4. **Authenticité** : une signature valide relie un événement à une clé connue, sous réserve de la confiance accordée à cette clé.
5. **Autorisation** : une politique a permis l’opération au moment où elle a eu lieu.
6. **Reproductibilité** : les entrées, versions, configurations et dépendances disponibles permettent de répéter une exécution avec le niveau de fidélité déclaré.
7. **Correction sémantique** : le résultat est juste. Une empreinte, une signature ou un replay ne prouvent pas à eux seuls cette propriété.

**Principe de validation : aucune propriété ne peut être déclarée garantie sur la seule base d’un test de hash réussi.**

## 3. Processus, problème, solution

### 3.1 Processus

Un producteur émet un événement conforme au schéma versionné. Le composant de validation contrôle les champs obligatoires, les références aux événements parents, l’identité du producteur, la politique applicable et les artefacts liés. Le ledger attribue ou valide un identifiant, calcule l’engagement cryptographique, écrit l’événement de manière durable et retourne un accusé de réception seulement après la condition de durabilité définie.

Le vérificateur relit ensuite les événements depuis le stockage, recalcule les empreintes et les liens, contrôle les signatures et les relations causales, puis produit un rapport de conformité structuré.

### 3.2 Problème

Un journal peut sembler complet tout en contenant des trous, des événements dupliqués, une causalité incohérente, des signatures valides sur un contexte trompeur, ou des données présentes uniquement dans un cache volatil. Un replay peut également sembler identique alors que le modèle, les outils, les dépendances ou la politique ont changé.

### 3.3 Solution

Séparer les producteurs, le ledger, le vérificateur et le moteur de replay par des contrats explicites. Utiliser des identifiants stables, des formats canoniques versionnés, des liens cryptographiques, des règles de durabilité testées, des manifestes d’exécution et un rapport final qui distingue PASS, FAIL, INCONCLUSIVE et NOT_TESTED.

## 4. Contrat minimal d’un événement

Chaque événement de conformité doit inclure, ou référencer explicitement, au minimum :

- `event_id` : identifiant stable et unique ;
- `schema_version` : version du schéma ;
- `run_id` : exécution concernée ;
- `event_type` : action normalisée ;
- `producer_id` et `producer_key_id` : producteur et clé associée ;
- `logical_time` : séquence monotone dans le périmètre du producteur ;
- `parent_event_ids` : dépendances causales connues ;
- `input_artifact_ids` et `output_artifact_ids` : artefacts référencés ;
- `policy_version` et résultat d’autorisation lorsque pertinent ;
- `payload_digest` et méthode de canonicalisation ;
- `previous_event_digest` ou référence équivalente à la chaîne ;
- `signature` lorsque le profil d’assurance l’exige ;
- `observability_status` : observé, partiellement observé, non instrumenté ou indisponible ;
- métadonnées temporelles déclarées et source de l’horloge ;
- référence aux preuves et à la classe de sensibilité des données.

Les secrets, clés privées et données personnelles non nécessaires ne doivent jamais être ajoutés au ledger en clair au seul motif d’améliorer la traçabilité. Le contenu sensible peut être chiffré et référencé par un identifiant et une empreinte, avec une politique de conservation séparée.

### Règles de validation

- Un identifiant d’événement ne peut pas désigner deux contenus différents.
- Un parent référencé doit exister, ou l’événement doit être marqué explicitement comme en attente de résolution.
- Un cycle dans le graphe causal est refusé, sauf si un type d’événement et un protocole de cycle sont spécifiquement définis.
- Une signature valide ne dispense pas du contrôle de schéma, de politique ou de causalité.
- Une référence manquante ne doit jamais être transformée silencieusement en preuve de complétude.
- Toute évolution incompatible du schéma exige une nouvelle version et des tests de migration.

## 5. Profils de conformité

| Profil | Garantie évaluée | Preuve minimale attendue |
|---|---|---|
| C0 — Structure | Schéma et champs valides | Rapport de validation du schéma |
| C1 — Identité | Identifiants uniques et clés connues | Registre d’identités et résultat de vérification |
| C2 — Intégrité | Altération détectée | Empreintes recalculées et résultat du vérificateur |
| C3 — Causalité | Dépendances cohérentes | Graphe causal et rapport de résolution |
| C4 — Durabilité | Événement récupérable après confirmation | Test de reprise et lecture depuis stockage durable |
| C5 — Autorisation | Opération reliée à une décision de politique | Version de politique, décision et références |
| C6 — Replay | Reconstitution selon un niveau annoncé | Manifeste, différences et résultat de comparaison |
| C7 — Résilience | Défaillances et interruptions détectées | Rapport de panne/reprise |
| C8 — Confidentialité | Données sensibles protégées selon le profil | Rapport de contrôle des champs et accès |
| C9 — Couverture | Instrumentation mesurée et limites exposées | Matrice des points instrumentés et non instrumentés |

Un profil ne doit être marqué PASS que si tous ses critères obligatoires sont satisfaits. Une exécution interrompue ou un environnement non disponible donne INCONCLUSIVE ou NOT_TESTED, jamais PASS par défaut.

## 6. Vecteurs de conformité du ledger

Les vecteurs ci-dessous sont des cas de test spécifiés, pas des résultats d’exécution déjà obtenus.

### LGR-001 — Événement valide

**Processus :** soumettre un événement conforme, avec identifiant, schéma, empreinte et références valides.  
**Attendu :** acceptation, écriture durable selon le contrat et possibilité de relire le même contenu canonique.  
**Échec si :** l’événement est acquitté avant la condition de durabilité promise ou si les octets relus ne correspondent pas au contenu accepté.

### LGR-002 — Mutation après écriture

**Processus :** modifier un octet d’un événement déjà enregistré dans un environnement de test isolé.  
**Attendu :** la vérification de l’empreinte, de la chaîne ou de la signature signale l’altération.  
**Échec si :** le vérificateur annonce PASS sans expliquer la divergence.

### LGR-003 — Suppression d’un événement intermédiaire

**Processus :** retirer un événement entre deux événements qui le référencent ou dont la chaîne dépend.  
**Attendu :** référence non résolue, rupture de chaîne ou divergence de racine détectée.  
**Limite :** une suppression du dernier événement non ancré peut être indétectable si aucun compteur, checkpoint externe ou engagement indépendant ne permet de connaître l’état attendu.

### LGR-004 — Réordonnancement

**Processus :** permuter des événements sans modifier leur contenu individuel.  
**Attendu :** les contraintes de séquence et les dépendances causales signalent le conflit.  
**Échec si :** l’ordre de stockage est traité comme preuve suffisante de l’ordre causal.

### LGR-005 — Duplication

**Processus :** soumettre deux fois le même `event_id`, puis soumettre le même identifiant avec un contenu différent.  
**Attendu :** le doublon identique suit une règle idempotente explicite ; l’identifiant réutilisé avec un contenu différent est refusé et signalé.

### LGR-006 — Signature incorrecte

**Processus :** altérer la signature, utiliser une clé inconnue ou associer une signature valide à un autre identifiant de producteur.  
**Attendu :** échec d’authentification. Le rapport précise la cause sans révéler de secret.

### LGR-007 — Rotation ou révocation de clé

**Processus :** vérifier des événements produits avant et après rotation, puis un événement signé avec une clé révoquée.  
**Attendu :** le résultat applique la politique temporelle de confiance et conserve la référence à la clé historique. La révocation ne doit pas effacer l’historique de vérification.

### LGR-008 — Événement hors schéma

**Processus :** omettre un champ obligatoire, fournir un type invalide ou une version inconnue.  
**Attendu :** rejet ou quarantaine explicite, sans normalisation silencieuse qui change le sens de l’événement.

### LGR-009 — Référence parent absente

**Processus :** déclarer un parent inconnu.  
**Attendu :** événement en attente ou rejet selon le contrat ; le graphe ne doit pas être déclaré complet.

### LGR-010 — Cycle causal

**Processus :** créer A dépendant de B et B dépendant de A.  
**Attendu :** détection du cycle et rapport contenant les identifiants impliqués.

### LGR-011 — Panne avant acquittement

**Processus :** arrêter le processus après l’écriture partielle mais avant l’accusé de réception.  
**Attendu :** reprise déterministe : l’événement est soit absent et peut être soumis à nouveau, soit présent et reconnu de manière idempotente. Aucun état ambigu ne doit être présenté comme confirmé.

### LGR-012 — Panne après acquittement

**Processus :** arrêter le service immédiatement après l’acquittement puis redémarrer et relire.  
**Attendu :** l’événement acquitté satisfait la garantie de durabilité annoncée.

### LGR-013 — Cache différent du stockage

**Processus :** corrompre ou vider le cache tout en conservant le stockage durable.  
**Attendu :** le vérificateur utilise la source de vérité déclarée ; le cache peut être reconstruit sans réécrire l’historique de référence.

### LGR-014 — Canonicalisation ambiguë

**Processus :** fournir deux représentations sérialisées qui diffèrent dans l’ordre des clés, les nombres, l’encodage ou les séparateurs.  
**Attendu :** une règle de canonicalisation versionnée produit une représentation stable ou refuse les cas ambigus. Le hash ne doit pas dépendre d’une sérialisation implicite non documentée.

### LGR-015 — Contenu sensible

**Processus :** soumettre un événement contenant un champ interdit, un secret factice ou une donnée classée sensible.  
**Attendu :** blocage, chiffrement ou redaction selon la politique, avec trace de la décision sans recopier le secret dans le rapport.

### LGR-016 — Événement signé mais non autorisé

**Processus :** signer correctement une opération interdite par la politique active.  
**Attendu :** authenticité PASS, autorisation FAIL. Les deux résultats sont distincts.

### LGR-017 — Perte d’instrumentation

**Processus :** désactiver un point de collecte dans un environnement contrôlé.  
**Attendu :** le système signale une baisse de couverture ou une interruption de source ; il ne prétend pas que l’absence d’événements prouve l’absence d’opérations.

### LGR-018 — Divergence de checkpoint

**Processus :** comparer la racine recalculée à un checkpoint conservé indépendamment.  
**Attendu :** toute divergence est rapportée avec la première plage vérifiable, si elle peut être localisée. Un checkpoint détenu par le même composant compromis ne doit pas être présenté comme une preuve indépendante.

## 7. Protocole d’intégrité

### Étape 1 — Figer le périmètre

Le manifeste de test identifie le dépôt, le commit, la version du schéma, la version du vérificateur, les paramètres, les fixtures et le profil testé. Les secrets ne sont jamais consignés dans le manifeste.

### Étape 2 — Préparer une fixture connue

Créer un ensemble synthétique avec événements valides, relations causales, doublons contrôlés, références, signatures de test et artefacts non sensibles. Enregistrer l’empreinte de la fixture de référence.

### Étape 3 — Exécuter le test nominal

Soumettre les événements dans l’ordre prévu. Conserver les accusés de réception, les identifiants retournés, les empreintes et le manifeste. Relire les événements depuis le stockage déclaré comme source de vérité.

### Étape 4 — Recalculer indépendamment

Un vérificateur séparé recalcule les empreintes et les liens à partir des octets relus. Lorsque possible, utiliser une implémentation ou un chemin de lecture distinct de celui qui a écrit les événements.

### Étape 5 — Injecter une seule anomalie à la fois

Chaque scénario adversarial possède un identifiant, une précondition, une mutation contrôlée, un résultat attendu et un critère d’échec. Les tests sont isolés afin qu’un échec ne contamine pas les fixtures suivantes.

### Étape 6 — Comparer les résultats

Le rapport de test contient le statut, les versions, les identifiants touchés, les preuves non sensibles, les différences et les limites. Les résultats bruts peuvent être conservés comme artefacts hors du dépôt ; aucun log brut ou secret ne doit être commité dans le dépôt de projet.

### Étape 7 — Répéter et vérifier la reprise

Répéter les tests pertinents après redémarrage, reconstruction du cache et relecture depuis stockage durable. Un résultat non répétable est documenté, pas masqué.

## 8. Protocole de replay

Le replay doit annoncer son niveau de garantie. « Replay réussi » ne suffit pas.

### R0 — Replay structurel

Vérifie que les événements peuvent être relus et que le graphe causal peut être reconstruit.

### R1 — Replay de décisions déterministes

Rejoue les transitions du moteur de politique à partir des mêmes événements, règles et versions. Compare les décisions et les motifs structurés.

### R2 — Replay d’outils simulés

Rejoue l’orchestration avec des réponses d’outils enregistrées ou simulées. Aucun appel externe imprévu ne doit être effectué pendant le replay.

### R3 — Replay d’exécution contrôlée

Réexécute les composants déterministes avec les mêmes entrées, versions, paramètres et dépendances déclarées. Compare les sorties canoniques et les empreintes.

### R4 — Replay IA avec fidélité qualifiée

Pour un LLM externe ou non déterministe, le replay peut seulement garantir la reconstruction du contexte et des appels enregistrés, ou une comparaison de sortie selon une tolérance définie. Il ne faut pas promettre une réponse identique si le fournisseur, le modèle, les poids, le routage, les paramètres ou l’environnement ne sont pas figés.

### Manifeste de replay obligatoire

- `run_id` et racine/empreinte de l’exécution originale ;
- commit logiciel et versions des composants ;
- version du schéma et de la politique ;
- identifiants et empreintes des entrées ;
- versions de modèle et paramètres disponibles ;
- outils, versions, réponses enregistrées et dépendances ;
- graines aléatoires lorsqu’elles sont contrôlables ;
- environnement et variables pertinentes, sans secrets ;
- événements inclus, exclus ou indisponibles ;
- niveau R0–R4 demandé et réellement atteint ;
- différences observées et motifs ;
- résultat final : PASS, FAIL, INCONCLUSIVE ou NOT_TESTED.

### Règle de décision

Un replay R0 réussi ne prouve pas que le calcul d’origine était correct. Un replay R3 réussi ne prouve pas la vérité sémantique du résultat. Un replay R4 peut être fidèle au contexte sans reproduire exactement une génération LLM. Chaque rapport doit énoncer la garantie effectivement testée.

## 9. Matrice de résultats attendus

| Cas | Résultat attendu | Ce qui serait une anomalie |
|---|---|---|
| Fixture valide | PASS | Rejet inexpliqué ou octets différents |
| Mutation d’octet | FAIL d’intégrité | Altération non détectée |
| Signature invalide | FAIL d’authenticité | Signature acceptée |
| Opération interdite bien signée | Authentique, mais FAIL d’autorisation | Signature considérée comme autorisation |
| Parent manquant | FAIL ou INCONCLUSIVE de causalité | Complétude annoncée |
| Panne avant acquittement | État récupérable sans ambiguïté | Événement fantôme ou perte silencieuse |
| Panne après acquittement | Événement durable récupéré | Événement confirmé puis perdu |
| Replay avec dépendance indisponible | INCONCLUSIVE/NOT_TESTED | PASS sans réserve |
| Source non instrumentée | Couverture réduite déclarée | Absence d’événement assimilée à absence d’action |

## 10. Seuils de sortie avant implémentation

Le développement futur ne devrait pas déclarer le ledger conforme tant que les critères suivants ne sont pas définis et vérifiés :

1. Le schéma d’événement est versionné et canonique.
2. Chaque garantie dispose d’au moins un test positif et un test négatif.
3. Les événements acquittés respectent une définition écrite de la durabilité.
4. La détection des mutations, suppressions intermédiaires et réordonnancements est démontrée sur des fixtures.
5. Les règles d’idempotence et de collision d’identifiants sont explicites.
6. La rotation et la révocation des clés sont testées sans effacer les preuves historiques.
7. Le graphe causal détecte les références absentes et les cycles interdits.
8. Le replay annonce un niveau R0–R4 et refuse de surdéclarer la fidélité.
9. Les pertes d’instrumentation et les limites de couverture sont visibles.
10. Les données sensibles et les secrets factices sont détectés ou protégés selon la politique.
11. Les résultats peuvent être reproduits depuis un manifeste et des fixtures versionnées.
12. Les tests produisent un rapport structuré et un résumé de preuve vérifiable.
13. Les logs bruts sont conservés hors du dépôt Git ; seuls les rapports assainis et les références d’artefacts nécessaires sont versionnés.
14. Aucune fonction de sécurité ne dépend uniquement d’un contrôle que l’agent contrôlé peut falsifier lui-même.

Ces critères sont des conditions proposées. Ils ne sont pas encore déclarés satisfaits.

## 11. Architecture de validation recommandée

- **Producteurs Python :** émettent des événements via un contrat stable et incluent le contexte disponible.
- **Security Core Rust, si cette décision est retenue à l’implémentation :** valide les événements, les identifiants, les règles d’intégrité et les transitions critiques.
- **Stockage durable :** applique une sémantique explicite d’écriture, d’acquittement et de reprise.
- **Vérificateur indépendant :** relit et recalcule les preuves sans se fier uniquement au cache ou au statut du producteur.
- **Moteur de replay :** consomme un manifeste figé et des réponses d’outils enregistrées ; il n’exécute pas d’effets externes non autorisés.
- **Rapporteur de conformité :** publie les résultats et les limites sans inclure de secrets ni de logs bruts.

Cette architecture est une recommandation de conception, pas la description d’un logiciel déjà présent dans le dépôt TERMINATOR.

## 12. Risques résiduels à inscrire dans tout rapport

- Un hash prouve une correspondance avec une empreinte, pas l’exhaustivité de la collecte.
- Une signature prouve l’usage d’une clé, pas que l’agent a dit vrai.
- Une chaîne append-only n’est pas inviolable si un attaquant peut réécrire toute la chaîne et les seuls checkpoints.
- Une horloge locale peut être fausse ; l’ordre causal et l’heure murale doivent être distingués.
- Un replay peut dépendre de services, modèles ou données disparus.
- La conservation totale peut contenir des secrets ou des données personnelles : la traçabilité ne justifie pas leur exposition.
- Un composant de collecte compromis peut omettre les événements qu’il devrait émettre.
- Une preuve cryptographique peut être parfaitement valide pour un calcul incorrect ou une politique mal conçue.

Les contrôles complémentaires possibles incluent des checkpoints signés conservés séparément, des témoins indépendants, une politique de clés documentée, une surveillance de couverture, des fixtures adversariales et une procédure de récupération testée.

## 13. Continuité des rapports et travaux en attente

R594 prolonge directement R593 et doit être lu avec les rapports R590–R593. Les autres chantiers historiques signalés dans les documents du projet — migration sélective Rust/Python, mémoire artificielle totale et provenance, Node Key/TPM, confidentialité/FHE et préparation Track 2 — restent des axes distincts à réconcilier dans les futurs rapports. R594 ne prétend ni les avoir terminés ni les avoir testés.

La suite logique proposée est **R595 — contrat d’événement canonique et modèle de données de référence**, comprenant les champs normatifs, la canonicalisation, les règles d’idempotence, les identifiants, les versions et les exemples de fixtures. Cette étape restera une spécification tant qu’aucune implémentation ou exécution de tests n’aura été explicitement réalisée.

## 14. Contrôle de périmètre

| Contrôle | Résultat de cette étape |
|---|---|
| Rapport destiné à `rapports/` dans `ARTCB-TERMINATOR` | Oui, chemin de création demandé |
| Dépôt source `vgactech/artcb` modifié | Non |
| Code applicatif TERMINATOR modifié | Non |
| LUM/VORAC ou Memory Tracker intégré | Non |
| Logs bruts ajoutés au dépôt | Non |
| Tests automatisés réellement exécutés | Non |
| Conformité du ledger déclarée acquise | Non |
| Contenu relu après création | À vérifier après commit |

**Conclusion :** R594 définit comment tester l’intégrité, la causalité, la durabilité et le replay sans transformer une spécification en résultat fictif. La priorité n’est pas de déclarer le système sûr, mais de rendre chaque revendication testable, chaque échec visible et chaque limite explicite.
