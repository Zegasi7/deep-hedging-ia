import numpy as np
import pandas as pd
from arch import arch_model
from utils import fit_t_copula, simulate_t_copula
from scipy.stats import t as t_dist

def fit_garch(returns):
    """Fit GJR-GARCH(1,1) to each column of returns. Returns fitted models and params."""
    models = []
    params = []
    std_residuals = np.zeros_like(returns)
    for i in range(returns.shape[1]):
        am = arch_model(returns.iloc[:, i], vol='Garch', p=1, q=1, o=1, dist='skewt')
        res = am.fit(disp='off')
        models.append(res)
        std_residuals[:, i] = res.std_resid
        params.append(res.params)
    return models, std_residuals, params

def simulate_paths(models, cop_R, cop_nu, dfs, S0, n_paths, horizon_days):
    """
    Simulate price paths using fitted GARCH + t-copula.
    models: list of fitted GARCH result objects
    cop_R: correlation matrix
    cop_nu: copula df
    dfs: df for each marginal t-dist
    S0: initial prices array
    n_paths: number of Monte Carlo paths
    horizon_days: length of simulation in days
    
    Returns simulated prices (n_paths x horizon_days+1 x n_assets)
    and volatilities (n_paths x horizon_days x n_assets).
    """
    n_assets = len(models)
    T = horizon_days
    # Simulate copula innovations (n_paths * T, n_assets)
    u = simulate_t_copula(cop_R, cop_nu, n_paths * T)
    innovations = np.zeros_like(u)
    for i in range(n_assets):
        innovations[:, i] = t_dist.ppf(u[:, i], df=dfs[i])
    innovations = innovations.reshape(n_paths, T, n_assets)
    
    # Reconstruct GARCH variances and returns
    prices = np.zeros((n_paths, T+1, n_assets))
    vols = np.zeros((n_paths, T, n_assets))
    prices[:, 0, :] = S0
    
    # Extract GARCH parameters
    omega = np.array([m.params['omega'] for m in models])
    alpha = np.array([m.params['alpha[1]'] for m in models])
    gamma = np.array([m.params.get('gamma[1]', 0) for m in models])
    beta = np.array([m.params['beta[1]'] for m in models])
    # Start variance from unconditional variance
    var0 = np.array([omega[i]/(1 - alpha[i] - gamma[i]/2 - beta[i]) for i in range(n_assets)])
    var = np.tile(var0, (n_paths, 1))
    
    for t in range(T):
        # Returns = sqrt(var) * innovation
        ret = np.sqrt(var) * innovations[:, t, :]
        prices[:, t+1, :] = prices[:, t, :] * np.exp(ret)
        vols[:, t, :] = np.sqrt(var)
        # Update variance for next step
        neg_ret = np.minimum(ret, 0)
        var = omega + alpha * ret**2 + gamma * neg_ret**2 + beta * var
        var = np.maximum(var, 1e-8)  # avoid negative
    return prices, vols
