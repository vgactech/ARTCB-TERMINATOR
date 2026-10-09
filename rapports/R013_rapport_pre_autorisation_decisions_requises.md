# R013 — Rapport pré-autorisation : état réel, décisions requises et présentation pour validation

**Date :** 2026-10-09  
**Dépôt cible :** `vgactech/ARTCB-TERMINATOR`  
**Emplacement autorisé :** `rapports/` uniquement  
**Objet :** présenter à l'utilisateur l'état réel du projet, les deux décisions bloquantes et le résumé de ce qui sera construit — avant toute autorisation de coder  
**Sources :** R001–R012 lus intégralement + inventaire réel du clone local `vgactech/artcb`  
**Aucun code modifié. Aucun test exécuté. Aucune implémentation réalisée.**

---

## Ce que ce rapport fait

Ce rapport est le document que tu dois lire, corriger et valider avant que le développement puisse commencer. Il contient :

1. Ce qui existe réellement dans le code (pas ce qui est promis, ce qui est là)
2. Ce qui doit être construit (uniquement ce qui manque)
3. Les deux décisions bloquantes à prendre
4. Le plan de construction proposé

---

## PARTIE 1 — CE QUI EXISTE RÉELLEMENT

### Le dépôt `vgactech/artcb` — chiffres réels

| Élément | Valeur réelle |
|---|---|
| Fichiers trackés | 3 051 |
| Fichiers Python | 878 |
| Fichiers C/H | 30 |
| Tests | 295 |
| Rapports historiques | 667 |
| Taille | 27 GB |
| Dernier commit audité | `0cc5db744142` (2026-10-08) |

### Les composants qui existent et fonctionnent

**Composant 1 — Journal d'exécution agent (`AgentRunLedger`)**

Fichier : `src/artcb/trace/agent_run.py`

Ce composant enregistre chaque action d'un agent avec un identifiant, un hash de l'entrée, un hash de la sortie et un hash de chaîne calculé comme suit :

`hash_i = SHA256(événement_i + hash_précédent)`

C'est-à-dire que si on modifie un événement passé, le hash de tous les suivants change. La falsification est détectable.

Ce qui manque par rapport aux spécifications Guardian :
- Le format de sérialisation utilise `sort_keys=True` (Python) mais pas JCS (RFC 8785)
- Il n'y a pas de préfixe de domaine (`ARTCB-GUARDIAN-EVENT-V1`) dans le calcul du hash
- Il n'y a pas d'identifiant UUIDv7
- Il n'y a pas de schéma JSON Schema 2020-12

---

**Composant 2 — Firewall de divulgation (`disclosure_firewall.py`)**

Fichier : `src/artcb/security/disclosure_firewall.py`

Ce composant existe, est testé et est opérationnel. Il prend une décision selon deux paramètres :
- Le niveau de sensibilité de la donnée (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED, CLIENT_RESTRICTED, DEFENSE_CRITICAL)
- L'audience destinataire (PUBLIC_EXTERNAL, INTERNAL_TEAM, OPERATOR, OWNER, DEFENSE_CLEARED)

Il produit l'une des décisions suivantes : `ALLOW`, `SANITIZE`, `REVIEW`, `BLOCK`.

Le principe fail-closed est implémenté : si la classification est inconnue (`UNKNOWN`), la décision est automatiquement `BLOCK`.

Ce qui manque :
- Chaque décision BLOCK ne produit pas encore un identifiant de preuve (`EvidenceId`)
- Le firewall n'est pas encore en Rust (il est en Python)
- Les termes `SANITIZE` et `REVIEW` diffèrent des spécifications Guardian qui utilisent `REDACT` et `ESCALATE`

---

**Composant 3 — Canal agent-agent (`AgentChannel`)**

Fichier : `src/artcb/memory/agent_channel.py`

Ce composant permet à deux agents de communiquer en binaire pur, sans texte humain, via des `ConceptID`. Agent A encode un concept en binaire, l'envoie à Agent B qui le décode depuis son propre stockage.

Ce qui manque pour Guardian :
- L'enveloppe de sécurité n'est pas encore là : pas d'identifiant de l'agent émetteur, pas de hash du contenu, pas de décision de politique, pas de référence de preuve
- Les messages ne sont pas encore des événements dans le ledger

---

**Composant 4 — WAL C (Write-Ahead Log)**

Fichier : `src/c/libartcb_wal.c/.h`

Ce composant écrit des entrées sur disque avec un magic number (`0x41574C21`), une version, un CRC32, et un fsync. En cas de crash, les entrées peuvent être relues et rejouées.

Ce qui manque :
- CRC32 ≠ preuve cryptographique. Un CRC détecte les corruptions accidentelles mais ne résiste pas à une modification intentionnelle
- Il n'y a pas de hash SHA-256 enchaîné entre les entrées
- Ce composant sera remplacé par le Rust Durable Event Store

---

**Composant 5 — Serveur MCP**

Fichier : `src/artcb/mcp/server.py`

Le serveur MCP est opérationnel en stdio et HTTP. Il expose des outils (`tools/`), des ressources (`resources/`) et des prompts (`prompts/`). Quand un agent appelle un outil via `tools/call`, l'outil est exécuté.

Ce qui manque :
- Chaque appel d'outil n'est pas enregistré dans le ledger
- Aucun contrôle de politique Rust n'est appliqué avant l'exécution
- Il n'y a pas de preuve produite après chaque appel

---

**Composant 6 — Graphe IR et provenance (`IRGraph`)**

Fichier : `src/artcb/ir/models.py`

Ce composant représente un graphe de concepts avec un checksum. Il sert de base à la communication binaire entre agents.

Ce qui manque :
- Un checksum de graphe n'est pas un graphe causal. Il ne dit pas quel agent a produit quoi, à partir de quel événement, pour quelle raison
- Les relations causales typées (CREATED, READ, SENT, BLOCKED, etc.) définies dans R002 ne sont pas encore là

---

**Composant 7 — Liaison TPM (`node_tpm_binding.py`)**

Fichier : `src/artcb/security/node_tpm_binding.py`

Ce composant lie un identifiant de nœud à un TPM via une signature hybride Ed25519 + ML-DSA-65. Cinq niveaux de garantie matérielle sont définis (A=TPM physique, B=vTPM, C=TEE, D=HSM, E=logiciel uniquement).

Ce qui manque :
- L'attestation distante avec nonce frais (challenge/response) est documentée comme non implémentée dans le code lui-même et dans le rapport R462

---

**Composant 8 — Cryptographie post-quantique**

Fichiers : `src/artcb/crypto/pqc.py`, `crypto/hybrid.py`, `crypto/kem.py`

ML-DSA-65 et ML-KEM-768 (NIST PQC 2024) sont implémentés avec fallback automatique vers Ed25519 si liboqs n'est pas disponible. FHE Paillier opérationnel pour la biométrie.

---

**Composant 9 — 295 tests existants**

Tests présents : unitaires, E2E multi-nœuds, adversariaux, TPM, biométriques, FHE, PQC, PBFT, forensic. Parmi les tests importants : `test_r460_node_tpm_binding.py`, `test_r582_disclosure_firewall.py`, `test_r451_forensic_event_ledger.py`, `test_e2e262_evidence_replica.py`.

Ces tests couvrent le code existant. Ils ne couvrent pas encore le code Guardian qui n'est pas encore écrit.

---

## PARTIE 2 — CE QUI DOIT ÊTRE CONSTRUIT

Voici uniquement ce qui manque. Rien d'autre.

| ID | Composant à construire | Dans quel langage | Pourquoi |
|---|---|---|---|
| C-01 | Rust Event Ledger | Rust | Remplace `AgentRunLedger` Python avec JCS + préfixe domaine + UUIDv7 |
| C-02 | Rust Durable Event Store | Rust | Remplace WAL C avec SHA-256 enchaîné à la place du CRC |
| C-03 | Provenance Engine | Rust | Remplace `IRGraph` checksum avec graphe causal typé |
| C-04 | Enveloppe AgentChannel | Rust (intégrité) + Python (protocole) | Ajoute la sécurité au canal existant |
| C-05 | Rust Policy/Firewall Core | Rust | Migre les décisions critiques vers Rust + réconcilie la nomenclature |
| C-06 | Replay Engine | Rust | Construit le replay R0–R4 avec vérification de hash |
| C-07 | MCP ToolCall instrumenté | Python (adaptateur) + Rust (politique) | Enregistre chaque appel d'outil dans le ledger |
| C-08 | Binding PyO3 | Rust + Python | Expose les fonctions Rust comme module Python |

Ces 8 composants sont les seuls à construire pour la démo Guardian Track 2.

---

## PARTIE 3 — LES DEUX DÉCISIONS BLOQUANTES

### DÉCISION 1 — La nomenclature des actions de sécurité

**Situation actuelle dans le code :**

Le firewall existant utilise ces 4 termes :
- `ALLOW` — laisser passer
- `SANITIZE` — nettoyer la donnée
- `REVIEW` — soumettre à vérification
- `BLOCK` — bloquer

**Situation dans les spécifications Guardian (R002/R003) :**

Les rapports Guardian utilisent ces 4 termes :
- `ALLOW` — laisser passer
- `BLOCK` — bloquer
- `REDACT` — masquer une information sensible
- `ESCALATE` — transmettre à un niveau supérieur

**Le problème :**

Ce ne sont pas des synonymes exacts.

| Terme actuel | Terme Guardian | Sont-ils équivalents ? |
|---|---|---|
| `ALLOW` | `ALLOW` | OUI — identique |
| `BLOCK` | `BLOCK` | OUI — identique |
| `SANITIZE` | `REDACT` | NON — SANITIZE neutralise une donnée dangereuse ; REDACT masque une information confidentielle |
| `REVIEW` | `ESCALATE` | NON — REVIEW demande une vérification interne ; ESCALATE transfère à un niveau supérieur |

**Deux options pour toi :**

**Option A — Garder les quatre termes existants ET ajouter REDACT et ESCALATE**

Résultat : 6 termes au total (ALLOW, BLOCK, SANITIZE, REVIEW, REDACT, ESCALATE). Chacun a une sémantique précise et distincte. Plus expressif, mais plus complexe à implémenter et à tester.

**Option B — Remplacer SANITIZE→REDACT et REVIEW→ESCALATE**

Résultat : 4 termes (ALLOW, BLOCK, REDACT, ESCALATE). Aligné sur les spécifications Guardian. Nécessite de migrer le firewall existant. Plus simple pour la démo.

**Ma recommandation technique :** Option A pour le projet complet, Option B pour la démo Guardian (plus simple, directement conforme aux specs, et les 295 tests du firewall existant devront être mis à jour de toute façon lors de la migration Rust).

**→ Décision A : quelle option choisis-tu ?**

---

### DÉCISION 2 — Autorisation de démarrer le code

**Ce qui sera construit si tu autorises :**

Les 8 composants de la Partie 2, dans cet ordre :

1. Rust Event Ledger (C-01) — un événement, un hash, un parent, une persistance
2. Rust Durable Event Store (C-02) — écriture durable, récupération après crash
3. Provenance Engine (C-03) — graphe causal, relations typées
4. Enveloppe AgentChannel (C-04) — sécuriser le canal existant
5. Policy/Firewall Core Rust (C-05) — décisions Rust avec EvidenceId
6. Replay Engine (C-06) — reconstruction et vérification
7. MCP instrumenté (C-07) — chaque tools/call = événement ledger
8. Binding PyO3 (C-08) — pont Python↔Rust

**Ce qui ne sera PAS touché :**

- Le dépôt `vgactech/artcb` — aucune modification
- Le code existant de Guardian non encore créé — il sera créé dans TERMINATOR
- Les 295 tests existants — ils restent en place

**Ce que signifie concrètement l'autorisation :**

Passer de `rapports/` uniquement → autoriser la création de code dans `vgactech/ARTCB-TERMINATOR` hors du dossier `rapports/`.

**→ Décision B : OUI ou NON ?**

---

## PARTIE 4 — LE PLAN DE CONSTRUCTION (si tu dis OUI)

### Phase 1 — Fondations (Composants C-01 et C-02)

Construire le noyau Rust minimal :
- Un type `Event` avec tous les champs définis dans R005
- La sérialisation JCS conforme RFC 8785
- Le calcul du hash avec préfixe de domaine `ARTCB-GUARDIAN-EVENT-V1`
- Le stockage append-only avec durabilité (fsync)
- La récupération après crash

Preuve de fin : les vecteurs de test golden de R006 (F-001 à F-020) passent dans Rust ET Python.

### Phase 2 — Provenance (Composant C-03)

- Graphe causal avec relations CREATED, READ, SENT, BLOCKED, ALLOWED, DERIVED_FROM
- Reconstruction d'un incident de A jusqu'à la décision finale

Preuve de fin : partir du résultat dangereux et remonter jusqu'à l'agent initial.

### Phase 3 — Firewall Rust (Composant C-05)

- Décisions ALLOW/BLOCK/REDACT/ESCALATE (selon la nomenclature retenue)
- Chaque BLOCK produit un `EvidenceId` dans le ledger

Preuve de fin : une tentative d'exfiltration simulée produit BLOCK + EvidenceId + entrée ledger.

### Phase 4 — MCP et AgentChannel (Composants C-04 et C-07)

- Chaque `tools/call` = événement dans le ledger
- AgentChannel avec enveloppe de sécurité

Preuve de fin : un appel d'outil malveillant simulé est bloqué et visible dans le replay.

### Phase 5 — Replay et Binding (Composants C-06 et C-08)

- Replay R0–R4 avec vérification de hash
- Module PyO3 exposant les 8 fonctions stables à Python

Preuve de fin : modifier un événement historique → le replay détecte la divergence.

### Phase 6 — Démonstration complète

Le scénario de 6 minutes de R003 :
- 0:00 — État nominal, agents identifiés
- 0:45 — Injection d'un document hostile
- 1:30 — Propagation de A vers B
- 2:15 — Tentative d'exfiltration → BLOCK
- 3:00 — Preuve : règle, version, hashes
- 4:00 — Replay : reconstruction depuis l'événement initial
- 5:00 — Test d'altération : modifier un événement → détection

---

## PARTIE 5 — CE QUE TU DOIS VÉRIFIER AVANT DE RÉPONDRE

Avant de donner tes décisions, vérifie les points suivants :

1. **R011 et R012 sur GitHub** — les rapports sont accessibles aux liens suivants :
   - R011 : https://github.com/vgactech/ARTCB-TERMINATOR/blob/main/rapports/R011_audit_complet_reconciliation_r001_r010_plan_fermeture.md
   - R012 : https://github.com/vgactech/ARTCB-TERMINATOR/blob/main/rapports/R012_inventaire_artcb_cartographie_27_couches_code_reel.md

2. **La nomenclature du firewall** — lis la Décision 1 et choisis A ou B.

3. **L'autorisation de coder** — lis la Décision 2 et réponds OUI ou NON.

4. **Le plan de construction** — lis la Partie 4 et signale si quelque chose ne correspond pas à ce que tu veux.

---

## PARTIE 6 — CE QUI N'A PAS ÉTÉ FAIT ET DOIT RESTER OUVERT

Ces éléments sont identifiés comme manquants. Ils ne seront pas résolus par le seul fait d'autoriser le développement. Ils nécessitent des étapes séparées.

| Élément | Pourquoi ouvert |
|---|---|
| Attestation TPM distante (nonce frais) | Non implémentée selon R462 et confirmée dans le code |
| Digest golden F-001 recalculé par JCS conforme | Pas encore exécuté — action disponible maintenant |
| Questions Q9–Q15 de R008 | Objectifs de performance, certification, retour arrière — non documentés |
| Espace de test `SPECIal` | Non créé — à faire localement |
| Identification de la clé USB | Non vérifiée depuis cette session |

---

## Résumé en deux lignes

**Ce qui existe :** le code source, les composants de base, 295 tests, le firewall, le WAL, l'IR, le MCP — tout cela existe déjà dans `artcb`.

**Ce qui manque :** la couche Rust de confiance, la sérialisation JCS, le graphe causal, l'instrumentation MCP et le replay vérifiable — c'est ce que Guardian doit apporter.

---

**Aucun code modifié. Aucun test exécuté. Ce rapport attend tes corrections et tes décisions.**
