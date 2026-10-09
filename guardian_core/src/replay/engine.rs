//! C-06 — Replay Engine
//!
//! Reconstruction vérifiable d'un incident depuis les événements du ledger.
//! Niveaux R0–R4 définis dans R004 §8.
//! Un replay PASS signifie que les hashes reconstruits correspondent à l'archive.

use serde::{Deserialize, Serialize};

use crate::event::ledger::{canonicalize, compute_event_hash, LedgerEntry, LedgerError};
use crate::types::VerificationResult;

// ─── Niveaux de replay (R004 §8) ─────────────────────────────────────────────

/// Niveau de garantie d'un replay
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReplayLevel {
    /// R0 — Replay structurel : les événements peuvent être relus
    /// et le graphe causal peut être reconstruit
    R0Structural,
    /// R1 — Replay de décisions déterministes : compare décisions et raisons
    R1PolicyDecisions,
    /// R2 — Replay d'outils simulés : réponses enregistrées ou simulées
    R2SimulatedTools,
    /// R3 — Replay d'exécution contrôlée : mêmes entrées, mêmes sorties canoniques
    R3ControlledExecution,
    /// R4 — Replay IA avec fidélité qualifiée : reconstruction du contexte uniquement
    R4AIQualified,
}

/// Manifeste d'un replay — doit être fourni avant exécution
#[derive(Debug, Serialize, Deserialize)]
pub struct ReplayManifest {
    pub run_id: String,
    pub original_chain_tip: String,
    pub schema_version: String,
    pub policy_version: String,
    pub requested_level: ReplayLevel,
    pub entries_count: u64,
    pub created_at: String,
}

/// Résultat d'un replay
#[derive(Debug, Serialize, Deserialize)]
pub struct ReplayReport {
    pub manifest: ReplayManifest,
    pub level_achieved: ReplayLevel,
    pub result: VerificationResult,
    pub entries_replayed: u64,
    pub mismatches: Vec<ReplayMismatch>,
    pub limits: Vec<String>,
}

/// Une divergence détectée pendant le replay
#[derive(Debug, Serialize, Deserialize)]
pub struct ReplayMismatch {
    pub stream_sequence: u64,
    pub event_id: String,
    pub field: String,
    pub original: String,
    pub replayed: String,
}

// ─── Moteur de replay ─────────────────────────────────────────────────────────

pub struct ReplayEngine;

impl ReplayEngine {
    /// Replay R0 — vérifie que tous les événements peuvent être relus
    /// et que les hashes correspondent aux archives
    pub fn replay_r0(
        entries: &[LedgerEntry],
        manifest: ReplayManifest,
    ) -> Result<ReplayReport, LedgerError> {
        let mut mismatches = Vec::new();
        let mut entries_replayed = 0u64;

        for entry in entries {
            // Recalculer le hash du corps
            let canonical = canonicalize(&entry.body)?;
            let recomputed = compute_event_hash(&canonical);

            if recomputed != entry.event_hash {
                mismatches.push(ReplayMismatch {
                    stream_sequence: entry.stream_sequence,
                    event_id: entry.body.event_id.0.clone(),
                    field: "event_hash".to_string(),
                    original: entry.event_hash.clone(),
                    replayed: recomputed,
                });
            }
            entries_replayed += 1;
        }

        let result = if mismatches.is_empty() {
            VerificationResult::Pass
        } else {
            VerificationResult::Fail
        };

        Ok(ReplayReport {
            manifest,
            level_achieved: ReplayLevel::R0Structural,
            result,
            entries_replayed,
            mismatches,
            limits: vec![
                "R0 vérifie uniquement l'intégrité des hashes, pas la correction sémantique".to_string(),
                "Un replay R0 réussi ne prouve pas que le calcul d'origine était correct".to_string(),
            ],
        })
    }

    /// Replay R1 — vérifie les décisions de politique
    pub fn replay_r1_policy(
        entries: &[LedgerEntry],
        manifest: ReplayManifest,
    ) -> Result<ReplayReport, LedgerError> {
        let mut r0_report = Self::replay_r0(entries, manifest)?;

        // En plus de R0, vérifier la cohérence des décisions de politique
        let mut policy_mismatches = Vec::new();
        for entry in entries {
            if let Some(policy) = &entry.body.policy {
                // Vérifier que chaque BLOCK a un evidence_id
                if policy.decision == crate::types::PolicyDecision::Block
                    && policy.evidence_id.is_none()
                {
                    policy_mismatches.push(ReplayMismatch {
                        stream_sequence: entry.stream_sequence,
                        event_id: entry.body.event_id.0.clone(),
                        field: "evidence_id".to_string(),
                        original: "Some(...)".to_string(),
                        replayed: "None".to_string(),
                    });
                }
            }
        }

        r0_report.mismatches.extend(policy_mismatches);
        r0_report.level_achieved = ReplayLevel::R1PolicyDecisions;
        r0_report.result = if r0_report.mismatches.is_empty() {
            VerificationResult::Pass
        } else {
            VerificationResult::Fail
        };
        r0_report.limits.push(
            "R1 vérifie les décisions de politique mais pas la réexécution du LLM".to_string(),
        );

        Ok(r0_report)
    }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::ledger::{
        build_event, canonicalize, compute_chain_hash, compute_event_hash,
        DurabilityStatus, LedgerEntry, GENESIS_HASH, INTEGRITY_PROFILE_VERSION,
    };
    use crate::types::{
        AgentId, DataClassification, OperationStatus, SessionId, VerificationResult,
        utc_now_rfc3339,
    };

    fn make_entry(seq: u64, prev_hash: &str) -> LedgerEntry {
        let body = build_event(
            "agent.test.replay",
            AgentId("agent:test".to_string()),
            SessionId("session:test".to_string()),
            "run:test",
            seq,
            vec![],
            "test_op",
            OperationStatus::Success,
            None,
            DataClassification::PublicTest,
        );
        let canonical = canonicalize(&body).unwrap();
        let event_hash = compute_event_hash(&canonical);
        let chain_hash = compute_chain_hash(prev_hash, &event_hash, seq).unwrap();
        LedgerEntry {
            body,
            canonicalization_profile: "JCS-RFC8785".to_string(),
            hash_algorithm: "SHA-256".to_string(),
            event_hash,
            stream_id: "stream:test".to_string(),
            stream_sequence: seq,
            previous_event_hash: prev_hash.to_string(),
            chain_hash,
            ingested_at: utc_now_rfc3339(),
            durability_status: DurabilityStatus::Durable,
            integrity_profile_version: INTEGRITY_PROFILE_VERSION.to_string(),
        }
    }

    fn make_manifest(entries: &[LedgerEntry]) -> ReplayManifest {
        ReplayManifest {
            run_id: "run:test".to_string(),
            original_chain_tip: entries.last()
                .map(|e| e.chain_hash.clone())
                .unwrap_or(GENESIS_HASH.to_string()),
            schema_version: "1.0.0".to_string(),
            policy_version: "1.0.0".to_string(),
            requested_level: ReplayLevel::R0Structural,
            entries_count: entries.len() as u64,
            created_at: utc_now_rfc3339(),
        }
    }

    // ─── Tests R1 ─────────────────────────────────────────────────────────────

    fn make_entry_with_policy(
        seq: u64,
        prev_hash: &str,
        decision: crate::types::PolicyDecision,
        evidence_id: Option<String>,
    ) -> LedgerEntry {
        use crate::event::ledger::PolicyInfo;
        let mut entry = make_entry(seq, prev_hash);
        entry.body.policy = Some(PolicyInfo {
            policy_id: crate::types::PolicyId("policy:guardian-default".to_string()),
            policy_version: "1.0.0".to_string(),
            decision: decision.clone(),
            reason: crate::types::PolicyReason::PolicyApplied,
            evidence_id: evidence_id.clone(),
        });
        // Recalculer le hash avec le corps modifié
        let canonical = canonicalize(&entry.body).unwrap();
        let event_hash = compute_event_hash(&canonical);
        let chain_hash = compute_chain_hash(prev_hash, &event_hash, seq).unwrap();
        entry.event_hash = event_hash;
        entry.chain_hash = chain_hash;
        entry
    }

    #[test]
    fn test_replay_r1_pass() {
        // BLOCK avec evidence_id présent — cohérence vérifiée
        use crate::types::PolicyDecision;
        let e1 = make_entry_with_policy(
            1,
            GENESIS_HASH,
            PolicyDecision::Block,
            Some("01a00000-0000-7000-8000-000000000001".to_string()),
        );
        let entries = vec![e1];
        let mut manifest = make_manifest(&entries);
        manifest.requested_level = ReplayLevel::R1PolicyDecisions;
        let report = ReplayEngine::replay_r1_policy(&entries, manifest).unwrap();
        assert_eq!(report.result, VerificationResult::Pass);
        assert_eq!(report.level_achieved, ReplayLevel::R1PolicyDecisions);
        assert!(report.mismatches.is_empty(), "Pas de divergence attendue");
    }

    #[test]
    fn test_replay_r1_fail_block_sans_evidence() {
        // BLOCK sans evidence_id — incohérence détectée (invariant Guardian)
        use crate::types::PolicyDecision;
        let e1 = make_entry_with_policy(1, GENESIS_HASH, PolicyDecision::Block, None::<String>);
        let entries = vec![e1];
        let mut manifest = make_manifest(&entries);
        manifest.requested_level = ReplayLevel::R1PolicyDecisions;
        let report = ReplayEngine::replay_r1_policy(&entries, manifest).unwrap();
        assert_eq!(report.result, VerificationResult::Fail);
        assert!(!report.mismatches.is_empty(), "Divergence BLOCK sans evidence attendue");
        assert_eq!(report.mismatches[0].field, "evidence_id");
    }

    #[test]
    fn test_replay_r1_allow_sans_evidence_ok() {
        // ALLOW sans evidence_id — normal, pas de divergence
        use crate::types::PolicyDecision;
        let e1 = make_entry_with_policy(1, GENESIS_HASH, PolicyDecision::Allow, None::<String>);
        let entries = vec![e1];
        let mut manifest = make_manifest(&entries);
        manifest.requested_level = ReplayLevel::R1PolicyDecisions;
        let report = ReplayEngine::replay_r1_policy(&entries, manifest).unwrap();
        assert_eq!(report.result, VerificationResult::Pass);
        assert!(report.mismatches.is_empty());
    }

    // ─── Tests R0 ─────────────────────────────────────────────────────────────

    #[test]
    fn test_replay_r0_pass() {
        let e1 = make_entry(1, GENESIS_HASH);
        let e2 = make_entry(2, &e1.chain_hash);
        let entries = vec![e1, e2];
        let manifest = make_manifest(&entries);
        let report = ReplayEngine::replay_r0(&entries, manifest).unwrap();
        assert_eq!(report.result, VerificationResult::Pass);
        assert_eq!(report.entries_replayed, 2);
        assert!(report.mismatches.is_empty());
    }

    #[test]
    fn test_replay_r0_fail_si_altere() {
        let mut e1 = make_entry(1, GENESIS_HASH);
        // Altérer le hash après création
        e1.event_hash = "a".repeat(64);
        let entries = vec![e1];
        let manifest = make_manifest(&entries);
        let report = ReplayEngine::replay_r0(&entries, manifest).unwrap();
        assert_eq!(report.result, VerificationResult::Fail);
        assert!(!report.mismatches.is_empty(), "La divergence doit être détectée");
    }
}
