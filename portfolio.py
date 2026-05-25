import numpy as np
import pandas as pd
from option_pricer import black_scholes, bs_greeks

class Option:
    def __init__(self, underlying, strike, expiry_days, option_type, position):
        self.underlying = underlying      # ticker index
        self.K = strike
        self.T = expiry_days / 252        # time in years
        self.type = option_type           # 'call' or 'put'
        self.position = position          # +1 long, -1 short

class OptionsPortfolio:
    def __init__(self, options, S0, r=0.05):
        self.options = options
        self.n_assets = S0.shape[0]       # number of underlyings
        self.S0 = S0                      # initial spot array
        self.r = r

    def price(self, S, T_remaining, sigma):
        """Total portfolio value. S: (n_assets,), T_remaining: float, sigma: (n_assets,)"""
        val = 0.0
        for opt in self.options:
            # Use volatility of the underlying
            vol = sigma[opt.underlying]
            # Remaining time: original T minus elapsed, but we pass T_remaining directly
            opt_price = black_scholes(S[opt.underlying], opt.K, T_remaining, self.r, vol, opt.type)
            val += opt.position * opt_price
        return val

    def greeks(self, S, T_remaining, sigma):
        """Return dict of total delta per asset, gamma, vega, theta."""
        deltas = np.zeros(self.n_assets)
        gammas = np.zeros(self.n_assets)
        vegas = np.zeros(self.n_assets)
        thetas = 0.0
        for opt in self.options:
            vol = sigma[opt.underlying]
            d, g, v, t = bs_greeks(S[opt.underlying], opt.K, T_remaining, self.r, vol, opt.type)
            deltas[opt.underlying] += opt.position * d
            gammas[opt.underlying] += opt.position * g
            vegas[opt.underlying] += opt.position * v
            thetas += opt.position * t
        return deltas, gammas, vegas, thetas
