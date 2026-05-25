import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

def fit_t_copula(residuals):
    """
    Fit a t-copula to a (T x d) array of standardised residuals.
    Returns: correlation matrix R and degrees of freedom nu.
    """
    # Transform to uniform using Student-t marginal CDF
    n = residuals.shape[0]
    # Estimate df for each series (simplified: use MLE)
    params = [t_dist.fit(residuals[:, i]) for i in range(residuals.shape[1])]
    dfs = np.array([p[0] for p in params])
    # Use mean df for the copula (simplification)
    nu_cop = np.mean(dfs)
    # Transform to uniform
    u = np.zeros_like(residuals)
    for i in range(residuals.shape[1]):
        u[:, i] = t_dist.cdf(residuals[:, i], df=dfs[i])
    # Transform to standard normal (for correlation estimation)
    z = np.sqrt(2) * np.erfinv(2 * u - 1)
    R = np.corrcoef(z.T)
    # Ensure positive semi-definite
    R = (R + R.T) / 2
    return R, nu_cop, dfs

def simulate_t_copula(R, nu, n_sim):
    """
    Simulate from t-copula with correlation R and df nu.
    Returns uniform marginals (n_sim x d).
    """
    from scipy.stats import multivariate_t
    d = R.shape[0]
    # Simulate multivariate t
    mvt = multivariate_t(shape=R, df=nu)
    samples = mvt.rvs(n_sim)          # (n_sim, d)
    # Transform to uniform via univariate t CDF
    u = t_dist.cdf(samples, df=nu)
    return u
