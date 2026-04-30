import numpy as np
from scipy.stats import norm
from simulator.models import Campaign


def _make_valid_correlation_matrix(matrix: np.ndarray) -> np.ndarray:
    """Ensure the matrix is symmetric and positive semi-definite for Cholesky decomposition."""
    matrix = (matrix + matrix.T) / 2
    np.fill_diagonal(matrix, 1.0)
    eigvals, eigvecs = np.linalg.eigh(matrix)
    eigvals = np.clip(eigvals, 1e-6, None)
    return eigvecs @ np.diag(eigvals) @ eigvecs.T


def _simulate_core(campaign: Campaign) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Core simulation using Gaussian copula.
    Returns (correlated_U, per_platform_frequencies, total_frequencies).
    correlated_U is used by both baseline and EUID simulations.
    """
    n = campaign.n_simulations
    k = len(campaign.platforms)

    corr = _make_valid_correlation_matrix(campaign.overlap_matrix[:k, :k])
    L = np.linalg.cholesky(corr)

    Z = np.random.normal(0, 1, (n, k))
    correlated_Z = Z @ L.T
    correlated_U = norm.cdf(correlated_Z)

    per_platform = np.zeros((n, k))
    for i, platform in enumerate(campaign.platforms):
        reached_mask = correlated_U[:, i] < platform.reach_rate
        sampled_freq = np.random.poisson(platform.avg_frequency, n)
        sampled_freq = np.clip(sampled_freq, 1, platform.frequency_cap)
        per_platform[:, i] = reached_mask * sampled_freq

    return correlated_U, per_platform, per_platform.sum(axis=1)


def run_simulation(campaign: Campaign) -> np.ndarray:
    """Baseline simulation — no cross-platform frequency coordination."""
    _, _, total = _simulate_core(campaign)
    return total


def run_euid_simulation(campaign: Campaign) -> np.ndarray:
    """
    EUID scenario simulation.

    For each household, impressions are split into two pools:
    - EUID-coordinated: impressions from platforms with EUID adoption,
      weighted by each platform's adoption rate. These are shared across a
      single cap, modelling deterministic cross-platform frequency control.
    - Uncoordinated: remaining impressions (non-EUID inventory or platforms
      with no EUID participation, e.g. Netflix). These accumulate freely.

    The household's total frequency = capped(euid_pool) + uncoordinated_pool.
    Netflix's 0.0 EUID rate means all its impressions remain uncoordinated,
    reflecting its proprietary ad stack.
    """
    n = campaign.n_simulations
    k = len(campaign.platforms)
    cap = campaign.target_frequency_cap

    _, per_platform, _ = _simulate_core(campaign)

    euid_rates = np.array([p.euid_adoption_rate for p in campaign.platforms])

    # For each platform, use binomial sampling to determine how many of each
    # household's impressions are EUID-matched. This ensures the total always
    # equals baseline (euid_pool + uncoordinated_pool == baseline), and that
    # capping the euid_pool can only reduce — never increase — total impressions.
    euid_pool = np.zeros(n)
    uncoordinated_pool = np.zeros(n)

    for i in range(k):
        rate = euid_rates[i]
        imps_int = per_platform[:, i].astype(int)
        if rate > 0:
            euid_from_platform = np.random.binomial(imps_int, rate)
        else:
            euid_from_platform = np.zeros(n, dtype=int)
        euid_pool         += euid_from_platform
        uncoordinated_pool += (imps_int - euid_from_platform)

    # EUID-coordinated impressions share a single cross-platform cap.
    # Capping here is what EUID coordination actually achieves in practice.
    capped_euid = np.minimum(euid_pool, cap)

    return capped_euid + uncoordinated_pool


def analyse(frequencies: np.ndarray, campaign: Campaign) -> dict:
    """Derive summary metrics from a simulated frequency distribution."""
    cap = campaign.target_frequency_cap
    reached = frequencies[frequencies > 0]

    if len(reached) == 0:
        return {}

    over_exposed_mask = frequencies > cap
    over_exposed_impressions = np.maximum(frequencies - cap, 0)

    total_impressions = frequencies.sum()
    wasted_impressions = over_exposed_impressions.sum()
    total_budget = sum(p.budget for p in campaign.platforms)
    wasted_spend = (wasted_impressions / total_impressions) * total_budget if total_impressions > 0 else 0

    max_freq = int(frequencies.max())
    freq_dist = np.bincount(frequencies.astype(int), minlength=max_freq + 1)

    return {
        "unique_reach": int(len(reached)),
        "total_hh": int(len(frequencies)),
        "reach_pct": len(reached) / len(frequencies) * 100,
        "avg_frequency": float(reached.mean()),
        "over_exposure_pct": float(len(frequencies[over_exposed_mask]) / len(reached) * 100),
        "wasted_impressions": float(wasted_impressions),
        "wasted_spend": float(wasted_spend),
        "total_budget": float(total_budget),
        "waste_pct_of_budget": float(wasted_spend / total_budget * 100) if total_budget > 0 else 0,
        "frequency_distribution": freq_dist.tolist(),
    }
