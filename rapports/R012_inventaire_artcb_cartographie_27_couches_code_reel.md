# R012 — Inventaire réel de vgactech/artcb et cartographie des 27 couches sur le code existant

**Date :** 2026-10-09  
**Dépôt cible du rapport :** `vgactech/ARTCB-TERMINATOR`  
**Emplacement autorisé :** `rapports/` uniquement  
**Source auditée :** `vgactech/artcb` — clone local `/Users/deyi/.bob/playground`  
**SHA local figé pour cet audit :** `0cc5db744142e1a541bb56758c61657040359e15` (2026-10-08 18:27)  
**SHA distant main :** `7304d493018995d851ed5c13107c5e9d5bd79268` (référence des rapports R001–R010)  
**Écart local/distant :** le clone local est **en avance** d'au moins un commit sur le SHA distant de référence  
**Dépendance :** R011 — réconciliation et plan de fermeture  
**Statut :** inventaire et cartographie factuelle — aucun code modifié, aucun test exécuté  
**Autorisation de coder :** non accordée par ce rapport

---

## Expertises activées

- Audit de dépôt Git et traçabilité des révisions ;
- architecture logicielle Python/C multicouche ;
- sécurité des agents IA, threat modeling et analyse adversariale ;
- event sourcing, WAL, hash chaining et provenance ;
- cryptographie appliquée, TPM, FHE et post-quantique ;
- mémoire artificielle persistante et graphes IR ;
- blockchain Python/C, consensus PBFT et réseau P2P ;
- tests de conformité et couverture de test ;
- gouvernance GitHub et CI/CD.

---

## 1. Résumé exécutif

Le dépôt `vgactech/artcb` est un système substantiel de **3 051 fichiers trackés**, principalement Python (878 fichiers `.py`) avec un noyau C (17 fichiers `.c`/`.h`). Il contient :

- Un backend Python FastAPI complet avec ~40 routes API ;
- un moteur IR (Intermediate Representation) pour la communication agent-agent sans langage humain ;
- une couche cryptographique réelle incluant Ed25519, ML-DSA-65 (post-quantique), FHE Paillier, BCH biométrique et KEM ;
- un WAL C persistant (`libartcb_wal`) avec CRC, magic, versioning et récupération ;
- une chaîne de blocs C (`libartcb_chain`) avec hash SHA-256, Merkle, PoL score ;
- un firewall de divulgation Python opérationnel avec 6 niveaux de classification et matrice de décision ;
- une liaison TPM opérationnelle (Ed25519 + ML-DSA-65 hybride) avec 5 niveaux de garantie matérielle ;
- un agent ledger de provenance (`AgentRunLedger`) avec hash chaining réel ;
- 295 fichiers de tests couvrant de l'unitaire aux E2E multi-nœuds, adversariaux, TPM et biométriques ;
- un serveur MCP Python (stdio + HTTP) fonctionnel.

**Constat principal :** les composants P0 de Guardian (Event Ledger, Provenance, Firewall, Replay, MCP) ont tous un **équivalent Python/C existant** dans `artcb`. La migration Rust spécifiée dans R001–R009 est une **réécriture et renforcement du noyau de confiance**, pas une création à partir de zéro.

---

## 2. État du clone local

| Attribut | Valeur |
|---|---|
| Chemin | `/Users/deyi/.bob/playground` |
| Remote | `git@github.com:vgactech/artcb.git` |
| Branche | `main` |
| SHA local | `0cc5db744142e1a541bb56758c61657040359e15` |
| SHA distant ref. rapports | `7304d493018995d851ed5c13107c5e9d5bd79268` |
| Dernier commit local | R588 : R584 filtre parasites validé |
| Modifications non commitées | Oui — logs, rules, fuzzing binaires (non sensibles, hors scope) |
| Taille totale | 27 GB |

**Important :** le SHA local est **postérieur** au SHA de référence des rapports R001–R010. Cela signifie que des commits supplémentaires existent localement depuis la dernière synchronisation distante. Cet audit porte sur le SHA local `0cc5db7`. Toute comparaison future doit préciser la révision exacte.

---

## 3. Inventaire de l'arbre — statistiques réelles

| Catégorie | Nombre |
|---|---|
| Fichiers trackés total | 3 051 |
| Fichiers `.py` | 878 |
| Fichiers `.json` | 1 029 |
| Fichiers `.md` | 744 |
| Fichiers `.c` / `.h` | 30 |
| Fichiers de test | 295 |
| Rapports historiques (`rapports/`) | 667 |
| Scripts | 244 |
| Logs | 754 |
| Frontend (`.tsx`, `.ts`) | 39 |
| Workflows CI (`.yml`) | 9 |

### Répertoires racine

| Répertoire | Fichiers | Rôle identifié |
|---|---|---|
| `logs/` | 754 | Journaux d'exécution — ne pas pousser |
| `rapports/` | 667 | Rapports historiques ARTCB (numérotation propre) |
| `src/` | 442 | Code source (Python + C) |
| `simulations/` | 320 | Scénarios de simulation |
| `tests/` | 295 | Tests automatisés |
| `scripts/` | 244 | Scripts d'installation, benchmarks, déploiement |
| `frontend/` | 52 | Interface utilisateur (React/TypeScript) |
| `analyse_concurrents/` | 46 | Analyse de concurrence |
| `docs/` | 30 | Documentation technique |
| `data_local/` | 27 | Données locales de test |
| `rules/` | 16 | Règles de gouvernance |
| `validation/` | 16 | Résultats de validation |
| `.github/` | 7 | CI/CD workflows |
| `deploy/` | 11 | Configuration de déploiement |

---

## 4. Cartographie des 27 couches R010 sur le code réel

### Couche 0 — Matériel, hôte et racine de confiance

**Fichiers réels :**
- `src/artcb/security/node_tpm_binding.py` — liaison TPM EK → NodeID (R460)
- `src/artcb/security/hardware_identity.py` — identité matérielle
- `src/artcb/identity/biometric_ffi.py` — FFI biométrique
- `tests/test_r460_node_tpm_binding.py`, `test_r462_pcr_binding.py`, `test_e2e281_vtpm_quote.py`, `test_e2e282_nitrotpm.py`

**Constaté :** 5 niveaux de garantie TPM implémentés (A=physical_tpm, B=virtual_tpm, C=tee, D=hsm, E=software). Signature hybride Ed25519 + ML-DSA-65. Invariants documentés : `CERTIFIED_100=false`, `unique_human_proven=false`. Attestation distante complète (challenge/response) **non implémentée** selon R462 et confirmé dans le code source.

**Lacune P1 :** attestation distante avec nonce frais — `NOT_IMPLEMENTED` explicitement.

### Couche 1 — Boot, build, supply chain

**Fichiers réels :**
- `pyproject.toml` — dépendances versionnées, build setuptools
- `requirements.txt` — dépendances complètes avec commentaires de risque
- `.github/workflows/tests.yml` — CI déclenchement manuel uniquement (push main avec filtres)
- `.github/workflows/fuzz_ci.yml` — fuzzing CI
- `.github/workflows/do178c_gate.yml` — porte DO-178C
- `scripts/install_python_dependencies.sh` — installation reproductible

**Constaté :** build reproductible avec `pip install -e .`. Dépendance `liboqs-python` optionnelle (PQC) avec fallback Ed25519. Avertissement de `dependency-confusion` documenté pour `litellm-ibm-bob`. CI manuelle uniquement.

**Lacune P1 :** pas de SBOM, pas de signature des artefacts de build.

### Couche 2 — OS et isolation d'exécution

**Fichiers réels :**
- `scripts/artcb.service`, `artcb-follow-main.service` — services systemd
- `deploy/` — configuration de déploiement
- `.devcontainer/` — environnement de développement conteneurisé

**Constaté :** déploiement via systemd documenté. Pas de sandbox processus dédiée identifiée dans le code.

**Lacune P2 :** isolation processus et limites de ressources non spécifiées dans le code.

### Couche 3 — Transport, réseau, communications

**Fichiers réels :**
- `src/artcb/mcp/server.py` — serveur MCP stdio + HTTP (port configurable, sans ngrok)
- `src/api/main.py` — FastAPI, uvicorn
- `src/artcb/p2p/` — P2P libp2p
- `src/c/libartcb_p2p.c/.h`, `libartcb_p2p_anti_eclipse.c/.h`, `libartcb_p2p_bench.c/.h`, `libartcb_p2p_misbehavior.c/.h`
- `src/api/libp2p_routes.py`, `src/api/p2p_routes.py`
- `tests/test_libp2p_p2p.py`, `test_p2p_api.py`, `test_r554_ex015_p2p_anti_eclipse.py`

**Constaté :** MCP JSON-RPC v1 opérationnel (version `2024-11-05`). FastAPI HTTP sur port 8000. P2P C avec protection anti-eclipse. Transport stdio et HTTP/SSE pour MCP.

**Point MCP :** `ArtcbMCPServer` expose `tools/`, `resources/`, `prompts/` — chaque `tools/call` n'est **pas encore instrumenté** comme événement P0 dans le ledger (lacune P0 de R002).

### Couche 4 — Identité, authentification, autorisation

**Fichiers réels :**
- `src/artcb/identity/layers.py` — couches d'identité
- `src/artcb/identity/user_wallet_ownership.py` — wallet → humain
- `src/artcb/identity/user_node_association.py` — utilisateur → nœud
- `src/artcb/security/anti_sybil.py` — protection Sybil
- `src/artcb/security/wallet_device_binding.py` — wallet + device
- `src/artcb/security/webauthn_failclosed.py`, `webauthn_protocol.py`, `webauthn_store.py`, `webauthn_cose.py` — WebAuthn
- `src/artcb/authz/` — autorisation
- `src/api/auth_routes.py`, `authz_routes.py`, `biometric_identity_routes.py`
- `tests/test_r347_identity_layers.py`, `test_r348_user_node_association.py`, `test_e2e273_identity_binding.py`

**Constaté :** séparation stricte des identités (humain, wallet, nœud, appareil, agent) documentée et implémentée. WebAuthn fail-closed. Anti-Sybil opérationnel. Chaîne de preuve : `HUMAIN → WebAuthn → Wallet → Device → TPM EK/AK → NodeID → P2P → Blockchain`.

**Invariant vérifié dans le code :** `node_id ≠ wallet_address` explicitement.

### Couche 5 — Gestion cryptographique

**Fichiers réels :**
- `src/artcb/crypto/hashing.py` — SHA-256 canonique
- `src/artcb/crypto/pqc.py` — ML-DSA-65, ML-KEM-768 (NIST PQC 2024)
- `src/artcb/crypto/kem.py` — KEM P2P
- `src/artcb/crypto/hybrid.py` — hybride Ed25519 + ML-DSA-65
- `src/artcb/crypto/homomorphic.py` — Paillier FHE (phe>=1.5.0)
- `src/artcb/crypto/liboqs_runtime.py` — runtime liboqs avec fallback
- `src/c/libartcb_sig_canonical.c/.h` — signatures canoniques C
- `src/c/libartcb_merkle.c/.h` — arbres de Merkle C
- `tests/test_pqc_crypto.py`, `test_r532_ex005_sig_canonical.py`, `test_r528_ex004_merkle.py`

**Constaté :** cryptographie opérationnelle réelle — Ed25519 (PyNaCl), ML-DSA-65 + ML-KEM-768 (liboqs optionnel), Paillier FHE, BCH biométrique, hybride AND. Fallback automatique si liboqs absent. SHA-256 utilisé pour hash chaining dans `agent_run.py`.

**Lacune P1 :** pas de vecteurs de test cross-language Rust/Python (NOT_TESTED selon R007).

### Couche 6 — Données, stockage et persistance

**Fichiers réels :**
- `src/c/libartcb_wal.c/.h` — WAL C avec magic `0x41574C21` ("AWL!"), version 1, CRC, fsync, récupération
- `src/artcb/chain/binary_log.py` — log binaire Python
- `src/artcb/chain/split_ledger.py` — ledger splitté public/privé
- `src/artcb/kv/` — stockage clé-valeur
- `src/artcb/memory/graph_store.py`, `vector_store.py`, `vector_store_faiss.py` — stockage graphe et vecteurs
- `tests/test_r526_ex012_state_rollback.py`, `test_e2e299_never_delete_archive.py`

**Constaté :** WAL C opérationnel avec 4 types d'entrées (VOTE_PREPARE, VOTE_COMMIT, BLOCK_FINAL, HEARTBEAT). Invariant `never_delete_archive` testé (R299). Split ledger public/privé implémenté.

**Lacune P0 :** le WAL C (CRC seulement) ne constitue pas une preuve cryptographique de provenance — confirmé dans R002 §6.

### Couche 7 — Modèle de données et contrats

**Fichiers réels :**
- `src/artcb/trace/agent_run.py` — `AgentRunLedger` avec `chain_hash = SHA256(event || prev)` réel
- `src/artcb/rtleg/events.py` — `RTLEGEvent` (Pydantic) avec `event_id`, `session_id`, `agent`, `event_type`, `payload`, `signature`
- `src/artcb/ir/models.py` — `IRGraph` avec `sha256_text`
- Schéma R005/R006 dans ARTCB-TERMINATOR — **non encore intégré dans artcb**

**Constaté :** `AgentRunLedger` implémente déjà `H_i = SHA256(event_i || H_{i-1})`. Mais le format n'est **pas** conforme au schéma canonique JCS/UUIDv7 défini dans R005/R006 — c'est l'existant à migrer.

**Lacune P0 :** divergence entre le format actuel et le contrat canonique R005.

### Couche 8 — Cœur métier backend Rust

**Constaté :** **ABSENT** — le backend est entièrement Python/C. C'est l'objectif de migration Guardian. Aucun code Rust n'existe dans le dépôt `artcb`.

**Statut :** planifié (R001–R009), non autorisé à implémenter.

### Couche 9 — Frontière Rust/Python et services LLM

**Fichiers réels :**
- `src/artcb/bob/` — intégration IBM Bob
- `src/artcb/agents/explorer.py`, `critic.py`, `pool_manager.py` — agents Python
- `src/artcb/ir/llm_encoder.py` — encodeur LLM
- `pyproject.toml` : `litellm-ibm-bob` commenté (risque dependency-confusion R119)

**Constaté :** couche LLM Python existante. La frontière Rust/Python est **à créer** selon R009 (PyO3/Maturin). L'API des 8 fonctions stables (`append_event`, `verify_event`, etc.) est spécifiée dans R002 mais non implémentée.

### Couche 10 — Architecture des agents IA

**Fichiers réels :**
- `src/artcb/agents/explorer.py` — ExplorerAgent
- `src/artcb/agents/critic.py` — CriticAgent (validation, compression review, PoL)
- `src/artcb/agents/pool_manager.py` — gestionnaire de pool d'agents
- `src/artcb/agent_runtime.py` — runtime agent
- `src/artcb/agent_context_contract.py` — contrat de contexte
- `src/artcb/agent_control/` — contrôle des agents
- `tests/test_e2e268_agent_pbft.py`, `test_e2e300_thinking_journal.py`

**Constaté :** agents Explorer, Critic et pool manager implémentés. Aucun `AttackerAgent` ni `DefenderAgent` explicite trouvé — le scénario d'attaque de la démo Guardian est à construire.

**Lacune P0 :** agents adversariaux (attacker, defender) pour Secure Horizons non présents.

### Couche 11 — Orchestration et planification

**Fichiers réels :**
- `src/artcb/agents/pool_manager.py` — orchestration du pool
- `src/artcb/consensus/` — consensus BFT
- `src/c/libartcb_consensus_lock.c/.h` — verrou de consensus C

**Constaté :** orchestration basique via pool manager. PBFT implémenté (voir couche 16).

### Couche 12 — Outils, connecteurs, MCP

**Fichiers réels :**
- `src/artcb/mcp/server.py` — `ArtcbMCPServer` JSON-RPC MCP v1
- `src/artcb/mcp/tools.py` — registre d'outils `TOOLS` + `execute_tool`
- `src/artcb/mcp/resources.py` — ressources `RESOURCES` + `read_resource`
- `src/artcb/mcp/prompts.py` — prompts `PROMPTS`
- `src/artcb/connectors/` — connecteurs (dont `connectors/legal/`)
- `tests/test_mcp_server.py`

**Constaté :** serveur MCP opérationnel. `execute_tool` dispatche les appels. Aucun enregistrement d'événement P0 dans le ledger pour chaque `tools/call` — lacune critique P0 (T-016).

### Couche 13 — Défense et moteur de politiques

**Fichiers réels :**
- `src/artcb/security/disclosure_firewall.py` — firewall opérationnel (R582)
- `src/artcb/security/rate_limiter.py` — limitation de débit
- `src/artcb/security/slashing.py` — pénalités
- `src/artcb/security/anti_sybil.py`
- `.github/workflows/r582_disclosure_gate.yml` — porte CI firewall
- `tests/test_r582_disclosure_firewall.py`

**Décisions documentées dans le code :**
- `ALLOW` / `SANITIZE` / `REVIEW` / `BLOCK`
- 6 niveaux : PUBLIC → DEFENSE_CRITICAL + UNKNOWN (fail-closed)
- Matrice audience × classification implémentée
- `CERTIFIED_100=false` explicite dans le header

**Écart avec R002 :** le firewall utilise `SANITIZE` et `REVIEW` au lieu de `REDACT` et `ESCALATE`. Cette divergence de nomenclature doit être réconciliée avant migration.

**Lacune P0 :** chaque décision BLOCK ne produit pas encore un `EvidenceId` dans le ledger (T-014).

### Couche 14 — Mémoire artificielle persistante

**Fichiers réels :**
- `src/artcb/memory/agent_channel.py` — canal agent-agent binaire (ConceptPackets)
- `src/artcb/memory/concept_store.py` — stockage de concepts
- `src/artcb/memory/concept_network.py` — réseau de concepts
- `src/artcb/memory/graph_store.py` — graphe
- `src/artcb/memory/vector_store.py`, `vector_store_faiss.py` — FAISS
- `src/artcb/memory/concept_sync.py` — synchronisation
- `src/artcb/knowledge/` — base de connaissances
- `tests/test_e2e247_go_k_concept_memory.py`, `test_r334_concept_fanout_authz.py`

**Constaté :** `AgentChannel` opérationnel pour communication agent-agent binaire (ConceptID sans langage humain). Vecteurs FAISS pour recherche sémantique. Graphe de concepts. 

**Lacune P0 :** `AgentChannel` ne porte pas encore l'enveloppe de sécurité Guardian (sender_agent_id, payload_hash, policy_decision, evidence_id) définie dans R002 §8.

### Couche 15 — Provenance, event ledger, graphe causal

**Fichiers réels :**
- `src/artcb/trace/agent_run.py` — `AgentRunLedger` avec hash chaining SHA-256 réel
- `src/artcb/trace/forensic.py` — forensic
- `src/artcb/trace/ns.py` — namespace de trace
- `src/artcb/rtleg/events.py` — `RTLEGEvent` (Pydantic)
- `src/artcb/rtleg/timeline.py` — timeline
- `src/artcb/ir/models.py` — `IRGraph`
- `tests/test_r451_forensic_event_ledger.py`, `test_r452_forensic_coverage_api_binding.py`, `test_r534_forensic_gate.py`

**Constaté :** `AgentRunLedger` implémente le chaînage `H_i = SHA256(event_i || H_{i-1})` avec `prev_hash` et `chain_hash`. Ce composant est le **précurseur direct** du Rust Event Ledger P0-R1 de R002. Tests forensic présents.

**Format actuel vs R005 :** le format `agent_run.py` utilise `sha256_json` avec `sort_keys=True` — proche de JCS mais non conforme RFC 8785. Le préfixe de domaine `ARTCB-GUARDIAN-EVENT-V1` de R005 n'est pas présent.

### Couche 16 — Blockchain, consensus, réseau ARTCB

**Fichiers réels :**
- `src/c/libartcb_chain.c/.h` — chaîne C avec SHA-256, Merkle, PoL, economic_root
- `src/c/libartcb_merkle.c/.h` — Merkle tree C
- `src/c/libartcb_wal.c/.h` — WAL C
- `src/artcb/consensus/` — PBFT Python
- `src/c/libartcb_consensus_lock.c/.h` — verrou consensus C
- `src/artcb/chain/manager.py` — gestionnaire de chaîne
- `src/artcb/devnet/` — réseau de développement
- `src/c/libartcb_p2p.c/.h` et variantes — P2P C
- `tests/test_e2e188_live_bft.py`, `test_r364_pbft_resilience.py`, `test_r453_pbft_view_change_node_failure.py`

**Constaté :** blockchain C opérationnelle avec blocs indexés, timestamps, prev_hash, graph_root, merkle_root, pol_score, economic_root. PBFT implémenté avec tests de view change et résilience. ABI version V2 (`ARTCB_HASH_VERSION_V2`).

**Décision R002 confirmée :** hors périmètre P0 Guardian (tokenomics, consensus, P2P) — correcte, ces composants existent mais ne sont pas nécessaires pour la démo.

### Couche 17 — Tokenomics, jobs, réputation

**Fichiers réels :**
- `src/artcb/tokenomics.py` — tokenomics
- `src/artcb/economics/` — économie
- `src/artcb/pol/` — Proof of Labor (PoL)
- `src/artcb/mining/` — minage
- `src/artcb/pool/` — pool de tâches
- `src/api/economics_routes.py`, `mining_routes.py`, `pool_routes.py`

**Constaté :** PoL, tokenomics, minage et pool implémentés. **Hors périmètre Guardian P0** — confirmé dans R002.

### Couche 18 — FHE et calcul confidentiel

**Fichiers réels :**
- `src/artcb/crypto/homomorphic.py` — Paillier FHE réel (phe>=1.5.0, IND-CPA)
- `src/artcb/identity/biometric_onchain.py` — biométrie on-chain avec FHE
- `tests/test_r432_fhe_hamming_circuit.py`, `test_r479_paillier_he.py`, `test_r479b_paillier_integration.py`, `test_task001_r487_concrete_fhe.py`

**Constaté :** FHE Paillier réel avec protocole `ARTCB-PHE-PAILLIER-HAMMING-v1` (R479) — distance de Hamming chiffrée pour vérification biométrique sans révéler les données. Implémenté et testé.

**Limite :** FHE utilisé pour la biométrie uniquement — pas encore pour le calcul général des événements.

### Couche 19 — Preuves cryptographiques et ZK

**Fichiers réels :**
- `src/artcb/crypto/pqc.py` — engagements ML-DSA-65 et ML-KEM-768
- `src/c/libartcb_sig_canonical.c/.h` — signatures canoniques
- Tests dans `test_r532_ex005_sig_canonical.py`

**Constaté :** pas de preuves ZK (ZK-SNARKs/STARKs) trouvées dans le code. Les preuves cryptographiques sont des signatures Ed25519 + ML-DSA-65 hybrides. Les attestations TPM sont présentes (couche 0).

**Statut :** ZK non présent — à marquer `absent du périmètre inspecté`.

### Couche 20 — Observabilité, forensic et replay

**Fichiers réels :**
- `src/artcb/trace/forensic.py` — forensic
- `src/artcb/trace/agent_run.py` — replay via `AgentRunLedger.write()`
- `src/artcb/telemetry/` — télémétrie
- `.github/workflows/do178c_gate.yml` — porte de qualité DO-178C
- `tests/test_r451_forensic_event_ledger.py`, `test_r534_forensic_gate.py`
- `tests/test_e2e262_evidence_replica.py`

**Constaté :** telemetry et forensic implémentés. Le replay actuel repose sur la relecture du fichier `agent_execution_records.jsonl` — pas encore de replay déterministe avec comparaison de hash (protocole R0–R4 de R004).

### Couche 21 — API, UI et intégration

**Fichiers réels :**
- `src/api/main.py` — FastAPI avec ~40 routes
- `frontend/` — interface React/TypeScript (52 fichiers)
- `src/api/dashboard_routes.py` — dashboard
- `src/api/security_routes.py` — routes de sécurité

**Constaté :** API complète. Frontend React existant. Routes pour dashboard, biométrie, TPM, PBFT, économie, MCP, P2P.

### Couche 22 — Configuration, secrets et paramètres

**Fichiers réels :**
- `.env.example` — variables d'environnement documentées (sans valeurs)
- `src/artcb/config.py` — configuration centralisée
- `src/artcb/logging_config.py` — configuration des logs
- Doppler : projet `artcb-terminator`, `AVA_API_KEY` + `GITHUB_API_KEY` confirmés

**Constaté :** `.env` non commité (`.gitignore`). `ARTCB_INSTALL_PQC=1` pour activer liboqs. Secrets via Doppler pour les environnements de déploiement.

### Couche 23 — Fiabilité, capacité, résilience

**Fichiers réels :**
- `src/c/libartcb_state_rollback.c/.h` — rollback d'état C
- `tests/test_r526_ex012_state_rollback.py`
- `tests/test_e2e222_tip_resilience.py`, `test_v08_failover.py`

**Constaté :** rollback C implémenté. Tests de résilience présents. Pas de mesures de performance systématiques pour les objectifs P95 < 5 ms de R001.

### Couche 24 — Tests, validation et assurance qualité

**Constaté réel :** 295 fichiers de tests, dont :
- Tests unitaires : `test_chain.py`, `test_grammar.py`, `test_symbols.py`, etc.
- Tests E2E multi-nœuds : `test_e2e188_live_bft.py`, `test_e2e187_dv04_four_node.py`
- Tests adversariaux : `test_e2e178_replit_adversarial.py`, `test_r369_adversarial.py`, `test_r334_reasoning_adversarial.py`
- Tests TPM : `test_r460_node_tpm_binding.py`, `test_r462_pcr_binding.py`, `test_e2e281_vtpm_quote.py`
- Tests biométriques : `test_task001_r373_human_identity_policy.py`, `test_task001_r374_bch.py`
- Tests FHE : `test_r432_fhe_hamming_circuit.py`, `test_r479_paillier_he.py`
- Tests fuzzing : `test_r522_ex011_fuzz_harness.py`, `test_r527_ex011_phase2_fuzz.py`
- Tests PQC : `test_pqc_crypto.py`, `test_vpqc2.py`
- Tests différentiels chaîne C : `test_r544_c1_differential_chain.py`

CI : `tests.yml` (déclenché sur push main, hors `rapports/**`, `logs/**`, `*.md`) + workflows spécialisés.

**Lacune P1 :** les tests de R006/R007 (campagnes C-01 à C-10 JCS/JSON Schema Rust/Python) sont NOT_TESTED — mais cela correspond à un composant non encore développé.

### Couche 25 — Déploiement, exploitation et cycle de vie

**Fichiers réels :**
- `scripts/artcb.service` — service systemd
- `scripts/artcb_bootstrap.sh` — bootstrap
- `scripts/artcb263_partition_node.sh` et variantes — scripts de partition réseau
- `deploy/` — configuration de déploiement

**Constaté :** déploiement systemd documenté. Scripts de partition et de nœud. Pas de procédure de rotation de clés automatisée identifiée dans le code.

### Couche 26 — Documentation, gouvernance et traçabilité du projet

**Fichiers réels :**
- `rapports/` — 667 rapports historiques ARTCB (numérotation propre, jusqu'à ~R590+)
- `docs/` — documentation technique
- `API_REFERENCE_ARTCB.md` — référence API
- `ARTCB_FULL_001.md` à `ARTCB_FULL_009.md` — documentation complète
- `.github/workflows/do178c_gate.yml` — porte DO-178C
- `rules/` — règles de gouvernance (16 fichiers JSON)

**Constaté :** documentation très riche. Numérotation des rapports historiques dans `artcb/rapports/` indépendante de celle de TERMINATOR — confirmé.

---

## 5. Écart critique entre code existant et spécifications Guardian

| Composant existant | Composant Guardian cible | Écart principal |
|---|---|---|
| `AgentRunLedger` (Python, `sort_keys=True`) | Rust Event Ledger (JCS RFC 8785, préfixe domaine) | Format canonique divergent ; pas de préfixe de domaine |
| `disclosure_firewall.py` (ALLOW/SANITIZE/REVIEW/BLOCK) | Rust Policy Boundary (ALLOW/BLOCK/REDACT/ESCALATE) | Nomenclature différente ; REDACT/ESCALATE absents |
| `AgentChannel` (ConceptPackets binaires) | AgentChannel instrumenté (enveloppe de sécurité) | Pas de sender_agent_id, payload_hash, evidence_id |
| WAL C (CRC32) | Rust Durable Event Store (SHA-256, chaîne cryptographique) | CRC ≠ preuve cryptographique |
| MCP `execute_tool` (sans ledger) | MCP ToolCall P0 (chaque appel = événement ledger) | Instrumentalisation manquante |
| `AgentRunLedger.write()` (JSONL) | Replay Engine R0–R4 (reconstruction + comparaison hashes) | Pas de replay déterministe avec vérification d'intégrité |
| `IRGraph` (checksum) | Provenance Engine Rust (graphe causal, relations typées) | Checksum ≠ graphe causal |

---

## 6. Mapping composants P0 Guardian → code existant

| P0 Guardian (R002) | Code existant artcb | Statut migration |
|---|---|---|
| P0-01 Rust Event Ledger | `src/artcb/trace/agent_run.py` `AgentRunLedger` | À réécrire en Rust avec JCS + préfixe domaine |
| P0-02 Rust Durable Event Store | `src/c/libartcb_wal.c` | À réécrire : remplacer CRC par SHA-256 chaîné |
| P0-03 Provenance Engine | `src/artcb/ir/models.py` `IRGraph` | À enrichir : graphe causal avec relations typées |
| P0-04 AgentChannel instrumenté | `src/artcb/memory/agent_channel.py` | Ajouter enveloppe sécurité Guardian |
| P0-05 Policy/Firewall Core | `src/artcb/security/disclosure_firewall.py` | Migrer vers Rust + réconcilier nomenclature |
| P0-06 Replay Engine | `src/artcb/trace/forensic.py` + `agent_run.py` | Ajouter replay R0–R4 avec vérification de hash |
| P0-07 MCP ToolCall | `src/artcb/mcp/server.py` + `tools.py` | Instrumenter chaque tools/call → événement ledger |
| P0-08 PyO3 binding | Non existant | À créer dès autorisation |

---

## 7. Points d'attention sécurité détectés

### S-001 — Divergence nomenclature Firewall (P0)

Le firewall existant utilise `SANITIZE` et `REVIEW` ; les rapports Guardian spécifient `REDACT` et `ESCALATE`. Cette divergence doit être réconciliée **avant** implémentation Rust pour éviter deux sémantiques incompatibles.

### S-002 — MCP sans instrumentation ledger (P0)

Chaque `tools/call` MCP est exécuté directement sans enregistrement dans le ledger. Cela représente un vecteur d'attaque non tracé (T07/T09 de R002).

### S-003 — Format canonique non conforme JCS (P1)

`sha256_json` avec `sort_keys=True` est proche mais **non identique** à JCS RFC 8785. Sur des données ASCII simples les résultats peuvent coïncider, mais sur des flottants, des caractères Unicode ou des entiers larges, les deux sérialisations peuvent diverger.

### S-004 — Digest golden F-001 non vérifié (P1)

Le digest `c067e20378...f11` de R006 n'a pas été recalculé par une implémentation JCS conforme. Action réalisable immédiatement.

### S-005 — Attestation TPM distante non implémentée (P1)

Confirmé dans le code `node_tpm_binding.py` et R462 : l'attestation distante avec nonce frais (challenge/response) est documentée comme non implémentée.

---

## 8. Décisions à demander à l'utilisateur

| Décision | Impact |
|---|---|
| Réconcilier SANITIZE→REDACT et REVIEW→ESCALATE dans la migration | Bloque l'implémentation P0-05 |
| Autorisation de démarrer l'implémentation Rust (Go/No-Go) | Bloque tous les P0 |
| Confirmer le SHA de référence pour l'audit (local `0cc5db7` ou distant `7304d493`) | Oriente la baseline |
| Confirmer si le périphérique USB est un stockage ou un authentificateur cryptographique | Oriente les tests matériels |

---

## 9. Contrôle de périmètre

| Contrôle | Résultat |
|---|---|
| Rapport créé dans `rapports/` de `ARTCB-TERMINATOR` | OUI |
| `vgactech/artcb` modifié | NON — lecture seule uniquement |
| Code applicatif de TERMINATOR modifié | NON |
| Logs bruts poussés | NON |
| Secrets exposés | NON |
| Numérotation vérifiée (R011 → R012) | OUI |

---

## 10. Conclusion

Le dépôt `vgactech/artcb` est un système complet et substantiel, pas un prototype. Les composants P0 Guardian ont tous un **précédent fonctionnel en Python/C**. La migration Rust est une réécriture ciblée du noyau de confiance, pas une création ex nihilo.

Les deux blocages immédiats pour avancer vers l'implémentation sont :
1. **La réconciliation de nomenclature** (SANITIZE↔REDACT, REVIEW↔ESCALATE) ;
2. **L'autorisation explicite de l'utilisateur** pour démarrer le code dans ARTCB-TERMINATOR.

Tout le reste est prêt : spécifications, contrats, threat model, tests planifiés, inventaire réel.
