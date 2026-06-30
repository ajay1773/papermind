class PapermindError(Exception):
    """Base exception for all Papermind errors."""


class IngestionError(PapermindError):
    """Raised when document ingestion fails."""


class RetrievalError(PapermindError):
    """Raised when retrieval pipeline fails."""


class AgentError(PapermindError):
    """Raised when the research agent encounters an unrecoverable error."""


class MCPConnectionError(PapermindError):
    """Raised when an MCP server is unreachable."""
