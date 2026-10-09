//! C-08 — Bindings PyO3
//!
//! Expose les 8 fonctions principales du Guardian Core comme module Python.
//! Ce module n'est compilé que lorsque la feature "python" est activée
//! (via maturin ou --features python).
//!
//! # Usage Python
//!
//! ```python,ignore
//! import artcb_guardian_core as guardian
//!
//! # Construire un événement
//! body_json = guardian.build_event_json(
//!     event_type="agent.input.received",
//!     agent_id="agent:test",
//!     session_id="session:abc",
//!     run_id="run:xyz",
//!     sequence_no=1,
//!     operation_name="receive_input",
//! )
//!
//! # Canonicaliser et hasher
//! canonical = guardian.canonicalize_json(body_json)
//! digest = guardian.compute_event_hash_from_canonical(canonical)
//!
//! # Évaluer une politique
//! result = guardian.evaluate_policy(
//!     agent_id="agent:test",
//!     event_id="evt:123",
//!     session_id="session:abc",
//!     tool_name="blockchain.query",
//!     classification_level=0,
//!     is_external_destination=False,
//!     contains_injection=False,
//! )
//! ```

#[cfg(feature = "python")]
mod python_bindings {
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;

    use crate::event::ledger::{
        build_event, canonicalize, compute_event_hash, validate_event_body,
    };
    use crate::policy::engine::{PolicyEngine, PolicyInput};
    use crate::types::{
        AgentId, DataClassification, EventId, OperationStatus, SessionId,
    };

    // ─── Helpers de conversion d'erreur ──────────────────────────────────────

    fn ledger_err(e: impl std::fmt::Display) -> PyErr {
        PyValueError::new_err(e.to_string())
    }

    // ─── Fonctions exposées ───────────────────────────────────────────────────

    /// Construit un corps d'événement Guardian et retourne du JSON.
    #[pyfunction]
    #[pyo3(signature = (
        event_type,
        agent_id,
        session_id,
        run_id,
        sequence_no,
        operation_name,
        classification = 0u8,
    ))]
    fn build_event_json(
        event_type: &str,
        agent_id: &str,
        session_id: &str,
        run_id: &str,
        sequence_no: u64,
        operation_name: &str,
        classification: u8,
    ) -> PyResult<String> {
        let class = match classification {
            0 => DataClassification::PublicTest,
            1 => DataClassification::Public,
            2 => DataClassification::Internal,
            3 => DataClassification::Confidential,
            4 => DataClassification::TopSecret,
            _ => return Err(PyValueError::new_err("classification invalide (0–4)")),
        };
        let body = build_event(
            event_type,
            AgentId(agent_id.to_string()),
            SessionId(session_id.to_string()),
            run_id,
            sequence_no,
            vec![],
            operation_name,
            OperationStatus::Success,
            None,
            class,
        );
        serde_json::to_string(&body).map_err(ledger_err)
    }

    /// Canonicalise un corps d'événement JSON (JCS RFC 8785).
    /// Retourne les octets canoniques (str UTF-8).
    #[pyfunction]
    fn canonicalize_json(body_json: &str) -> PyResult<String> {
        let body: crate::event::ledger::EventBody =
            serde_json::from_str(body_json).map_err(ledger_err)?;
        let bytes = canonicalize(&body).map_err(ledger_err)?;
        String::from_utf8(bytes).map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Calcule le hash SHA-256 d'un corps canonique (préfixe domaine inclus).
    /// `canonical` est la chaîne retournée par `canonicalize_json`.
    #[pyfunction]
    fn compute_event_hash_from_canonical(canonical: &str) -> String {
        compute_event_hash(canonical.as_bytes())
    }

    /// Valide les champs obligatoires d'un corps d'événement JSON.
    /// Retourne `None` si valide, ou un message d'erreur.
    #[pyfunction]
    fn validate_event_body_json(body_json: &str) -> PyResult<Option<String>> {
        let body: crate::event::ledger::EventBody =
            serde_json::from_str(body_json).map_err(ledger_err)?;
        match validate_event_body(&body) {
            Ok(()) => Ok(None),
            Err(e) => Ok(Some(e.to_string())),
        }
    }

    /// Évalue la politique Guardian pour un appel d'outil.
    ///
    /// Retourne un dict Python :
    ///   { "decision": str, "reason": str, "evidence_id": str | None }
    #[pyfunction]
    #[pyo3(signature = (
        agent_id,
        event_id,
        session_id,
        tool_name = None,
        output_content = None,
        classification_level = 0u8,
        is_external_destination = false,
        contains_injection = false,
    ))]
    fn evaluate_policy(
        py: Python<'_>,
        agent_id: &str,
        event_id: &str,
        session_id: &str,
        tool_name: Option<&str>,
        output_content: Option<&str>,
        classification_level: u8,
        is_external_destination: bool,
        contains_injection: bool,
    ) -> PyResult<PyObject> {
        let input = PolicyInput {
            agent_id: AgentId(agent_id.to_string()),
            event_id: EventId(event_id.to_string()),
            session_id: SessionId(session_id.to_string()),
            tool_name: tool_name.map(str::to_string),
            output_content: output_content.map(str::to_string),
            classification_level,
            is_external_destination,
            contains_prompt_injection_indicators: contains_injection,
        };

        let engine = PolicyEngine::guardian_default();
        let result = engine.evaluate(&input);

        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("decision", result.decision.to_string())?;
        dict.set_item("reason", format!("{:?}", result.reason))?;
        dict.set_item(
            "evidence_id",
            result.evidence_id.map(|e| e.0),
        )?;
        Ok(dict.into())
    }

    /// Génère un nouvel EventId (UUIDv7).
    #[pyfunction]
    fn new_event_id() -> String {
        EventId::new().0
    }

    /// Retourne le digest golden F-001 de référence (R006).
    #[pyfunction]
    fn golden_f001_digest() -> &'static str {
        "c067e20378788d5d32e25c489064efd624224596c1987b5315f8dde296892f11"
    }

    /// Retourne la version du profil d'intégrité.
    #[pyfunction]
    fn integrity_profile_version() -> &'static str {
        crate::event::ledger::INTEGRITY_PROFILE_VERSION
    }

    // ─── Module Python ────────────────────────────────────────────────────────

    #[pymodule]
    pub fn artcb_guardian_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(build_event_json, m)?)?;
        m.add_function(wrap_pyfunction!(canonicalize_json, m)?)?;
        m.add_function(wrap_pyfunction!(compute_event_hash_from_canonical, m)?)?;
        m.add_function(wrap_pyfunction!(validate_event_body_json, m)?)?;
        m.add_function(wrap_pyfunction!(evaluate_policy, m)?)?;
        m.add_function(wrap_pyfunction!(new_event_id, m)?)?;
        m.add_function(wrap_pyfunction!(golden_f001_digest, m)?)?;
        m.add_function(wrap_pyfunction!(integrity_profile_version, m)?)?;
        m.add("__version__", env!("CARGO_PKG_VERSION"))?;
        Ok(())
    }
}

// Point d'entrée PyO3 quand la feature "python" est activée
#[cfg(feature = "python")]
pub use python_bindings::artcb_guardian_core;
