"""Domain exceptions."""


class AgentError(Exception):
    """Base error for agent failures."""


class ClassificationError(AgentError):
    """Raised when intent classification fails."""


class KnowledgeRetrievalError(AgentError):
    """Raised when knowledge base lookup fails."""


class EmailProcessingError(AgentError):
    """Raised when email parsing or routing fails."""


class DraftGenerationError(AgentError):
    """Raised when the LLM fails to produce a draft response."""


class ReviewError(AgentError):
    """Raised when the review node encounters an unrecoverable error."""


class EscalationError(AgentError):
    """Raised when an escalation cannot be dispatched."""


class FollowUpError(AgentError):
    """Raised when a follow-up cannot be scheduled."""
