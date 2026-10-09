//! C-02 — Rust Durable Event Store
//!
//! Successeur fonctionnel du WAL C (libartcb_wal.c).
//! Remplace CRC32 par SHA-256 enchaîné pour preuve cryptographique.
//! Garanties : append-only, crash recovery, détection de corruption.

use std::fs::{File, OpenOptions};
use std::io::{BufReader, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::event::ledger::{
    canonicalize, compute_chain_hash, compute_event_hash, validate_event_body,
    DurabilityStatus, EventBody, LedgerEntry, LedgerError, GENESIS_HASH,
    INTEGRITY_PROFILE_VERSION,
};

// ─── Constantes ──────────────────────────────────────────────────────────────

/// Magic identifier du store Guardian (8 octets ASCII)
pub const STORE_MAGIC: &[u8; 8] = b"AGRD\x01\x00\x00\x00";
pub const STORE_VERSION: u32 = 1;

// ─── Store ───────────────────────────────────────────────────────────────────

/// Store durable d'événements Guardian
/// Chaque entrée est précédée de sa longueur (u32 LE) puis sérialisée en JSON.
/// Un fsync est effectué après chaque écriture confirmée.
pub struct DurableEventStore {
    path: PathBuf,
    stream_id: String,
    stream_sequence: u64,
    previous_event_hash: String,
}

impl DurableEventStore {
    /// Ouvre ou crée un store durable
    pub fn open(path: &Path, stream_id: &str) -> Result<Self, LedgerError> {
        // Créer le répertoire parent si nécessaire
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| LedgerError::Io(e.to_string()))?;
        }

        let (stream_sequence, previous_event_hash) = if path.exists() {
            // Récupérer l'état depuis le fichier existant
            Self::recover_state(path)?
        } else {
            // Nouveau store — écrire l'en-tête
            let mut file = File::create(path)
                .map_err(|e| LedgerError::Io(e.to_string()))?;
            file.write_all(STORE_MAGIC)
                .map_err(|e| LedgerError::Io(e.to_string()))?;
            let version_bytes = STORE_VERSION.to_le_bytes();
            file.write_all(&version_bytes)
                .map_err(|e| LedgerError::Io(e.to_string()))?;
            file.sync_all()
                .map_err(|e| LedgerError::Durability(e.to_string()))?;
            (0u64, GENESIS_HASH.to_string())
        };

        Ok(Self {
            path: path.to_path_buf(),
            stream_id: stream_id.to_string(),
            stream_sequence,
            previous_event_hash,
        })
    }

    /// Récupère l'état (séquence + dernier hash) depuis le fichier existant
    fn recover_state(path: &Path) -> Result<(u64, String), LedgerError> {
        let file = File::open(path)
            .map_err(|e| LedgerError::Io(e.to_string()))?;
        let mut reader = BufReader::new(file);

        // Vérifier le magic
        let mut magic = [0u8; 8];
        reader.read_exact(&mut magic)
            .map_err(|e| LedgerError::Io(e.to_string()))?;
        if &magic != STORE_MAGIC {
            return Err(LedgerError::Io("Magic number invalide".to_string()));
        }

        // Lire la version
        let mut version_bytes = [0u8; 4];
        reader.read_exact(&mut version_bytes)
            .map_err(|e| LedgerError::Io(e.to_string()))?;
        let version = u32::from_le_bytes(version_bytes);
        if version != STORE_VERSION {
            return Err(LedgerError::Io(format!(
                "Version store incompatible : {}", version
            )));
        }

        // Relire toutes les entrées pour trouver la dernière
        let mut last_seq = 0u64;
        let mut last_chain_hash = GENESIS_HASH.to_string();

        loop {
            // Lire longueur de l'entrée (u32 LE)
            let mut len_bytes = [0u8; 4];
            match reader.read_exact(&mut len_bytes) {
                Ok(_) => {}
                Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => break,
                Err(e) => return Err(LedgerError::Io(e.to_string())),
            }
            let entry_len = u32::from_le_bytes(len_bytes) as usize;

            // Lire l'entrée
            let mut entry_bytes = vec![0u8; entry_len];
            match reader.read_exact(&mut entry_bytes) {
                Ok(_) => {}
                Err(_) => {
                    // Entrée tronquée — crash pendant écriture
                    // L'entrée partielle est ignorée (pas encore acquittée)
                    break;
                }
            }

            // Désérialiser pour extraire la séquence et le chain_hash
            if let Ok(entry) = serde_json::from_slice::<LedgerEntry>(&entry_bytes) {
                last_seq = entry.stream_sequence;
                last_chain_hash = entry.chain_hash.clone();
            }
        }

        Ok((last_seq, last_chain_hash))
    }

    /// Ajoute un événement au store de manière durable.
    /// Retourne l'entrée complète avec hashes et séquence.
    pub fn append(
        &mut self,
        body: EventBody,
    ) -> Result<LedgerEntry, LedgerError> {
        // 1. Valider le schéma
        validate_event_body(&body)?;

        // 2. Canonicaliser
        let canonical = canonicalize(&body)?;

        // 3. Calculer event_hash
        let event_hash = compute_event_hash(&canonical);

        // 4. Incrémenter la séquence
        self.stream_sequence += 1;

        // 5. Calculer chain_hash
        let chain_hash = compute_chain_hash(
            &self.previous_event_hash,
            &event_hash,
            self.stream_sequence,
        )?;

        // 6. Construire l'entrée
        let entry = LedgerEntry {
            body,
            canonicalization_profile: "JCS-RFC8785".to_string(),
            hash_algorithm: "SHA-256".to_string(),
            event_hash: event_hash.clone(),
            stream_id: self.stream_id.clone(),
            stream_sequence: self.stream_sequence,
            previous_event_hash: self.previous_event_hash.clone(),
            chain_hash: chain_hash.clone(),
            ingested_at: crate::types::utc_now_rfc3339(),
            durability_status: DurabilityStatus::Writing,
            integrity_profile_version: INTEGRITY_PROFILE_VERSION.to_string(),
        };

        // 7. Sérialiser
        let entry_bytes = serde_json::to_vec(&entry)
            .map_err(|e| LedgerError::Serialization(e.to_string()))?;

        // 8. Écrire avec longueur préfixée + fsync
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)
            .map_err(|e| LedgerError::Io(e.to_string()))?;

        let len_bytes = (entry_bytes.len() as u32).to_le_bytes();
        file.write_all(&len_bytes)
            .map_err(|e| LedgerError::Io(e.to_string()))?;
        file.write_all(&entry_bytes)
            .map_err(|e| LedgerError::Io(e.to_string()))?;

        // fsync — garantie de durabilité
        file.sync_all()
            .map_err(|e| LedgerError::Durability(e.to_string()))?;

        // 9. Mettre à jour l'état interne
        self.previous_event_hash = chain_hash;

        // 10. Retourner l'entrée avec statut Durable
        let mut durable_entry = entry;
        durable_entry.durability_status = DurabilityStatus::Durable;
        Ok(durable_entry)
    }

    /// Relit et vérifie toutes les entrées du store.
    /// Retourne FAIL si une altération est détectée.
    pub fn verify_chain(&self) -> Result<VerificationReport, LedgerError> {
        let file = File::open(&self.path)
            .map_err(|e| LedgerError::Io(e.to_string()))?;
        let mut reader = BufReader::new(file);

        // Sauter l'en-tête (8 magic + 4 version)
        reader.seek(SeekFrom::Start(12))
            .map_err(|e| LedgerError::Io(e.to_string()))?;

        let mut entries_checked = 0u64;
        let mut prev_hash = GENESIS_HASH.to_string();
        let mut seq = 0u64;

        loop {
            let mut len_bytes = [0u8; 4];
            match reader.read_exact(&mut len_bytes) {
                Ok(_) => {}
                Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => break,
                Err(e) => return Err(LedgerError::Io(e.to_string())),
            }
            let entry_len = u32::from_le_bytes(len_bytes) as usize;
            let mut entry_bytes = vec![0u8; entry_len];
            reader.read_exact(&mut entry_bytes)
                .map_err(|e| LedgerError::Io(e.to_string()))?;

            let entry: LedgerEntry = serde_json::from_slice(&entry_bytes)
                .map_err(|e| LedgerError::Serialization(e.to_string()))?;

            seq += 1;

            // Recalculer le hash du corps
            let canonical = canonicalize(&entry.body)?;
            let recomputed_event_hash = compute_event_hash(&canonical);

            if recomputed_event_hash != entry.event_hash {
                return Ok(VerificationReport {
                    entries_checked,
                    result: crate::types::VerificationResult::Fail,
                    first_invalid_sequence: Some(seq),
                    error: Some(format!(
                        "event_hash invalide à la séquence {} : attendu {}, calculé {}",
                        seq, entry.event_hash, recomputed_event_hash
                    )),
                });
            }

            // Recalculer le chain_hash
            let recomputed_chain =
                compute_chain_hash(&prev_hash, &entry.event_hash, seq)?;
            if recomputed_chain != entry.chain_hash {
                return Ok(VerificationReport {
                    entries_checked,
                    result: crate::types::VerificationResult::Fail,
                    first_invalid_sequence: Some(seq),
                    error: Some(format!(
                        "chain_hash invalide à la séquence {} : rupture de chaîne",
                        seq
                    )),
                });
            }

            prev_hash = entry.chain_hash.clone();
            entries_checked += 1;
        }

        Ok(VerificationReport {
            entries_checked,
            result: crate::types::VerificationResult::Pass,
            first_invalid_sequence: None,
            error: None,
        })
    }

    pub fn stream_sequence(&self) -> u64 {
        self.stream_sequence
    }
}

/// Rapport de vérification du store
#[derive(Debug, Serialize, Deserialize)]
pub struct VerificationReport {
    pub entries_checked: u64,
    pub result: crate::types::VerificationResult,
    pub first_invalid_sequence: Option<u64>,
    pub error: Option<String>,
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::ledger::build_event;
    use crate::types::{AgentId, DataClassification, OperationStatus, SessionId};
    use tempfile::TempDir;

    fn make_body(seq: u64) -> EventBody {
        build_event(
            "agent.test.event",
            AgentId("agent:test".to_string()),
            SessionId("session-test".to_string()),
            "run-test",
            seq,
            vec![],
            "test_operation",
            OperationStatus::Success,
            None,
            DataClassification::PublicTest,
        )
    }

    #[test]
    fn test_append_et_verify() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join("test.gstore");

        let mut store = DurableEventStore::open(&path, "stream-test").unwrap();
        let e1 = store.append(make_body(1)).unwrap();
        let e2 = store.append(make_body(2)).unwrap();

        assert_eq!(e1.stream_sequence, 1);
        assert_eq!(e2.stream_sequence, 2);
        assert_eq!(e1.durability_status, DurabilityStatus::Durable);

        let report = store.verify_chain().unwrap();
        assert_eq!(
            report.result,
            crate::types::VerificationResult::Pass,
            "La vérification doit passer"
        );
        assert_eq!(report.entries_checked, 2);
    }

    #[test]
    fn test_crash_recovery() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join("crash.gstore");

        // Écrire 3 événements
        {
            let mut store = DurableEventStore::open(&path, "stream-crash").unwrap();
            store.append(make_body(1)).unwrap();
            store.append(make_body(2)).unwrap();
            store.append(make_body(3)).unwrap();
        }

        // Rouvrir — simuler un redémarrage
        let store2 = DurableEventStore::open(&path, "stream-crash").unwrap();
        assert_eq!(store2.stream_sequence(), 3, "La récupération doit retrouver 3 événements");

        let report = store2.verify_chain().unwrap();
        assert_eq!(report.result, crate::types::VerificationResult::Pass);
    }

    #[test]
    fn test_tampering_detecte() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join("tamper.gstore");

        {
            let mut store = DurableEventStore::open(&path, "stream-tamper").unwrap();
            store.append(make_body(1)).unwrap();
        }

        // Corrompre un octet dans le fichier (après l'en-tête de 12 octets)
        let mut contents = std::fs::read(&path).unwrap();
        if contents.len() > 100 {
            contents[80] ^= 0xFF; // Inverser un octet
        }
        std::fs::write(&path, &contents).unwrap();

        // La vérification doit échouer
        // Note : on rouvre sans passer par recover_state pour forcer la vérification
        let file = File::open(&path).unwrap();
        drop(file); // juste pour vérifier que le fichier est lisible

        // Tester directement verify en construisant un store sans recover
        let store = DurableEventStore {
            path: path.clone(),
            stream_id: "stream-tamper".to_string(),
            stream_sequence: 1,
            previous_event_hash: GENESIS_HASH.to_string(),
        };
        let report = store.verify_chain();
        // Doit être soit une erreur soit un FAIL
        match report {
            Ok(r) => assert_eq!(
                r.result,
                crate::types::VerificationResult::Fail,
                "La corruption doit être détectée"
            ),
            Err(_) => {} // Une erreur de désérialisation est aussi acceptable
        }
    }
}
