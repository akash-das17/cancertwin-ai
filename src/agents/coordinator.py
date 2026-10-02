"""
Twin Coordinator Agent.
Main orchestrator for CancerTwin AI. Coordinates Intake, 5-Cancer Risk RAG,
Pre-Simulation Guidance, What-If Simulations, and Safety Staging via LangGraph.
"""
from typing import Dict, Any, List, Optional
from src.agents.base import BaseAgent
from src.models.patient import PatientProfile, DigitalTwinState
from src.models.simulation import WhatIfScenario
from src.models.risk_report import RiskReport, PreSimulationRecommendationItem
from src.graphs.prevention_graph import run_prevention_pipeline
from src.agents.intake_agent import IntakeAgent
from src.agents.risk_agent import RiskAssessmentAgent
from src.utils.prompts import build_pre_simulation_recommendations

class TwinCoordinatorAgent(BaseAgent):
    """Main orchestrator for CancerTwin AI. Coordinates Intake, 5-Cancer Risk RAG, Pre-Simulation Guidance, What-If Simulations, and Safety Staging via LangGraph."""

    def __init__(self):
        super().__init__(
            name="Twin Coordinator Agent",
            role="Orchestrates specialized oncology agents and synthesizes personalized clinical reports across 5 cancer axes via LangGraph"
        )
        self.intake_agent = IntakeAgent()
        self.risk_agent = RiskAssessmentAgent()

    def generate_pre_simulation_guidance(self, profile: PatientProfile) -> List[PreSimulationRecommendationItem]:
        """Generates concrete clinical action items immediately following patient profile entry in <10ms."""
        return build_pre_simulation_recommendations(profile, {})

    def run(
        self,
        profile: PatientProfile,
        scenario: Optional[WhatIfScenario] = None
    ) -> RiskReport:
        """Executes the compiled multi-agent LangGraph digital twin pipeline."""
        return run_prevention_pipeline(profile, scenario)

    # Backward compatibility alias
    run_full_pipeline = run
