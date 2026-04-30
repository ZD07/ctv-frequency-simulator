import numpy as np
from simulator.models import Platform

# Household universe sizes — UK estimates (approx)
DEFAULT_PLATFORMS = [
    Platform(name="YouTube",    universe_size=18_000_000, budget=20_000, cpm=12.0, frequency_cap=5),
    Platform(name="Netflix",    universe_size=17_000_000, budget=15_000, cpm=35.0, frequency_cap=4),
    Platform(name="Amazon",     universe_size=13_000_000, budget=15_000, cpm=22.0, frequency_cap=4),
    Platform(name="Disney+",    universe_size=8_000_000,  budget=10_000, cpm=28.0, frequency_cap=3),
    Platform(name="ITV X",      universe_size=12_000_000, budget=10_000, cpm=18.0, frequency_cap=4),
]

PLATFORM_NAMES = [p.name for p in DEFAULT_PLATFORMS]

# Overlap matrix: overlap[i][j] = estimated % of platform i's audience also on platform j
# Diagonal must be 1.0. Matrix must be symmetric and positive semi-definite.
# Sources: Ofcom, BARB, industry estimates (2024)
DEFAULT_OVERLAP = np.array([
    # YouTube  Netflix  Amazon  Disney+  ITV X
    [1.00,     0.55,    0.52,   0.38,    0.45],  # YouTube
    [0.55,     1.00,    0.48,   0.42,    0.35],  # Netflix
    [0.52,     0.48,    1.00,   0.40,    0.38],  # Amazon
    [0.38,     0.42,    0.40,   1.00,    0.28],  # Disney+
    [0.45,     0.35,    0.38,   0.28,    1.00],  # ITV X
])

def get_default_platforms() -> list[Platform]:
    return [Platform(
        name=p.name,
        universe_size=p.universe_size,
        budget=p.budget,
        cpm=p.cpm,
        frequency_cap=p.frequency_cap
    ) for p in DEFAULT_PLATFORMS]
