"""Prompt Management and Dynamic Rollback System."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    template_id: str
    agent_name: str
    version: str
    content: str
    is_active: bool = True
    groundedness_benchmark: float = 0.95


class PromptManager:
    """Manages versioned agent prompt templates with rollback capabilities."""

    def __init__(self):
        self._templates: Dict[str, Dict[str, PromptTemplate]] = {}
        self._seed_prompts()

    def _seed_prompts(self):
        # SAR Synthesis v1.0
        self.register_template(
            PromptTemplate(
                template_id="SAR_SYNTH_V1",
                agent_name="SARSynthesisAgent",
                version="v1.0.0",
                content=(
                    "You are a Senior AML Compliance Officer drafting a FinCEN Suspicious Activity Report (SAR). "
                    "You must be strictly factual, objective, and chronological. "
                    "Cite all amounts, accounts, timestamps, and statutory activity codes without speculation."
                ),
                is_active=True,
                groundedness_benchmark=0.95,
            )
        )
        # Compliance Critic v1.0
        self.register_template(
            PromptTemplate(
                template_id="CRITIC_V1",
                agent_name="ComplianceCriticAgent",
                version="v1.0.0",
                content=(
                    "You are an adversarial Compliance Auditor verifying that every factual assertion in the "
                    "draft SAR narrative has direct documentary evidence in the system dossier. "
                    "Reject any ungrounded assertions or speculative language."
                ),
                is_active=True,
                groundedness_benchmark=0.98,
            )
        )

    def register_template(self, template: PromptTemplate):
        """Register a new template version."""
        if template.agent_name not in self._templates:
            self._templates[template.agent_name] = {}
        self._templates[template.agent_name][template.version] = template

    def get_active_prompt(self, agent_name: str) -> Optional[str]:
        """Retrieve active prompt for given agent."""
        versions = self._templates.get(agent_name, {})
        for t in versions.values():
            if t.is_active:
                return t.content
        return None

    def rollback(self, agent_name: str, target_version: str) -> bool:
        """Rollback prompt template to certified earlier version."""
        versions = self._templates.get(agent_name, {})
        if target_version in versions:
            for v, t in versions.items():
                t.is_active = (v == target_version)
            return True
        return False


prompt_manager = PromptManager()
