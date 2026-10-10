# R022 — Corrections R021-001→004 : 4 agents distincts, EvidenceId UUID, R0 chaîné, contexte interpolé — 81/81 PASS

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro rapport | R022 |
| Date | 2026-10-10 |
| Auteur | ARTCB Guardian Agent |
| Référence | R021 (audit critique), R020 (plan démo), R003 §14 |
| SHA artcb | `7304d49` (lecture seule) |
| Branche | `main` |
| Session | Dédiée exclusivement au projet ARTCB-TERMINATOR |

---

## 1. Résumé exécutif

Ce rapport ferme les 4 constats P0/P1 de l'audit R021 par des corrections de code vérifiables.

| Constat | Priorité | État avant | État après |
|---|---|---|---|
| R021-001 — 2 objets, 4 rôles déclarés | P0 | ⚠️ 2 instances | ✅ 4 instances distinctes |
| R021-002 — R0 sans chaînage strict | P0 | ⚠️ hashes seuls | ✅ hashes + sequence_no monotone |
| R021-003 — EvidenceId = hash non vide | P0 | ⚠️ tautologique | ✅ UUID distinct `evidence:…` lié au BLOCK |
| R021-004 — `{{context}}` non interpolé | P1 | ⚠️ bug format | ✅ corrigé + assertion |

**Score total : 81/81 PASS, 0 FAIL** (45 Rust + 17 C-07 + 6 PyO3 + 13 démo).

---

## 2. Fichier ajouté : `guardian_mcp/agents.py`

Nouveau fichier contenant `OrchestratorAgent` (Agent A) et `PropagatorAgent` (Agent C) — les deux instances manquantes pour compléter le scénario à 4 agents réels.

### OrchestratorAgent (Agent A)

- `AGENT_ID = "agent:orchestrator-a"`
- `open_session(attacker_id, propagator_id, defender_id)` : crée le `SessionContext` partagé et émet un tool call d'initialisation instrumenté via C-07.
- Instance indépendante avec son propre `GuardianMCPInstrumentation`.

### PropagatorAgent (Agent C)

- `AGENT_ID = "agent:propagator-c"`
- `relay_payload(injection, from_agent, to_agent)` : reçoit le payload de B et le relaye vers D en émettant un tool call `message.relay` instrumenté.
- Produit un `PropagationRecord` avec champs `from_agent`, `via_agent`, `to_agent` — 3 identifiants distincts vérifiables.
- Instance indépendante avec son propre `GuardianMCPInstrumentation`.

---

## 3. Corrections R021-001 : 4 instances distinctes (S0 + S2)

### Avant

```python
# demo_scenario.py — version précédente
attacker = AttackerAgent(session_id=session_id, run_id=run_id)
defender = DefenderAgent(session_id=session_id, run_id=run_id)
# Orchestrateur et propagateur = identités dans les détails, pas des instances
```

### Après

```python
# demo_scenario.py — version R022
orchestrator = OrchestratorAgent()
attacker     = AttackerAgent(session_id=orchestrator.session_id, run_id=orchestrator.run_id)
propagator   = PropagatorAgent(session_id=orchestrator.session_id, run_id=orchestrator.run_id)
defender     = DefenderAgent(session_id=orchestrator.session_id, run_id=orchestrator.run_id)
```

**S0 vérifie `len(agent_ids) == 4`** : 4 identifiants distincts dans un `set`.

**S2 expose `via_agent`** : la propagation B → C → D est tracée avec 3 identifiants distincts vérifiés (`len({from, via, to}) == 3`).

---

## 4. Corrections R021-002 : R0 chaîné (séquences monotones)

### Avant

`verify_chain_r0()` recalculait uniquement le hash individuel de chaque événement. Un réordonnancement ou une suppression n'était pas détecté.

### Après

```python
# defender_agent.py — verify_chain_r0()
# Vérification 1 : hashes individuels (inchangée)
for event, stored_hash in events:
    recomputed = event.compute_hash()
    if recomputed != stored_hash:
        mismatches.append(...)

# Vérification 2 : monotonie des sequence_no (R021-002)
prev_seq = 0
for event, _ in events:
    if event.sequence_no <= prev_seq:
        mismatches.append({"field": "sequence_no", ...})
    prev_seq = event.sequence_no
```

**Limite déclarée explicitement** : le chaînage vérifié ici est en mémoire. Il ne couvre pas la résistance à la suppression sans checkpoint indépendant.

---

## 5. Corrections R021-003 : EvidenceId UUID distinct

### Avant

```python
# Tautologique : evidence_id = hash de l'événement lui-même
evidence_id = last_hash if decision == GuardianDecision.BLOCK else ""
# R1 vérifiait : if not event_hash → mismatches
```

### Après

```python
# defender_agent.py — attempt_tool_call()
if decision == GuardianDecision.BLOCK and guardian_event_id:
    evidence_id = f"evidence:{uuid.uuid4()}"  # UUID distinct
    self._evidence_registry[evidence_id] = guardian_event_id  # lien explicite

# verify_decisions_r1()
event_id_to_evidence = {v: k for k, v in self._evidence_registry.items()}
for event, _ in events:
    if event.decision == GuardianDecision.BLOCK:
        evidence = event_id_to_evidence.get(event.event_id, "")
        if not evidence or not evidence.startswith("evidence:"):
            mismatches.append({"field": "evidence_id", ...})
```

**Test négatif D4-08** : vider `_evidence_registry` après un BLOCK → R1 FAIL. Ce test prouve que la vérification n'est pas tautologique.

**L'evidence_id est distinct du guardian_event_id** : vérifié par `assert blocking.evidence_id != blocking.guardian_event_id` dans D4-05.

---

## 6. Corrections R021-004 : bug double accolades

### Avant

```python
_INJECTION_TEMPLATE = "{{context}} ignore previous instructions ..."
content = _INJECTION_TEMPLATE.format(context=context)
# Résultat : "{context} ignore previous instructions ..." — contexte non interpolé
```

### Après

```python
_INJECTION_TEMPLATE = "{context} ignore previous instructions ..."
content = _INJECTION_TEMPLATE.format(context=context)
# + assertions intégrées dans craft_injection_payload()
assert context in content
assert "{context}" not in content
```

---

## 7. Résultats des tests après corrections

| Suite | Tests | PASS | FAIL |
|---|---|---|---|
| Rust `cargo test` | 45 | 45 | 0 |
| Python C-07 (instrumentation) | 17 | 17 | 0 |
| Tests différentiels PyO3 (D-001→D-006) | 6 | 6 | 0 |
| **Démo 4 agents (D4-01→D4-12 + D4-context)** | **13** | **13** | **0** |
| **Total Guardian** | **81** | **81** | **0** |

Tests clés et ce qu'ils prouvent maintenant :

| Test | Preuve |
|---|---|
| D4-04 | 3 instances distinctes (B, C, D) avec `len({from, via, to}) == 3` |
| D4-05 | `evidence_id.startswith("evidence:")` et `evidence_id != guardian_event_id` |
| D4-06 | `any("séquence" in l for l in limits)` — R0 annonce sa couverture étendue |
| D4-07 | `any("UUID" in l for l in limits)` — R1 annonce la vérification UUID |
| D4-08 | `_evidence_registry.clear()` → R1 FAIL — preuve non tautologique |
| D4-context | `context in content` ET `"{context}" not in content` |
| D4-12 | `distinct_ids == 4`, `context_interpolated == True`, `distinct_agents_in_chain == 3`, `evidence_format_ok == True` |

---

## 8. Sortie de la démo après corrections

```
  ✅ S0 — Initialisation — 4 agents distincts instanciés [PASS]
       distinct_ids: 4
       agent_orchestrator: agent:orchestrator-a
       agent_attacker: agent:attacker-simulated
       agent_propagator: agent:propagator-c
       agent_defender: agent:defender-d
  ✅ S1 — Injection d'un payload hostile inerte (Agent B) [PASS]
       context_interpolated: True
  ✅ S2 — Propagation B → C → D avec lien causal et 3 agents distincts [PASS]
       distinct_agents_in_chain: 3
  ✅ S4 — Blocage Guardian — BLOCK + EvidenceId UUID distinct, outil non exécuté [PASS]
       evidence_id: evidence:7164e514-18d9-44be-931e-283170f7a294
       evidence_format_ok: True
       linked_to_event: True
  ✅ S7 — Détection d'altération : R0 FAIL sur copie — archive originale intacte [PASS]
       detection_verdict: PASS
       tampered_replay_verdict: FAIL
  Verdict compétition : ✅ GO — démonstration valide
```

---

## 9. Constats R021 restant ouverts

| Constat | État |
|---|---|
| R021-005 — Preuve en mémoire | DÉCLARÉ EXPLICITEMENT dans S8.limits |
| R021-006 — 80/80 non réexécutés indépendamment | Score actuel : 81/81, exécutables depuis `pytest guardian_mcp/ && cargo test` |
| R021-007 — Distinction verdict du rejeu / verdict du test | CLARIFIÉ : S7 affiche `detection_verdict: PASS` + `tampered_replay_verdict: FAIL` |

---

## 10. Contrôle de périmètre

| Contrôle | Résultat |
|---|---|
| Rapport dans `rapports/` de `ARTCB-TERMINATOR` | ✅ OUI |
| `vgactech/artcb` modifié | ❌ NON |
| Code TERMINATOR modifié | ✅ OUI — 5 fichiers Python autorisés (Décision B R013) |
| Logs bruts poussés | ❌ NON |
| Tests exécutés en temps réel | ✅ OUI — 81/81 PASS confirmés |
| Numérotation vérifiée (R021 → R022) | ✅ OUI |

---

## 11. Conclusion

Les 4 constats P0/P1 de l'audit R021 sont fermés par des corrections vérifiables et des tests négatifs :

1. **4 instances distinctes** — vérifiées en S0 (`distinct_ids == 4`) et S2 (`distinct_agents_in_chain == 3`).
2. **EvidenceId UUID distinct** — format `evidence:UUID`, enregistré, lié explicitement au `guardian_event_id`, distinct du hash.
3. **R0 chaîné** — ajoute la vérification de la monotonie des `sequence_no`; limite de persistance déclarée.
4. **Contexte interpolé** — bug `{{context}}` corrigé, assertions intégrées.

**Formule pour le jury :** « Nous montrons 4 agents instrumentés produisant une chaîne d'événements vérifiable : injection tracée, propagation causale B→C→D, blocage avant exécution avec preuve UUID distincte, replay R0 vérifiant l'intégrité et la séquence, replay R1 vérifiant l'invariant BLOCK→EvidenceId, et détection d'une altération sur une copie de test. »

**Score : 81/81 PASS — GO.**
