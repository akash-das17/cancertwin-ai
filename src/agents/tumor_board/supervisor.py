"""
Tumor Board Supervisor Agent.
Presides over the Multidisciplinary Virtual Tumor Board, orchestrating the compiled
LangGraph cyclical debate and synthesizing final multidisciplinary consensus.
No fictional human names or academic degrees.
"""
from typing import List, Tuple
from src.models.oncology_history import PriorCancerHistory
from src.models.risk_report import (
    TumorBoardAgentOpinion,
    TumorBoardDebateResult,
    AgentTraceLog,
    DebateMessage
)
class TumorBoardSupervisorAgent:
    """Orchestrates the 3-specialist multidisciplinary tumor board debate and adjudicates consensus relapse risk via LangGraph."""

    def __init__(self):
        self.role_name = "Tumor Board Supervisor Agent"
        self.chair_name = "Tumor Board Supervisor Agent"

    def adjudicate_debate(self, history: PriorCancerHistory) -> TumorBoardDebateResult:
        """Executes the compiled multi-agent LangGraph debate pipeline."""
        from src.graphs.tumor_board_graph import run_tumor_board_debate
        return run_tumor_board_debate(history)
