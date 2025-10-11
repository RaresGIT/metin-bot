"""Base strategy interface."""
from abc import ABC, abstractmethod


class BotStrategy(ABC):
    """Abstract base class for bot strategies."""

    @abstractmethod
    def execute(self) -> None:
        """Execute one iteration of the strategy."""
        pass

    @abstractmethod
    def should_continue(self) -> bool:
        """Check if the strategy should continue running."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup when strategy is stopped."""
        pass
