# ROO2 — Matrice de migration P0 ARTCB → Guardian Rust/Python

**Date :** 2026-10-09  
**Dépôt de travail :** `vgactech/ARTCB-TERMINATOR`  
**Dossier autorisé :** `rapports/` uniquement  
**Dépôt source audité :** `vgactech/artcb`  
**Référence source synchronisée :** commit R590 `7304d493018995d851ed5c13107c5e9d5bd79268`  
**Périmètre :** migration sélective P0 pour ARTCB Guardian / Secure Horizons Track 2  
**Décision blockchain :** pour ce chantier, seule la primitive **Event Ledger / WAL de preuve** est retenue. Tokenomics, économie, minage et migration complète de la blockchain sont hors périmètre sauf demande explicite ultérieure.

## 1. Expertises activées

- Architecture Rust/Python et migration sélective Python/C → Rust/Python
- Event sourcing et Write-Ahead Logging
- Hash chaining, intégrité et tamper evidence
- Provenance causale et forensic computing
- Architecture mémoire agentique
- Sécurité multi-agents
- Threat modeling et tests adversariaux
- MCP/API Security
- Disclosure Firewall
- Replay déterministe
- FFI Rust/Python avec PyO3/Maturin
- Conception de contrats de données
- Validation de non-régression
- Architecture de démonstration Secure Horizons
- Analyse de périmètre blockchain limitée au Ledger

## 2. Synchronisation effectuée

Le dépôt source `vgactech/artcb` a été resynchronisé avant cette analyse.

Le dépôt source est identifié par GitHub comme principalement Python et son dernier commit pertinent de positionnement compétition est R590, commit `7304d493...`.

Le dépôt cible `ARTCB-TERMINATOR` contient actuellement le dossier `rapports/` et le rapport R591. Aucun code applicatif n'est ajouté dans le présent rapport.

**Aucune modification du dépôt source `vgactech/artcb` n'est effectuée.**

## 3. Objectif exact de R592

R591 a défini l'architecture générale :

**Python = agents, orchestration, scénarios, MCP et expérimentation.**

**Rust = événements, intégrité, provenance, policy, firewall, replay et evidence.**

R592 descend maintenant d'un niveau : chaque composant P0 doit avoir un contrat de migration précis.

La règle est :

**existant ARTCB → responsabilité Guardian → contrat stable → cible Rust/Python → validation → attaque adversariale → critère de sortie.**

Le but n'est pas de recopier l'ancien code.

Le but est de conserver la propriété fonctionnelle utile et de déplacer la frontière de confiance vers Rust.

## 4. Décision importante concernant la blockchain

### Processus

ARTCB possède un historique blockchain et un WAL C. Le WAL actuel représente des événements persistants avec type, taille, CRC, écriture synchronisée sur disque et lecture destinée au replay.

### Problème

Pour Guardian, reconstruire toute la blockchain serait une dérive de périmètre. Cela déplacerait l'effort vers consensus, tokenomics, économie, réseau et compatibilité historique alors que la démonstration compétitive doit prouver une autre chose :

**attaque → détection → confinement → preuve → replay.**

### Solution

Nous ne migrons dans P0 que la primitive nécessaire :

**Event Ledger append-only + intégrité + récupération + replay.**

La blockchain complète reste une extension possible.

Donc :

- Event Ledger : P0
- WAL de durabilité : P0
- hash chain : P0
- vérification d'intégrité : P0
- replay : P0
- consensus : hors scope
- tokenomics : hors scope
- économie : hors scope
- minage : hors scope
- réseau blockchain public : hors scope

C'est exactement la limitation demandée pour la compétition.

## 5. P0-01 — AgentRunLedger → Rust Event Ledger

### Processus

Le module Python `src/artcb/trace/agent_run.py` possède déjà une primitive très utile : chaque événement contient un identifiant, un parent, un agent, une action, un statut, des hashes d'entrée/sortie/artefact, la version de policy et un hash de chaîne calculé à partir de l'événement précédent.

Le principe existant est donc déjà proche de :

**Event N → SHA-256(Event N + Hash N-1) → Event N+1.**

### Problème

Cette primitive reste Python et son stockage est essentiellement une représentation applicative. Pour Guardian, la chaîne d'intégrité doit devenir une frontière de confiance indépendante de l'orchestrateur.

### Solution

Créer en Rust un `Event Ledger Core` avec :

- EventId ;
- parent_event_id ;
- session_id ;
- agent_id ;
- event_type ;
- status ;
- input_hash ;
- output_hash ;
- artifact_hash ;
- policy_id ;
- policy_version ;
- timestamp ;
- previous_hash ;
- chain_hash ;
- schema_version ;
- evidence_id optionnel.

Python ne construit pas directement le hash final.

Python soumet un événement au Security Core.

Rust :

1. valide le schéma ;
2. canonise l'événement ;
3. calcule le hash ;
4. vérifie le parent ;
5. rend l'événement append-only ;
6. renvoie l'identifiant et la preuve d'intégrité.

### Validation

- deux événements identiques dans le même contexte ne doivent pas obtenir deux positions ambiguës ;
- une modification d'un événement doit être détectée ;
- une suppression intermédiaire doit être détectée ;
- un changement d'ordre doit être détecté ;
- un mauvais parent doit être détecté ;
- un crash pendant l'écriture ne doit pas produire un événement déclaré durable sans preuve de persistance.

### Critère de sortie

**PASS uniquement si le ledger détecte toute altération volontaire injectée dans un scénario de test.**

## 6. P0-02 — C WAL → Rust Durable Event Store

### Processus

Le WAL historique définit déjà une écriture persistante avec :

- magic ;
- version ;
- type ;
- longueur ;
- CRC ;
- écriture ;
- fsync ;
- lecture séquentielle ;
- repositionnement pour replay ;
- gestion des corruptions.

### Problème

Le CRC protège contre certaines corruptions accidentelles mais ne constitue pas à lui seul une preuve cryptographique de provenance. De plus, nous ne voulons pas maintenir une dépendance C dans le nouveau Security Core si Rust peut reprendre la responsabilité.

### Solution

Ne pas porter mécaniquement le C.

Conserver les invariants utiles :

**écriture durable → récupération → lecture → replay → détection corruption.**

Puis ajouter :

**hash cryptographique → chaîne de provenance → vérification indépendante.**

Le Rust Ledger doit donc devenir le successeur fonctionnel du WAL P0, sans chercher à reproduire toute l'API C historique.

### Critère de sortie

- arrêt brutal pendant écriture testé ;
- récupération testée ;
- corruption détectée ;
- hash chain vérifiable ;
- replay possible ;
- aucune dépendance au cœur C pour le scénario Guardian.

## 7. P0-03 — IRGraph → Provenance Engine

### Processus

Le modèle IR existant contient déjà des nœuds, des relations, un checksum, une source et des champs de provenance tels que `layer`, `source_hash` et `created_at`.

### Problème

Un checksum de graphe ne suffit pas à démontrer la causalité d'un incident agentique.

Il faut savoir :

**quel agent a produit quelle donnée, à partir de quel événement, avec quel outil, puis quelle autre opération a consommé cette donnée.**

### Solution

Le Rust Provenance Engine doit construire un graphe causal minimal :

**Agent → Event → Artifact → Memory → Agent → ToolCall → Output → Policy → Evidence.**

Relations minimales :

- CREATED;
- READ;
- TRANSFORMED;
- SENT;
- RECEIVED;
- STORED;
- RETRIEVED;
- CALLED;
- BLOCKED;
- ALLOWED;
- REJECTED;
- DERIVED_FROM.

### Critère de sortie

Pour un incident de démonstration, il doit être possible de partir du résultat dangereux et de remonter jusqu'à :

**agent initial → événement initial → donnée contaminante → propagation → appel outil → décision défense.**

## 8. P0-04 — AgentChannel → message instrumenté

### Processus

`AgentChannel` fournit déjà une communication agent-agent fondée sur des ConceptID et des paquets binaires. Le texte humain n'est pas nécessaire à chaque échange.

### Problème

Le canal sémantique actuel n'est pas encore, à lui seul, un journal de sécurité complet.

Un message doit devenir un événement causal.

### Solution

Conserver le protocole fonctionnel mais enrichir l'enveloppe de sécurité avec :

- sender_agent_id ;
- receiver_agent_id ;
- message_id ;
- parent_event_id ;
- payload_hash ;
- schema_version ;
- policy_decision ;
- evidence_id.

Le contenu peut rester binaire.

Le ledger n'a pas besoin de stocker systématiquement le contenu en clair : il doit pouvoir enregistrer son empreinte et sa référence d'archive selon la classification.

### Critère de sortie

Une contamination envoyée de A vers B doit être reconstructible sans ambiguïté :

**A → message → B → consommation → mutation mémoire.**

## 9. P0-05 — Disclosure Firewall → Rust Policy Boundary

### Processus

Le firewall Python historique possède déjà une classification, une audience et une matrice de décision fail-closed. Il distingue notamment PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED et DEFENSE_CRITICAL.

### Problème

Pour Guardian, le firewall ne doit pas être uniquement une fonction de filtrage de texte. Il doit protéger une décision de sécurité et laisser une preuve.

### Solution

La décision critique devient Rust :

**input → classification → policy → decision → evidence.**

Décisions P0 :

- ALLOW ;
- BLOCK ;
- REDACT ;
- ESCALATE.

Chaque décision doit être associée à :

- policy_id ;
- policy_version ;
- agent_id ;
- event_id ;
- reason_code ;
- evidence_id ;
- input_hash ;
- output_hash.

Le Python Firewall peut rester une couche de détection/classification pendant la transition, mais aucune action P0 dangereuse ne doit contourner la décision du Security Core.

### Critère de sortie

Toute tentative d'exfiltration de démonstration doit produire :

**BLOCK + reason + EvidenceId + événement ledger.**

## 10. P0-06 — Replay Engine

### Processus

ARTCB possède déjà des mécanismes de WAL replay et plusieurs outils de replay historiques.

### Problème

Un replay qui exécute simplement à nouveau le système n'est pas une preuve.

Le LLM peut changer, un outil externe peut changer, une API peut changer.

### Solution

Le replay Guardian doit être fondé d'abord sur les événements enregistrés.

Il reconstruit :

- ordre ;
- agents ;
- parents ;
- mutations ;
- appels d'outils ;
- décisions ;
- hashes ;
- preuves.

Il doit ensuite comparer l'état reconstruit aux empreintes enregistrées.

### Critère de sortie

Si un événement historique est modifié :

**REPLAY = FAIL / INTEGRITY MISMATCH.**

Si aucun événement n'est modifié :

**REPLAY = PASS / provenance reconstruite.**

## 11. P0-07 — MCP ToolCall

### Processus

Le dépôt source possède un serveur MCP Python permettant à des agents et IDE d'interagir avec ARTCB.

### Problème

MCP devient une surface d'attaque directe.

Un agent compromis peut tenter :

- outil interdit ;
- argument malveillant ;
- exfiltration ;
- appels en chaîne ;
- abus de fréquence ;
- utilisation d'un outil non approuvé.

### Solution

Chaque `tools/call` devient un événement P0.

Pipeline :

**MCP → Python adapter → Rust policy → tool → Rust evidence → Python response.**

Le tool ne doit pas être exécuté avant le contrôle de policy lorsqu'il appartient à une catégorie protégée.

### Critère de sortie

Un outil malveillant simulé doit être :

1. identifié ;
2. refusé ;
3. enregistré ;
4. associé à une preuve ;
5. visible dans le replay.

## 12. P0-08 — Contrat Python ↔ Rust

### Processus

PyO3/Maturin permettent de présenter le Security Core Rust comme un module Python.

### Problème

Si Python manipule les structures internes Rust, la frontière de confiance devient artificielle.

### Solution

API minimale stable :

- append_event ;
- verify_event ;
- verify_chain ;
- add_provenance_edge ;
- evaluate_policy ;
- create_evidence ;
- replay_incident ;
- verify_evidence.

Les structures internes restent privées.

Le contrat doit être versionné.

### Critère de sortie

Les tests Python doivent pouvoir appeler Rust sans connaître les détails d'implémentation internes.

## 13. Matrice P0 synthétique

| ID | Existant ARTCB | Cible | Rust | Python | Validation |
|---|---|---|---:|---:|---|
| P0-01 | AgentRunLedger | Event Ledger | OUI | adaptateur | tamper detection |
| P0-02 | C WAL | Durable Event Store | OUI | non | crash/recovery |
| P0-03 | IRGraph provenance | Provenance Engine | OUI | export | causal reconstruction |
| P0-04 | AgentChannel | Secure AgentChannel envelope | OUI pour intégrité | OUI pour protocole | A→B replay |
| P0-05 | Disclosure Firewall | Policy/Firewall Core | OUI | classification | BLOCK + evidence |
| P0-06 | replay/WAL | Replay Engine | OUI | UI/scenario | deterministic reconstruction |
| P0-07 | MCP server | MCP security adapter | OUI pour policy | OUI pour transport | malicious tool blocked |
| P0-08 | Python APIs | PyO3 binding | OUI | OUI | cross-language tests |

## 14. Ce qui n'est PAS P0

Les éléments suivants ne doivent pas détourner l'effort actuel :

- tokenomics ;
- Universal Dividend ;
- pARTCB/pubARTCB ;
- consensus BFT complet ;
- réseau blockchain public complet ;
- migration de toutes les transactions historiques ;
- wallet economy ;
- minage ;
- fonctionnalités commerciales non nécessaires à Guardian.

Cela ne signifie pas qu'ils sont inutiles au projet ARTCB global.

Cela signifie seulement qu'ils ne sont pas nécessaires pour démontrer la proposition Secure Horizons.

## 15. Threat tests P0

Chaque composant doit être attaqué, pas seulement testé nominalement.

### T01 — Event mutation

Modifier un événement après écriture.

Attendu : intégrité invalide.

### T02 — Event deletion

Supprimer un événement intermédiaire.

Attendu : rupture de chaîne ou provenance incomplète détectée.

### T03 — Event reorder

Inverser deux événements.

Attendu : parent/hash mismatch.

### T04 — Replay tampering

Modifier une décision historique.

Attendu : replay incohérent.

### T05 — Memory poisoning

Insérer une connaissance malveillante.

Attendu : provenance de la mutation et propagation visibles.

### T06 — Cross-agent propagation

Envoyer la donnée contaminée de A à B.

Attendu : lineage A→B.

### T07 — Tool abuse

Agent compromis → outil interdit.

Attendu : BLOCK.

### T08 — Exfiltration

Agent → donnée sensible → sortie externe.

Attendu : BLOCK ou REDACT selon policy.

### T09 — Malicious MCP

ToolCall conçu pour contourner l'orchestrateur.

Attendu : décision Rust avant action protégée.

### T10 — Corrupted evidence

Modifier l'artefact de preuve.

Attendu : Evidence verification FAIL.

## 16. Critères de sortie P0

P0 n'est terminé que si les conditions suivantes sont toutes satisfaites :

1. Event Ledger Rust fonctionnel ;
2. persistance crash-safe validée ;
3. hash chain vérifiable ;
4. provenance causale reconstruisible ;
5. AgentChannel instrumenté ;
6. MCP ToolCall instrumenté ;
7. firewall/policy Rust capable de BLOCK ;
8. chaque BLOCK produit une evidence ;
9. replay d'incident fonctionnel ;
10. modification historique détectée ;
11. scénario multi-agent reproductible ;
12. tests adversariaux critiques PASS ;
13. aucun log sensible poussé dans Git ;
14. aucun code source `vgactech/artcb` modifié.

## 17. Architecture finale P0

La chaîne de confiance retenue est :

**Agent Python**

→ **Event Adapter**

→ **Rust Event Ledger**

→ **Provenance Engine**

→ **Policy Engine**

→ **Firewall**

→ **Evidence**

→ **Replay**

→ **Security View**

Le principe est :

**Python expérimente. Rust garantit.**

## 18. Conclusion

R592 confirme que la migration P0 peut être réalisée sans migrer toute la blockchain.

La seule partie blockchain conservée au niveau P0 est la primitive de journalisation nécessaire à la preuve :

**Event Ledger / WAL → intégrité → provenance → replay.**

Le reste de la blockchain historique demeure hors périmètre de Guardian tant qu'il n'est pas nécessaire au scénario.

La prochaine étape technique doit donc être R593 :

**spécification normative du format Event Ledger Rust**, avec schéma canonique, règles de hash, identifiants, versionnement, idempotence, crash recovery et vecteurs de tests adversariaux.

Aucune implémentation applicative n'est créée dans ce rapport.
