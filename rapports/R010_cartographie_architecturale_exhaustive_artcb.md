# R010 — Cartographie architecturale exhaustive ARTCB et protocole d’audit des couches

**Date :** 2026-10-09  
**Dépôt cible :** vgactech/ARTCB-TERMINATOR  
**Emplacement autorisé :** rapports/ uniquement  
**Référence de travail historique :** vgactech/artcb, à resynchroniser et figer par SHA avant l’audit effectif  
**Dernière référence numérotée observée avant ce rapport :** R009  
**Statut :** spécification de cartographie et plan d’audit ; ne constitue pas une preuve que tous les composants ci-dessous existent déjà  
**Décision d’architecture antérieure :** Track 2 — Defenders Augmented  
**Langages cibles retenus dans le cadrage récent :** Rust pour le backend ; Python uniquement pour les fonctions LLM dont la dépendance à Python est justifiée  
**Autorisation de coder :** non accordée par ce rapport

## Expertises activées

- Audit de dépôts Git et traçabilité des révisions ;
- architecture logicielle multicouche et cartographie des dépendances ;
- architecture Rust/Python et contrats inter-langages ;
- sécurité des agents IA et des outils ;
- threat modeling et analyse adversariale ;
- identité, authentification, autorisation et anti-Sybil ;
- cryptographie appliquée, signatures, engagements et gestion des clés ;
- blockchain, consensus, nœuds et protocoles P2P ;
- mémoire artificielle persistante et graphes de provenance ;
- FHE, MPC, preuves à divulgation nulle de connaissance et calcul vérifiable ;
- TPM 2.0, Secure Element, attestation matérielle et démarrage mesuré ;
- stockage, bases de données, event sourcing et reprise après incident ;
- observabilité, forensic, replay et intégrité des preuves ;
- tests de caractérisation, compatibilité et validation indépendante ;
- confidentialité, minimisation des données exposées et hygiène des journaux ;
- gouvernance GitHub, gestion de portée et prévention des modifications non autorisées.

## 1. Objet, portée et limites

Ce rapport définit une méthode pour produire une cartographie de l’architecture ARTCB aussi complète que les preuves disponibles le permettent. La cartographie doit couvrir toutes les couches et sous-couches observables, les composants, modules, fonctions critiques, contrats, flux, dépendances, états, événements, données persistées, contrôles de sécurité, modes de panne, tests et lacunes.

Le mot « exhaustif » décrit ici l’obligation de recherche et de traçabilité : chaque zone du dépôt doit être examinée, classée et déclarée couverte, non pertinente, inaccessible ou non vérifiée. Il ne permet pas d’affirmer qu’un logiciel complexe est absolument dépourvu de composants oubliés sans preuve reproductible.

### 1.1 Sources à distinguer

1. **Source primaire :** révision distante de vgactech/artcb, lue uniquement, avec SHA de commit enregistré avant analyse.
2. **Source cible :** révision distante de vgactech/ARTCB-TERMINATOR, utilisée pour connaître les rapports existants et l’ordre de numérotation.
3. **Documents de conception :** rapports et spécifications historiques, traités comme des affirmations à vérifier et non comme une preuve automatique d’implémentation.
4. **Documentation externe :** standards, manuels et documentation des bibliothèques, consultés seulement lorsqu’ils aident à vérifier une technologie ou un contrat.
5. **Inférences de l’auditeur :** propositions et hypothèses explicitement étiquetées comme telles.

Chaque affirmation importante doit être liée à une preuve : chemin de fichier, symbole, ligne ou plage de lignes, commit, test exécuté ou référence documentaire. Si la preuve n’est pas disponible, écrire « non vérifié », « introuvable dans le périmètre inspecté » ou « à confirmer ».

### 1.2 Frontières impératives

- Ne jamais modifier le dépôt historique vgactech/artcb.
- Dans vgactech/ARTCB-TERMINATOR, ne créer ou modifier que des fichiers dans rapports/.
- Ne jamais pousser de logs bruts, dumps, traces privées, captures, données utilisateur, secrets ou artefacts de test.
- Ne jamais formater un périphérique, modifier une configuration de production, déployer un service ou lancer une action destructive dans le cadre d’une simple cartographie.
- Ne jamais confondre une capacité envisagée, un prototype, un test simulé, un test matériel et une fonction validée en production.
- Ne pas coder de fonctionnalité applicative. Toute implémentation ultérieure exige une autorisation explicite distincte de l’utilisateur.
- Ne pas élargir le périmètre fonctionnel de migration par défaut : inventorier les capacités existantes avant de proposer leur sélection.

## 2. Méthode d’inventaire sans angle mort

### 2.1 Figer l’état étudié

Avant l’analyse, relever :
- dépôt, branche, URL canonique et SHA exact du commit ;
- date et heure de consultation ;
- état de la branche et commits récents ;
- éventuels sous-modules, dépendances externes ou sous-arbres ;
- fichiers ignorés, fichiers générés et éléments absents de l’index ;
- fichiers de configuration et manifestes de dépendances ;
- rapports précédents et travaux explicitement laissés incomplets.

Ne pas utiliser « la dernière version » sans SHA. Les références peuvent changer pendant l’audit ; la cartographie doit toujours indiquer la révision qu’elle décrit.

### 2.2 Inventaire de fichiers

Parcourir l’arbre complet, y compris les répertoires cachés et les fichiers de configuration, sous réserve des limites d’accès. Classer au minimum :
- code source ;
- tests unitaires, d’intégration, système, sécurité et performance ;
- fichiers de configuration ;
- manifestes et fichiers de verrouillage des dépendances ;
- scripts de build, d’installation et de lancement ;
- workflows CI/CD ;
- conteneurs et fichiers de déploiement ;
- migrations de bases de données ;
- schémas de données et protocoles ;
- documentation, ADR et rapports ;
- exemples, fixtures et données de test ;
- code généré ;
- outils de développement ;
- licences et avis de dépendances ;
- fichiers ignorés ou exclus de la distribution.

Pour chaque répertoire, produire un statut explicite : inspecté, partiellement inspecté, inaccessible, vide, généré ou hors périmètre avec justification. Un répertoire non inspecté n’est jamais réputé vide.

### 2.3 Inventaire des symboles et dépendances

L’analyse doit aller au-delà des noms de dossiers. Identifier, dans la mesure permise par les langages et outils disponibles :
- modules, paquets, bibliothèques et exécutables ;
- classes, structures, enums, traits, interfaces et types ;
- fonctions, méthodes, handlers et points d’entrée ;
- tâches asynchrones, workers, files, timers et callbacks ;
- API publiques, routes, endpoints, commandes CLI et événements ;
- accès disque, base de données, réseau, matériel, système et processus ;
- appels externes, appels inter-agents et appels d’outils ;
- dépendances directes et transitives ;
- zones de privilèges, frontières de confiance et chemins d’erreur.

Construire un graphe dirigé où chaque arête est typée : appelle, importe, lit, écrit, authentifie, autorise, signe, chiffre, transmet, transforme, dépend de, déclenche, vérifie, restaure ou invalide.

### 2.4 Contrôle de couverture

La cartographie finale doit contenir une matrice de couverture indiquant pour chaque zone :
- nombre de fichiers recensés ;
- nombre de fichiers inspectés ;
- nombre de symboles repérés si mesurable ;
- tests associés ;
- composants dont la responsabilité est comprise ;
- zones restant à examiner ;
- preuves et limites.

Les nombres doivent être issus de commandes ou d’outils réellement exécutés, jamais estimés. Si le système ne permet pas de compter, indiquer « non mesuré ».

## 3. Cartographie des couches et sous-couches à examiner

Les couches suivantes sont un **plan de recherche exhaustif**, pas une affirmation que tous ces mécanismes sont déjà implémentés. Pour chaque couche, le rapport d’audit doit établir : rôle, processus, composants réels, interfaces, données, dépendances, menaces, contrôles, tests, preuves, lacunes et recommandations.

### Couche 0 — Matériel, hôte et racine de confiance

Sous-couches à rechercher :
- CPU, architecture, extensions matérielles et environnement d’exécution ;
- mémoire vive, stockage local, disques amovibles et périphériques ;
- système d’exploitation, noyau, comptes et privilèges ;
- TPM 2.0, PCR, quotes et attestation ;
- Secure Element, HSM, authentificateur FIDO2 ou clé cryptographique USB ;
- Secure Boot et measured boot ;
- TEE, enclaves et confidential computing, si présents ;
- générateur d’aléa et sources d’entropie ;
- horloge, synchronisation temporelle et source de temps ;
- inventaire matériel, identifiants et cycle de vie ;
- mises à jour de firmware, révocation et récupération.

Questions d’audit :
- Quel matériel est effectivement détecté, et par quelle API ?
- Un support USB est-il simplement du stockage ou un authentificateur cryptographique ?
- La preuve d’attestation est-elle locale ou distante ?
- Un nonce frais empêche-t-il le rejeu ?
- Quels PCR sont mesurés et selon quelle politique ?
- Quels états sont simulés et lesquels ont été testés sur matériel réel ?
- La perte ou le remplacement du matériel entraîne-t-il un verrouillage récupérable ?

Ne jamais déclarer qu’une clé USB classique fournit les garanties d’un TPM ou d’un Secure Element.

### Couche 1 — Boot, installation, build et chaîne d’approvisionnement logicielle

Sous-couches :
- installation et désinstallation ;
- compilation native et cross-compilation ;
- dépendances et fichiers de verrouillage ;
- reproductibilité des builds ;
- provenance des artefacts ;
- signature des binaires et packages ;
- SBOM et licences ;
- gestion des secrets de build ;
- mises à jour, rollback et migrations ;
- CI, tests, publication et artefacts de release ;
- configuration de production et de développement ;
- isolation des environnements de test.

Vérifier que le build et les scripts n’exécutent pas d’action inattendue, ne publient pas de données sensibles et n’écrivent pas en dehors du périmètre autorisé.

### Couche 2 — Système d’exploitation et isolation d’exécution

Sous-couches :
- processus et services ;
- utilisateurs, groupes et permissions ;
- isolation de processus, sandbox et conteneurs ;
- accès fichiers, sockets et périphériques ;
- IPC et RPC locaux ;
- limites de ressources ;
- signaux, arrêt et redémarrage ;
- gestion des crashs et des dumps ;
- stockage de secrets dans l’environnement ;
- politique réseau et filtrage sortant ;
- séparation test, staging et production.

Pour chaque processus, identifier ses privilèges réels, ses ressources accessibles, ses données d’entrée, ses effets de bord et ses voies de sortie.

### Couche 3 — Transport, réseau et communications distribuées

Sous-couches :
- sockets, HTTP(S), WebSocket, gRPC ou autres transports réellement présents ;
- TLS, certificats, pinning éventuel et renouvellement ;
- protocole P2P et découverte de pairs ;
- identité des pairs ;
- authentification mutuelle ;
- format et version des messages ;
- sérialisation, canonicalisation et limites de taille ;
- timeouts, retry, backoff et idempotence ;
- files de messages et ordre des événements ;
- protection contre rejeu, usurpation et flooding ;
- segmentation réseau et règles d’accès ;
- gestion de déconnexion et reprise.

Ne pas attribuer un protocole au projet sans trouver le code, la configuration ou la documentation qui le confirme.

### Couche 4 — Identité, authentification, autorisation et gouvernance

Sous-couches :
- identité humaine ;
- compte utilisateur ;
- wallet et adresse ;
- identité du nœud ;
- identité de l’appareil ;
- Node Key ou authentificateur matériel ;
- identité d’agent et d’agent enfant ;
- identité de service et de pair réseau ;
- association entre identités, sans les fusionner ;
- preuve de possession de clé ;
- authentification locale et distante ;
- autorisation par rôle, capacité, politique ou attribut ;
- permissions par outil et par ressource ;
- délégation, expiration et révocation ;
- récupération et rotation ;
- limites anti-Sybil et réputation ;
- gouvernance, organisations et administrateurs ;
- séparation des rôles et audit des décisions.

Vérifier notamment que l’identité matérielle ne prouve pas à elle seule une identité humaine, qu’une adresse de wallet n’est pas confondue avec un NodeID et qu’une signature valide n’implique pas automatiquement l’autorisation d’effectuer une action.

### Couche 5 — Gestion cryptographique

Sous-couches :
- primitives et bibliothèques cryptographiques ;
- génération et stockage des clés ;
- signatures et vérification ;
- hachage et canonicalisation ;
- MAC et authentification des messages ;
- chiffrement symétrique et asymétrique ;
- KDF, sel et dérivation de clés ;
- enveloppement et rotation de clés ;
- certificats et chaînes de confiance ;
- nonce, compteurs et anti-rejeu ;
- révocation, expiration et récupération ;
- RNG et validation de l’entropie ;
- séparation des clés par usage ;
- algorithmes, paramètres et versions ;
- cryptographie post-quantique, si présente ou explicitement planifiée ;
- vecteurs de test et compatibilité inter-implémentations.

La présence d’une bibliothèque cryptographique ne prouve pas que le protocole l’utilise correctement. Vérifier les paramètres, les frontières d’usage, la gestion des erreurs et les tests négatifs.

### Couche 6 — Données, stockage et persistance

Sous-couches :
- bases relationnelles, clés-valeurs, documents ou fichiers ;
- schémas et migrations ;
- caches, index et vues dérivées ;
- données temporaires et données persistantes ;
- chiffrement au repos ;
- sauvegardes et restauration ;
- cohérence, transactions et concurrence ;
- verrouillage, corruption et réparation ;
- versionnage et rétention ;
- suppression logique et destruction de clés ;
- séparation des données publiques, privées et sensibles ;
- contrôle d’accès au stockage ;
- import/export et portabilité ;
- réplication et synchronisation ;
- intégrité des fichiers et détection de modification.

Pour chaque donnée importante, suivre sa création, sa lecture, sa transformation, sa transmission, son stockage, sa sauvegarde, sa suppression et sa restauration.

### Couche 7 — Modèle de données et contrats de compatibilité

Sous-couches :
- types et identifiants ;
- schémas JSON, Protobuf, CBOR ou formats réellement présents ;
- valeurs obligatoires, optionnelles et par défaut ;
- encodages, dates, fuseaux et nombres ;
- erreurs et codes de retour ;
- version de protocole ;
- compatibilité ascendante et descendante ;
- migrations de données ;
- canonicalisation cryptographique ;
- identifiants d’événements et de corrélation ;
- enveloppes de messages ;
- validation des entrées ;
- règles d’extension et champs inconnus.

Les contrats doivent avoir des exemples de référence assainis, des tests de sérialisation/désérialisation et des tests différentiels lorsque plusieurs langages les implémentent.

### Couche 8 — Cœur métier et services backend Rust

Sous-couches :
- points d’entrée ;
- validation des entrées ;
- logique métier ;
- gestion des états ;
- règles d’autorisation ;
- orchestration des services ;
- accès au stockage ;
- transactions ;
- gestion des erreurs ;
- concurrence et tâches asynchrones ;
- limites de ressources ;
- API internes et externes ;
- modules de sécurité ;
- instrumentation et événements ;
- arrêt gracieux et reprise.

Pour chaque module, justifier la responsabilité Rust et identifier les dépendances qui le relient aux composants Python, à la base de données, au réseau et aux mécanismes cryptographiques.

### Couche 9 — Frontière Rust/Python et services LLM

Sous-couches :
- processus Python et dépendances ;
- frameworks LLM réellement utilisés ;
- appels de modèles locaux ou distants ;
- wrappers, adaptateurs et clients ;
- contrats d’entrée et de sortie ;
- schémas versionnés ;
- sérialisation ;
- timeouts, retries et annulation ;
- erreurs et indisponibilité ;
- gestion de secrets ;
- confidentialité des prompts ;
- validation des réponses ;
- isolation et privilèges du service ;
- observabilité sans fuite de données ;
- compatibilité des versions ;
- tests de contrat et de non-régression.

Chaque composant conservé en Python doit être justifié par une dépendance LLM ou une capacité de l’écosystème Python clairement identifiée. Ne pas déplacer arbitrairement du code vers Rust ou Python sans analyser son contrat et ses effets de bord.

### Couche 10 — Architecture des agents IA

Sous-couches :
- agent racine ;
- planner, researcher, executor, critic ou autres rôles effectivement trouvés ;
- agents spécialisés ;
- sous-agents et délégation ;
- cycle de vie d’un agent ;
- état et contexte de travail ;
- objectifs, contraintes et budgets ;
- mémoire de session ;
- appels d’outils ;
- communication agent-agent ;
- sélection et routage de modèles ;
- validation des résultats ;
- arrêt, annulation et reprise ;
- limites de profondeur et de fan-out ;
- identité et permissions de chaque agent ;
- traces de causalité entre agents.

Pour chaque agent, cartographier les entrées, sorties, outils, privilèges, mémoire accessible, modèles, dépendances, événements et risques.

### Couche 11 — Orchestration, planification et exécution des tâches

Sous-couches :
- graphe de tâches ;
- dépendances et prérequis ;
- planification ;
- exécution parallèle et séquentielle ;
- files et workers ;
- reprise après panne ;
- idempotence ;
- déduplication ;
- annulation ;
- limites de temps et de ressources ;
- priorités et quotas ;
- état de tâche ;
- compensation et rollback ;
- ordonnancement des événements ;
- contrôle des effets de bord.

Vérifier qu’une tâche n’est pas déclarée terminée avant que ses effets et preuves requis soient persistés. Identifier les cas où une action externe peut avoir réussi malgré une erreur locale.

### Couche 12 — Outils, connecteurs et MCP

Sous-couches :
- registre d’outils ;
- schémas d’arguments ;
- validation stricte ;
- autorisation par outil et opération ;
- authentification des connecteurs ;
- MCP client et serveur si présents ;
- sélection de ressources ;
- secrets et tokens ;
- appels réseau et fichiers ;
- exécution de commandes ;
- gestion des erreurs ;
- quotas, timeouts et retry ;
- provenance des résultats ;
- isolation des sorties non fiables ;
- défense contre prompt injection et tool injection ;
- confirmation des opérations sensibles selon la politique ;
- tests de simulation et tests sur intégrations réelles.

Un résultat d’outil doit être traité comme une donnée potentiellement non fiable, même si le transport est authentifié.

### Couche 13 — Défense des agents et moteur de politiques

Sous-couches :
- détection d’attaque ;
- analyse de risque ;
- policy engine ;
- règles d’autorisation ;
- Disclosure Firewall ;
- validation des sorties ;
- redaction et minimisation ;
- contrôle de flux de données ;
- détection d’exfiltration ;
- containment ;
- révocation et isolement d’agent ;
- limites d’actions ;
- supervision et alertes ;
- gestion des exceptions ;
- journal des décisions de sécurité ;
- tests adversariaux.

Étudier notamment prompt injection, memory poisoning, usurpation d’agent, abus d’outils, exfiltration, élévation de privilèges, rejeu, altération de journaux, confusion de contexte et attaques de chaîne d’approvisionnement.

Si une décision de sécurité est représentée par ALLOW, BLOCK, REDACT ou ESCALATE, vérifier si ces états existent réellement, comment ils sont calculés et comment leurs décisions sont auditées.

### Couche 14 — Mémoire artificielle persistante totale

Sous-couches :
- mémoire de travail ;
- mémoire de session ;
- mémoire épisodique ;
- mémoire sémantique ;
- mémoire procédurale ;
- mémoire de connaissances ;
- mémoire de provenance ;
- historique complet des événements instrumentés ;
- branches parallèles ;
- hypothèses, alternatives, erreurs et corrections ;
- sources externes ;
- résultats d’outils ;
- transformations et dérivations ;
- états de mémoire successifs ;
- index et embeddings ;
- cache et résumés ;
- identifiants de connaissance et d’usage ;
- recherche et récupération ;
- contrôle d’accès ;
- chiffrement ;
- synchronisation ;
- migration, export et récupération ;
- versionnage et rétention.

Principe à préserver : les vues résumées, index, embeddings et caches sont des vues dérivées ; ils ne remplacent pas l’archive source complète lorsque la conservation intégrale est exigée.

La cartographie doit distinguer les éléments réellement observables et instrumentables des états internes non accessibles. Ne pas prétendre enregistrer littéralement chaque état neuronal d’un modèle si l’architecture ne l’expose pas. Documenter les pertes de visibilité, les appels non instrumentés et les zones hors contrôle.

### Couche 15 — Provenance, event ledger et graphe causal

Sous-couches :
- événement immuable ou append-only ;
- identifiants et corrélation ;
- horodatage et source temporelle ;
- agent, outil, processus et version ;
- entrées et sorties ;
- liens parent-enfant ;
- causalité et branches ;
- dépendances de données ;
- hash et signature ;
- ordre logique et séquences ;
- gestion des doublons ;
- validation de schéma ;
- détection de mutation ;
- stockage et réplication ;
- politique de rétention ;
- preuves et métadonnées ;
- replay et reconstruction.

Pour chaque événement, préciser ce qui est garanti par le schéma, ce qui est signé, ce qui est seulement journalisé et ce qui est vérifié indépendamment. Une chaîne de hash détecte certaines modifications mais ne prouve pas à elle seule que les événements initiaux étaient vrais ou complets.

### Couche 16 — Blockchain, consensus et réseau ARTCB

Sous-couches :
- nœud et cycle de vie ;
- P2P et découverte ;
- identité et authentification des pairs ;
- messages et versions de protocole ;
- transaction et validation ;
- blocs, état et stockage ;
- consensus si présent ;
- mempool ou file de transactions ;
- signatures et règles de validité ;
- synchronisation ;
- fork et réorganisation ;
- finalité ;
- reprise et resynchronisation ;
- gouvernance ;
- mises à jour de protocole ;
- gestion des clés ;
- anti-Sybil ;
- disponibilité et protection contre le spam ;
- ponts et interopérabilité, si présents.

Ne pas supposer qu’un composant nommé blockchain possède un consensus opérationnel, une finalité déterminée ou une sécurité économique donnée. Chaque propriété doit être associée à un protocole et à des tests.

### Couche 17 — Tokenomics, jobs, réputation et incitations

Sous-couches à rechercher seulement si elles sont présentes ou retenues :
- unités de valeur et règles d’émission ;
- jobs et marchés de tâches ;
- preuve de travail, preuve de contribution ou PoL ;
- mesure de contribution ;
- attribution de récompenses ;
- réputation ;
- pénalités et contestation ;
- anti-Sybil ;
- validation des résultats ;
- identité humaine et matérielle ;
- gouvernance et paramètres ;
- comptabilité et audits ;
- abus économiques et collusion.

Pour chaque mécanisme économique, identifier les variables d’entrée, les règles, les acteurs qui peuvent les manipuler, les preuves exigées et les tests adversariaux.

### Couche 18 — FHE et calcul confidentiel

Sous-couches :
- bibliothèques et schémas FHE réellement présents ;
- génération et distribution des clés ;
- chiffrement et déchiffrement ;
- paramètres et niveaux de sécurité ;
- budget de bruit ;
- bootstrapping et profondeur ;
- opérations supportées ;
- sérialisation des ciphertexts ;
- calculs et résultats chiffrés ;
- vérification des paramètres ;
- gestion des erreurs ;
- limites mathématiques et de compatibilité ;
- comparaison entre simulation et exécution réelle.

Le FHE protège certaines données pendant le calcul, mais ne prouve pas à lui seul que le calcul a été exécuté correctement, que le code est autorisé ou que le résultat est exact. Associer chaque garantie revendiquée à son mécanisme réel et à une preuve de test.

### Couche 19 — Preuves cryptographiques et calcul vérifiable

Sous-couches :
- engagements cryptographiques ;
- preuves ZK ;
- preuves d’exécution ;
- attestations matérielles ;
- signatures ;
- vérification indépendante ;
- preuves de provenance ;
- preuves de cohérence ;
- vérification des entrées et sorties ;
- gestion des paramètres et clés de vérification ;
- reproductibilité ;
- tests de falsification ;
- coûts et limites documentés.

Distinguer preuve de possession, preuve d’intégrité, preuve d’exécution, preuve de calcul correct, preuve de provenance et preuve d’autorisation. Ces propriétés ne sont pas interchangeables.

### Couche 20 — Observabilité, audit, forensic et replay

Sous-couches :
- logs structurés ;
- métriques ;
- traces distribuées ;
- événements métier ;
- événements de sécurité ;
- identifiants de corrélation ;
- masquage des données sensibles ;
- conservation et rotation ;
- protection contre modification ;
- collecte locale ;
- export contrôlé ;
- reconstruction d’incident ;
- replay déterministe ou quasi déterministe ;
- version des dépendances et du modèle ;
- limites du replay ;
- chaîne de conservation des preuves.

Ne jamais publier les journaux bruts. Les rapports Git ne doivent contenir que des résumés assainis, les versions, les commandes non sensibles, les résultats et les empreintes autorisées.

### Couche 21 — API, interface utilisateur et intégration

Sous-couches :
- API publiques et privées ;
- authentification ;
- validation ;
- quotas et limites ;
- réponses et erreurs ;
- compatibilité ;
- CLI ;
- interface utilisateur ou dashboard ;
- permissions ;
- gestion de session ;
- affichage des alertes ;
- exposition de preuves ;
- téléchargement et export ;
- accessibilité ;
- intégrations externes.

Vérifier que l’interface ne transforme pas un résultat non vérifié en affirmation de sécurité et qu’elle ne révèle pas de données auxquelles l’utilisateur n’est pas autorisé à accéder.

### Couche 22 — Configuration, secrets et paramètres opérationnels

Sous-couches :
- fichiers de configuration ;
- variables d’environnement ;
- gestionnaire de secrets ;
- rotation des credentials ;
- clés API ;
- certificats ;
- paramètres réseau ;
- feature flags ;
- environnements ;
- valeurs par défaut ;
- validation au démarrage ;
- rechargement à chaud ;
- séparation des environnements ;
- détection de configuration dangereuse ;
- contrôle des permissions.

Ne jamais lire, afficher ou recopier une valeur secrète dans le rapport. Signaler la présence d’un secret potentiel par son emplacement et son type, en le masquant.

### Couche 23 — Fiabilité, capacité et résilience

Sous-couches :
- timeouts ;
- retry et backoff ;
- circuit breakers ;
- files et backpressure ;
- limites mémoire et disque ;
- concurrence ;
- deadlocks et starvation ;
- arrêt gracieux ;
- crash recovery ;
- cohérence après panne ;
- sauvegardes ;
- reprise après perte de clé ;
- dégradation contrôlée ;
- disponibilité du réseau ;
- tests de chaos dans un environnement autorisé ;
- objectifs de récupération.

La vitesse n’est pas la priorité architecturale retenue pour la traçabilité, mais les limites physiques, les risques de saturation et la disponibilité doivent rester mesurés. Accepter un coût de calcul élevé ne signifie pas ignorer les risques de panne ou d’épuisement de ressources.

### Couche 24 — Tests, validation et assurance qualité

Sous-couches :
- tests unitaires ;
- tests de contrat ;
- tests d’intégration ;
- tests système de bout en bout ;
- tests différentiels Rust/Python ;
- tests de compatibilité ;
- tests de migration ;
- tests cryptographiques par vecteurs connus ;
- tests adversariaux ;
- tests de sécurité ;
- fuzzing ;
- tests de charge et de ressources ;
- tests de panne et de reprise ;
- tests de corruption et de rejeu ;
- tests matériels réels ;
- tests de confidentialité ;
- tests de restauration ;
- tests de régression ;
- validation indépendante.

Pour chaque test, conserver le nom, la révision, l’environnement, les préconditions, la commande, le résultat, les limites, les preuves et les éventuels artefacts locaux. Un test non exécuté ne doit jamais être marqué PASS.

### Couche 25 — Déploiement, exploitation et cycle de vie

Sous-couches :
- installation ;
- configuration initiale ;
- démarrage et arrêt ;
- mises à jour ;
- migrations ;
- rollback ;
- surveillance ;
- rotation de clés ;
- révocation ;
- récupération ;
- sauvegarde ;
- restauration ;
- changement de machine ;
- transfert de nœud ;
- remplacement matériel ;
- désinstallation ;
- destruction contrôlée de secrets ;
- fin de vie et retrait de service.

Étudier les conséquences d’une panne de disque, d’une perte de Node Key, d’un TPM remplacé, d’une clé révoquée, d’un nœud hors ligne ou d’une migration incomplète.

### Couche 26 — Documentation, gouvernance et traçabilité du projet

Sous-couches :
- README et guides ;
- ADR et décisions ;
- spécifications de protocoles ;
- rapports numérotés ;
- historique des décisions ;
- tâches incomplètes ;
- matrice exigences-preuves ;
- suivi des risques ;
- responsabilités ;
- approbations ;
- licences et conformité ;
- plan de continuité de l’audit ;
- historique des changements de périmètre.

Les rapports précédents doivent être relus pour extraire les tâches ouvertes. Une nouvelle priorité ne doit pas effacer les travaux précédemment déclarés incomplets.

## 4. Dimensions transversales obligatoires

Les couches ne suffisent pas à elles seules. Pour chaque couche et chaque composant, examiner aussi les dimensions suivantes.

### 4.1 Sécurité

- actifs à protéger ;
- frontières de confiance ;
- acteurs et privilèges ;
- surface d’attaque ;
- entrées non fiables ;
- abus d’API et d’outils ;
- élévation de privilèges ;
- injection de prompt ;
- compromission de dépendance ;
- altération de données ;
- rejeu ;
- exfiltration ;
- déni de service ;
- secrets ;
- contrôles préventifs et détectifs ;
- récupération ;
- risque résiduel.

### 4.2 Données et provenance

- source ;
- identifiant ;
- schéma ;
- classification ;
- propriétaire ou autorité ;
- transformations ;
- agent et version ;
- outils ;
- horodatage ;
- stockage ;
- preuve d’intégrité ;
- politique d’accès ;
- rétention ;
- export ;
- suppression ;
- liens de causalité.

### 4.3 Compatibilité

- API ;
- protocole ;
- schéma ;
- données persistées ;
- identifiants ;
- événements ;
- comportement d’erreur ;
- ordre ;
- idempotence ;
- formats cryptographiques ;
- versions anciennes ;
- stratégie de migration ;
- rollback.

### 4.4 Performance et ressources

- CPU ;
- mémoire ;
- stockage ;
- réseau ;
- latence ;
- débit ;
- profondeur de tâches ;
- parallélisme ;
- taille des preuves ;
- coût du FHE ;
- croissance des archives ;
- rétention ;
- saturation et dégradation.

Les mesures sont à documenter, même si l’optimisation de la vitesse est secondaire.

### 4.5 Gouvernance

- décision attendue ;
- décideur autorisé ;
- approbation ;
- preuve d’approbation ;
- portée exacte ;
- exclusions ;
- conséquences ;
- retour arrière ;
- conditions de réouverture.

## 5. Modèle de données de la cartographie

Chaque composant doit posséder une fiche structurée contenant au minimum :

- identifiant stable ;
- nom exact observé ;
- couche et sous-couche ;
- chemin de fichier ;
- symboles associés ;
- rôle constaté ;
- statut : implémenté, partiel, prototype, documenté, planifié, absent du périmètre inspecté ou inconnu ;
- preuves ;
- entrées et sorties ;
- dépendances entrantes et sortantes ;
- données manipulées ;
- privilèges ;
- contrats et versions ;
- événements émis et consommés ;
- contrôles de sécurité ;
- tests associés ;
- risques ;
- tâches ouvertes ;
- niveau de confiance de l’analyse ;
- date et révision de la preuve.

Ne pas assigner un statut « implémenté » sur la seule base d’un nom de fichier ou d’un commentaire.

## 6. Matrice de traçabilité requise

La cartographie doit relier :

**Exigence → couche → composant → interface → donnée → événement → contrôle de sécurité → test → preuve → risque résiduel → décision.**

Chaque exigence doit être :
- couverte par une preuve ;
- couverte partiellement ;
- non testée ;
- bloquée par une dépendance ;
- hors périmètre avec justification ;
- ou impossible à vérifier avec les accès disponibles.

Aucune exigence ne doit disparaître silencieusement de la matrice.

## 7. Tests de fermeture de cartographie

Avant de déclarer la cartographie complète, l’agent doit vérifier :

1. Tous les répertoires accessibles ont un statut explicite.
2. Tous les fichiers non générés ont été classés.
3. Les fichiers de configuration, tests, workflows, scripts et dépendances ont été examinés.
4. Les points d’entrée sont recensés.
5. Les dépendances entre modules sont reliées au graphe.
6. Les API et formats de données sont inventoriés.
7. Les données persistées et leur cycle de vie sont décrits.
8. Les flux entre agents, outils et modèles sont cartographiés.
9. Les frontières Rust/Python sont identifiées et justifiées.
10. Les mécanismes cryptographiques sont reliés aux garanties qu’ils apportent réellement.
11. Les composants matériels sont distingués des simulations.
12. Les rapports précédents et tâches incomplètes sont repris.
13. Les preuves et limites sont attachées aux conclusions.
14. Les zones inaccessibles ou non testées sont explicites.
15. Aucun code applicatif n’a été modifié.
16. Aucun journal brut ou secret n’a été poussé.
17. Le diff final ne contient que les rapports autorisés.
18. La numérotation a été vérifiée avant création.
19. Le rapport est reproductible à partir du SHA source déclaré.
20. Les conclusions n’affirment pas une certification que les preuves ne démontrent pas.

## 8. Livrables attendus de l’audit détaillé

Le rapport de cartographie produit par l’agent chargé de l’exécution devra contenir :

1. Résumé exécutif et périmètre exact.
2. SHA des dépôts et date de synchronisation.
3. Inventaire de tous les fichiers et répertoires.
4. Cartographie complète des couches et sous-couches.
5. Graphe des dépendances et des flux.
6. Matrice des composants et statuts d’implémentation.
7. Carte des identités, permissions et frontières de confiance.
8. Carte des données, événements et provenance.
9. Carte des API, protocoles et contrats de compatibilité.
10. Carte des agents, outils, modèles et délégations.
11. Carte des composants cryptographiques, blockchain et matériels.
12. Carte de la mémoire artificielle et de ses mécanismes de persistance.
13. Threat model et chemins d’attaque.
14. Inventaire des tests et preuves réellement exécutés.
15. Liste des écarts, zones inconnues et tâches antérieures ouvertes.
16. Priorisation P0/P1/P2 avec justification.
17. Plan de vérification et critères de fermeture.
18. Liste des décisions nécessitant l’approbation de l’utilisateur.
19. Confirmation du respect du périmètre Git.
20. Conclusion bornée par les preuves.

## 9. Priorisation

- **P0 — Blocage de confiance :** risque de fuite de secret, frontière de confiance non contrôlée, preuve fausse ou non vérifiable, corruption silencieuse, accès non autorisé, modification interdite ou impossibilité de vérifier une garantie critique.
- **P1 — Incomplétude majeure :** absence de contrat, de test de non-régression, de provenance, de récupération, de gestion d’erreur ou de couverture d’un composant important.
- **P2 — Amélioration :** amélioration de lisibilité, automatisation de l’inventaire, documentation complémentaire, optimisation ou ergonomie qui ne bloque pas une garantie fondamentale.

La priorité doit être motivée par la menace et l’impact, non par la facilité d’implémentation.

## 10. Tâches héritées à maintenir ouvertes jusqu’à preuve de clôture

Les rapports antérieurs identifient notamment des sujets à réexaminer sans supposer qu’ils sont résolus :
- inventaire des capacités réellement retenues pour migration ;
- justification composant par composant de la frontière Rust/Python ;
- contrats de données et compatibilité ;
- baseline de tests de caractérisation ;
- parité Rust/Python et tests différentiels ;
- espace de test isolé et prévention de publication des journaux ;
- identification réelle du périphérique USB ;
- distinction USB, authentificateur cryptographique et TPM ;
- validation sur matériel réel ;
- vérification de l’attestation distante et de la protection anti-rejeu ;
- provenance complète et replay ;
- tests adversariaux des agents et outils ;
- récupération, rotation de clés et migration de nœud ;
- validation indépendante et critères de Go/No-Go.

Chaque élément doit être reclassé avec une preuve actuelle : ouvert, terminé avec preuve, bloqué, remplacé par une décision documentée ou hors périmètre approuvé.

## 11. Critère de sortie

La cartographie peut être déclarée « complète au regard du périmètre inspecté » seulement si :
- le SHA étudié est figé ;
- la couverture de l’arbre de fichiers est mesurée ou ses limites explicitées ;
- chaque couche et chaque sous-couche a un statut ;
- les composants découverts sont reliés à leurs preuves ;
- les flux et dépendances sont cartographiés ;
- les zones inconnues sont listées ;
- les tâches héritées sont réconciliées ;
- aucun élément n’est déclaré validé sans preuve ;
- les contraintes de dépôt sont respectées.

Cette déclaration ne vaut pas certification de sécurité globale, absence de vulnérabilité ni preuve de conformité formelle.

## 12. Conclusion

La cartographie doit être une représentation vérifiable du système réel, et non une architecture idéale présentée comme déjà existante. Le plan ci-dessus fournit les familles de couches à examiner ; l’audit devra confirmer, infirmer, compléter ou marquer comme non applicable chaque sous-couche à partir des dépôts et preuves disponibles.

**Aucun code applicatif n’est autorisé par ce rapport. Le périmètre d’écriture demeure rapports/ dans ARTCB-TERMINATOR.**
