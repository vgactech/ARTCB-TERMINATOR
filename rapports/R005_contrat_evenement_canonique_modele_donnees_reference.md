# R005 — Contrat d’événement canonique et modèle de données de référence ARTCB Guardian

**Date :** 2026-10-09  
**Dépôt cible :** `vgactech/ARTCB-TERMINATOR`  
**Branche cible :** `main`  
**Dossier autorisé :** `rapports/` uniquement  
**Rapports de référence :** R001 (roadmap Rust/Python), R002 (migration P0), R003 (traçabilité atomique), R004 (conformité du ledger et replay)  
**Objet :** fixer les identifiants, la représentation canonique, les règles d’idempotence, les versions de schéma et les fixtures de référence avant toute implémentation.  
**Statut :** contrat de conception normatif proposé. Aucune implémentation applicative ni test automatisé n’est revendiqué par ce rapport.

## 1. Expertises activées

- Architecture de données et contrats d’événements ;
- event sourcing, ledger append-only et Write-Ahead Logging ;
- canonicalisation JSON et interopérabilité Rust/Python ;
- cryptographie appliquée, hashage, signatures et séparation de domaines ;
- identifiants distribués, idempotence et traitement « at least once » ;
- provenance causale et graphes d’événements ;
- versionnage de schémas et compatibilité ;
- sécurité des agents IA, des outils MCP et des flux inter-agents ;
- protection des données sensibles et références d’artefacts ;
- tests de conformité, fixtures golden et validation différentielle ;
- forensic computing, reprise après panne et replay ;
- préparation technique du Track 2 — Defenders Augmented.

## 2. Décision exécutive

Le contrat de référence est un événement immuable, versionné, identifié de manière unique, sérialisé de façon canonique et relié à ses causes. Il doit pouvoir être produit par Python et vérifié par Rust sans dépendre de l’ordre d’insertion des champs, des conventions d’une bibliothèque ou du formatage d’un journal humain.

**Décision proposée :**
1. JSON comme format d’échange initial ;
2. JSON Canonicalization Scheme (JCS), RFC 8785, pour produire les octets canoniques ;
3. JSON Schema Draft 2020-12 pour valider la structure ;
4. UUIDv7, selon RFC 9562, pour les identifiants d’événements nouvellement créés, sans utiliser l’UUID comme preuve d’ordre causal ;
5. SHA-256 pour l’empreinte initiale du contenu canonique, avec séparation de domaine ;
6. une clé d’idempotence distincte de `event_id` ;
7. références d’artefacts avec empreinte, taille, média, classification et localisation logique, plutôt que l’inclusion automatique de contenus sensibles dans le ledger ;
8. un contrat de compatibilité explicite : aucune modification silencieuse d’un événement accepté ; toute correction produit un nouvel événement.

Ces choix forment une baseline d’interopérabilité. Ils ne prouvent pas à eux seuls la complétude de l’instrumentation, la véracité du producteur ou la correction d’une décision.

## 3. Processus, problème, solution

### 3.1 Processus

Un producteur crée un événement selon un schéma précis. Le validateur contrôle les champs et les références. Le sérialiseur canonique transforme le corps de l’événement en une séquence d’octets unique. Le moteur d’intégrité calcule une empreinte. Le ledger applique l’idempotence, vérifie les dépendances et les contraintes de séquence, puis persiste l’événement. Une signature peut ensuite authentifier l’enveloppe selon le profil de confiance retenu.

### 3.2 Problème

Sans contrat commun, Python et Rust peuvent sérialiser le même objet différemment. Les reprises réseau peuvent dupliquer un événement. Un horodatage peut être pris à tort pour une preuve de causalité. Un changement de schéma peut altérer le sens d’anciens événements. Enfin, un hash ne dit rien sur une donnée qui n’a jamais été collectée.

### 3.3 Solution

Définir un corps de données stable, un profil de canonicalisation déterministe, des identifiants aux rôles distincts, une règle d’idempotence transactionnelle, des versions explicites et des fixtures identiques exécutées par les deux langages. Tout résultat de validation doit distinguer au minimum `PASS`, `FAIL`, `INCONCLUSIVE` et `NOT_TESTED`.

## 4. Vocabulaire normatif

- **Événement** : déclaration immuable d’une action, d’une transition ou d’un fait observable dans le périmètre instrumenté.
- **Corps canonique** : objet de données soumis à la canonicalisation et au calcul d’empreinte ; il exclut les champs calculés à partir de lui-même.
- **Enveloppe** : métadonnées de transport et d’intégrité entourant le corps, telles que l’empreinte, la signature et les informations d’ingestion.
- **Artefact** : donnée référencée ou produite, stockée dans l’archive ou dans un stockage externe contrôlé.
- **Causalité** : relation explicite de dépendance entre événements. Elle ne se déduit pas uniquement de l’horloge.
- **Clé d’idempotence** : identifiant stable d’une intention d’écriture ou d’une opération, réutilisé lors d’une nouvelle tentative.
- **Producteur** : agent ou composant qui émet un événement ; le nom déclaré n’est pas à lui seul une preuve d’identité.
- **Fixture golden** : entrée de référence et résultat attendu, versionnés, utilisés pour comparer plusieurs implémentations.
- **Correction** : nouvel événement qui référence l’événement précédent ; jamais une réécriture de l’historique.
- **Événement externe** : événement dont le producteur, l’horloge ou le stockage ne sont pas entièrement contrôlés par Guardian.

Les mots **DOIT**, **NE DOIT PAS**, **DEVRAIT** et **PEUT** sont employés au sens normatif de ce contrat.

## 5. Modèle de données de référence

### 5.1 Identifiants et espaces de noms

| Champ | Format proposé | Règle |
|---|---|---|
| `event_id` | UUIDv7 en texte canonique minuscule avec tirets | Unique dans le ledger ; généré une fois et réutilisé lors des retries |
| `run_id` | UUIDv7 | Identifie une exécution logique, pas chaque tentative réseau |
| `session_id` | UUIDv7 | Identifie la session ou le scénario ; peut couvrir plusieurs runs si le scénario le prévoit |
| `producer_id` | identifiant opaque et versionné | Référence l’agent ou le composant déclaré |
| `producer_instance_id` | UUIDv7 ou identifiant d’instance opaque | Distingue deux instances du même producteur |
| `idempotency_key` | chaîne opaque, limitée et non secrète | Stable pour une même intention d’écriture ; distincte de `event_id` |
| `parent_event_ids` | tableau d’`event_id` | Ensemble des dépendances causales directes connues |
| `artifact_id` | UUIDv7 ou identifiant opaque stable | Identifie un artefact, indépendamment de son emplacement |
| `policy_id` | identifiant opaque stable | Désigne une politique ; `policy_version` identifie sa version exacte |
| `schema_version` | version explicite, par exemple `1.0.0` | Ne doit pas être déduite de la date ni du nom de fichier |
| `event_type` | valeur d’une nomenclature versionnée | Les valeurs inconnues sont refusées ou mises en quarantaine selon le profil |

UUIDv7 fournit un identifiant largement distribuable et approximativement ordonné par temps de création. **Il ne remplace pas** `sequence_no`, la relation causale ou le mécanisme de chaîne. Une horloge incorrecte, une collision opérationnelle ou un producteur compromis restent des cas à traiter.

Les identifiants ne doivent contenir ni nom de personne, ni adresse e-mail, ni secret, ni donnée sensible encodée.

### 5.2 Corps canonique de l’événement

Le corps version 1 doit comporter les champs suivants :

| Champ | Type | Obligatoire | Règle de validation |
|---|---|---:|---|
| `schema_id` | chaîne | oui | URI ou identifiant stable du schéma |
| `schema_version` | chaîne | oui | Version exacte du contrat |
| `event_id` | chaîne | oui | UUIDv7 valide ou format d’identifiant explicitement autorisé par le profil |
| `event_type` | chaîne | oui | Valeur de l’énumération versionnée |
| `occurred_at` | chaîne RFC 3339 | oui | Date-heure avec décalage explicite ; préférer UTC avec suffixe `Z` |
| `producer` | objet | oui | `producer_id`, `producer_instance_id`, `component_version` |
| `execution` | objet | oui | `run_id`, `session_id`, `sequence_no` |
| `causality` | objet | oui | `parent_event_ids` et références de corrélation pertinentes |
| `operation` | objet | oui | `name`, `status` et paramètres non sensibles ou références vers ceux-ci |
| `inputs` | tableau | oui | Références d’artefacts consommés ; tableau vide explicite si aucun |
| `outputs` | tableau | oui | Références d’artefacts produits ; tableau vide explicite si aucun |
| `policy` | objet ou `null` contrôlé | oui | Identifiant/version/décision si une politique s’applique ; null autorisé uniquement pour les événements non décisionnels |
| `observability` | objet | oui | État de collecte, source et limites de couverture |
| `classification` | chaîne | oui | Classification connue ou valeur explicite `unknown` |
| `extensions` | objet | oui | Objet vide par défaut ; extensions namespacées et versionnées |

Le corps ne doit pas inclure `event_hash`, `signature`, `ingested_at` ou `previous_event_hash` dans le calcul d’empreinte de lui-même. Ces valeurs appartiennent à l’enveloppe ou à la structure du ledger. Cela évite les dépendances circulaires et sépare le fait déclaré du mécanisme d’enregistrement.

### 5.3 Enveloppe et métadonnées du ledger

L’enveloppe de stockage doit conserver, au minimum :

- `canonicalization_profile` : valeur figée, initialement `JCS-RFC8785` ;
- `hash_algorithm` : initialement `SHA-256` ;
- `event_hash` : empreinte du corps canonique avec séparation de domaine ;
- `stream_id` : identifiant du flux append-only ;
- `stream_sequence` : numéro attribué dans le flux par le ledger ;
- `previous_event_hash` : empreinte du précédent événement de ce flux, ou valeur initiale explicitement définie ;
- `signature_profile` et `signature` si la signature est requise ;
- `producer_key_id` si une clé de signature est utilisée ;
- `ingested_at` : horodatage d’ingestion du ledger, distinct de `occurred_at` ;
- `durability_status` : état de persistance et condition d’acquittement ;
- `validation_profile` et résultat de validation ;
- `integrity_profile_version` : version des règles de hashage et de chaînage.

L’enveloppe est elle-même structurée et validée. Un champ de signature absent ne signifie jamais « signature vérifiée » : le statut doit être explicite, par exemple `NOT_REQUIRED`, `VERIFIED`, `INVALID` ou `NOT_CHECKED`.

## 6. Canonicalisation normative

### 6.1 Baseline retenue

Le profil initial est **JCS selon RFC 8785**, combiné à un schéma JSON versionné. JCS définit une représentation JSON déterministe adaptée aux opérations cryptographiques ; le standard s’appuie notamment sur les règles de sérialisation JSON et le tri déterministe des propriétés. Voir RFC 8785 : https://www.rfc-editor.org/rfc/rfc8785.html

### 6.2 Règles d’encodage

1. Les octets canoniques sont encodés en UTF-8, sans BOM.
2. Les noms de propriétés dupliqués sont refusés au parsing, avant canonicalisation.
3. Les valeurs de chaîne doivent être des chaînes Unicode valides.
4. JCS ne normalise pas automatiquement les chaînes Unicode : les producteurs doivent préserver les chaînes telles qu’elles ont été validées ; toute normalisation métier doit être explicite et versionnée en amont.
5. Les champs numériques de sécurité ou de comptage doivent être des entiers dans la plage interopérable JSON. Les entiers arbitrairement grands sont représentés comme chaînes décimales selon un format spécifié.
6. Les valeurs flottantes ne doivent pas être utilisées pour des montants, compteurs, identifiants, tailles exactes ou valeurs cryptographiques. Utiliser une représentation entière ou une chaîne décimale normalisée.
7. Les dates sont des chaînes RFC 3339 validées ; elles ne sont pas converties silencieusement entre fuseaux horaires au moment du hashage.
8. Les tableaux dont l’ordre est sémantique conservent cet ordre. Les tableaux définis comme ensembles, tels que `parent_event_ids`, sont triés selon une règle de comparaison ASCII sur leurs identifiants avant canonicalisation, et les doublons sont refusés.
9. Les champs absents, `null`, chaîne vide, tableau vide et objet vide sont des états distincts. Aucun ne doit être substitué implicitement à un autre.
10. Les champs d’extension doivent être namespacés, validés et inclus dans le hash s’ils font partie du corps canonique.
11. Le format d’affichage humain, l’ordre d’écriture d’origine et l’indentation n’entrent pas dans le calcul d’empreinte.
12. Une canonicalisation inconnue ou un schéma non pris en charge provoque un rejet explicite ou une mise en quarantaine ; aucun fallback silencieux n’est permis.

### 6.3 Profil d’empreinte

Pour la version initiale, calculer l’empreinte du corps canonique ainsi :

`event_hash = SHA-256(UTF8("ARTCB-GUARDIAN-EVENT-V1") || 0x00 || canonical_body_bytes)`

Le préfixe et l’octet nul séparent ce domaine d’autres usages de SHA-256. Le nom du profil et sa version doivent être conservés avec le résultat. Le hash ne doit pas inclure l’empreinte elle-même, la signature ni les champs d’ingestion ajoutés après la création du corps.

Le chaînage du ledger utilise le profil séparé suivant :

`chain_hash = SHA-256(UTF8("ARTCB-GUARDIAN-CHAIN-V1") || 0x00 || previous_event_hash_bytes || event_hash_bytes || uint64_be(stream_sequence))`

Les valeurs `*_hash_bytes` désignent les 32 octets du digest, pas la représentation hexadécimale imprimée. Le flux initial doit avoir une règle de genesis explicite et testée ; il ne doit pas utiliser une chaîne vide ambiguë.

Ce chaînage rend des altérations détectables par rapport à une référence de confiance. Il ne prouve pas à lui seul qu’un dernier événement n’a pas été tronqué ; pour cette garantie, conserver des checkpoints ou racines signés/ancrés indépendamment.

## 7. Règles d’idempotence et de reprise

### 7.1 Principe

Les transports peuvent livrer un même message plusieurs fois. Le ledger doit donc tolérer la répétition d’une requête identique sans créer plusieurs faits historiques, tout en refusant qu’une même clé d’idempotence soit réutilisée pour un contenu différent.

### 7.2 Règles obligatoires

1. Le producteur crée `event_id` et `idempotency_key` avant la première soumission et les conserve pour chaque retry de la même opération.
2. La portée d’une clé d’idempotence est le tuple `(producer_id, run_id, idempotency_key)`, sauf si un profil versionné définit une portée plus large.
3. Si la clé n’existe pas, le ledger valide puis enregistre l’événement.
4. Si la clé existe et que le `event_hash` est identique, le ledger retourne le résultat déjà enregistré avec le même `event_id` et le statut `DUPLICATE_SAME_CONTENT`. Aucun nouvel événement historique n’est ajouté.
5. Si la clé existe mais que le `event_hash` diffère, le ledger rejette la requête avec `IDEMPOTENCY_CONFLICT`, enregistre une trace de sécurité non sensible et ne remplace pas le premier contenu.
6. Si `event_id` existe avec le même hash, le résultat existant est retourné. Si le hash diffère, le cas est un conflit d’identité et doit être rejeté.
7. L’index d’idempotence et l’écriture durable doivent être transactionnels ou avoir un protocole de récupération équivalent démontré.
8. Un accusé de réception de succès ne doit être renvoyé qu’après la condition de durabilité promise par le profil actif.
9. Après une panne avant acquittement, une nouvelle soumission doit produire soit la création unique de l’événement, soit la reconnaissance de l’événement déjà durable. Aucun état ambigu ne peut être présenté comme confirmé.
10. Les clés d’idempotence ne sont pas des secrets d’authentification et ne remplacent ni une signature ni une autorisation.

### 7.3 Séparer événement, tentative et résultat

Un retry réseau n’est pas nécessairement un nouvel événement métier. Si une tentative distincte constitue elle-même un fait pertinent (par exemple timeout, retry déclenché, réponse reçue), elle doit produire un événement séparé avec son propre identifiant et un lien vers l’événement ou l’opération d’origine. L’idempotence ne doit pas effacer l’histoire des tentatives réellement observées.

## 8. Causalité, séquences et horloges

- `sequence_no` est monotone dans le flux local d’un producteur ; il ne prétend pas établir un ordre global.
- `stream_sequence` est attribué par le ledger dans un flux précis.
- `parent_event_ids` exprime les dépendances causales directes connues.
- `occurred_at` est l’heure déclarée par le producteur ; `ingested_at` est l’heure d’ingestion du ledger.
- Une différence entre les horloges doit être conservée et signalée, pas corrigée silencieusement.
- Un événement dont le parent est inconnu est rejeté ou mis en attente de résolution ; il ne doit pas être compté comme causalement complet.
- Les cycles du graphe causal sont refusés, sauf protocole explicitement versionné.
- L’ordre de réception du réseau ne doit pas remplacer les relations de causalité.
- Un événement externe doit déclarer son statut d’observabilité et les limites de confiance de sa source.

## 9. Références d’artefacts et confidentialité

Une référence d’artefact version 1 comprend :

- `artifact_id` ;
- `digest_algorithm` et `digest` ;
- `byte_length` ;
- `media_type` ;
- `classification` ;
- `storage_ref` ou localisation logique ;
- `encryption_profile` et référence de clé, si applicable, sans jamais inclure la clé secrète ;
- `created_by_event_id` ;
- `retention_policy_id` ;
- statut de disponibilité et de vérification.

Le ledger peut conserver des empreintes et des références à un contenu chiffré. Il ne doit pas publier par défaut les prompts privés, données personnelles, secrets, clés, dumps mémoire ou réponses brutes sensibles. La conservation totale s’applique aux artefacts autorisés et instrumentés ; elle n’impose pas de rendre les contenus publics.

Un digest atteste seulement que le contenu relu correspond au digest attendu. Il ne garantit ni l’authenticité de la source initiale, ni la légalité de la collecte, ni la vérité sémantique de l’artefact.

## 10. Versionnage et compatibilité

### 10.1 Version de schéma

La baseline utilise `schema_version = "1.0.0"` pour le contrat initial. La version doit être associée à un schéma immuable identifié par `schema_id`.

- **Patch** : correction documentaire ou clarification qui ne modifie ni les données acceptées ni leur interprétation canonique.
- **Minor** : ajout compatible d’un champ optionnel ou d’une valeur explicitement extensible ; le validateur de la version antérieure doit continuer à traiter les événements existants sans réinterprétation.
- **Major** : suppression, renommage, changement de type, nouvelle sémantique, changement de canonicalisation, de hashage ou d’idempotence.

Une modification des règles d’empreinte est une modification de profil d’intégrité, même si le schéma de données n’a pas changé. Les deux versions doivent être enregistrées séparément.

### 10.2 Champs inconnus

Les champs inconnus dans le corps de base sont refusés par défaut pour la version 1, à l’exception de l’objet `extensions`, où les clés doivent être namespacées et le schéma de l’extension identifié. Cela empêche qu’un producteur ajoute un champ de sécurité que l’autre langage ignore silencieusement.

### 10.3 Migration

Les événements historiques ne sont jamais réécrits pour les faire paraître conformes à un nouveau schéma. Une migration produit une représentation dérivée et un événement de migration qui référence l’événement original, le convertisseur/version et les éventuelles pertes sémantiques. L’empreinte originale reste conservée.

## 11. Énumérations initiales

Les valeurs suivantes constituent le vocabulaire minimal proposé. Toute extension doit être versionnée.

**Statuts d’opération :** `SUCCESS`, `FAILURE`, `BLOCKED`, `REJECTED`, `TIMEOUT`, `CANCELLED`, `UNKNOWN`.

**Décisions de politique :** `ALLOW`, `BLOCK`, `REDACT`, `ESCALATE`, `NOT_APPLICABLE`.

**Observabilité :** `COMPLETE`, `PARTIAL`, `EXTERNAL`, `UNKNOWN`, `NOT_INSTRUMENTED`.

**Résultats de vérification :** `PASS`, `FAIL`, `INCONCLUSIVE`, `NOT_TESTED`.

**État de signature :** `NOT_REQUIRED`, `VERIFIED`, `INVALID`, `NOT_CHECKED`, `KEY_UNKNOWN`, `KEY_REVOKED`.

**Statut d’ingestion :** `ACCEPTED`, `DUPLICATE_SAME_CONTENT`, `REJECTED_SCHEMA`, `REJECTED_CAUSALITY`, `IDEMPOTENCY_CONFLICT`, `IDENTITY_CONFLICT`, `QUARANTINED`.

## 12. Fixtures de référence

Les fixtures doivent être conservées comme données de test synthétiques dans le rapport ou dans des artefacts de test ultérieurs autorisés. Aucune fixture ne doit contenir de secret réel, de donnée personnelle ou de log d’exécution réelle.

### 12.1 Fixture F-001 — corps minimal valide

Entrée JSON logique :

{
  "schema_id": "https://artcb.example/schemas/guardian/event/1.0.0",
  "schema_version": "1.0.0",
  "event_id": "0199a111-2222-7222-8222-222222222222",
  "event_type": "agent.input.received",
  "occurred_at": "2026-10-09T00:00:00Z",
  "producer": {
    "producer_id": "agent:fixture-a",
    "producer_instance_id": "0199a111-2222-7222-8222-333333333333",
    "component_version": "fixture-1"
  },
  "execution": {
    "run_id": "0199a111-2222-7222-8222-444444444444",
    "session_id": "0199a111-2222-7222-8222-555555555555",
    "sequence_no": 1
  },
  "causality": {
    "parent_event_ids": []
  },
  "operation": {
    "name": "receive_input",
    "status": "SUCCESS"
  },
  "inputs": [],
  "outputs": [],
  "policy": null,
  "observability": {
    "status": "COMPLETE",
    "source": "fixture",
    "limitations": []
  },
  "classification": "PUBLIC_TEST",
  "extensions": {}
}

Les UUID ci-dessus sont des valeurs synthétiques de fixture au format UUIDv7 attendu ; les implémentations de test doivent vérifier leur forme et leur version. Ils ne sont pas des identités réelles.

**Résultat attendu :** le schéma accepte le corps ; JCS produit les mêmes octets canoniques en Rust et Python ; les deux implémentations calculent exactement le même digest SHA-256 selon le profil R005. Le digest golden doit être calculé une fois par un outil de référence indépendant et figé dans les tests avant que le code applicatif soit considéré conforme. Ce rapport ne prétend pas avoir exécuté ce calcul.

### 12.2 Fixture F-002 — ordre de propriétés différent

Utiliser le même contenu logique que F-001 en permutant l’ordre des propriétés JSON et en changeant l’indentation.

**Attendu :** octets canoniques et empreinte identiques à F-001.

### 12.3 Fixture F-003 — chaîne Unicode préservée

Créer deux fixtures distinctes avec les chaînes `"é"` et `"é"`.

**Attendu :** JCS préserve les séquences Unicode validées ; ces deux chaînes ne doivent pas être fusionnées automatiquement. Si l’application veut une normalisation métier, celle-ci doit être explicite avant l’événement et versionnée.

### 12.4 Fixture F-004 — doublon idempotent

Soumettre deux fois le même corps avec le même `producer_id`, `run_id`, `idempotency_key` et `event_hash`.

**Attendu :** un seul événement durable ; la seconde soumission renvoie l’événement existant et `DUPLICATE_SAME_CONTENT`.

### 12.5 Fixture F-005 — conflit idempotent

Réutiliser la clé d’idempotence de F-004, mais changer le statut ou un champ du corps.

**Attendu :** `IDEMPOTENCY_CONFLICT`, aucun écrasement, aucune deuxième écriture sous la même clé.

### 12.6 Fixture F-006 — identifiant réutilisé avec contenu différent

Réutiliser `event_id` de F-001 avec un autre `event_hash`.

**Attendu :** `IDENTITY_CONFLICT` ; le contenu historique reste inchangé.

### 12.7 Fixture F-007 — parent absent

Déclarer un `parent_event_id` qui n’existe pas dans le ledger et qui n’est pas marqué externe.

**Attendu :** rejet ou attente de résolution selon la politique configurée ; aucune affirmation de graphe complet.

### 12.8 Fixture F-008 — cycle causal

Créer A dépendant de B et B dépendant de A.

**Attendu :** `REJECTED_CAUSALITY` avec les identifiants du cycle.

### 12.9 Fixture F-009 — propriété dupliquée

Fournir un document JSON avec deux propriétés du même nom.

**Attendu :** rejet au parsing ; aucune canonicalisation ne doit masquer l’ambiguïté.

### 12.10 Fixture F-010 — champ inconnu

Ajouter un champ inattendu au niveau racine sans l’insérer dans `extensions`.

**Attendu :** rejet par le schéma version 1.

### 12.11 Fixture F-011 — retry après panne

Simuler une panne après écriture durable mais avant l’acquittement. Répéter ensuite la requête avec la même clé d’idempotence.

**Attendu :** l’événement existant est retourné une seule fois ; aucun doublon historique n’est créé.

### 12.12 Fixture F-012 — chaîne altérée

Modifier un événement intermédiaire, sa séquence ou le digest précédent dans une copie de test isolée.

**Attendu :** échec de vérification de chaîne ou divergence de checkpoint ; le rapport doit préciser le premier élément vérifiable en conflit.

### 12.13 Fixture F-013 — donnée sensible

Inclure une valeur de test marquée secrète dans un champ interdit au ledger.

**Attendu :** blocage, redaction ou référence vers un artefact chiffré selon la politique ; la valeur sensible ne doit pas être reproduite dans le message d’erreur ou le rapport.

### 12.14 Fixture F-014 — versions inconnues

Soumettre un `schema_version` ou un `canonicalization_profile` non supporté.

**Attendu :** rejet ou quarantaine explicite ; aucun fallback silencieux vers la version courante.

## 13. Critères d’acceptation avant implémentation

Le contrat ne sera prêt pour codage que lorsque les éléments suivants auront été produits et revus :

1. Schéma JSON Schema 2020-12 exact et versionné pour le corps et l’enveloppe.
2. Implémentation de référence de canonicalisation conforme à RFC 8785.
3. Fixtures golden contenant les octets canoniques et les digests SHA-256 attendus, générés indépendamment et revérifiés.
4. Tests différentiels Rust/Python sur toutes les fixtures valides et invalides.
5. Tests de propriété sur l’ordre des clés, l’Unicode, les nombres, les champs absents/null et les tableaux ordonnés/non ordonnés.
6. Tests d’idempotence concurrents et après panne, avec preuve que l’index et l’écriture sont atomiques.
7. Tests de collision d’identifiants et de conflits de clés d’idempotence.
8. Tests de causalité : parent absent, doublons, cycle, séquence non monotone et événements externes.
9. Tests de versionnage et de compatibilité avec au moins une fixture historique par version prise en charge.
10. Revue sécurité des données sensibles, des signatures et de la gestion des clés.
11. Rapport de conformité distinguant les garanties testées des garanties seulement spécifiées.
12. Confirmation qu’aucun code applicatif n’a été modifié dans ce chantier de conception.

Aucune de ces validations ne doit être déclarée réussie avant exécution et conservation d’une preuve de test.

## 14. Plan d’exécution futur

**P0 — verrouiller le contrat :** approuver les noms des champs, la version initiale, le profil JCS, les règles d’empreinte et la portée d’idempotence.

**P1 — générer les artefacts de référence :** publier le JSON Schema versionné et les fixtures golden avec octets canoniques et digests calculés indépendamment.

**P2 — implémenter les validateurs :** un validateur Rust et un validateur Python, sans encore confondre validation de schéma et autorisation métier.

**P3 — vérifier la parité :** exécuter les mêmes fixtures dans les deux langages, comparer octets, digests, erreurs et statuts.

**P4 — vérifier le ledger :** intégrer idempotence transactionnelle, chaînage, checkpoints et reprise après panne dans un environnement de test isolé.

**P5 — audit adversarial :** muter événements, parents, séquences, clés, versions et artefacts ; vérifier que chaque garantie revendiquée échoue de manière explicite quand sa précondition est violée.

## 15. Risques et points à décider explicitement

| Risque | Conséquence | Mesure proposée |
|---|---|---|
| Implémentations JCS divergentes | Hash différents entre Rust et Python | Fixtures golden indépendantes et tests différentiels |
| UUIDv7 traité comme ordre causal | Reconstruction trompeuse | Maintenir séquences et parents explicites |
| Retry traité comme nouvel événement | Doublons de provenance | Clé d’idempotence et écriture transactionnelle |
| Clé d’idempotence réutilisée | Perte ou substitution de faits | Conflit explicite si le digest diffère |
| Schéma évoluant sans version | Interprétation historique instable | Version immuable et événement de migration |
| Parent ou événement supprimé | Graphe incomplet | Vérification des références, checkpoints indépendants et couverture |
| Signature interprétée comme autorisation | Opération non autorisée acceptée | Vérifier authenticité et politique séparément |
| Données privées dans le ledger | Fuite irréversible | Références chiffrées, classification et contrôle des champs |
| Hash considéré comme preuve de vérité | Surpromesse de sécurité | Documenter exactement ce que chaque preuve établit |

## 16. Références techniques publiques

- RFC 8785 — JSON Canonicalization Scheme (JCS) : https://www.rfc-editor.org/rfc/rfc8785.html
- RFC 9562 — Universally Unique IDentifiers, incluant UUIDv7 : https://www.rfc-editor.org/rfc/rfc9562.html
- JSON Schema Draft 2020-12 : https://json-schema.org/draft/2020-12

Ces références valident des standards de format, de sérialisation et d’identifiants ; elles ne valident pas automatiquement l’architecture ARTCB. La conformité doit être démontrée par des tests de référence.

## 17. Limites de l’audit

Ce rapport est une spécification. Aucun binaire, service, test automatisé, benchmark ou test adversarial n’a été exécuté. Aucun code applicatif n’a été modifié. Les fixtures présentées définissent les entrées et résultats attendus ; les digests golden doivent être calculés et vérifiés indépendamment avant de servir de critères de conformité.

La traçabilité ne dépasse pas les limites de l’instrumentation : une absence d’événement ne prouve pas l’absence d’action si le point de collecte est défaillant ou contourné. Une signature prouve le contrôle d’une clé dans les limites du système de signature, pas la véracité sémantique de l’événement. Une empreinte et une chaîne rendent les altérations détectables seulement si une référence de confiance ou un checkpoint indépendant permet la comparaison.

## 18. Conclusion

R005 établit la frontière de contrat entre producteurs Python, cœur de sécurité Rust, ledger, archive d’artefacts et vérificateur. La règle fondamentale est :

**même événement logique → même corps canonique → même empreinte ; même intention rejouée → une seule écriture durable ; toute différence de contenu ou de version → conflit ou migration explicite, jamais une réinterprétation silencieuse.**

L’étape suivante, R006, devrait produire le schéma JSON Schema 2020-12 complet et les fixtures golden réellement calculées, puis spécifier les erreurs de validation et les résultats attendus pour chaque cas.
