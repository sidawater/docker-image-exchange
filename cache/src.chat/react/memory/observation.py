"""Observation Manager"""

from typing import List
from react.model.reasoning import Observation


class ObservationManager:
    """Observation Manager"""

    def __init__(self) -> None:
        self._observations: List[Observation] = []

    def add_observation(self, observation: Observation) -> None:
        """Add observation"""
        self._observations.append(observation)

    def get_observations(self) -> List[Observation]:
        """Get observation list"""
        return self._observations.copy()

    def clear(self) -> None:
        """Clear observations"""
        self._observations.clear()

    def get_last_observation(self) -> Observation | None:
        """Get last observation"""
        return self._observations[-1] if self._observations else None
