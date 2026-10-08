# R593 — Spécification normative de traçabilité atomique des exécutions ARTCB Guardian

**Date :** 2026-10-09  
**Dépôt de travail :** `vgactech/ARTCB-TERMINATOR`  
**Dossier autorisé :** `rapports/` uniquement  
**Dépôt source audité :** `vgactech/artcb`  
**Branche source :** `main`  
**Référence source synchronisée :** R590, commit `7304d493018995d851ed5c13107c5e9d5bd79268`  
**Rapports précédents de référence :** R590, R591, R592  
**Objet :** spécifier une traçabilité atomique, causale, vérifiable et rejouable pour les exécutions d’ARTCB Guardian, en s’inspirant du niveau de rigueur demandé pour les exécutions « neurone/atome par atome » du chantier LVX&ARTCB, sans importer ni intégrer les technologies LUM/VORAC ou Memory Tracker.  
**Statut :** spécification et plan de validation — aucune implémentation applicative réalisée.

---

## 1. Expertises mobilisées

- Audit GitHub et traçabilité des changements ;
- cybersécurité agentique et défense des systèmes multi-agents ;
- provenance computationnelle et causalité ;
- event sourcing, journal append-only et Write-Ahead Logging ;
- cryptographie appliquée, hash chaining et signatures ;
- forensic computing et reconstruction d’incidents ;
- replay déterministe et reproductibilité ;
- intégrité des archives et gestion des versions ;
- architecture Rust/Python et contrats d’interface ;
- sécurité MCP/API et contrôle des outils ;
- instrumentation des exécutions IA ;
- tests adversariaux et validation des preuves ;
- protection des données sensibles et minimisation de l’exposition ;
- préparation de démonstration Secure Horizons — Track 2, Defenders Augmented.

## 2. Décision exécutive

ARTCB Guardian doit traiter chaque exécution instrumentée comme une séquence de faits distincts, reliés causalement et vérifiables indépendamment. Il ne suffit pas de conserver le résumé final d’un agent, ni un journal textuel qui pourrait être modifié sans détection.

Le modèle cible est :

**entrée → événement atomique → validation → transformation → événement atomique → décision de politique → preuve → sortie contrôlée → replay vérifiable.**

« Atomique » signifie ici qu’une action observable ou une transition d’état significative produit une unité d’événement séparément identifiable. Un événement peut représenter, par exemple, la réception d’un prompt, la lecture d’un artefact, la transmission d’un message à un autre agent, l’appel d’un outil, une modification de mémoire, le rejet d’une hypothèse, un blocage de sortie ou la création d’une preuve.

Cette exigence ne signifie pas que l’on peut enregistrer littéralement chaque opération physique interne ou chaque neurone d’un grand modèle de langage. Le périmètre rigoureux est celui de toutes les entrées, sorties, transitions, opérations, artefacts et métadonnées qui sont accessibles et instrumentables par ARTCB. Toute zone non instrumentée doit être explicitement signalée comme une limite de couverture, et jamais présentée comme observée.

### Processus

Chaque composant instrumenté émet des événements structurés. Un cœur de sécurité valide leur schéma, établit leur ordre causal, calcule les empreintes, les écrit durablement et permet ensuite de vérifier la chaîne.

### Problème

Un journal ordinaire peut être incomplet, réordonné, supprimé ou réécrit. Un hash isolé prouve seulement l’égalité d’un objet à une empreinte connue ; il ne démontre pas à lui seul que l’exécution entière est complète, correcte ou autorisée.

### Solution

Combiner plusieurs garanties distinctes : identifiants stables, liens parent-enfant, horodatages déclarés et monotones, empreintes cryptographiques, chaînage, signatures lorsque l’identité de l’émetteur doit être prouvée, archivage durable, politique versionnée, marqueurs de couverture et replay avec comparaison des états. Chaque garantie doit être testée séparément.

## 3. Synchronisation et périmètre

Le dépôt source `vgactech/artcb` a été consulté avant la rédaction. Le commit R590, `7304d493018995d851ed5c13107c5e9d5bd79268`, est la référence de positionnement actuellement vérifiée dans l’historique consulté. Le dépôt cible contient déjà R591, cahier des charges Rust/Python, et R592, matrice de migration P0.

R592 identifie comme éléments prioritaires le ledger d’événements, la persistance, la provenance, le firewall de divulgation, le replay et les appels d’outils MCP. R593 précise le contrat de traçabilité à appliquer à ces composants avant toute implémentation.

### Limites d’écriture obligatoires

- Écrire uniquement dans `vgactech/ARTCB-TERMINATOR/rapports/`.
- Ne modifier aucun fichier de code ou de configuration dans `vgactech/ARTCB-TERMINATOR`.
- Ne modifier aucun fichier dans `vgactech/artcb`.
- Ne transférer ni fusionner du code, des dépendances ou des données depuis le chantier LVX&ARTCB.
- Ne publier aucun log brut, secret, donnée personnelle, clé, dump mémoire ou artefact d’exécution sensible dans Git.
- Ne pas intégrer ni utiliser les technologies LUM/VORAC ou Memory Tracker. La référence LVX&ARTCB porte uniquement sur le niveau de rigueur de traçabilité demandé, pas sur la réutilisation de ses technologies.
- Toute évolution de périmètre doit être documentée dans un rapport ultérieur avant implémentation.

## 4. Vocabulaire normatif

**Événement atomique** : unité indivisible du journal du point de vue du contrat de traçabilité. Une fois validé et durablement engagé, son contenu historique n’est pas modifié ; une correction crée un nouvel événement qui référence l’événement corrigé.

**Artefact** : donnée ou objet manipulé ou produit par le système : entrée, réponse, fichier, message, résultat d’outil, décision, preuve, snapshot ou état dérivé.

**Événement parent** : événement causal dont dépend directement l’événement courant. Un événement peut avoir plusieurs dépendances explicites si une opération combine plusieurs sources.

**Empreinte** : digest cryptographique d’une représentation canonique des données. Une empreinte ne remplace pas l’archive du contenu.

**Provenance** : liens explicites entre agents, événements, artefacts, outils, politiques, décisions et résultats.

**Couverture** : proportion des opérations attendues qui sont effectivement instrumentées et vérifiées. La couverture doit préciser son dénominateur ; elle ne peut pas être extrapolée à des opérations invisibles.

**Replay** : reconstruction de l’ordre et des transitions à partir des événements archivés, suivie de la comparaison avec les empreintes et états attendus. Le replay n’implique pas que l’appel d’un LLM ou d’une API externe produira de nouveau la même réponse.

**Preuve** : objet vérifiable associé à une affirmation limitée et clairement définie, par exemple l’intégrité d’une chaîne, l’identité du signataire, la décision de blocage ou la correspondance d’un état reconstruit.

## 5. Contrat minimal d’un événement atomique

Chaque événement doit contenir les champs suivants, ou une justification versionnée lorsqu’un champ est inapplicable :

| Champ | Fonction | Contrôle attendu |
|---|---|---|
| `schema_version` | Version du contrat | Refuser ou mettre en quarantaine les versions inconnues |
| `event_id` | Identité unique de l’événement | Unicité dans son espace de noms |
| `run_id` | Exécution concernée | Stable durant l’exécution |
| `session_id` | Session ou scénario | Permet de regrouper les événements |
| `sequence_no` | Position dans le flux local | Monotone, sans prétendre remplacer la causalité |
| `parent_event_ids` | Dépendances causales | Tous les parents référencés doivent exister ou être explicitement externes |
| `agent_id` | Agent initiateur | Identité déclarée, vérifiée selon le niveau de confiance |
| `component_id` | Composant exécutant | Composant/version connus |
| `event_type` | Type d’action | Enumération versionnée, pas de type arbitraire silencieux |
| `operation` | Opération effectuée | Action concise et non ambiguë |
| `status` | Résultat opérationnel | SUCCESS, FAILURE, BLOCKED, REJECTED, UNKNOWN ou valeur versionnée |
| `input_refs` | Références des entrées | Identifiants et empreintes, sans exposer inutilement les secrets |
| `output_refs` | Références des sorties | Identifiants et empreintes |
| `artifact_refs` | Artefacts associés | Références d’archive et classification |
| `policy_id/version` | Politique appliquée | Obligatoire pour toute décision protégée |
| `timestamp_utc` | Heure déclarée | UTC ; conserver séparément l’information d’horloge si nécessaire |
| `monotonic_counter` | Ordre local résistant aux retours d’horloge | Monotone dans le périmètre du producteur |
| `previous_event_hash` | Lien avec le précédent événement du flux | Vérification de continuité |
| `event_hash` | Empreinte canonique de l’événement | Recalculable indépendamment |
| `signature_ref` | Signature du producteur, si exigée | Vérification de la clé et de son statut |
| `evidence_refs` | Preuves associées | Chaque preuve doit avoir un type et un vérificateur |
| `classification` | Niveau de sensibilité | UNKNOWN doit être traité explicitement |
| `coverage_status` | État d’instrumentation | COMPLETE, PARTIAL, EXTERNAL ou UNKNOWN |

Les champs optionnels doivent être définis comme tels dans le schéma. L’absence d’une valeur ne doit jamais être interprétée implicitement comme une validation réussie.

## 6. Canonicalisation et calcul d’empreinte

### Processus

Pour qu’un même événement produise la même empreinte sur plusieurs implémentations, il faut définir une représentation canonique : encodage, ordre des champs, normalisation des chaînes, traitement des nombres, représentation des valeurs nulles et format des références.

### Problème

Si Python et Rust sérialisent le même objet différemment, les empreintes peuvent diverger sans qu’aucune donnée ait été altérée. À l’inverse, une sérialisation ambiguë peut permettre à deux structures différentes de produire la même séquence d’octets avant hachage.

### Solution

1. Définir un schéma versionné et une représentation canonique indépendante du langage.
2. Refuser les champs inconnus non autorisés ou les conserver dans une enveloppe explicitement versionnée.
3. Calculer l’empreinte sur la représentation canonique, pas sur l’affichage humain.
4. Inclure dans la représentation les identifiants, références de parents, type, statut, empreintes d’entrées/sorties, politique et version de schéma.
5. Écrire des vecteurs de test publics au sein du rapport technique futur : entrée canonique, octets attendus, empreinte attendue et cas invalides.
6. Vérifier les mêmes vecteurs dans Rust et Python.
7. Ne jamais inventer une preuve de signature à partir d’un simple hash.

Le choix exact de sérialisation et de domaine de hachage doit être arrêté dans un rapport de conception normatif suivant, puis figé par des tests de compatibilité. Toute modification ultérieure doit augmenter la version du contrat.

## 7. Modèle de causalité et ordre

L’ordre chronologique ne suffit pas à établir la causalité. Deux agents peuvent travailler en parallèle, et l’horloge d’une machine peut dériver.

Chaque opération doit donc conserver les deux éléments suivants :

- un ordre local monotone pour le producteur ;
- des références explicites aux événements dont elle dépend.

Pour une communication entre agents, la chaîne minimale doit relier l’émission, le message, la réception, la décision de consommation et l’action qui en découle. Une transmission qui n’a pas été reçue ne doit pas être présentée comme consommée. Un résultat d’outil doit référencer l’appel exact qui l’a déclenché.

### Exemple conceptuel

Agent A crée un artefact → A émet un message → le message reçoit un identifiant et une empreinte → Agent B accuse réception → B lit l’artefact → B prend une décision → B appelle un outil → le résultat de l’outil est archivé → le firewall autorise ou bloque la sortie → la décision et la preuve sont liées à la même exécution.

Chaque flèche doit correspondre à un événement ou à une relation causale explicite, et non à une inférence ajoutée après coup.

## 8. Couverture « atome par atome » de l’exécution instrumentée

La couverture de référence doit inclure les catégories suivantes.

1. Réception et validation des entrées.
2. Création de session et sélection du scénario.
3. Chargement du contexte et lecture d’artefacts.
4. Résolution de références mémoire et récupération d’informations.
5. Construction des messages destinés aux agents.
6. Émission, transport, réception et validation des messages inter-agents.
7. Appels d’outils, arguments normalisés, décision de policy, résultat et erreurs.
8. Transformations de données, parsing, OCR, extraction, normalisation et conversion.
9. Création, mise à jour, rejet ou invalidation d’un artefact mémoire.
10. Décisions du Disclosure Firewall : ALLOW, BLOCK, REDACT ou ESCALATE.
11. Échecs, exceptions, timeouts, retries et changements de branche.
12. Création et vérification des preuves.
13. Écriture durable, récupération après crash et détection de corruption.
14. Construction des vues dérivées, index et résumés, avec références vers les sources.
15. Export, affichage, publication ou transmission vers une frontière externe.
16. Fin de l’exécution, bilan de couverture et vérification de chaîne.

Les raisonnements internes non exposés par le modèle ne doivent pas être inventés ni reconstitués comme s’ils avaient été observés. On peut enregistrer les entrées/sorties instrumentables, les appels d’outils, les hypothèses explicitement émises, les décisions déclarées et les résultats vérifiables. Toute prétention plus forte nécessite un mécanisme technique démontré.

## 9. Mémoire totale : archive de preuve et vues dérivées

La mémoire complète de provenance est l’archive historique de référence pour les opérations instrumentées. Les résumés, embeddings, index, caches et graphes accélérateurs sont des vues dérivées.

Règles :

- une vue dérivée doit pointer vers les événements et artefacts sources ;
- la suppression ou la reconstruction d’un cache ne doit pas supprimer la source historique ;
- un résumé erroné doit pouvoir être comparé à la source ;
- une correction est ajoutée comme nouvel événement, pas écrasée sur l’événement initial ;
- une donnée confidentielle peut être conservée chiffrée avec empreinte et référence, sans être copiée en clair dans le ledger ;
- la conservation « totale » s’applique au périmètre instrumenté et autorisé ; elle ne justifie pas de publier des secrets ou des données personnelles dans Git.

Un ancrage blockchain peut certifier une empreinte ou un engagement, mais il ne remplace ni l’archive, ni le contrôle d’accès, ni les preuves de complétude. Il ne faut donc pas écrire sur la chaîne publique tout le contenu brut des événements par défaut.

## 10. Intégrité, signature et limites de preuve

Les garanties doivent être nommées précisément :

- **empreinte** : détecte une divergence par rapport à une empreinte de référence ;
- **chaînage** : rend détectables les altérations, suppressions ou réordonnancements dans une chaîne vérifiée ;
- **signature** : rattache un message signé à une clé, sous réserve de la validité de cette clé et de la protection du processus de signature ;
- **attestation matérielle** : concerne un état matériel ou de démarrage défini ; elle ne prouve pas automatiquement que chaque décision métier est correcte ;
- **journal durable** : permet la récupération après panne selon les garanties d’écriture effectivement testées ;
- **replay** : vérifie la reconstruction selon les événements conservés ; il ne garantit pas qu’un modèle non déterministe répondra identiquement lors d’une nouvelle exécution ;
- **preuve de politique** : montre quelle règle versionnée a été évaluée et quel résultat a été produit ; elle ne démontre pas à elle seule que la règle est complète ou appropriée.

La sécurité ne doit jamais être décrite comme absolue. Le rapport doit indiquer les hypothèses de confiance, les frontières instrumentées et les scénarios non couverts.

## 11. Contrat Rust/Python recommandé

Conformément à R591/R592, Python peut rester responsable de l’orchestration et des scénarios. Le cœur Rust doit valider les événements, calculer les empreintes, imposer l’ordre du ledger, vérifier la chaîne et produire les résultats de contrôle.

Interface fonctionnelle cible à spécifier :

- validation de schéma ;
- canonicalisation ;
- ajout d’événement atomique ;
- lecture d’événements par plage ou exécution ;
- vérification d’un événement ;
- vérification d’une chaîne ;
- ajout et vérification de relations de provenance ;
- décision de policy pour les opérations protégées ;
- création et vérification d’une preuve ;
- replay d’un scénario ;
- rapport de couverture ;
- récupération et vérification après arrêt brutal.

Python ne doit pas pouvoir fournir arbitrairement le hash final comme s’il s’agissait d’une preuve calculée par le cœur de sécurité. Les erreurs d’intégrité doivent être explicites et bloquer les opérations qui dépendent de la preuve, selon une politique fail-closed versionnée.

Ce rapport ne crée pas ces fonctions : il en définit les exigences pour une phase d’implémentation future.

## 12. Threat model : attaques et contrôles obligatoires

| ID | Attaque ou panne | Détection attendue | Preuve attendue |
|---|---|---|---|
| T01 | Modification d’un événement déjà engagé | Échec d’empreinte/chaîne | Événement d’intégrité invalide |
| T02 | Suppression d’un événement intermédiaire | Rupture de séquence ou parent manquant | Rapport de chaîne incomplète |
| T03 | Réordonnancement d’événements | Parent ou hash précédent incohérent | Rapport d’ordre invalide |
| T04 | Réutilisation d’un identifiant avec contenu différent | Conflit d’idempotence | Ancienne et nouvelle empreintes référencées |
| T05 | Message inter-agent non relié à sa source | Parent/message absent | Provenance PARTIAL ou FAIL |
| T06 | Résultat d’outil sans appel correspondant | Référence d’appel manquante | Événement orphelin détecté |
| T07 | Tentative d’exfiltration | Policy BLOCK/REDACT/ESCALATE | Décision, règle, raison et empreintes |
| T08 | Empoisonnement de mémoire | Mutation et provenance de la source | Lignée jusqu’à l’événement initial |
| T09 | Rejeu d’une ancienne décision | Nonce, identifiant ou état incompatible selon protocole | Détection de replay |
| T10 | Crash pendant écriture | Récupération contrôlée | Aucun événement déclaré durable sans garantie confirmée |
| T11 | Fichier de preuve altéré | Vérification négative | Evidence verification FAIL |
| T12 | Version de schéma inconnue | Rejet ou quarantaine explicite | Motif et version reçue |
| T13 | Horloge reculant ou dérivant | Écart entre ordre monotone et timestamp | Anomalie temporelle enregistrée |
| T14 | Perte d’instrumentation | Écart de couverture ou séquence manquante | Marqueur PARTIAL/UNKNOWN |
| T15 | Secret copié dans un rapport Git | Contrôle de classification avant export | Export bloqué et événement de sécurité |

Le test doit vérifier non seulement que l’alerte apparaît, mais aussi que l’événement de sécurité lui-même est durable, vérifiable et présent dans le replay.

## 13. Critères d’acceptation mesurables

Le statut global doit être calculé à partir de résultats observables, pas attribué par intuition.

- **Intégrité** : toutes les mutations injectées dans les tests sont détectées.
- **Ordre** : tous les réordonnancements ciblés sont détectés.
- **Causalité** : chaque opération protégée du scénario possède ses parents ou est marquée explicitement comme externe/inconnue.
- **Appels d’outils** : chaque appel instrumenté est lié à ses arguments normalisés, sa décision de policy, son résultat et son statut.
- **Firewall** : chaque BLOCK/REDACT/ESCALATE possède une policy versionnée et une preuve référencée.
- **Durabilité** : les tests de crash distinguent les événements écrits, synchronisés et récupérables ; aucune garantie n’est revendiquée sans test.
- **Replay** : la reconstruction des événements instrumentés correspond à l’archive de référence ; une modification historique fait échouer la vérification.
- **Couverture** : le rapport indique le nombre d’événements attendus, capturés, validés, manquants et inconnus.
- **Non-régression** : les vecteurs canoniques sont identiques entre Rust et Python.
- **Confidentialité** : aucun secret brut ni log sensible n’est ajouté au dépôt Git.
- **Périmètre** : aucune modification de code source n’est faite pendant la phase de spécification.

Un « 100 % » ne peut être affiché que pour un dénominateur explicitement défini, par exemple « 100 % des événements attendus du scénario instrumenté ont été capturés et vérifiés ». Cela ne signifie pas « 100 % de l’activité interne de tout modèle IA a été observée ».

## 14. Démonstration Secure Horizons — Track 2

Le scénario doit démontrer une attaque contenue et reconstructible, pas une promesse d’invulnérabilité.

### Chronologie proposée, environ 6 minutes

**0:00–0:45 — État nominal.** Présenter les agents et leur identité déclarée, les événements initiaux et le statut de couverture.

**0:45–1:30 — Injection.** Introduire un document ou un message hostile contrôlé. Le contenu reçoit une empreinte et une provenance initiale.

**1:30–2:15 — Propagation.** Faire transmettre l’artefact à un autre agent. Afficher les événements d’émission, réception, lecture et décision.

**2:15–3:00 — Action dangereuse simulée.** Un agent tente d’appeler un outil protégé ou de divulguer une donnée de test. La politique décide BLOCK ou REDACT avant l’action protégée.

**3:00–4:00 — Preuve.** Montrer l’événement de blocage, la règle et sa version, les empreintes d’entrée/sortie et la relation causale.

**4:00–5:00 — Replay.** Reconstruire la chaîne depuis l’entrée jusqu’au blocage, sans dépendre d’une nouvelle réponse du modèle.

**5:00–6:00 — Test d’altération.** Modifier une copie de test d’un événement historique ; le vérificateur doit détecter la divergence. Ne jamais altérer les données de production pour la démonstration.

Formule à dire au jury : **« Nous ne prétendons pas empêcher toute attaque. Nous montrons quelles opérations ont été observées, comment l’attaque s’est propagée, quelle action a été bloquée et comment vérifier la reconstruction. »**

## 15. Gestion des archives, secrets et journaux

Les logs bruts de test, données KYC, identifiants, secrets d’API, clés, données biométriques, prompts privés et dumps mémoire ne doivent pas être poussés dans Git. Le dépôt doit recevoir les rapports, schémas non sensibles et résultats de tests expurgés uniquement.

Pour les scénarios reproductibles, conserver plutôt :
- un identifiant d’exécution ;
- un manifeste de fichiers de test non sensibles ;
- les empreintes des entrées ;
- les versions de logiciel et de policy ;
- les événements expurgés nécessaires à la compréhension ;
- les résultats PASS/FAIL ;
- la procédure de reproduction ;
- les limites et écarts constatés.

Si l’archive complète contient des informations confidentielles, elle doit rester dans le stockage sécurisé prévu par l’architecture ; le rapport Git n’en conserve que les références et empreintes autorisées.

## 16. Dépendances et technologies : interdictions de périmètre

R593 ne propose pas de reprendre le moteur, les bibliothèques, les formats internes ou les mécanismes du chantier LVX&ARTCB. La seule transposition recherchée est la discipline de traçabilité : granularité des événements, relations de provenance, intégrité, contrôle, replay et preuve.

**LUM/VORAC et Memory Tracker sont explicitement exclus de l’architecture, des dépendances, de l’implémentation et de la démonstration ARTCB Guardian.** Aucun code, module, service, protocole propriétaire, base de données ou mécanisme de ces technologies ne doit être appelé, copié ou intégré dans ce chantier.

Le besoin doit être satisfait par des contrats et composants ARTCB propres, documentés, testables et indépendants. Le nom LVX&ARTCB est une référence de repérage/audit du niveau de rigueur demandé, et non une autorisation de migration.

## 17. Travaux précédents et continuité

R593 ne clôt aucun chantier précédent. Il s’appuie sur :
- **R590** : positionnement Track 2 et scénario de défense ;
- **R591** : cahier des charges et architecture cible Rust/Python ;
- **R592** : matrice P0 du ledger, de la provenance, du firewall et du replay ;
- **R589** : distinction entre mémoire de décision et archive de provenance complète ;
- **R587** : tests biométriques, sans extrapoler les résultats en preuve absolue d’unicité humaine ;
- **R582 et travaux connexes** : divulgation, classification et contrôle de sortie ;
- **R584/R588** : filtres de mémoire décisionnelle, qui ne doivent pas être confondus avec une archive complète de provenance.

Les éléments précédents restent des chantiers actifs ou des références. La priorité courante ne doit pas les effacer ni les déclarer achevés sans preuve vérifiable.

## 18. Plan d’action suivant

**R594 — Vecteurs de conformité du ledger et protocole de replay.** Définir, avant implémentation :
1. le schéma canonique complet et les versions ;
2. les vecteurs de hachage de référence ;
3. les règles de parenté et d’ordre ;
4. les transitions de statut et erreurs ;
5. les garanties de persistance et scénarios de crash ;
6. les formats d’évidence ;
7. les fixtures adversariales synthétiques ;
8. les règles de mesure de couverture ;
9. les tests de compatibilité Rust/Python ;
10. les critères exacts de PASS/FAIL.

Puis seulement, dans un chantier ultérieur explicitement autorisé, implémenter et tester le cœur correspondant. Aucun code n’est modifié par R593.

## 19. Verdict final

La traçabilité atomique d’ARTCB Guardian doit être une propriété du contrat d’exécution, et non une simple option de journalisation. Chaque opération instrumentée doit être identifiable, ordonnée, reliée à ses dépendances, classifiée, vérifiable et rejouable ; chaque lacune doit rester visible au lieu d’être masquée par un résumé.

**Principe directeur : aucune transformation instrumentée ne disparaît silencieusement ; toute correction crée une nouvelle trace ; toute prétention de sécurité doit correspondre à une preuve testable ; toute limite de couverture doit être explicitement déclarée.**

**Résultat de cette étape : spécification rédigée uniquement dans le dossier de rapports. Aucun code applicatif, aucune configuration et aucun log brut n’ont été modifiés ou ajoutés.**
