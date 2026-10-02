from abc import ABC, abstractmethod
from typing import List, Any
from datetime import datetime
from src.models.risk_report import AgentTraceLog

class BaseAgent(ABC):
    """Base class for CancerTwin AI agents."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.traces: List[AgentTraceLog] = []

    def log(self, step_title: str, details: str) -> AgentTraceLog:
        """Records an explainable reasoning trace step."""
        trace = AgentTraceLog(
            agent_name=self.name,
            step_title=step_title,
            details=details,
            timestamp=datetime.utcnow()
        )
        self.traces.append(trace)
        return trace

    def get_traces(self) -> List[AgentTraceLog]:
        return list(self.traces)

    def clear_traces(self):
        self.traces.clear()

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute agent's dedicated responsibility."""
        pass
