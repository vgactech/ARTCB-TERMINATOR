# R591 — Cahier des charges et roadmap de migration ARTCB Guardian vers Rust + Python

**Date :** 2026-10-09  
**Dépôt cible :** `vgactech/ARTCB-TERMINATOR`  
**Dépôt source audité :** `vgactech/artcb`  
**Branche source auditée :** `main`  
**Objet :** étude préalable, architecture cible, plan de migration et roadmap compétition Secure Horizons — Track 2 « Defenders Augmented »

## 1. Expertises activées

- Architecture logicielle et migration Python/C vers Rust/Python
- Cybersécurité agentique et AI Security
- Threat modeling / abuse-case engineering
- Provenance, forensic computing et incident replay
- Event sourcing, hash chaining et intégrité cryptographique
- Sécurité MCP/API et contrôle des outils
- Architecture multi-agents et mémoire persistante
- Interopérabilité Rust/Python, FFI et packaging
- Performance, concurrence et fiabilité
- Tests adversariaux et validation expérimentale
- Architecture de démonstration hackathon
- Gestion de cahier des charges, exigences et roadmap
- Analyse de dette technique et stratégie de migration

## 2. Synchronisation et constat de départ

Le dépôt cible `ARTCB-TERMINATOR` est actuellement vide : taille GitHub déclarée 0, branche par défaut `main`. Aucun code applicatif ne peut donc être migré « en place » dans ce dépôt à ce stade.

Le dépôt source `vgactech/artcb` est au contraire substantiel et contient une architecture majoritairement Python, avec un cœur blockchain spécifié en C dans le cahier des charges historique.

Conclusion importante : **la migration demandée n'est pas une conversion Go → Rust**. L'état réel audité est principalement **Python + C**, et la cible retenue devient **Rust + Python**.

Le rapport R590 a déjà validé le positionnement Secure Horizons : **Track 2 — Defenders Augmented, 9,5/10**, avec ARTCB Guardian — « Agentic Attack Replay & Evidence Firewall » et la chaîne de valeur « Detect. Contain. Reconstruct. Prove. » Le présent rapport transforme cette décision stratégique en cahier des charges technique de migration. 

## 3. Ce que nous devons conserver

La migration ne doit pas détruire les propriétés fonctionnelles déjà acquises.

Les briques à préserver ou réutiliser sont notamment :

- Agent Memory Protocol et événements idempotents ;
- AgentChannel et mémoire agent-agent ;
- IR / graphe conceptuel ;
- provenance et hashage ;
- RT-LEG et événements d'exécution ;
- Disclosure Firewall ;
- distinction entre archive de provenance et vues décisionnelles ;
- identité agentique et anti-Sybil ;
- signatures et intégrité ;
- MCP ;
- UXR / Model Registry lorsque pertinent ;
- mémoire persistante ;
- mécanismes de replay ;
- tests et rapports historiques servant de preuves.

Le R590 identifie explicitement ces briques comme les actifs les plus exploitables pour la compétition. fileciteturn0file0L30-L47

## 4. Décision d'architecture : Rust + Python

### Processus

Python reste la couche d'expérimentation et d'intelligence : agents, scénarios d'attaque, orchestration LLM, MCP, génération de scénarios, tests, scoring et interface de démonstration.

Rust devient le noyau de confiance : journal d'événements, provenance, intégrité, validation des entrées/sorties, politiques de sécurité, replay déterministe et production de preuves.

### Problème

Le cahier des charges historique place une partie critique du système dans un cœur C et fait reposer une grande quantité de logique sur Python. Cette architecture est adaptée au prototypage historique, mais elle ne donne pas encore une frontière de confiance nette pour le produit de compétition.

### Solution

Architecture cible :

**Agents Python → API/SDK Python → Security Core Rust → Evidence Archive → Security Views → Replay/Proof**

La règle d'architecture est :

**Python décide ce que les agents expérimentent ; Rust garantit ce qui doit rester vérifiable.**

Rust apporte une gestion mémoire fondée sur ownership/borrowing vérifiée par le compilateur, sans garbage collector. Cette propriété est particulièrement pertinente pour le composant de confiance. citeturn0search11turn0search12

## 5. Pourquoi l'interopérabilité Rust/Python est réaliste

Le choix Rust + Python ne nécessite pas deux applications totalement indépendantes.

PyO3 permet de produire des modules Python natifs écrits en Rust, et Maturin fournit le mécanisme de build/distribution courant. La documentation actuelle de PyO3 indique également le support des distributions Python modernes et du Python free-threaded. citeturn0search0turn0search10

### Architecture recommandée

Python appelle un module Rust nommé conceptuellement `artcb_guardian_core`.

Le module expose uniquement des interfaces stables :

- append_event ;
- verify_event ;
- verify_chain ;
- compute_provenance ;
- evaluate_policy ;
- create_evidence ;
- replay_incident ;
- verify_evidence ;
- sanitize_output.

Les structures internes Rust restent privées.

C'est-à-dire que Python ne doit pas manipuler directement les structures internes du ledger ou de la chaîne de provenance.

## 6. Études obligatoires avant migration

### Étude E01 — Inventaire fonctionnel

**Processus :** établir la correspondance entre chaque module ARTCB existant et une responsabilité Guardian.

**Problème :** migrer les fichiers un par un conduirait à reproduire l'ancienne architecture sans sélectionner ce qui est réellement utile au Track 2.

**Solution :** créer une matrice « fonction actuelle → valeur compétition → cible Rust/Python → priorité ».

Priorités :

- P0 : provenance, événements, identité agent, firewall, replay, preuves ;
- P1 : AgentChannel, mémoire, MCP sécurisé, scoring ;
- P2 : blockchain/tokens/PoL historiques non nécessaires à la démo Guardian ;
- P3 : fonctionnalités hors scénario de compétition.

### Étude E02 — Contrats de données

Définir avant toute réécriture :

- AgentId ;
- SessionId ;
- EventId ;
- ToolCallId ;
- IncidentId ;
- EvidenceId ;
- hashes ;
- timestamps ;
- parent_event_id ;
- input/output references ;
- policy decision ;
- block/ledger reference.

Chaque identifiant doit être stable et sérialisable.

### Étude E03 — Modèle de provenance

La provenance doit répondre à une question simple :

**« Pourquoi cette action est-elle arrivée ? »**

Le graphe minimal doit permettre :

Agent A → input → memory write → Agent B → tool call → output attempt → firewall decision → evidence.

Le R589 fournit la contrainte conceptuelle essentielle : une vue décisionnelle filtrée n'est pas une preuve exhaustive. Il faut donc conserver séparément **Evidence Archive** et **Security Views**.

### Étude E04 — Threat model

Scénarios P0 à tester :

1. prompt injection ;
2. memory poisoning ;
3. agent impersonation ;
4. tool abuse ;
5. cross-agent contamination ;
6. exfiltration ;
7. provenance tampering ;
8. replay tampering ;
9. malicious MCP tool ;
10. disclosure of private evidence ;
11. event duplication ;
12. event reordering ;
13. corrupted evidence;
14. denial of service sur le journal.

Chaque attaque doit produire un résultat mesurable :

**attaque → détection → décision → confinement → preuve → replay.**

### Étude E05 — Security Firewall

Le Disclosure Firewall doit être requalifié pour Guardian.

Il doit distinguer :

- donnée autorisée ;
- donnée sensible ;
- secret ;
- contenu privé ;
- propriété intellectuelle ;
- outil interdit ;
- sortie à risque.

Le firewall ne doit pas seulement « nettoyer du texte ». Il doit produire une décision traçable :

**ALLOW / BLOCK / REDACT / ESCALATE**

avec raison, policy_id, agent_id, event_id et evidence_id.

### Étude E06 — Replay déterministe

Un incident doit pouvoir être rejoué à partir des événements enregistrés sans réexécuter aveuglément les agents.

Le replay doit reconstruire :

- ordre des événements ;
- agents ;
- entrées ;
- décisions ;
- appels d'outils ;
- mutations mémoire ;
- décisions du firewall ;
- preuves produites.

Le replay doit détecter toute divergence de hash.

### Étude E07 — MCP security

Le serveur MCP actuel permet aux IDE et agents d'interagir avec ARTCB. Pour Guardian, MCP devient une surface d'attaque à instrumenter.

Chaque `tools/call` doit être représenté dans le ledger.

Une politique doit pouvoir bloquer :

- outil non autorisé ;
- argument interdit ;
- cible interdite ;
- fréquence excessive ;
- sortie sensible ;
- chaîne d'appels suspecte.

### Étude E08 — Performance

Mesures de référence à établir avant migration :

- latence append_event ;
- événements/seconde ;
- coût hash ;
- coût signature ;
- taille d'un événement ;
- temps de reconstruction ;
- temps de replay ;
- coût d'une décision firewall ;
- coût Python ↔ Rust.

Objectif initial Guardian :

- append local P95 < 5 ms ;
- décision policy P95 < 10 ms ;
- replay d'un incident de démo < 1 s ;
- aucune perte d'événement après arrêt brutal ;
- vérification d'intégrité reproductible.

Ces valeurs sont des **objectifs d'ingénierie à mesurer**, pas des performances déjà démontrées.

## 7. Ce qui doit migrer en Rust en premier

### P0-R1 — Event Ledger

Responsabilités :

- append-only ;
- hash chaining ;
- identifiants ;
- idempotence ;
- validation de schéma ;
- persistance durable ;
- récupération après crash.

### P0-R2 — Provenance Engine

Responsabilités :

- relations parent/enfant ;
- causalité ;
- propagation inter-agent ;
- tool-call lineage ;
- memory lineage ;
- incident graph.

### P0-R3 — Integrity Verifier

Responsabilités :

- recalcul des hashes ;
- vérification des chaînes ;
- détection des trous ;
- détection des duplications ;
- détection des modifications.

### P0-R4 — Policy/Firewall Core

Responsabilités :

- décision ;
- reason code ;
- policy version ;
- redaction ;
- block ;
- evidence emission.

### P0-R5 — Replay Engine

Responsabilités :

- reconstruction ;
- validation de séquence ;
- comparaison d'états ;
- preuve de cohérence.

## 8. Ce qui doit rester Python

### P0-P1

- agents de démonstration ;
- attacker agent ;
- defender agent ;
- orchestrateur ;
- connecteurs LLM ;
- scénarios d'attaque ;
- génération de données de test ;
- MCP adapter ;
- API HTTP ;
- UI/demo backend ;
- métriques ;
- scripts de benchmark ;
- export de rapports.

Python est donc la couche d'innovation rapide ; Rust est la couche de confiance.

## 9. Migration de l'existant

### Agent Memory Protocol

Conserver le protocole externe et remplacer progressivement son stockage critique par les primitives Rust.

L'objectif n'est pas de casser l'API existante mais de déplacer le mécanisme de persistance/intégrité sous-jacent.

### AgentChannel

Conserver l'idée de communication sémantique agent-agent.

Ajouter dans chaque message :

- sender_agent_id ;
- receiver_agent_id ;
- message_id ;
- parent_event_id ;
- content hash ;
- policy decision ;
- evidence reference.

Le contenu humain ne doit pas être exigé pour le fonctionnement interne.

### MCP

Conserver le serveur Python comme adaptateur de compatibilité.

Intercaler Rust avant toute action sensible :

**MCP → Python adapter → Rust policy → tool → Rust evidence → Python response**

### Blockchain

Pour la compétition, ne pas faire de la blockchain le centre de la démo.

La primitive prioritaire devient :

**tamper-evident event ledger + provenance + evidence**

La blockchain peut rester un ancrage externe ou une extension future.

C'est cohérent avec R590 : la proposition compétitive doit être une infrastructure de défense et de preuve, pas une démonstration de fonctionnalités blockchain.

## 10. Cahier des charges Guardian — MVP compétition

### Fonctionnalités P0

| ID | Fonction | Critère d'acceptation |
|---|---|---|
| G-01 | Enregistrer action agent | événement signé/hashé |
| G-02 | Identifier agent | AgentId vérifiable |
| G-03 | Tracer mémoire | mutation reliée à l'agent |
| G-04 | Tracer outil | ToolCall relié à l'événement parent |
| G-05 | Détecter injection | attaque détectée dans scénario connu |
| G-06 | Détecter poisoning | contamination mémoire visible |
| G-07 | Bloquer exfiltration | firewall = BLOCK |
| G-08 | Produire preuve | EvidenceId + hash |
| G-09 | Rejouer incident | graphe reconstruit |
| G-10 | Vérifier intégrité | tampering détecté |
| G-11 | Vue défenseur | timeline lisible |
| G-12 | Export incident | paquet de preuve reproductible |

### Fonctionnalités P1

- AgentChannel instrumenté ;
- MCP sécurisé ;
- redaction ;
- scoring de risque ;
- comparaison de politiques ;
- export JSON/HTML ;
- signature cryptographique ;
- mode multi-agent.

### Hors scope compétition

- tokenomics complète ;
- minage ;
- réseau blockchain public ;
- économie ARTCB ;
- UI administrative complète ;
- migration intégrale de tous les modules historiques.

## 11. Démonstration cible

La démonstration doit rester extrêmement narrative.

### Scénario

**4 agents → attaque → contamination → propagation → tentative d'exfiltration → blocage → replay**

Exemple conceptuel :

**Agent A → événement 1024 → mémoire contaminée → Agent B → MCP tool X → tentative d'exfiltration → Firewall BLOCK**

Puis :

**REPLAY INCIDENT**

Le système montre :

1. l'entrée malveillante ;
2. la mutation mémoire ;
3. la propagation ;
4. l'appel d'outil ;
5. la décision du firewall ;
6. le blocage ;
7. la preuve ;
8. le graphe causal.

Cette démonstration correspond directement au scénario recommandé par R590. fileciteturn0file0L51-L65

## 12. Métriques de compétition

Les métriques doivent être orientées défense.

### M1 — Detection rate

Attaques détectées / attaques exécutées.

### M2 — Containment rate

Attaques bloquées avant exfiltration / attaques détectées.

### M3 — Provenance completeness

Événements reconstructibles / événements attendus.

### M4 — Replay fidelity

États reconstruits conformes / états attendus.

### M5 — Evidence integrity

Preuves vérifiables / preuves produites.

### M6 — False positive rate

Blocages légitimes / actions légitimes.

### M7 — Latency overhead

Temps supplémentaire imposé par la défense.

La présentation finale doit privilégier ces métriques plutôt que le nombre de fichiers, lignes de code ou fonctionnalités.

## 13. Architecture de dépôt cible

Le dépôt vide doit être organisé autour de la compétition et non reproduire toute la structure historique.

Structure conceptuelle :

- `reports/` ou `rapports/` : uniquement rapports d'audit et migration ;
- `rust/` : Security Core ;
- `python/` : agents, orchestration et intégrations ;
- `tests/` : tests unitaires, intégration et adversariaux ;
- `scenarios/` : attaques reproductibles ;
- `evidence/` : uniquement artefacts de test non sensibles ;
- `docs/` : architecture et protocole ;
- `.github/` : CI.

**Important :** les logs d'exécution ne doivent jamais être poussés dans le dépôt.

## 14. Stratégie de migration : ne pas réécrire tout ARTCB

### Processus

Une migration « big bang » consisterait à réécrire l'ensemble du dépôt historique en Rust.

### Problème

Elle consommerait le temps de compétition sans augmenter proportionnellement la valeur démontrée.

### Solution

Utiliser une migration par frontière de confiance :

**Phase A : conserver Python**

→ instrumenter

→ identifier les événements

→ définir les contrats

**Phase B : Rust shadow mode**

→ Rust observe les événements sans décider

→ comparaison Python/Rust

**Phase C : Rust enforcement**

→ Rust prend les décisions de sécurité

**Phase D : retrait progressif des anciennes primitives**

→ uniquement après tests équivalents.

## 15. Roadmap de développement

### Étape 0 — Baseline

Livrables :

- inventaire ;
- contrats ;
- threat model ;
- scénario d'attaque ;
- métriques de référence.

### Étape 1 — Rust Event Core

Livrables :

- événement ;
- hash ;
- append ;
- idempotence ;
- persistance ;
- vérification.

### Étape 2 — Provenance

Livrables :

- graphe causal ;
- agent lineage ;
- memory lineage ;
- tool lineage.

### Étape 3 — Firewall

Livrables :

- policy ;
- decision ;
- block/redact ;
- evidence.

### Étape 4 — Replay

Livrables :

- incident package ;
- reconstruction ;
- integrity verification.

### Étape 5 — Python adapter

Livrables :

- module PyO3 ;
- API Python ;
- tests cross-language.

PyO3 est adapté à cette architecture : il permet d'exposer des fonctions et classes Rust comme objets Python natifs. citeturn0search3turn0search5turn0search7

### Étape 6 — Agents adversariaux

Livrables :

- attacker ;
- poisoned memory ;
- malicious tool;
- exfiltration scenario.

### Étape 7 — MCP instrumentation

Livrables :

- ToolCall event ;
- policy check ;
- evidence ;
- replay.

### Étape 8 — Demo

Livrables :

- scénario unique ;
- UI défenseur ;
- timeline ;
- replay ;
- métriques.

## 16. Roadmap compétition — priorité absolue

Compte tenu de la proximité de l'événement, la priorité n'est pas « terminer ARTCB ».

La priorité est :

**faire fonctionner une boucle complète et crédible.**

Ordre impératif :

1. Event ;
2. Provenance ;
3. Attack ;
4. Detection ;
5. Block ;
6. Evidence ;
7. Replay ;
8. UI ;
9. Metrics ;
10. polish.

Si une fonctionnalité ne renforce pas cette boucle, elle est secondaire.

## 17. Critères de sortie avant présentation

Le MVP est considéré comme démontrable seulement si :

- une attaque réelle de scénario est exécutée ;
- au moins deux agents participent à la propagation ;
- une mutation mémoire est enregistrée ;
- un appel d'outil est enregistré ;
- une sortie dangereuse est bloquée ;
- une preuve est produite ;
- l'intégrité de la preuve est vérifiée ;
- l'incident est rejoué ;
- le graphe causal est lisible ;
- aucune donnée secrète n'apparaît dans les logs ;
- les tests critiques passent ;
- le scénario peut être relancé depuis zéro.

## 18. Risques critiques

### R1 — Sur-migration

**Risque :** tenter de migrer tout ARTCB.

**Réponse :** migration P0 Guardian uniquement.

### R2 — Complexité Rust

**Risque :** perdre le temps de compétition dans le langage.

**Réponse :** API Rust minimale, peu de dépendances, PyO3/Maturin, tests très ciblés.

### R3 — Démo non reproductible

**Risque :** dépendance à un LLM externe ou à un réseau.

**Réponse :** scénario déterministe local avec LLM optionnel.

### R4 — Preuve insuffisante

**Risque :** montrer une détection sans pouvoir démontrer la causalité.

**Réponse :** Evidence Archive séparée de Security Views.

### R5 — MCP trop ouvert

**Risque :** un outil malveillant contourne la défense.

**Réponse :** chaque ToolCall passe par la policy Rust.

### R6 — Logs sensibles

**Risque :** secrets ou données privées dans le dépôt.

**Réponse :** redaction, .gitignore, artefacts locaux, aucun log brut poussé.

## 19. Décisions à verrouiller avant développement

Les points suivants doivent être considérés comme des décisions d'architecture, pas comme des détails de dernière minute :

1. format canonique Event ;
2. algorithme de hash ;
3. mécanisme de signature ;
4. format Evidence ;
5. identifiant AgentId ;
6. modèle de policy ;
7. sémantique BLOCK/REDACT/ALLOW/ESCALATE ;
8. modèle de replay ;
9. contrat Python ↔ Rust ;
10. versionnement des événements ;
11. stratégie de persistance ;
12. scénario d'attaque officiel ;
13. métriques officielles ;
14. frontière exacte du P0.

## 20. Conclusion

La migration recommandée n'est pas :

**« réécrire ARTCB en Rust »**.

Elle est :

**« extraire le noyau de confiance nécessaire à ARTCB Guardian et le rendre vérifiable en Rust, tout en conservant Python pour l'agentique et l'expérimentation »**.

La cible est donc :

**Python = agents, attaques, orchestration, MCP, expérimentation.**

**Rust = événements, intégrité, provenance, policy, firewall, replay, evidence.**

Cette séparation transforme les briques historiques ARTCB en un produit beaucoup plus lisible pour Secure Horizons :

**Detect → Contain → Reconstruct → Prove.**

Le choix Track 2 reste la décision stratégique de référence : **9,5/10**. fileciteturn0file1L16-L23

Aucune modification du dépôt source `vgactech/artcb` n'est effectuée dans le cadre de ce rapport. Le dépôt cible `ARTCB-TERMINATOR` reste également sans code applicatif à ce stade ; le présent travail constitue le cahier des charges et la roadmap nécessaires avant implémentation.
