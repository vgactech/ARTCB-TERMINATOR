//! ARTCB Guardian Core — Point d'entrée de la bibliothèque
//!
//! C-01 Rust Event Ledger
//! C-02 Rust Durable Event Store
//! C-03 Provenance Engine
//! C-04 Secure Agent Channel
//! C-05 Rust Policy/Firewall Core
//! C-06 Replay Engine

pub mod channel;
pub mod event;
pub mod policy;
pub mod provenance;
pub mod python_bindings;
pub mod replay;
pub mod store;
pub mod types;

// API publique stable — exposée à Python via PyO3 (C-08)
pub use channel::secure::{ChannelError, SecureChannel, SecureMessage};
pub use event::ledger::{
    build_event, canonicalize, compute_chain_hash, compute_event_hash,
    validate_event_body, EventBody, LedgerEntry, LedgerError,
};
pub use policy::engine::{PolicyEngine, PolicyInput, PolicyResult};
pub use provenance::graph::ProvenanceGraph;
pub use replay::engine::{ReplayEngine, ReplayManifest, ReplayReport};
pub use store::durable::{DurableEventStore, VerificationReport};
pub use types::{
    AgentId, DataClassification, EvidenceId, EventId, OperationStatus,
    PolicyDecision, PolicyId, PolicyReason, SessionId, VerificationResult,
};
