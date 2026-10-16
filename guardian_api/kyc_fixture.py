"""
ARTCB TERMINATOR — KYC Fixture synthétique
SIMULATED: toutes les données sont générées de façon déterministe.
Aucune donnée réelle, aucun PII, aucun flux tiers requis.
Mode DEBUG actif. CERTIFIED_100=false.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

# Marqueur obligatoire ARTCB
DATA_SOURCE = "SIMULATED"
CERTIFIED_100 = False
UNIQUE_HUMAN_PROVEN = False


@dataclass
class KycIdentity:
    """Identité KYC synthétique — SIMULATED."""
    first_name: str
    last_name: str
    doc_id: str
    dob: str
    nationality: str = "FR"
    source: str = DATA_SOURCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "doc_id": self.doc_id,
            "dob": self.dob,
            "nationality": self.nationality,
            "source": self.source,
            "certified_100": CERTIFIED_100,
            "unique_human_proven": UNIQUE_HUMAN_PROVEN,
        }


@dataclass
class KycEvent:
    """Événement d'audit KYC — schéma stable."""
    event_id: str
    run_id: str
    timestamp: float
    source: str          # "guardian" | "attacker" | "system"
    severity: str        # "INFO" | "WARNING" | "CRITICAL"
    action: str
    detail: str
    blocked: bool = False
    data_source: str = DATA_SOURCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "severity": self.severity,
            "action": self.action,
            "detail": self.detail,
            "blocked": self.blocked,
            "data_source": self.data_source,
        }


@dataclass
class KycFixtureResult:
    """Résultat complet d'un scénario KYC synthétique."""
    run_id: str
    identity: KycIdentity
    events: list[KycEvent] = field(default_factory=list)
    verdict: str = "PENDING"   # APPROVED | REJECTED | PENDING
    score: int = 0             # 0–100
    attacks_blocked: int = 0
    chain_hash: str = ""
    data_source: str = DATA_SOURCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "identity": self.identity.to_dict(),
            "events": [e.to_dict() for e in self.events],
            "verdict": self.verdict,
            "score": self.score,
            "attacks_blocked": self.attacks_blocked,
            "chain_hash": self.chain_hash,
            "data_source": self.data_source,
            "certified_100": CERTIFIED_100,
            "unique_human_proven": UNIQUE_HUMAN_PROVEN,
        }


def build_kyc_fixture(
    run_id: str,
    first_name: str = "Alice",
    last_name: str = "Dupont",
    doc_id: str = "FR-2024-000000",
    dob: str = "1990-01-01",
    attack_type: str = "wallet.sign",
) -> KycFixtureResult:
    """
    Construit une fixture KYC synthétique déterministe.

    Le résultat est entièrement SIMULATED — reproductible à partir des mêmes
    paramètres. Aucune randomisation dépendant de l'horloge dans les champs
    fonctionnels (run_id est fourni par le ScenarioController).
    """
    t0 = time.time()
    identity = KycIdentity(
        first_name=first_name,
        last_name=last_name,
        doc_id=doc_id,
        dob=dob,
    )

    events: list[KycEvent] = [
        KycEvent(
            event_id=f"{run_id}:evt:001",
            run_id=run_id,
            timestamp=t0,
            source="system",
            severity="INFO",
            action="session.open",
            detail=f"KYC session opened for {first_name} {last_name}",
        ),
        KycEvent(
            event_id=f"{run_id}:evt:002",
            run_id=run_id,
            timestamp=t0 + 0.1,
            source="guardian",
            severity="INFO",
            action="identity.verify",
            detail=f"Document {doc_id} verified (SIMULATED)",
        ),
        KycEvent(
            event_id=f"{run_id}:evt:003",
            run_id=run_id,
            timestamp=t0 + 0.2,
            source="attacker",
            severity="CRITICAL",
            action=attack_type,
            detail=f"Hostile tool invocation: {attack_type} — attempt to exfiltrate",
            blocked=True,
        ),
        KycEvent(
            event_id=f"{run_id}:evt:004",
            run_id=run_id,
            timestamp=t0 + 0.3,
            source="guardian",
            severity="WARNING",
            action="policy.block",
            detail=f"Guardian blocked {attack_type} — policy DENY matched",
            blocked=False,
        ),
        KycEvent(
            event_id=f"{run_id}:evt:005",
            run_id=run_id,
            timestamp=t0 + 0.4,
            source="guardian",
            severity="INFO",
            action="chain.seal",
            detail="Event chain sealed — cryptographic proof anchored",
        ),
    ]

    attacks_blocked = sum(1 for e in events if e.blocked)
    score = max(0, 100 - (attacks_blocked * 15))
    verdict = "APPROVED" if score >= 70 else "REJECTED"

    # Empreinte déterministe de la chaîne d'événements
    chain_raw = "|".join(e.event_id for e in events)
    chain_hash = hashlib.sha256(chain_raw.encode()).hexdigest()

    return KycFixtureResult(
        run_id=run_id,
        identity=identity,
        events=events,
        verdict=verdict,
        score=score,
        attacks_blocked=attacks_blocked,
        chain_hash=chain_hash,
    )
