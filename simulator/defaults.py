import numpy as np
from simulator.models import Platform

# ── Platform Defaults ─────────────────────────────────────────────────────────
# Universe sizes: UK household estimates from BARB Q4 2024 / Ofcom 2025
# CPMs: UK programmatic CTV market rates (2025)
# EUID adoption: estimated proportion of impressions addressable via EUID
#   Netflix = 0.0 (proprietary ad stack, no EUID participation)
#   YouTube = 0.30 (Google uses own identity graph, partial EUID coverage)
#   UK broadcasters (ITV X, Channel 4) = higher adoption as open ecosystem participants
# Sources: BARB, Ofcom Media Nations 2025, IAB UK, industry estimates

DEFAULT_PLATFORMS = [
    Platform(name="YouTube",    universe_size=18_000_000, budget=20_000, cpm=12.0, frequency_cap=5, euid_adoption_rate=0.30),
    Platform(name="Netflix",    universe_size=17_000_000, budget=15_000, cpm=35.0, frequency_cap=4, euid_adoption_rate=0.00),
    Platform(name="Amazon",     universe_size=13_000_000, budget=15_000, cpm=22.0, frequency_cap=4, euid_adoption_rate=0.15),
    Platform(name="Disney+",    universe_size=7_500_000,  budget=10_000, cpm=28.0, frequency_cap=3, euid_adoption_rate=0.40),
    Platform(name="ITV X",      universe_size=12_000_000, budget=10_000, cpm=18.0, frequency_cap=4, euid_adoption_rate=0.45),
    Platform(name="Channel 4",  universe_size=12_000_000, budget=10_000, cpm=16.0, frequency_cap=4, euid_adoption_rate=0.40),
    Platform(name="Sky/NOW TV", universe_size=3_500_000,  budget=8_000,  cpm=22.0, frequency_cap=4, euid_adoption_rate=0.30),
    Platform(name="Paramount+", universe_size=1_500_000,  budget=5_000,  cpm=20.0, frequency_cap=3, euid_adoption_rate=0.38),
    Platform(name="Discovery+", universe_size=2_000_000,  budget=5_000,  cpm=15.0, frequency_cap=3, euid_adoption_rate=0.35),
]

PLATFORM_NAMES = [p.name for p in DEFAULT_PLATFORMS]

# ── Overlap Matrix ────────────────────────────────────────────────────────────
# overlap[i][j] = estimated % of platform i's audience also on platform j
# Diagonal = 1.0. Matrix is symmetric.
# UK estimates derived from BARB Establishment Survey, Ofcom VoD Survey 2024/25,
# and IPA TouchPoints 2025. Treat as modelled assumptions.
#
# Order: YouTube, Netflix, Amazon, Disney+, ITV X, Channel 4, Sky/NOW, Paramount+, Discovery+

DEFAULT_OVERLAP = np.array([
    # YT    Nflx   Amzn   Dis+   ITVX   Ch4    Sky    Para   Disc
    [1.00,  0.55,  0.52,  0.38,  0.45,  0.42,  0.35,  0.28,  0.30],  # YouTube
    [0.55,  1.00,  0.48,  0.42,  0.35,  0.32,  0.40,  0.35,  0.32],  # Netflix
    [0.52,  0.48,  1.00,  0.40,  0.38,  0.35,  0.45,  0.32,  0.35],  # Amazon
    [0.38,  0.42,  0.40,  1.00,  0.28,  0.25,  0.35,  0.38,  0.30],  # Disney+
    [0.45,  0.35,  0.38,  0.28,  1.00,  0.55,  0.32,  0.22,  0.25],  # ITV X
    [0.42,  0.32,  0.35,  0.25,  0.55,  1.00,  0.30,  0.20,  0.25],  # Channel 4
    [0.35,  0.40,  0.45,  0.35,  0.32,  0.30,  1.00,  0.30,  0.35],  # Sky/NOW TV
    [0.28,  0.35,  0.32,  0.38,  0.22,  0.20,  0.30,  1.00,  0.35],  # Paramount+
    [0.30,  0.32,  0.35,  0.30,  0.25,  0.25,  0.35,  0.35,  1.00],  # Discovery+
])


def get_default_platforms() -> list[Platform]:
    return [Platform(
        name=p.name,
        universe_size=p.universe_size,
        budget=p.budget,
        cpm=p.cpm,
        frequency_cap=p.frequency_cap,
        euid_adoption_rate=p.euid_adoption_rate,
    ) for p in DEFAULT_PLATFORMS]
