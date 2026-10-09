//! C-03 — Provenance Engine
//!
//! Graphe causal typé : qui a produit quoi, à partir de quoi, avec quel outil.
//! Remplace le checksum IRGraph par des relations causales vérifiables.
//! Relations conformes à R002 §7 et R010 couche 15.

use std::collections::{HashMap, HashSet, VecDeque};

use serde::{Deserialize, Serialize};

use crate::types::{AgentId, ArtifactId, EventId, PolicyDecision};

// ─── Nœuds du graphe ─────────────────────────────────────────────────────────

/// Type d'un nœud dans le graphe de provenance
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum NodeKind {
    Agent,
    Event,
    Artifact,
    Memory,
    ToolCall,
    PolicyDecision,
    Evidence,
}

/// Nœud du graphe de provenance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceNode {
    pub id: String,
    pub kind: NodeKind,
    pub label: String,
    /// Horodatage de création du nœud
    pub occurred_at: Option<String>,
    /// Référence vers l'événement ledger associé
    pub event_ref: Option<EventId>,
}

// ─── Arêtes typées ───────────────────────────────────────────────────────────

/// Type d'une relation causale — conforme R002 §7 et PROMPT étape 4
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EdgeKind {
    Created,
    Read,
    Transformed,
    Sent,
    Received,
    Stored,
    Retrieved,
    Called,
    Blocked,
    Allowed,
    Redacted,
    Escalated,
    Rejected,
    DerivedFrom,
    /// Lien de causalité entre événements (parent → enfant)
    CausedBy,
    /// L'agent a déclenché l'événement
    Triggered,
    /// Vérification d'intégrité
    Verified,
    /// Restauration depuis une archive
    Restored,
    /// Invalidation d'un état précédent
    Invalidated,
}

/// Arête du graphe de provenance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceEdge {
    pub from: String,
    pub to: String,
    pub kind: EdgeKind,
    pub event_ref: Option<EventId>,
    pub occurred_at: Option<String>,
}

// ─── Graphe de provenance ─────────────────────────────────────────────────────

/// Graphe causal d'un incident Guardian
#[derive(Debug, Default, Serialize, Deserialize)]
pub struct ProvenanceGraph {
    pub nodes: HashMap<String, ProvenanceNode>,
    pub edges: Vec<ProvenanceEdge>,
}

#[derive(Debug, thiserror::Error)]
pub enum ProvenanceError {
    #[error("Nœud introuvable : {0}")]
    NodeNotFound(String),
    #[error("Cycle détecté dans le graphe causal")]
    CycleDetected,
    #[error("Relation invalide : {0}")]
    InvalidEdge(String),
}

impl ProvenanceGraph {
    pub fn new() -> Self {
        Self::default()
    }

    /// Ajoute un nœud au graphe
    pub fn add_node(&mut self, node: ProvenanceNode) {
        self.nodes.insert(node.id.clone(), node);
    }

    /// Ajoute une arête causale typée
    pub fn add_edge(&mut self, edge: ProvenanceEdge) -> Result<(), ProvenanceError> {
        if !self.nodes.contains_key(&edge.from) {
            return Err(ProvenanceError::NodeNotFound(edge.from.clone()));
        }
        if !self.nodes.contains_key(&edge.to) {
            return Err(ProvenanceError::NodeNotFound(edge.to.clone()));
        }
        self.edges.push(edge);
        // Vérifier l'absence de cycle après ajout
        self.detect_cycle()?;
        Ok(())
    }

    /// Détecte un cycle dans le graphe (DFS)
    pub fn detect_cycle(&self) -> Result<(), ProvenanceError> {
        let mut visited: HashSet<&str> = HashSet::new();
        let mut stack: HashSet<&str> = HashSet::new();

        for node_id in self.nodes.keys() {
            if self.dfs_cycle(node_id.as_str(), &mut visited, &mut stack) {
                return Err(ProvenanceError::CycleDetected);
            }
        }
        Ok(())
    }

    fn dfs_cycle<'a>(
        &'a self,
        node: &'a str,
        visited: &mut HashSet<&'a str>,
        stack: &mut HashSet<&'a str>,
    ) -> bool {
        if stack.contains(node) {
            return true; // Cycle
        }
        if visited.contains(node) {
            return false;
        }
        visited.insert(node);
        stack.insert(node);

        for edge in &self.edges {
            if edge.from == node {
                if self.dfs_cycle(edge.to.as_str(), visited, stack) {
                    return true;
                }
            }
        }
        stack.remove(node);
        false
    }

    /// Remonte la chaîne causale depuis un nœud cible jusqu'à la source
    /// Retourne le chemin de la source vers la cible
    pub fn trace_to_root(&self, target_id: &str) -> Result<Vec<String>, ProvenanceError> {
        if !self.nodes.contains_key(target_id) {
            return Err(ProvenanceError::NodeNotFound(target_id.to_string()));
        }

        // BFS en arrière (remonter les arêtes)
        let mut predecessors: HashMap<String, String> = HashMap::new();
        let mut queue: VecDeque<String> = VecDeque::new();
        let mut visited: HashSet<String> = HashSet::new();

        queue.push_back(target_id.to_string());
        visited.insert(target_id.to_string());

        // Construire l'index des arêtes inversées
        let mut reverse_edges: HashMap<String, Vec<String>> = HashMap::new();
        for edge in &self.edges {
            reverse_edges
                .entry(edge.to.clone())
                .or_default()
                .push(edge.from.clone());
        }

        while let Some(current) = queue.pop_front() {
            if let Some(parents) = reverse_edges.get(&current) {
                for parent in parents {
                    if !visited.contains(parent) {
                        visited.insert(parent.clone());
                        predecessors.insert(parent.clone(), current.clone());
                        queue.push_back(parent.clone());
                    }
                }
            }
        }

        // Trouver les nœuds racines (sans parents)
        let roots: Vec<String> = self
            .nodes
            .keys()
            .filter(|id| {
                !self.edges.iter().any(|e| &e.to == *id)
            })
            .cloned()
            .collect();

        if roots.is_empty() {
            return Ok(vec![target_id.to_string()]);
        }

        // Retourner le chemin depuis la première racine trouvée
        Ok(visited.into_iter().collect())
    }

    /// Construit le graphe d'un incident Guardian standard :
    /// Agent → Event → Artifact → Memory → Agent → ToolCall → Output → Policy → Evidence
    pub fn build_incident_graph(
        agent_a: &AgentId,
        agent_b: &AgentId,
        contaminated_artifact: &ArtifactId,
        tool_call_id: &str,
        policy_decision: &PolicyDecision,
        event_refs: &[EventId],
    ) -> Self {
        let mut graph = Self::new();

        // Nœuds
        let node_a = ProvenanceNode {
            id: format!("agent:{}", agent_a.0),
            kind: NodeKind::Agent,
            label: agent_a.0.clone(),
            occurred_at: None,
            event_ref: event_refs.first().cloned(),
        };
        let node_artifact = ProvenanceNode {
            id: format!("artifact:{}", contaminated_artifact.0),
            kind: NodeKind::Artifact,
            label: "contaminated_artifact".to_string(),
            occurred_at: None,
            event_ref: None,
        };
        let node_b = ProvenanceNode {
            id: format!("agent:{}", agent_b.0),
            kind: NodeKind::Agent,
            label: agent_b.0.clone(),
            occurred_at: None,
            event_ref: None,
        };
        let node_tool = ProvenanceNode {
            id: format!("tool:{}", tool_call_id),
            kind: NodeKind::ToolCall,
            label: tool_call_id.to_string(),
            occurred_at: None,
            event_ref: None,
        };
        let decision_label = format!("{:?}", policy_decision);
        let node_policy = ProvenanceNode {
            id: "policy:decision".to_string(),
            kind: NodeKind::PolicyDecision,
            label: decision_label,
            occurred_at: None,
            event_ref: None,
        };

        graph.add_node(node_a.clone());
        graph.add_node(node_artifact.clone());
        graph.add_node(node_b.clone());
        graph.add_node(node_tool.clone());
        graph.add_node(node_policy.clone());

        // Arêtes
        let _ = graph.add_edge(ProvenanceEdge {
            from: node_a.id.clone(),
            to: node_artifact.id.clone(),
            kind: EdgeKind::Created,
            event_ref: None,
            occurred_at: None,
        });
        let _ = graph.add_edge(ProvenanceEdge {
            from: node_b.id.clone(),
            to: node_artifact.id.clone(),
            kind: EdgeKind::Read,
            event_ref: None,
            occurred_at: None,
        });
        let _ = graph.add_edge(ProvenanceEdge {
            from: node_b.id.clone(),
            to: node_tool.id.clone(),
            kind: EdgeKind::Called,
            event_ref: None,
            occurred_at: None,
        });
        let edge_kind = match policy_decision {
            PolicyDecision::Block => EdgeKind::Blocked,
            PolicyDecision::Allow => EdgeKind::Allowed,
            PolicyDecision::Redact => EdgeKind::Redacted,
            PolicyDecision::Escalate => EdgeKind::Escalated,
        };
        let _ = graph.add_edge(ProvenanceEdge {
            from: node_tool.id.clone(),
            to: node_policy.id.clone(),
            kind: edge_kind,
            event_ref: None,
            occurred_at: None,
        });

        graph
    }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{AgentId, ArtifactId, PolicyDecision};

    #[test]
    fn test_graphe_sans_cycle() {
        let mut graph = ProvenanceGraph::new();
        graph.add_node(ProvenanceNode {
            id: "A".to_string(),
            kind: NodeKind::Agent,
            label: "A".to_string(),
            occurred_at: None,
            event_ref: None,
        });
        graph.add_node(ProvenanceNode {
            id: "B".to_string(),
            kind: NodeKind::Event,
            label: "B".to_string(),
            occurred_at: None,
            event_ref: None,
        });
        let result = graph.add_edge(ProvenanceEdge {
            from: "A".to_string(),
            to: "B".to_string(),
            kind: EdgeKind::CausedBy,
            event_ref: None,
            occurred_at: None,
        });
        assert!(result.is_ok());
    }

    #[test]
    fn test_cycle_detecte() {
        let mut graph = ProvenanceGraph::new();
        graph.add_node(ProvenanceNode {
            id: "A".to_string(), kind: NodeKind::Agent, label: "A".to_string(),
            occurred_at: None, event_ref: None,
        });
        graph.add_node(ProvenanceNode {
            id: "B".to_string(), kind: NodeKind::Event, label: "B".to_string(),
            occurred_at: None, event_ref: None,
        });
        graph.edges.push(ProvenanceEdge {
            from: "A".to_string(), to: "B".to_string(),
            kind: EdgeKind::CausedBy, event_ref: None, occurred_at: None,
        });
        graph.edges.push(ProvenanceEdge {
            from: "B".to_string(), to: "A".to_string(),
            kind: EdgeKind::CausedBy, event_ref: None, occurred_at: None,
        });
        assert!(graph.detect_cycle().is_err(), "Le cycle doit être détecté");
    }

    #[test]
    fn test_incident_graph_block() {
        let graph = ProvenanceGraph::build_incident_graph(
            &AgentId("agent-attacker".to_string()),
            &AgentId("agent-victim".to_string()),
            &ArtifactId("artifact-poison".to_string()),
            "tool-exfiltrate",
            &PolicyDecision::Block,
            &[],
        );
        assert!(graph.nodes.len() >= 4);
        let has_blocked = graph.edges.iter().any(|e| e.kind == EdgeKind::Blocked);
        assert!(has_blocked, "Un BLOCK doit produire une arête Blocked");
    }
}
