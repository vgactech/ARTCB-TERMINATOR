//! ARTCB Guardian Core — Types partagés
//!
//! Définit les types fondamentaux utilisés par tous les composants Guardian.
//! Aucune dépendance cyclique entre modules.

use chrono::Utc;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ─── Identifiants ────────────────────────────────────────────────────────────

/// Identifiant unique d'un événement (UUIDv7)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EventId(pub String);

/// Identifiant d'une session ou d'un scénario
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SessionId(pub String);

/// Identifiant d'un agent
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct AgentId(pub String);

/// Identifiant d'une preuve
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EvidenceId(pub String);

/// Identifiant d'une politique
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PolicyId(pub String);

/// Identifiant d'un artefact
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ArtifactId(pub String);

impl EventId {
    pub fn new() -> Self {
        Self(Uuid::now_v7().to_string())
    }
    pub fn from(s: &str) -> Self {
        Self(s.to_string())
    }
}

impl EvidenceId {
    pub fn new() -> Self {
        Self(Uuid::now_v7().to_string())
    }
}

// ─── Statuts ─────────────────────────────────────────────────────────────────

/// Statut d'une opération
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OperationStatus {
    Success,
    Failure,
    Blocked,
    Rejected,
    Timeout,
    Cancelled,
    Unknown,
}

/// Décision de politique Guardian
/// Option B retenue : 4 décisions normalisées pour Guardian
/// Le moteur interne conserve la distinction SANITIZE/REVIEW via PolicyReason
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PolicyDecision {
    /// Autoriser l'opération
    Allow,
    /// Refuser l'opération
    Block,
    /// Masquer les informations sensibles avant divulgation
    Redact,
    /// Transmettre le cas à un niveau de décision supérieur
    Escalate,
}

/// Raison interne de la décision — conserve les distinctions sémantiques
/// conformément à la Décision 1 Option B : l'interface affiche 4 décisions
/// mais le moteur trace exactement ce qu'il a fait
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PolicyReason {
    /// Neutralisation d'un contenu dangereux (anciennement SANITIZE)
    ContentNeutralized,
    /// Masquage d'une donnée confidentielle (REDACT)
    SensitiveDataMasked,
    /// Vérification interne demandée (anciennement REVIEW)
    InternalReviewRequired,
    /// Transfert vers autorité supérieure (ESCALATE)
    EscalatedToAuthority,
    /// Accès non autorisé
    Unauthorized,
    /// Outil interdit
    ToolForbidden,
    /// Exfiltration détectée
    ExfiltrationAttempt,
    /// Injection de prompt détectée
    PromptInjection,
    /// Contamination mémoire détectée
    MemoryPoisoning,
    /// Politique appliquée normalement
    PolicyApplied,
}

/// État d'observabilité d'un événement
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ObservabilityStatus {
    Complete,
    Partial,
    External,
    Unknown,
    NotInstrumented,
}

/// Résultat d'une vérification
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum VerificationResult {
    Pass,
    Fail,
    Inconclusive,
    NotTested,
}

/// Classification de sensibilité des données
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DataClassification {
    PublicTest,
    Public,
    Internal,
    Confidential,
    Restricted,
    Secret,
    Unknown,
}

// ─── Référence d'artefact ────────────────────────────────────────────────────

/// Référence à un artefact — jamais le contenu brut
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactRef {
    pub artifact_id: ArtifactId,
    pub digest_algorithm: String,
    pub digest: String,
    pub byte_length: u64,
    pub media_type: String,
    pub classification: DataClassification,
    pub storage_ref: String,
    pub created_by_event_id: EventId,
    pub retention_policy_id: String,
}

// ─── Horodatage ──────────────────────────────────────────────────────────────

/// Retourne l'horodatage UTC actuel en RFC 3339 avec suffixe Z
pub fn utc_now_rfc3339() -> String {
    Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string()
}
