"""LLM provider abstraction layer.

Defines the ModelId format (provider:model) and LLMProvider protocol
for vendor-agnostic LLM integration.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from google.adk.models import BaseLlm


@dataclass
class ModelId:
    """Represents a model in provider:model format.

    Examples:
        - openai:gpt-4o
        - anthropic:claude-3.5-sonnet
        - google:gemini-2.0-flash
        - meta-llama:llama-3.1-70b-instruct
    """

    provider: str
    model: str

    @classmethod
    def from_string(cls, s: str) -> "ModelId":
        """Parse a model ID from provider:model format.

        Args:
            s: String in format "provider:model"

        Returns:
            ModelId instance

        Raises:
            ValueError: If string doesn't contain ':'
        """
        if ":" not in s:
            raise ValueError(
                f"Invalid model ID format: '{s}'. Expected 'provider:model'"
            )
        provider, model = s.split(":", 1)
        return cls(provider=provider, model=model)

    def __str__(self) -> str:
        """Return the model ID in provider:model format."""
        return f"{self.provider}:{self.model}"


class LLMProvider(Protocol):
    """Protocol for LLM provider adapters.

    Implementations should provide a way to create ADK-compatible
    LLM instances from ModelId specifications.
    """

    def get_model(self, model_id: ModelId) -> "BaseLlm":
        """Create an ADK-compatible LLM instance for the given model.

        Args:
            model_id: The model identifier

        Returns:
            An ADK BaseLlm-compatible instance
        """
        ...

    def list_models(self) -> list[ModelId]:
        """List available models for this provider.

        Returns:
            List of available ModelId instances
        """
        ...
