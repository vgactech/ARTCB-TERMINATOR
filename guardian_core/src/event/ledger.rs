//! C-01 — Rust Event Ledger
//!
//! Contrat : même événement logique → même corps canonique → même empreinte.
//! Conforme au schéma R005/R006 : JCS RFC 8785, UUIDv7, SHA-256 avec préfixe domaine.
//!
//! Domaine de hash : SHA-256("ARTCB-GUARDIAN-EVENT-V1" || 0x00 || canonical_body_bytes)

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

use crate::types::{
    AgentId, ArtifactRef, DataClassification, EventId, ObservabilityStatus,
    OperationStatus, PolicyDecision, PolicyId, PolicyReason, SessionId,
    utc_now_rfc3339,
};

// ─── Constantes ──────────────────────────────────────────────────────────────

pub const SCHEMA_ID: &str = "https://artcb.example/schemas/guardian/event/1.0.0";
pub const SCHEMA_VERSION: &str = "1.0.0";
pub const INTEGRITY_PROFILE_VERSION: &str = "1.0.0";
pub const DOMAIN_PREFIX: &str = "ARTCB-GUARDIAN-EVENT-V1";
pub const CHAIN_DOMAIN_PREFIX: &str = "ARTCB-GUARDIAN-CHAIN-V1";
pub const GENESIS_HASH: &str = "0000000000000000000000000000000000000000000000000000000000000000";

// ─── Corps canonique (R005 §5.2) ─────────────────────────────────────────────

/// Corps canonique d'un événement Guardian.
/// NE contient PAS event_hash, signature, ingested_at — ces champs
/// appartiennent à l'enveloppe pour éviter les dépendances circulaires.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventBody {
    pub schema_id: String,
    pub schema_version: String,
    pub event_id: EventId,
    pub event_type: String,
    pub occurred_at: String,
    pub producer: Producer,
    pub execution: Execution,
    pub causality: Causality,
    pub operation: Operation,
    pub inputs: Vec<ArtifactRef>,
    pub outputs: Vec<ArtifactRef>,
    pub policy: Option<PolicyInfo>,
    pub observability: Observability,
    pub classification: DataClassification,
    pub extensions: serde_json::Map<String, Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Producer {
    pub producer_id: AgentId,
    pub producer_instance_id: String,
    pub component_version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Execution {
    pub run_id: String,
    pub session_id: SessionId,
    pub sequence_no: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Causality {
    /// Dépendances causales directes connues — triées avant canonicalisation
    pub parent_event_ids: Vec<EventId>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Operation {
    pub name: String,
    pub status: OperationStatus,
}

/// Décision de politique associée à l'événement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyInfo {
    pub policy_id: PolicyId,
    pub policy_version: String,
    pub decision: PolicyDecision,
    /// Raison interne — conserve la sémantique complète (Option B Décision 1)
    pub reason: PolicyReason,
    pub evidence_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Observability {
    pub status: ObservabilityStatus,
    pub source: String,
    pub limitations: Vec<String>,
}

// ─── Enveloppe du ledger (R005 §5.3) ─────────────────────────────────────────

/// Enveloppe complète : corps + métadonnées d'intégrité du ledger
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerEntry {
    pub body: EventBody,
    pub canonicalization_profile: String,
    pub hash_algorithm: String,
    /// SHA-256(domaine || 0x00 || corps_canonique)
    pub event_hash: String,
    pub stream_id: String,
    pub stream_sequence: u64,
    /// Hash de l'entrée précédente dans ce flux
    pub previous_event_hash: String,
    /// SHA-256(domaine_chaine || 0x00 || previous_hash || event_hash || stream_sequence_be)
    pub chain_hash: String,
    pub ingested_at: String,
    pub durability_status: DurabilityStatus,
    pub integrity_profile_version: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DurabilityStatus {
    /// Écrit et fsync confirmé
    Durable,
    /// Écrit mais pas encore confirmé
    Pending,
    /// En cours d'écriture
    Writing,
}

// ─── Canonicalisation JCS (RFC 8785) ─────────────────────────────────────────

/// Sérialise un corps d'événement en représentation canonique JCS.
///
/// JCS RFC 8785 : tri récursif des clés par ordre Unicode, représentation
/// compacte sans espaces superflus, encodage UTF-8 sans BOM.
/// Les tableaux parent_event_ids sont triés lexicographiquement.
pub fn canonicalize(body: &EventBody) -> Result<Vec<u8>, LedgerError> {
    // Sérialiser vers Value serde_json
    let mut val = serde_json::to_value(body)
        .map_err(|e| LedgerError::Serialization(e.to_string()))?;

    // Trier récursivement les clés (JCS RFC 8785)
    sort_keys_recursive(&mut val);

    // Trier parent_event_ids lexicographiquement (R005 §6.2 règle 8)
    if let Some(causality) = val.get_mut("causality") {
        if let Some(parents) = causality.get_mut("parent_event_ids") {
            if let Some(arr) = parents.as_array_mut() {
                arr.sort_by(|a, b| {
                    a.as_str().unwrap_or("").cmp(b.as_str().unwrap_or(""))
                });
            }
        }
    }

    // Sérialiser en JSON compact UTF-8 sans BOM
    let bytes = serde_json::to_vec(&val)
        .map_err(|e| LedgerError::Serialization(e.to_string()))?;

    Ok(bytes)
}

/// Tri récursif des clés d'un objet JSON (JCS)
fn sort_keys_recursive(val: &mut Value) {
    match val {
        Value::Object(map) => {
            // Reconstruire la map triée
            let mut sorted: serde_json::Map<String, Value> = serde_json::Map::new();
            let mut keys: Vec<String> = map.keys().cloned().collect();
            keys.sort();
            for key in keys {
                if let Some(mut v) = map.remove(&key) {
                    sort_keys_recursive(&mut v);
                    sorted.insert(key, v);
                }
            }
            *map = sorted;
        }
        Value::Array(arr) => {
            for v in arr.iter_mut() {
                sort_keys_recursive(v);
            }
        }
        _ => {}
    }
}

// ─── Calcul d'empreinte (R005 §6.3 / R006 §5.3) ──────────────────────────────

/// Calcule l'empreinte du corps canonique avec séparation de domaine.
/// SHA-256("ARTCB-GUARDIAN-EVENT-V1" || 0x00 || canonical_body_bytes)
pub fn compute_event_hash(canonical_bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(DOMAIN_PREFIX.as_bytes());
    hasher.update([0x00u8]);
    hasher.update(canonical_bytes);
    hex::encode(hasher.finalize())
}

/// Calcule le hash de chaîne.
/// SHA-256("ARTCB-GUARDIAN-CHAIN-V1" || 0x00 || previous_hash_bytes || event_hash_bytes || stream_sequence_u64_be)
pub fn compute_chain_hash(
    previous_event_hash: &str,
    event_hash: &str,
    stream_sequence: u64,
) -> Result<String, LedgerError> {
    let prev_bytes = hex::decode(previous_event_hash)
        .map_err(|_| LedgerError::InvalidHash("previous_event_hash mal formé".to_string()))?;
    let evt_bytes = hex::decode(event_hash)
        .map_err(|_| LedgerError::InvalidHash("event_hash mal formé".to_string()))?;

    let mut hasher = Sha256::new();
    hasher.update(CHAIN_DOMAIN_PREFIX.as_bytes());
    hasher.update([0x00u8]);
    hasher.update(&prev_bytes);
    hasher.update(&evt_bytes);
    hasher.update(stream_sequence.to_be_bytes());
    Ok(hex::encode(hasher.finalize()))
}

// ─── Erreurs ─────────────────────────────────────────────────────────────────

#[derive(Debug, thiserror::Error)]
pub enum LedgerError {
    #[error("Erreur de sérialisation : {0}")]
    Serialization(String),
    #[error("Hash invalide : {0}")]
    InvalidHash(String),
    #[error("Schéma invalide : {0}")]
    InvalidSchema(String),
    #[error("Identifiant en conflit : {0}")]
    IdentityConflict(String),
    #[error("Conflit d'idempotence : {0}")]
    IdempotencyConflict(String),
    #[error("Parent manquant : {0}")]
    MissingParent(String),
    #[error("Cycle causal détecté : {0}")]
    CausalCycle(String),
    #[error("Erreur d'entrée/sortie : {0}")]
    Io(String),
    #[error("Erreur de persistance : {0}")]
    Durability(String),
    #[error("Version de schéma inconnue : {0}")]
    UnknownSchemaVersion(String),
}

// ─── Constructeur d'événement ─────────────────────────────────────────────────

/// Construit un EventBody minimal valide
pub fn build_event(
    event_type: &str,
    agent_id: AgentId,
    session_id: SessionId,
    run_id: &str,
    sequence_no: u64,
    parent_event_ids: Vec<EventId>,
    operation_name: &str,
    status: OperationStatus,
    policy: Option<PolicyInfo>,
    classification: DataClassification,
) -> EventBody {
    EventBody {
        schema_id: SCHEMA_ID.to_string(),
        schema_version: SCHEMA_VERSION.to_string(),
        event_id: EventId::new(),
        event_type: event_type.to_string(),
        occurred_at: utc_now_rfc3339(),
        producer: Producer {
            producer_id: agent_id,
            producer_instance_id: uuid::Uuid::now_v7().to_string(),
            component_version: "0.1.0".to_string(),
        },
        execution: Execution {
            run_id: run_id.to_string(),
            session_id,
            sequence_no,
        },
        causality: Causality { parent_event_ids },
        operation: Operation {
            name: operation_name.to_string(),
            status,
        },
        inputs: vec![],
        outputs: vec![],
        policy,
        observability: Observability {
            status: ObservabilityStatus::Complete,
            source: "guardian-core".to_string(),
            limitations: vec![],
        },
        classification,
        extensions: serde_json::Map::new(),
    }
}

// ─── Validation de schéma ─────────────────────────────────────────────────────

/// Valide les champs obligatoires d'un EventBody
pub fn validate_event_body(body: &EventBody) -> Result<(), LedgerError> {
    if body.schema_id != SCHEMA_ID {
        return Err(LedgerError::InvalidSchema(format!(
            "schema_id attendu : {}, reçu : {}",
            SCHEMA_ID, body.schema_id
        )));
    }
    if body.schema_version != SCHEMA_VERSION {
        return Err(LedgerError::UnknownSchemaVersion(body.schema_version.clone()));
    }
    if body.event_id.0.is_empty() {
        return Err(LedgerError::InvalidSchema("event_id vide".to_string()));
    }
    if body.event_type.len() < 3 {
        return Err(LedgerError::InvalidSchema(
            "event_type trop court (min 3 caractères)".to_string(),
        ));
    }
    if body.execution.sequence_no < 1 {
        return Err(LedgerError::InvalidSchema(
            "sequence_no doit être >= 1".to_string(),
        ));
    }
    if !body.occurred_at.ends_with('Z') {
        return Err(LedgerError::InvalidSchema(
            "occurred_at doit se terminer par Z (UTC)".to_string(),
        ));
    }
    // Vérifier les doublons dans parent_event_ids
    let mut seen = std::collections::HashSet::new();
    for pid in &body.causality.parent_event_ids {
        if !seen.insert(pid.0.clone()) {
            return Err(LedgerError::InvalidSchema(format!(
                "parent_event_id en double : {}",
                pid.0
            )));
        }
    }
    Ok(())
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn make_test_body() -> EventBody {
        build_event(
            "agent.input.received",
            AgentId("agent:fixture-a".to_string()),
            SessionId("0199a111-2222-7222-8222-555555555555".to_string()),
            "0199a111-2222-7222-8222-444444444444",
            1,
            vec![],
            "receive_input",
            OperationStatus::Success,
            None,
            DataClassification::PublicTest,
        )
    }

    #[test]
    fn test_validation_body_valide() {
        let mut body = make_test_body();
        // Forcer l'event_id du golden pour reproduire F-001
        body.event_id = EventId("0199a111-2222-7222-8222-222222222222".to_string());
        body.occurred_at = "2026-10-09T00:00:00Z".to_string();
        body.producer.producer_instance_id =
            "0199a111-2222-7222-8222-333333333333".to_string();
        body.producer.component_version = "fixture-1".to_string();
        body.schema_id = SCHEMA_ID.to_string();
        body.schema_version = SCHEMA_VERSION.to_string();

        let result = validate_event_body(&body);
        assert!(result.is_ok(), "Validation échouée : {:?}", result);
    }

    #[test]
    fn test_canonicalisation_deterministe() {
        let mut body = make_test_body();
        body.event_id = EventId("0199a111-2222-7222-8222-222222222222".to_string());
        body.occurred_at = "2026-10-09T00:00:00Z".to_string();
        body.producer.producer_instance_id =
            "0199a111-2222-7222-8222-333333333333".to_string();
        body.producer.component_version = "fixture-1".to_string();

        let bytes1 = canonicalize(&body).unwrap();
        let bytes2 = canonicalize(&body).unwrap();
        assert_eq!(bytes1, bytes2, "La canonicalisation doit être déterministe");
        println!("Longueur corps canonique : {} octets", bytes1.len());
        println!("Corps canonique : {}", String::from_utf8_lossy(&bytes1));
    }

    #[test]
    fn test_golden_f001_hash() {
        // Fixture F-001 de R006 — vecteur de référence
        // Corps canonique attendu : 735 octets
        // Digest golden R006 : c067e20378788d5d32e25c489064efd624224596c1987b5315f8dde296892f11
        let mut body = make_test_body();
        body.event_id = EventId("0199a111-2222-7222-8222-222222222222".to_string());
        body.event_type = "agent.input.received".to_string();
        body.occurred_at = "2026-10-09T00:00:00Z".to_string();
        body.producer = Producer {
            producer_id: AgentId("agent:fixture-a".to_string()),
            producer_instance_id: "0199a111-2222-7222-8222-333333333333".to_string(),
            component_version: "fixture-1".to_string(),
        };
        body.execution = Execution {
            run_id: "0199a111-2222-7222-8222-444444444444".to_string(),
            session_id: SessionId("0199a111-2222-7222-8222-555555555555".to_string()),
            sequence_no: 1,
        };
        // Le golden F-001 de R006 utilise source="fixture" (pas "guardian-core")
        body.observability.source = "fixture".to_string();

        let canonical = canonicalize(&body).unwrap();
        let digest = compute_event_hash(&canonical);

        println!("=== Test Golden F-001 ===");
        println!("Longueur : {} octets", canonical.len());
        println!("Corps    : {}", String::from_utf8_lossy(&canonical));
        println!("Digest   : {}", digest);
        println!("Attendu  : c067e20378788d5d32e25c489064efd624224596c1987b5315f8dde296892f11");

        // Vérifier la longueur (735 octets selon R006)
        assert_eq!(
            canonical.len(),
            735,
            "Longueur du corps canonique doit être 735 octets selon R006"
        );
        // Vérifier le digest golden
        assert_eq!(
            digest,
            "c067e20378788d5d32e25c489064efd624224596c1987b5315f8dde296892f11",
            "Digest golden F-001 ne correspond pas — vérifier la canonicalisation JCS"
        );
    }

    #[test]
    fn test_schema_invalide_sequence_zero() {
        let mut body = make_test_body();
        body.execution.sequence_no = 0;
        assert!(validate_event_body(&body).is_err());
    }

    #[test]
    fn test_schema_invalide_timestamp_sans_z() {
        let mut body = make_test_body();
        body.occurred_at = "2026-10-09T00:00:00+02:00".to_string();
        assert!(validate_event_body(&body).is_err());
    }

    #[test]
    fn test_parent_event_ids_doublons_rejetes() {
        let mut body = make_test_body();
        let dup = EventId("0199a111-2222-7222-8222-aaaaaaaaaaaa".to_string());
        body.causality.parent_event_ids = vec![dup.clone(), dup];
        assert!(validate_event_body(&body).is_err());
    }

    #[test]
    fn test_hash_chaine() {
        let chain = compute_chain_hash(GENESIS_HASH, "a".repeat(64).as_str(), 1);
        assert!(chain.is_ok());
        assert_eq!(chain.unwrap().len(), 64);
    }
}
