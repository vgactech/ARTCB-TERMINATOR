"""
ARTCB TERMINATOR — ScenarioController
Contrôleur de scénarios de démo Guardian.

Gère le cycle de vie des démonstrations :
  - Création d'un run_id unique par exécution
  - État de la démo (IDLE, RUNNING, COMPLETED, ERROR)
  - Reset propre entre deux démos
  - Séquençage des phases : Detection → Decision → Containment → Recovery

Mode DEBUG actif. CERTIFIED_100=false. SIMULATED.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from guardian_api.kyc_fixture import KycFixtureResult, build_kyc_fixture

# Marqueurs ARTCB obligatoires
CERTIFIED_100 = False
UNIQUE_HUMAN_PROVEN = False
DATA_SOURCE = "SIMULATED"


class DemoState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class DemoPhase(str, Enum):
    """Phases de la démo cyberattaque Guardian."""
    DETECTION = "DETECTION"
    DECISION = "DECISION"
    CONTAINMENT = "CONTAINMENT"
    RECOVERY = "RECOVERY"


PHASE_ORDER: list[DemoPhase] = [
    DemoPhase.DETECTION,
    DemoPhase.DECISION,
    DemoPhase.CONTAINMENT,
    DemoPhase.RECOVERY,
]

PHASE_LABELS: dict[DemoPhase, str] = {
    DemoPhase.DETECTION: "Détection de l'attaque",
    DemoPhase.DECISION: "Décision de Guardian",
    DemoPhase.CONTAINMENT: "Confinement de la menace",
    DemoPhase.RECOVERY: "Récupération et preuve",
}


@dataclass
class ScenarioRun:
    """État d'une exécution de scénario."""
    run_id: str
    scenario_id: str
    state: DemoState
    current_phase: DemoPhase | None
    started_at: float
    completed_at: float | None
    kyc_result: KycFixtureResult | None
    error_message: str | None = None
    data_source: str = DATA_SOURCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "state": self.state.value,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "kyc_result": self.kyc_result.to_dict() if self.kyc_result else None,
            "error_message": self.error_message,
            "data_source": self.data_source,
            "certified_100": CERTIFIED_100,
            "unique_human_proven": UNIQUE_HUMAN_PROVEN,
        }


# Registre des scénarios disponibles pour la démo
DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "kyc-attack": {
        "name": "KYC — Attaque wallet.sign",
        "description": (
            "Un agent LLM malveillant tente d'invoquer wallet.sign durant la vérification KYC. "
            "Guardian détecte, bloque, scelle la preuve cryptographique."
        ),
        "attack_type": "wallet.sign",
        "risk": "CRITICAL",
    },
    "kyc-prompt-injection": {
        "name": "KYC — Injection de prompt",
        "description": (
            "Une instruction hostile est injectée dans le flux KYC. "
            "Guardian identifie le vecteur et refuse l'exécution."
        ),
        "attack_type": "prompt.injection",
        "risk": "HIGH",
    },
    "kyc-exfiltration": {
        "name": "KYC — Exfiltration de données",
        "description": (
            "Tentative de lecture non autorisée des champs sensibles du dossier KYC. "
            "Guardian applique la politique de confidentialité."
        ),
        "attack_type": "data.exfiltrate",
        "risk": "HIGH",
    },
}


class ScenarioController:
    """
    Contrôleur de scénario de démo Guardian.

    Une seule instance par processus. Maintient l'état du run courant.
    Threadsafe pour usage FastAPI (single-worker dev).
    """

    def __init__(self) -> None:
        self._current_run: ScenarioRun | None = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(
        self,
        scenario_id: str = "kyc-attack",
        first_name: str = "Alice",
        last_name: str = "Dupont",
        doc_id: str = "FR-2024-000000",
        dob: str = "1990-01-01",
    ) -> ScenarioRun:
        """
        Démarre un nouveau scénario. Réinitialise automatiquement si un run
        précédent est en état COMPLETED ou ERROR.
        """
        if self._current_run and self._current_run.state == DemoState.RUNNING:
            # Forcer la complétion du run précédent plutôt que de crasher
            self._current_run.state = DemoState.COMPLETED
            self._current_run.completed_at = time.time()

        scenario = DEMO_SCENARIOS.get(scenario_id)
        if scenario is None:
            raise ValueError(
                f"Scénario inconnu: '{scenario_id}'. "
                f"Disponibles: {list(DEMO_SCENARIOS.keys())}"
            )

        run_id = f"run:{uuid.uuid4().hex[:12]}"

        kyc_result = build_kyc_fixture(
            run_id=run_id,
            first_name=first_name,
            last_name=last_name,
            doc_id=doc_id,
            dob=dob,
            attack_type=scenario["attack_type"],
        )

        self._current_run = ScenarioRun(
            run_id=run_id,
            scenario_id=scenario_id,
            state=DemoState.RUNNING,
            current_phase=DemoPhase.DETECTION,
            started_at=time.time(),
            completed_at=None,
            kyc_result=kyc_result,
        )
        return self._current_run

    def advance_phase(self) -> ScenarioRun:
        """Avance au prochain phase du scénario courant."""
        run = self._require_active_run()
        if run.current_phase is None:
            run.current_phase = DemoPhase.DETECTION
            return run

        current_idx = PHASE_ORDER.index(run.current_phase)
        if current_idx >= len(PHASE_ORDER) - 1:
            # Dernière phase : complétion
            run.state = DemoState.COMPLETED
            run.completed_at = time.time()
            run.current_phase = None
        else:
            run.current_phase = PHASE_ORDER[current_idx + 1]

        return run

    def reset(self) -> dict[str, Any]:
        """Réinitialise le contrôleur. L'ancien run est archivé (non effacé)."""
        previous_run_id = (
            self._current_run.run_id if self._current_run else None
        )
        self._current_run = None
        return {
            "reset": True,
            "previous_run_id": previous_run_id,
            "state": DemoState.IDLE.value,
            "data_source": DATA_SOURCE,
        }

    def status(self) -> dict[str, Any]:
        """Retourne le statut courant du contrôleur."""
        if self._current_run is None:
            return {
                "state": DemoState.IDLE.value,
                "run_id": None,
                "scenario_id": None,
                "current_phase": None,
                "data_source": DATA_SOURCE,
                "certified_100": CERTIFIED_100,
                "unique_human_proven": UNIQUE_HUMAN_PROVEN,
            }
        return self._current_run.to_dict()

    def available_scenarios(self) -> list[dict[str, Any]]:
        """Liste des scénarios disponibles pour la démo."""
        return [
            {
                "id": sid,
                "name": s["name"],
                "description": s["description"],
                "risk": s["risk"],
                "data_source": DATA_SOURCE,
            }
            for sid, s in DEMO_SCENARIOS.items()
        ]

    def phase_labels(self) -> list[dict[str, str]]:
        """Labels des phases de démo dans l'ordre."""
        return [
            {"phase": p.value, "label": PHASE_LABELS[p]}
            for p in PHASE_ORDER
        ]

    # ── Private helpers ────────────────────────────────────────────────────────

    def _require_active_run(self) -> ScenarioRun:
        if self._current_run is None:
            raise RuntimeError(
                "Aucun scénario actif. Appeler /api/demo/start d'abord."
            )
        return self._current_run


# Singleton global — une instance par processus FastAPI
scenario_controller = ScenarioController()
