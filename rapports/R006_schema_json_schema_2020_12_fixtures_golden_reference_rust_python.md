# R006 — JSON Schema 2020-12, fixtures golden et résultats de référence Rust/Python

**Date :** 2026-10-09  
**Dépôt :** `vgactech/ARTCB-TERMINATOR`  
**Branche :** `main`  
**Dossier autorisé :** `rapports/` uniquement  
**Sources normatives :** R003, R004 et R005  
**Statut :** spécification et vecteur golden calculé ; validateurs applicatifs Rust/Python non exécutés.  
**Périmètre :** aucun code applicatif, aucune configuration et aucun fichier du dépôt `vgactech/artcb` ne sont modifiés.

## Expertises activées

- Architecture de contrats de données et JSON Schema Draft 2020-12 ;
- canonicalisation JSON JCS (RFC 8785) et interopérabilité Rust/Python ;
- cryptographie appliquée, SHA-256 et séparation de domaines ;
- tests de conformité différentielle et fixtures golden ;
- event sourcing, causalité, idempotence et ledger append-only ;
- validation adversariale et gestion des erreurs ;
- reproductibilité, forensic et preuves de test.

## 1. Résumé exécutif

R006 convertit les décisions de R005 en un contrat vérifiable avant implémentation :

1. un schéma JSON Schema 2020-12 complet pour le **corps canonique** d’un événement ;
2. des règles explicites de validation structurelle et des cas négatifs ;
3. un événement golden synthétique, sa représentation JCS exacte en UTF-8 et son empreinte SHA-256 avec séparation de domaine ;
4. des résultats attendus pour comparer les validateurs Rust et Python ;
5. un protocole de test différentiel et une matrice qui interdit de confondre résultats attendus et tests réellement exécutés.

**État des preuves :** le golden F-001 a un corps canonique de 735 octets UTF-8 et une empreinte de référence calculée. Les validateurs Rust et Python n’ont pas été exécutés dans ce chantier ; leur conformité reste donc **NOT_TESTED**, et non PASS.

## 2. Processus, problème, solution

### Processus

Le producteur construit le corps d’événement, le valide contre le schéma, le canonicalise avec JCS (RFC 8785), puis calcule :

`SHA-256(UTF8("ARTCB-GUARDIAN-EVENT-V1") || 0x00 || canonical_body_bytes)`

Rust et Python doivent recevoir les mêmes données logiques et obtenir les mêmes octets canoniques, le même digest et la même classe de résultat de validation.

### Problème

Un schéma seul ne définit pas les octets à hacher. Une sérialisation JSON ordinaire peut varier dans l’ordre des clés ou l’espacement. De plus, deux validateurs peuvent interpréter différemment les formats, les propriétés inconnues ou les contraintes temporelles si le profil n’est pas fixé.

### Solution

Le schéma ci-dessous fixe la structure ; RFC 8785 fixe la canonicalisation ; le profil de hashage fixe le domaine ; les fixtures fixent les réponses attendues. Les règles métier qui nécessitent un état du ledger — parent existant, unicité, idempotence, cycles, durabilité — restent des contrôles de protocole et ne sont pas présentées comme si JSON Schema pouvait les garantir.

## 3. Décisions normatives

- Dialecte : JSON Schema Draft 2020-12.
- Corps : `schema_version = "1.0.0"`.
- Canonicalisation : JCS selon RFC 8785, UTF-8 sans BOM.
- Hash du corps : SHA-256 sur le préfixe ASCII `ARTCB-GUARDIAN-EVENT-V1`, un octet nul, puis les octets JCS.
- Propriétés inconnues à la racine et dans les objets fermés : refusées par `additionalProperties: false`.
- Extensibilité : uniquement via `extensions`, dont les clés sont namespacées et versionnées selon une convention documentée.
- `policy` : soit `null` pour une opération non décisionnelle, soit un objet décisionnel complet.
- Les tableaux `inputs`, `outputs`, `parent_event_ids` et `observability.limitations` sont toujours présents, même vides.
- Le schéma valide la forme et les formats locaux. Il ne peut pas prouver qu’un parent existe, qu’un hash correspond à un artefact externe, qu’un événement est durable ou qu’une signature est valide.
- Les valeurs UUID des fixtures sont synthétiques. La contrainte de version UUIDv7 s’applique au format de la fixture, mais la validation de l’ordre causal ne doit jamais être déduite de l’UUID.

## 4. Schéma JSON Schema 2020-12 complet — corps canonique

Le document suivant est autonome. En production, il devra être publié comme fichier de schéma immuable dans un changement de périmètre autorisé ultérieur ; conformément à la consigne actuelle, il est livré ici dans le rapport uniquement.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://artcb.example/schemas/guardian/event/1.0.0",
  "title": "ARTCB Guardian Canonical Event Body",
  "description": "Corps immuable d'un événement Guardian. Les métadonnées d'ingestion, hash, chaîne et signature appartiennent à l'enveloppe du ledger.",
  "type": "object",
  "required": [
    "schema_id",
    "schema_version",
    "event_id",
    "event_type",
    "occurred_at",
    "producer",
    "execution",
    "causality",
    "operation",
    "inputs",
    "outputs",
    "policy",
    "observability",
    "classification",
    "extensions"
  ],
  "properties": {
    "schema_id": {
      "type": "string",
      "format": "uri",
      "const": "https://artcb.example/schemas/guardian/event/1.0.0"
    },
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "event_id": {
      "$ref": "#/$defs/uuid7"
    },
    "event_type": {
      "type": "string",
      "minLength": 3,
      "maxLength": 128,
      "pattern": "^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$"
    },
    "occurred_at": {
      "type": "string",
      "format": "date-time",
      "pattern": "Z$"
    },
    "producer": {
      "$ref": "#/$defs/producer"
    },
    "execution": {
      "$ref": "#/$defs/execution"
    },
    "causality": {
      "$ref": "#/$defs/causality"
    },
    "operation": {
      "$ref": "#/$defs/operation"
    },
    "inputs": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/artifact_ref"
      }
    },
    "outputs": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/artifact_ref"
      }
    },
    "policy": {
      "oneOf": [
        { "type": "null" },
        { "$ref": "#/$defs/policy_decision" }
      ]
    },
    "observability": {
      "$ref": "#/$defs/observability"
    },
    "classification": {
      "type": "string",
      "enum": [
        "PUBLIC_TEST",
        "PUBLIC",
        "INTERNAL",
        "CONFIDENTIAL",
        "RESTRICTED",
        "SECRET",
        "unknown"
      ]
    },
    "extensions": {
      "type": "object",
      "description": "Extensions explicitement namespacées. Chaque extension doit documenter son schéma et sa version dans sa propre valeur.",
      "propertyNames": {
        "pattern": "^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$"
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false,
  "$defs": {
    "uuid7": {
      "type": "string",
      "format": "uuid",
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    },
    "producer": {
      "type": "object",
      "required": [
        "producer_id",
        "producer_instance_id",
        "component_version"
      ],
      "properties": {
        "producer_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256,
          "pattern": "^[A-Za-z0-9][A-Za-z0-9:._/-]*$"
        },
        "producer_instance_id": {
          "$ref": "#/$defs/uuid7"
        },
        "component_version": {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        }
      },
      "additionalProperties": false
    },
    "execution": {
      "type": "object",
      "required": [
        "run_id",
        "session_id",
        "sequence_no"
      ],
      "properties": {
        "run_id": {
          "$ref": "#/$defs/uuid7"
        },
        "session_id": {
          "$ref": "#/$defs/uuid7"
        },
        "sequence_no": {
          "type": "integer",
          "minimum": 1,
          "maximum": 9007199254740991
        }
      },
      "additionalProperties": false
    },
    "causality": {
      "type": "object",
      "required": [
        "parent_event_ids"
      ],
      "properties": {
        "parent_event_ids": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "$ref": "#/$defs/uuid7"
          }
        }
      },
      "additionalProperties": false
    },
    "operation": {
      "type": "object",
      "required": [
        "name",
        "status"
      ],
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256,
          "pattern": "^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
        },
        "status": {
          "type": "string",
          "enum": [
            "SUCCESS",
            "FAILURE",
            "BLOCKED",
            "REJECTED",
            "TIMEOUT",
            "CANCELLED",
            "UNKNOWN"
          ]
        }
      },
      "additionalProperties": false
    },
    "artifact_ref": {
      "type": "object",
      "required": [
        "artifact_id",
        "digest_algorithm",
        "digest",
        "byte_length",
        "media_type",
        "classification",
        "storage_ref",
        "created_by_event_id",
        "retention_policy_id",
        "availability_status",
        "verification_status"
      ],
      "properties": {
        "artifact_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256,
          "pattern": "^[A-Za-z0-9][A-Za-z0-9:._/-]*$"
        },
        "digest_algorithm": {
          "type": "string",
          "enum": ["SHA-256"]
        },
        "digest": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "byte_length": {
          "type": "integer",
          "minimum": 0,
          "maximum": 9007199254740991
        },
        "media_type": {
          "type": "string",
          "pattern": "^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+$"
        },
        "classification": {
          "type": "string",
          "enum": [
            "PUBLIC_TEST",
            "PUBLIC",
            "INTERNAL",
            "CONFIDENTIAL",
            "RESTRICTED",
            "SECRET",
            "unknown"
          ]
        },
        "storage_ref": {
          "type": "string",
          "minLength": 1,
          "maxLength": 2048
        },
        "encryption_profile": {
          "type": ["string", "null"],
          "maxLength": 128
        },
        "key_ref": {
          "type": ["string", "null"],
          "maxLength": 256
        },
        "created_by_event_id": {
          "$ref": "#/$defs/uuid7"
        },
        "retention_policy_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256
        },
        "availability_status": {
          "type": "string",
          "enum": ["AVAILABLE", "MISSING", "QUARANTINED", "UNKNOWN"]
        },
        "verification_status": {
          "type": "string",
          "enum": ["PASS", "FAIL", "INCONCLUSIVE", "NOT_TESTED"]
        }
      },
      "additionalProperties": false
    },
    "policy_decision": {
      "type": "object",
      "required": [
        "policy_id",
        "policy_version",
        "decision"
      ],
      "properties": {
        "policy_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256
        },
        "policy_version": {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        "decision": {
          "type": "string",
          "enum": [
            "ALLOW",
            "BLOCK",
            "REDACT",
            "ESCALATE",
            "NOT_APPLICABLE"
          ]
        }
      },
      "additionalProperties": false
    },
    "observability": {
      "type": "object",
      "required": [
        "status",
        "source",
        "limitations"
      ],
      "properties": {
        "status": {
          "type": "string",
          "enum": [
            "COMPLETE",
            "PARTIAL",
            "EXTERNAL",
            "UNKNOWN",
            "NOT_INSTRUMENTED"
          ]
        },
        "source": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256
        },
        "limitations": {
          "type": "array",
          "items": {
            "type": "string",
            "maxLength": 2048
          }
        }
      },
      "additionalProperties": false
    }
  }
}
```

### 4.1 Points de vigilance du schéma

- Le `format: date-time` doit être vérifié en mode assertion par les deux validateurs. Certaines bibliothèques traitent les formats comme annotations si l’option correspondante n’est pas activée.
- La contrainte `pattern: "Z$"` impose UTC pour cette version du contrat. Si les offsets explicites autres que UTC deviennent nécessaires, il faudra une évolution documentée du profil.
- `additionalProperties: false` empêche qu’un champ de sécurité ajouté par un producteur soit ignoré silencieusement.
- `extensions` est la seule porte d’extension. Chaque extension acceptée doit avoir son propre contrat ; la permissivité structurelle de cette propriété ne constitue pas une autorisation métier.
- La contrainte UUIDv7 vérifie le format/version déclaré. Elle ne vérifie ni l’unicité globale, ni la qualité de l’aléa, ni l’ordre causal.
- Le schéma est celui du **corps canonique**, pas celui de l’enveloppe de stockage. L’enveloppe doit être spécifiée séparément avant implémentation du ledger.

## 5. Fixture golden F-001

### 5.1 Objet JSON logique

```json
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
```

### 5.2 Octets canoniques attendus

La représentation suivante est une ligne JSON sans espaces superflus, UTF-8, sans BOM et sans saut de ligne final. Les guillemets visibles sont des octets ASCII ; les caractères de cette fixture sont tous ASCII. La longueur exacte attendue est **735 octets**.

```text
{"causality":{"parent_event_ids":[]},"classification":"PUBLIC_TEST","event_id":"0199a111-2222-7222-8222-222222222222","event_type":"agent.input.received","execution":{"run_id":"0199a111-2222-7222-8222-444444444444","sequence_no":1,"session_id":"0199a111-2222-7222-8222-555555555555"},"extensions":{},"inputs":[],"observability":{"limitations":[],"source":"fixture","status":"COMPLETE"},"occurred_at":"2026-10-09T00:00:00Z","operation":{"name":"receive_input","status":"SUCCESS"},"outputs":[],"policy":null,"producer":{"component_version":"fixture-1","producer_id":"agent:fixture-a","producer_instance_id":"0199a111-2222-7222-8222-333333333333"},"schema_id":"https://artcb.example/schemas/guardian/event/1.0.0","schema_version":"1.0.0"}
```

### 5.3 Empreinte golden

Le profil de hashage est :

`SHA-256(ASCII("ARTCB-GUARDIAN-EVENT-V1") || 0x00 || canonical_body_bytes)`

- Algorithme : SHA-256.
- Préfixe de domaine : `ARTCB-GUARDIAN-EVENT-V1`.
- Séparateur : un octet `00`.
- Longueur du corps canonique : 735 octets.
- Digest hexadécimal attendu : **`c067e20378788d5d32e25c489064efd624224596c1987b5315f8dde296892f11`**.

Cette valeur a été calculée à partir de l’objet ci-dessus, avec tri récursif des clés et encodage compact UTF-8. Comme la fixture n’utilise ni flottants, ni caractères non ASCII, ni clés ambiguës, cette représentation doit correspondre à JCS. Elle doit néanmoins être revérifiée par au moins une implémentation JCS conforme à RFC 8785 et par les tests différentiels avant d’être déclarée validée par le projet.

### 5.4 Fixture F-002 — ordre des propriétés différent

Entrée : le même objet logique que F-001, mais avec l’ordre des propriétés source permuté et une indentation différente.

Résultat attendu :
- validation : PASS ;
- octets JCS : identiques à F-001, byte-for-byte ;
- longueur : 735 octets ;
- digest : identique à F-001.

### 5.5 Fixture F-003 — Unicode non normalisé implicitement

Deux objets dérivés de F-001, avec une extension namespacée contenant respectivement la valeur précomposée `é` (U+00E9) et la séquence `e` + accent combinant (U+0065 U+0301).

Résultat attendu :
- les deux chaînes restent distinctes, car JCS ne réalise pas de normalisation Unicode ;
- chaque objet possède ses propres octets canoniques et son propre digest ;
- aucune implémentation ne doit fusionner ces valeurs silencieusement.

Pour les tests, la clé d’extension utilisée doit être namespacée, par exemple `fixture.unicode`, et sa structure doit être figée dans la fixture.

## 6. Matrice des fixtures et résultats de référence

Les statuts ci-dessous sont des **résultats attendus**, pas des résultats d’exécution des validateurs.

| ID | Scénario | Schéma attendu | Contrôle protocolaire attendu | Résultat global attendu |
|---|---|---|---|---|
| F-001 | Corps minimal valide | PASS | Hash égal au golden | PASS |
| F-002 | Propriétés source réordonnées | PASS | Octets et hash identiques à F-001 | PASS |
| F-003 | Unicode précomposé vs combiné | PASS | Octets/digests distincts | PASS |
| F-004 | Même clé d’idempotence, même contenu | PASS | Une écriture, retour de l’événement existant | DUPLICATE_SAME_CONTENT |
| F-005 | Même clé d’idempotence, contenu différent | PASS structurel | Aucun écrasement ; conflit d’idempotence | IDEMPOTENCY_CONFLICT |
| F-006 | Même event_id, hash différent | PASS structurel | Rejeter le conflit d’identité | IDENTITY_CONFLICT |
| F-007 | Parent absent du ledger | PASS structurel | Rejeter ou mettre en attente, selon profil | REJECTED_CAUSALITY ou INCONCLUSIVE |
| F-008 | Cycle causal | PASS structurel | Détecter le cycle dans le graphe | REJECTED_CAUSALITY |
| F-009 | Nom de propriété dupliqué dans le JSON source | Parse FAIL | Ne pas canonicaliser un document ambigu | FAIL |
| F-010 | Propriété racine inconnue | FAIL | Aucun fallback silencieux | REJECTED_SCHEMA |
| F-011 | Retry après écriture durable mais avant ACK | PASS structurel | Une seule écriture durable | DUPLICATE_SAME_CONTENT |
| F-012 | Corps/chaîne modifié après engagement | PASS structurel possible | Hash ou chaîne/checkpoint diverge | FAIL |
| F-013 | Donnée sensible dans une zone interdite | Dépend du profil de classification | Bloquer/redacter/référencer chiffré sans divulgation | BLOCK ou REDACT |
| F-014 | schema_version inconnue | FAIL | Rejet/quarantaine explicite | REJECTED_SCHEMA |
| F-015 | event_id non UUIDv7 ou mal formé | FAIL | Aucun hash accepté comme événement conforme | REJECTED_SCHEMA |
| F-016 | sequence_no = 0 ou négatif | FAIL | Refus structurel | REJECTED_SCHEMA |
| F-017 | occurred_at sans suffixe UTC Z | FAIL dans le profil 1.0.0 | Pas de conversion silencieuse | REJECTED_SCHEMA |
| F-018 | status d’opération inconnu | FAIL | Refus de valeur non versionnée | REJECTED_SCHEMA |
| F-019 | parent_event_ids en double | FAIL | Refus de doublons | REJECTED_SCHEMA |
| F-020 | digest d’artefact de longueur incorrecte | FAIL | Refus de référence mal formée | REJECTED_SCHEMA |

### Limite importante sur les résultats

JSON Schema peut classer F-001 à F-003 et les erreurs purement structurelles. Il ne peut pas conclure seul F-004 à F-008 ou F-011 à F-013, qui nécessitent un ledger, un graphe causal, un état de stockage ou un moteur de politique. Les validateurs Rust/Python doivent exposer des résultats séparés : `schema_result`, `canonicalization_result`, `hash_result` et, lorsque le composant existe, `protocol_result`.

## 7. Contrat de sortie des validateurs

Chaque implémentation doit produire une sortie structurée équivalente contenant au minimum :

- `fixture_id` ;
- `schema_version` ;
- `schema_result` : `PASS`, `FAIL`, `INCONCLUSIVE` ou `NOT_TESTED` ;
- `canonicalization_profile` ;
- `canonical_bytes_length` ;
- `canonical_bytes_sha256` (SHA-256 simple des octets JCS, uniquement pour comparer la représentation, distinct du digest avec domaine) ;
- `event_hash` (digest SHA-256 avec séparation de domaine) ;
- `protocol_result` : valeur versionnée ou `NOT_TESTED` ;
- `errors` : codes stables, chemin JSON et message non sensible ;
- `implementation_name` et `implementation_version`.

Les messages d’erreur humains peuvent varier ; les codes, les chemins JSON et les statuts doivent être stables. Aucun validateur ne doit copier une valeur classée secrète dans le message d’erreur.

## 8. Protocole de comparaison Rust/Python

Pour chaque fixture, exécuter les étapes suivantes dans les deux langages :

1. Lire les octets source sans transformation implicite.
2. Refuser les noms de propriétés JSON dupliqués au parseur, avant de construire un objet ordinaire.
3. Valider avec JSON Schema Draft 2020-12 et activer explicitement l’assertion des formats.
4. Canonicaliser avec une bibliothèque JCS conforme à RFC 8785 ; ne pas utiliser uniquement `sort_keys` comme preuve générale de conformité.
5. Comparer les octets canoniques aux octets golden lorsqu’ils sont disponibles.
6. Calculer SHA-256 simple des octets canoniques pour le diagnostic.
7. Calculer le digest du corps avec le préfixe de domaine R005.
8. Comparer les résultats Rust et Python : statut, longueur, octets, digest et code d’erreur.
9. Exécuter séparément les tests d’état du ledger : idempotence, causalité, écriture transactionnelle, crash/reprise et chaîne.
10. Enregistrer un rapport synthétique de test, sans secrets, données personnelles ni logs bruts.

### Règle de décision

- `PASS` : tous les contrôles applicables ont été exécutés et correspondent à la référence.
- `FAIL` : au moins un résultat diverge ou une contrainte obligatoire est violée.
- `INCONCLUSIVE` : le test a été exécuté, mais les preuves sont insuffisantes pour conclure.
- `NOT_TESTED` : le test n’a pas été exécuté.

Un test non exécuté ne peut jamais être compté comme PASS.

## 9. Bibliothèques à évaluer — sans intégration à ce stade

Les bibliothèques suivantes sont des candidates à évaluer dans une phase d’implémentation autorisée, et non des dépendances déjà installées ou validées :

- Rust : validateur JSON Schema compatible Draft 2020-12, plus bibliothèque JCS conforme à RFC 8785 ; vérifier explicitement la prise en charge de `format` et le rejet des clés dupliquées.
- Python : `jsonschema` avec le validateur Draft 2020-12 et vérification des formats activée ; une bibliothèque JCS dédiée pour la canonicalisation.
- Les deux : SHA-256 de la bibliothèque standard, avec vecteurs de test connus.
- Pour la comparaison : fixtures statiques partagées, sorties JSON structurées et un comparateur qui ignore uniquement les messages humains non normatifs.

Le choix final des bibliothèques devra être fondé sur des tests de conformité, la maintenance active, la licence, la sécurité des dépendances et les différences de sémantique observées. R006 ne prétend pas qu’une bibliothèque a été installée, exécutée ou auditée.

## 10. Risques et contrôles

| Risque | Processus / problème | Contrôle requis |
|---|---|---|
| Canonicalisation différente | Les mêmes données peuvent produire des octets différents | Golden JCS et tests de conformité RFC 8785 |
| Clés JSON dupliquées | Un parseur peut masquer une ambiguïté | Détection au parsing avant validation |
| Format date-time traité comme annotation | Une date invalide peut passer | Activer l’assertion des formats et tester les deux langages |
| Champ inconnu ignoré | Les versions peuvent interpréter le même événement différemment | `additionalProperties: false` et versionnage |
| Hash pris pour preuve de vérité | L’intégrité est confondue avec l’authenticité | Documenter les limites ; signature et confiance séparées |
| Test attendu présenté comme exécuté | Fausse assurance de conformité | Statuts PASS/FAIL/INCONCLUSIVE/NOT_TESTED distincts |
| Parent absent ou cycle | Un objet valide isolément peut être causalement invalide | Validateur de graphe distinct du schéma |
| Conflit idempotent | Une tentative peut masquer un événement différent | Transaction, clé stable, comparaison du hash et refus du conflit |
| Donnée sensible dans une fixture ou un rapport | Fuite persistante dans Git | Données synthétiques et contrôle de classification avant publication |

## 11. Critères de sortie R006

R006 est **documentairement produit** avec le schéma et les références golden inscrits dans ce rapport. La conformité du système ne sera pas déclarée tant que les conditions suivantes ne seront pas satisfaites :

- [ ] Schéma parsé par deux implémentations Draft 2020-12 indépendantes.
- [ ] F-001 accepté par les deux validateurs.
- [ ] F-010 et F-014 à F-020 rejetés avec codes et chemins cohérents.
- [ ] F-002 produit exactement les mêmes octets et digest que F-001.
- [ ] F-001 recalculé par une implémentation JCS conforme et digest égal au golden publié.
- [ ] Les vecteurs de canonicalisation RFC 8785 pertinents passent.
- [ ] Les tests de propriétés et d’Unicode passent.
- [ ] Les tests de protocole F-004 à F-008 et F-011 à F-013 sont exécutés dans un environnement isolé.
- [ ] Les sorties Rust et Python sont comparées automatiquement.
- [ ] Les résultats bruts restent hors du dépôt ; seul un rapport synthétique expurgé peut être publié dans `rapports/`.
- [ ] Aucun code applicatif ou configuration n’a été modifié.

## 12. Références publiques

- RFC 8785 — JSON Canonicalization Scheme : https://www.rfc-editor.org/rfc/rfc8785.html
- RFC 9562 — UUIDs, incluant UUIDv7 : https://www.rfc-editor.org/rfc/rfc9562.html
- JSON Schema Draft 2020-12 : https://json-schema.org/draft/2020-12

Ces standards définissent des formats et des règles. La conformité du projet reste une propriété à démontrer par des tests exécutés et archivés.

## 13. Limites et conclusion

R006 livre un schéma de corps canonique, une fixture synthétique, des octets JCS et un digest golden de référence. Le digest doit encore être confirmé par une implémentation JCS conforme ; la représentation donnée est simple et entièrement ASCII, mais cela ne remplace pas un test normatif. Les résultats Rust/Python restent `NOT_TESTED`, car aucun validateur applicatif n’a été exécuté et le présent travail n’autorise pas à commencer la modification du code.

**Principe final :** un même corps logique doit produire les mêmes octets JCS et le même hash dans Rust et Python ; un écart doit être signalé comme échec, jamais masqué par une conversion implicite. La validation du schéma, l’intégrité cryptographique, la causalité, l’idempotence et la durabilité sont des garanties distinctes qui doivent rester distinctement testées.
