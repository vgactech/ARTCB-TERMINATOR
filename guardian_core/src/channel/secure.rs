//! C-04 — Secure Agent Channel
//!
//! Enveloppe cryptographique pour les messages inter-agents.
//! Chaque message transmis produit un événement Guardian dans le ledger.
//!
//! Propriétés garanties :
//! - Intégrité : SHA-256 du contenu binaire inclus dans le corps d'événement.
//! - Séquencement : numéro de séquence monotone par canal (paire émetteur→récepteur).
//! - Traçabilité : chaque send() retourne un EventId enregistrable dans le ledger.
//! - Non-répudiation : l'émetteur et le récepteur sont identifiés dans le corps.
//!
//! Successeur du protocole binaire Python (agent_channel.py), côté intégrité.

use sha2::{Digest, Sha256};

use crate::event::ledger::{
    build_event, canonicalize, compute_chain_hash, compute_event_hash, DurabilityStatus,
    LedgerEntry, LedgerError, GENESIS_HASH, INTEGRITY_PROFILE_VERSION,
};
use crate::types::{AgentId, DataClassification, EventId, OperationStatus, SessionId, utc_now_rfc3339};

// ─── Erreurs ─────────────────────────────────────────────────────────────────

/// Erreurs du canal sécurisé
#[derive(Debug, thiserror::Error)]
pub enum ChannelError {
    #[error("Sérialisation : {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("Ledger : {0}")]
    Ledger(#[from] LedgerError),
    #[error("Séquence invalide : attendu {expected}, reçu {received}")]
    InvalidSequence { expected: u64, received: u64 },
    #[error("Hash de contenu invalide : attendu {expected}, calculé {computed}")]
    ContentHashMismatch { expected: String, computed: String },
    #[error("Canal fermé")]
    ChannelClosed,
}

// ─── Enveloppe de message ─────────────────────────────────────────────────────

/// Enveloppe sécurisée d'un message inter-agents.
/// `payload` est le binaire ARTCB (ConceptPacket ou bundle).
#[derive(Debug, Clone)]
pub struct SecureMessage {
    /// Identifiant de l'événement dans le ledger Guardian
    pub event_id: EventId,
    /// Agent émetteur
    pub sender_id: AgentId,
    /// Agent récepteur
    pub receiver_id: AgentId,
    /// Numéro de séquence du canal (monotone, commence à 1)
    pub sequence_no: u64,
    /// SHA-256 du payload binaire (hex)
    pub content_hash: String,
    /// Taille du payload en octets
    pub payload_size: usize,
    /// Horodatage RFC-3339 UTC
    pub sent_at: String,
    /// Entrée de ledger correspondante
    pub ledger_entry: LedgerEntry,
}

// ─── Canal sécurisé ──────────────────────────────────────────────────────────

/// Canal sécurisé entre deux agents.
///
/// Produit des `LedgerEntry` pour chaque message, chaînables dans un
/// `DurableEventStore`. Le canal est directionnel : un `SecureChannel` gère
/// les envois d'un seul agent ; créez deux instances pour une communication
/// bidirectionnelle.
pub struct SecureChannel {
    sender_id: AgentId,
    receiver_id: AgentId,
    session_id: SessionId,
    run_id: String,
    /// Séquence globale partagée avec le store
    next_seq: u64,
    /// Hash de la dernière entrée de chaîne (GENESIS si aucune)
    last_chain_hash: String,
    /// Classification par défaut des messages de ce canal
    default_classification: DataClassification,
}

impl SecureChannel {
    /// Crée un canal sécurisé.
    ///
    /// `initial_seq` et `initial_chain_hash` permettent de reprendre un canal
    /// existant après un redémarrage (récupérer ces valeurs depuis le store).
    pub fn new(
        sender_id: AgentId,
        receiver_id: AgentId,
        session_id: SessionId,
        run_id: impl Into<String>,
        initial_seq: u64,
        initial_chain_hash: Option<String>,
        classification: DataClassification,
    ) -> Self {
        Self {
            sender_id,
            receiver_id,
            session_id,
            run_id: run_id.into(),
            next_seq: initial_seq.max(1),
            last_chain_hash: initial_chain_hash
                .unwrap_or_else(|| GENESIS_HASH.to_string()),
            default_classification: classification,
        }
    }

    /// Crée un canal sécurisé avec les paramètres par défaut (séquence à 1).
    pub fn open(
        sender_id: AgentId,
        receiver_id: AgentId,
        session_id: SessionId,
        run_id: impl Into<String>,
    ) -> Self {
        Self::new(
            sender_id,
            receiver_id,
            session_id,
            run_id,
            1,
            None,
            DataClassification::Internal,
        )
    }

    /// Envoie un message binaire et produit une `SecureMessage` avec son
    /// entrée de ledger. Le payload n'est PAS stocké dans le ledger —
    /// seul son hash l'est (minimisation de données).
    pub fn send(&mut self, payload: &[u8]) -> Result<SecureMessage, ChannelError> {
        let content_hash = sha256_hex(payload);
        let seq = self.next_seq;
        let sent_at = utc_now_rfc3339();

        // Construire le corps de l'événement
        let mut body = build_event(
            "channel.message.sent",
            self.sender_id.clone(),
            self.session_id.clone(),
            &self.run_id,
            seq,
            vec![],
            "send_message",
            OperationStatus::Success,
            None,
            self.default_classification.clone(),
        );
        // Surcharger l'horodatage pour le test reproductible
        body.occurred_at = sent_at.clone();

        // Stocker le hash et le récepteur dans les extensions
        body.extensions.insert(
            "channel.content_hash".to_string(),
            serde_json::Value::String(content_hash.clone()),
        );
        body.extensions.insert(
            "channel.receiver_id".to_string(),
            serde_json::Value::String(self.receiver_id.0.clone()),
        );
        body.extensions.insert(
            "channel.payload_size".to_string(),
            serde_json::Value::Number(serde_json::Number::from(payload.len())),
        );

        // Canonicaliser et calculer les hashes
        let canonical = canonicalize(&body)?;
        let event_hash = compute_event_hash(&canonical);
        let chain_hash =
            compute_chain_hash(&self.last_chain_hash, &event_hash, seq)?;

        let entry = LedgerEntry {
            body: body.clone(),
            canonicalization_profile: "JCS-RFC8785".to_string(),
            hash_algorithm: "SHA-256".to_string(),
            event_hash: event_hash.clone(),
            stream_id: format!(
                "channel:{}->{}",
                self.sender_id.0, self.receiver_id.0
            ),
            stream_sequence: seq,
            previous_event_hash: self.last_chain_hash.clone(),
            chain_hash: chain_hash.clone(),
            ingested_at: utc_now_rfc3339(),
            durability_status: DurabilityStatus::Pending,
            integrity_profile_version: INTEGRITY_PROFILE_VERSION.to_string(),
        };

        // Avancer l'état du canal
        self.last_chain_hash = chain_hash;
        self.next_seq += 1;

        let msg = SecureMessage {
            event_id: body.event_id.clone(),
            sender_id: self.sender_id.clone(),
            receiver_id: self.receiver_id.clone(),
            sequence_no: seq,
            content_hash,
            payload_size: payload.len(),
            sent_at,
            ledger_entry: entry,
        };

        Ok(msg)
    }

    /// Vérifie l'intégrité d'un message reçu (hash du payload).
    /// Retourne `Ok(())` si le hash correspond, `Err` sinon.
    pub fn verify_received(
        &self,
        payload: &[u8],
        msg: &SecureMessage,
    ) -> Result<(), ChannelError> {
        let computed = sha256_hex(payload);
        if computed != msg.content_hash {
            return Err(ChannelError::ContentHashMismatch {
                expected: msg.content_hash.clone(),
                computed,
            });
        }
        Ok(())
    }

    /// Numéro de séquence du prochain message à envoyer.
    pub fn next_sequence(&self) -> u64 {
        self.next_seq
    }

    /// Hash de chaîne de la dernière entrée (ou GENESIS).
    pub fn last_chain_hash(&self) -> &str {
        &self.last_chain_hash
    }
}

// ─── Utilitaires ─────────────────────────────────────────────────────────────

/// SHA-256 d'un slice d'octets, encodé en hex minuscule.
fn sha256_hex(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{AgentId, SessionId};

    fn make_channel() -> SecureChannel {
        SecureChannel::open(
            AgentId("agent:alice".to_string()),
            AgentId("agent:bob".to_string()),
            SessionId("session:test".to_string()),
            "run:test",
        )
    }

    #[test]
    fn test_send_produit_event_id_et_hash() {
        let mut ch = make_channel();
        let payload = b"hello guardian";
        let msg = ch.send(payload).expect("send doit réussir");

        // L'event_id doit être un UUID non vide
        assert!(!msg.event_id.0.is_empty());
        // Le hash doit être un hex SHA-256 de 64 chars
        assert_eq!(msg.content_hash.len(), 64);
        // La séquence commence à 1
        assert_eq!(msg.sequence_no, 1);
        // Le prochain numéro est 2
        assert_eq!(ch.next_sequence(), 2);
    }

    #[test]
    fn test_send_sequence_monotone() {
        let mut ch = make_channel();
        let m1 = ch.send(b"msg1").unwrap();
        let m2 = ch.send(b"msg2").unwrap();
        let m3 = ch.send(b"msg3").unwrap();

        assert_eq!(m1.sequence_no, 1);
        assert_eq!(m2.sequence_no, 2);
        assert_eq!(m3.sequence_no, 3);
        assert_eq!(ch.next_sequence(), 4);
    }

    #[test]
    fn test_chain_hash_avance() {
        let mut ch = make_channel();
        assert_eq!(ch.last_chain_hash(), GENESIS_HASH);

        ch.send(b"payload").unwrap();
        let h1 = ch.last_chain_hash().to_string();
        assert_ne!(h1, GENESIS_HASH, "Le hash de chaîne doit progresser");

        ch.send(b"payload2").unwrap();
        let h2 = ch.last_chain_hash().to_string();
        assert_ne!(h2, h1, "Chaque send doit faire avancer la chaîne");
    }

    #[test]
    fn test_verify_received_ok() {
        let mut ch = make_channel();
        let payload = b"concept_packet_binary";
        let msg = ch.send(payload).unwrap();

        let rx = SecureChannel::open(
            AgentId("agent:bob".to_string()),
            AgentId("agent:alice".to_string()),
            SessionId("session:test".to_string()),
            "run:test",
        );
        assert!(rx.verify_received(payload, &msg).is_ok());
    }

    #[test]
    fn test_verify_received_detecte_alteration() {
        let mut ch = make_channel();
        let payload = b"original";
        let msg = ch.send(payload).unwrap();

        let rx = SecureChannel::open(
            AgentId("agent:bob".to_string()),
            AgentId("agent:alice".to_string()),
            SessionId("session:test".to_string()),
            "run:test",
        );
        // Payload altéré
        let err = rx.verify_received(b"tampered", &msg);
        assert!(
            matches!(err, Err(ChannelError::ContentHashMismatch { .. })),
            "Une altération doit être détectée"
        );
    }

    #[test]
    fn test_ledger_entry_stream_id_correct() {
        let mut ch = make_channel();
        let msg = ch.send(b"test").unwrap();
        assert_eq!(
            msg.ledger_entry.stream_id,
            "channel:agent:alice->agent:bob"
        );
    }

    #[test]
    fn test_extensions_contiennent_hash_et_receiver() {
        let mut ch = make_channel();
        let payload = b"binary_concept_data";
        let msg = ch.send(payload).unwrap();

        let exts = &msg.ledger_entry.body.extensions;
        assert!(exts.contains_key("channel.content_hash"));
        assert!(exts.contains_key("channel.receiver_id"));
        assert!(exts.contains_key("channel.payload_size"));

        assert_eq!(
            exts["channel.content_hash"].as_str().unwrap(),
            msg.content_hash
        );
        assert_eq!(
            exts["channel.receiver_id"].as_str().unwrap(),
            "agent:bob"
        );
    }
}
