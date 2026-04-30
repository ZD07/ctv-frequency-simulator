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


def run_simulation(campaign: Campaign) -> np.ndarray:
    """
    Simulate cross-platform household frequency using a Gaussian copula.
    Returns an array of shape (n_simulations,) with total impressions per household.
    """
    n = campaign.n_simulations
    k = len(campaign.platforms)

    corr = _make_valid_correlation_matrix(campaign.overlap_matrix[:k, :k])
    L = np.linalg.cholesky(corr)

    Z = np.random.normal(0, 1, (n, k))
    correlated_Z = Z @ L.T
    correlated_U = norm.cdf(correlated_Z)

    household_frequencies = np.zeros(n)

    for i, platform in enumerate(campaign.platforms):
        reached_mask = correlated_U[:, i] < platform.reach_rate
        sampled_freq = np.random.poisson(platform.avg_frequency, n)
        sampled_freq = np.clip(sampled_freq, 1, platform.frequency_cap)
        household_frequencies += reached_mask * sampled_freq

    return household_frequencies


def analyse(frequencies: np.ndarray, campaign: Campaign) -> dict:
    """Derive summary metrics from the simulated frequency distribution."""
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
