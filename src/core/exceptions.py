"""Domain exceptions."""


class AgentError(Exception):
    """Base error for agent failures."""


class ClassificationError(AgentError):
    """Raised when intent classification fails."""


class KnowledgeRetrievalError(AgentError):
    """Raised when knowledge base lookup fails."""


class EmailProcessingError(AgentError):
    """Raised when email parsing or routing fails."""
