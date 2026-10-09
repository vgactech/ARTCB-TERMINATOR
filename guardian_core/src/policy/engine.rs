//! C-05 — Rust Policy / Firewall Core
//!
//! Décisions Guardian : ALLOW / BLOCK / REDACT / ESCALATE
//! Chaque BLOCK produit un EvidenceId enregistré dans le ledger.
//! Le moteur interne conserve PolicyReason pour tracer exactement ce qui s'est passé.
//! Conforme Décision 1 Option B validée dans R013.

use serde::{Deserialize, Serialize};

use crate::event::ledger::PolicyInfo;
use crate::types::{
    AgentId, EventId, EvidenceId, PolicyDecision, PolicyId, PolicyReason, SessionId,
};

// ─── Politique versionnée ─────────────────────────────────────────────────────

/// Une règle de politique Guardian
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyRule {
    pub id: String,
    pub description: String,
    pub condition: PolicyCondition,
    pub decision: PolicyDecision,
    pub reason: PolicyReason,
}

/// Condition déclenchant une règle
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum PolicyCondition {
    /// Outil interdit par son nom
    ForbiddenTool { tool_name: String },
    /// Tentative d'exfiltration vers un domaine externe
    ExfiltrationAttempt { pattern: String },
    /// Injection de prompt détectée
    PromptInjection { indicator: String },
    /// Contamination mémoire
    MemoryPoisoning,
    /// Classification sensible détectée
    SensitiveClassification { min_level: u8 },
    /// Toujours bloquer (catch-all)
    AlwaysBlock,
    /// Toujours autoriser
    AlwaysAllow,
}

/// Moteur de politique Guardian
pub struct PolicyEngine {
    pub policy_id: PolicyId,
    pub policy_version: String,
    pub rules: Vec<PolicyRule>,
}

/// Entrée soumise au moteur de politique
#[derive(Debug)]
pub struct PolicyInput {
    pub agent_id: AgentId,
    pub session_id: SessionId,
    pub event_id: EventId,
    pub tool_name: Option<String>,
    pub output_content: Option<String>,
    pub classification_level: u8,
    pub is_external_destination: bool,
    pub contains_prompt_injection_indicators: bool,
}

/// Résultat d'une décision de politique
#[derive(Debug, Serialize, Deserialize)]
pub struct PolicyResult {
    pub decision: PolicyDecision,
    pub reason: PolicyReason,
    pub policy_id: String,
    pub policy_version: String,
    pub evidence_id: Option<EvidenceId>,
    pub matching_rule_id: Option<String>,
    pub agent_id: AgentId,
    pub event_id: EventId,
}

impl PolicyEngine {
    /// Crée un moteur de politique Guardian avec les règles P0
    pub fn guardian_default() -> Self {
        Self {
            policy_id: PolicyId("guardian-policy-p0".to_string()),
            policy_version: "1.0.0".to_string(),
            rules: vec![
                PolicyRule {
                    id: "P0-EXFIL".to_string(),
                    description: "Bloquer toute tentative d'exfiltration".to_string(),
                    condition: PolicyCondition::ExfiltrationAttempt {
                        pattern: "exfil".to_string(),
                    },
                    decision: PolicyDecision::Block,
                    reason: PolicyReason::ExfiltrationAttempt,
                },
                PolicyRule {
                    id: "P0-INJECT".to_string(),
                    description: "Bloquer les injections de prompt".to_string(),
                    condition: PolicyCondition::PromptInjection {
                        indicator: "ignore previous".to_string(),
                    },
                    decision: PolicyDecision::Block,
                    reason: PolicyReason::PromptInjection,
                },
                PolicyRule {
                    id: "P0-POISON".to_string(),
                    description: "Escalader les contaminations mémoire".to_string(),
                    condition: PolicyCondition::MemoryPoisoning,
                    decision: PolicyDecision::Escalate,
                    reason: PolicyReason::MemoryPoisoning,
                },
                PolicyRule {
                    id: "P0-SENSITIVE".to_string(),
                    description: "Masquer les données de classification >= 3".to_string(),
                    condition: PolicyCondition::SensitiveClassification { min_level: 3 },
                    decision: PolicyDecision::Redact,
                    reason: PolicyReason::SensitiveDataMasked,
                },
                PolicyRule {
                    id: "P0-DEFAULT-ALLOW".to_string(),
                    description: "Autoriser par défaut".to_string(),
                    condition: PolicyCondition::AlwaysAllow,
                    decision: PolicyDecision::Allow,
                    reason: PolicyReason::PolicyApplied,
                },
            ],
        }
    }

    /// Évalue une entrée et retourne la décision avec preuve si BLOCK/REDACT/ESCALATE
    pub fn evaluate(&self, input: &PolicyInput) -> PolicyResult {
        for rule in &self.rules {
            if self.matches(&rule.condition, input) {
                let evidence_id = match rule.decision {
                    PolicyDecision::Allow => None,
                    _ => Some(EvidenceId::new()),
                };
                return PolicyResult {
                    decision: rule.decision.clone(),
                    reason: rule.reason.clone(),
                    policy_id: self.policy_id.0.clone(),
                    policy_version: self.policy_version.clone(),
                    evidence_id,
                    matching_rule_id: Some(rule.id.clone()),
                    agent_id: input.agent_id.clone(),
                    event_id: input.event_id.clone(),
                };
            }
        }
        // Fallback — ne devrait pas arriver car AlwaysAllow est en dernier
        PolicyResult {
            decision: PolicyDecision::Block,
            reason: PolicyReason::Unauthorized,
            policy_id: self.policy_id.0.clone(),
            policy_version: self.policy_version.clone(),
            evidence_id: Some(EvidenceId::new()),
            matching_rule_id: None,
            agent_id: input.agent_id.clone(),
            event_id: input.event_id.clone(),
        }
    }

    fn matches(&self, condition: &PolicyCondition, input: &PolicyInput) -> bool {
        match condition {
            PolicyCondition::ForbiddenTool { tool_name } => {
                input.tool_name.as_deref() == Some(tool_name.as_str())
            }
            PolicyCondition::ExfiltrationAttempt { pattern } => {
                input.is_external_destination
                    || input
                        .output_content
                        .as_deref()
                        .unwrap_or("")
                        .to_lowercase()
                        .contains(pattern.as_str())
            }
            PolicyCondition::PromptInjection { indicator } => {
                input.contains_prompt_injection_indicators
                    || input
                        .output_content
                        .as_deref()
                        .unwrap_or("")
                        .to_lowercase()
                        .contains(indicator.as_str())
            }
            PolicyCondition::MemoryPoisoning => false, // Déclenché explicitement
            PolicyCondition::SensitiveClassification { min_level } => {
                input.classification_level >= *min_level
            }
            PolicyCondition::AlwaysBlock => true,
            PolicyCondition::AlwaysAllow => true,
        }
    }

    /// Construit le PolicyInfo à intégrer dans un EventBody
    pub fn to_policy_info(&self, result: &PolicyResult) -> PolicyInfo {
        PolicyInfo {
            policy_id: self.policy_id.clone(),
            policy_version: self.policy_version.clone(),
            decision: result.decision.clone(),
            reason: result.reason.clone(),
            evidence_id: result.evidence_id.as_ref().map(|e| e.0.clone()),
        }
    }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{AgentId, EventId, PolicyDecision, SessionId};

    fn make_input(tool: Option<&str>, external: bool, injection: bool, level: u8) -> PolicyInput {
        PolicyInput {
            agent_id: AgentId("agent:test".to_string()),
            session_id: SessionId("session:test".to_string()),
            event_id: EventId::new(),
            tool_name: tool.map(|s| s.to_string()),
            output_content: None,
            classification_level: level,
            is_external_destination: external,
            contains_prompt_injection_indicators: injection,
        }
    }

    #[test]
    fn test_exfiltration_bloquee() {
        let engine = PolicyEngine::guardian_default();
        let input = make_input(None, true, false, 1);
        let result = engine.evaluate(&input);
        assert_eq!(result.decision, PolicyDecision::Block);
        assert!(result.evidence_id.is_some(), "BLOCK doit produire un EvidenceId");
    }

    #[test]
    fn test_injection_bloquee() {
        let engine = PolicyEngine::guardian_default();
        let input = make_input(None, false, true, 1);
        let result = engine.evaluate(&input);
        assert_eq!(result.decision, PolicyDecision::Block);
        assert!(result.evidence_id.is_some());
    }

    #[test]
    fn test_donnee_sensible_redactee() {
        let engine = PolicyEngine::guardian_default();
        let input = make_input(None, false, false, 4); // niveau >= 3
        let result = engine.evaluate(&input);
        assert_eq!(result.decision, PolicyDecision::Redact);
        assert!(result.evidence_id.is_some(), "REDACT doit produire un EvidenceId");
    }

    #[test]
    fn test_operation_normale_autorisee() {
        let engine = PolicyEngine::guardian_default();
        let input = make_input(None, false, false, 1);
        let result = engine.evaluate(&input);
        assert_eq!(result.decision, PolicyDecision::Allow);
        assert!(result.evidence_id.is_none(), "ALLOW ne produit pas d'EvidenceId");
    }

    #[test]
    fn test_policy_info_contient_reason() {
        let engine = PolicyEngine::guardian_default();
        let input = make_input(None, true, false, 1);
        let result = engine.evaluate(&input);
        let info = engine.to_policy_info(&result);
        // La raison interne est préservée (Décision 1 Option B)
        assert_eq!(info.reason, PolicyReason::ExfiltrationAttempt);
        assert_eq!(info.decision, PolicyDecision::Block);
    }

    // ── F-013 — Donnée sensible dans une zone interdite ───────────────────────
    // R006 §6 : BLOCK ou REDACT selon le profil de classification.
    // classification_level >= 3 → REDACT (confidentiel)
    // classification_level >= 3 + destination externe → BLOCK (exfiltration)
    #[test]
    fn test_f013_donnee_sensible_zone_interdite_redact() {
        let engine = PolicyEngine::guardian_default();
        // Niveau 3 (Confidential) sans destination externe → REDACT
        let input = make_input(None, false, false, 3);
        let result = engine.evaluate(&input);
        assert_eq!(
            result.decision,
            PolicyDecision::Redact,
            "F-013 : donnée confidentielle doit être redactée"
        );
        assert!(result.evidence_id.is_some(), "F-013 : REDACT doit produire un EvidenceId");
    }

    #[test]
    fn test_f013_donnee_sensible_zone_interdite_block() {
        let engine = PolicyEngine::guardian_default();
        // Niveau 3 + destination externe → BLOCK (exfiltration prioritaire)
        let input = make_input(None, true, false, 3);
        let result = engine.evaluate(&input);
        assert_eq!(
            result.decision,
            PolicyDecision::Block,
            "F-013 : tentative d'exfiltration de donnée confidentielle → BLOCK"
        );
        assert!(result.evidence_id.is_some());
    }
}
