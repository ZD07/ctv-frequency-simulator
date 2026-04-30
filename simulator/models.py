from dataclasses import dataclass
import numpy as np


@dataclass
class Platform:
    name: str
    universe_size: int
    budget: float
    cpm: float
    frequency_cap: int

    @property
    def impressions(self) -> float:
        return (self.budget / self.cpm) * 1000

    @property
    def raw_reach(self) -> float:
        return self.impressions / self.frequency_cap

    @property
    def capped_reach(self) -> float:
        return min(self.raw_reach, self.universe_size)

    @property
    def reach_rate(self) -> float:
        return self.capped_reach / self.universe_size

    @property
    def avg_frequency(self) -> float:
        return self.impressions / self.capped_reach if self.capped_reach > 0 else 0


@dataclass
class Campaign:
    platforms: list[Platform]
    overlap_matrix: np.ndarray
    target_frequency_cap: int = 5
    n_simulations: int = 100_000
