import torch
import torch.nn as nn
import numpy as np

class DeepHedger(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, output_dim=1):
        """
        input_dim: number of state features (spot, time, greeks, vol, etc.)
        output_dim: number of hedge assets (same as underlyings)
        """
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim),
            nn.Tanh()  # hedge ratio between -1 and 1 (scaled later)
        )
        self.scale = nn.Parameter(torch.ones(output_dim))  # learnable scaling

    def forward(self, x, hidden=None):
        # x shape: (batch, seq_len, input_dim)
        out, hidden = self.lstm(x, hidden)
        # take last time step output
        out = self.fc(out[:, -1, :]) * self.scale
        return out, hidden

def differentiable_pnl(portfolio, S_paths, vol_paths, T_remaining_seq, hedge_seq, dt, r, tc=0.001):
    """
    Computes hedged PnL for a batch of paths.
    S_paths: (batch, T, n_assets)  -- already simulated
    vol_paths: (batch, T, n_assets)
    T_remaining_seq: (T,) time to maturity at each step
    hedge_seq: (batch, T, n_assets) hedge positions output by model at each step.
    dt: time step in years (1/252)
    r: risk-free rate
    tc: proportional transaction cost
    """
    batch_size, T, n_assets = S_paths.shape
    # Initial portfolio value (without hedge) at t=0
    init_value = []
    for b in range(batch_size):
        init_value.append(portfolio.price(S_paths[b, 0], T_remaining_seq[0], vol_paths[b, 0]))
    init_value = torch.tensor(init_value, device=S_paths.device)
    
    # Initial cash borrowed = - (hedge * S) + option premium
    # Actually we compute self-financing P&L:
    # P&L = final_option_value - initial_option_value + cash_from_hedge - transaction_costs
    # cash_from_hedge = sum_{t} (hedge_{t-1} * (S_t - S_{t-1}))
    # transaction costs = tc * sum |(hedge_t - hedge_{t-1}) * S_t|
    
    option_values = []
    for b in range(batch_size):
        vals = []
        for t in range(T):
            vals.append(portfolio.price(S_paths[b, t], T_remaining_seq[t], vol_paths[b, t]))
        option_values.append(torch.stack(vals))
    option_values = torch.stack(option_values)  # (batch, T)
    
    # Shift hedge: hedge_seq[t] is the position held after rebalancing at time t.
    # We need positions before rebalancing: start with zero hedge, then after first model output we set hedge.
    # For P&L: at time t, the position that earns return is the hedge from previous period.
    # So we create hedge_prev = shifted hedge, with initial zero.
    hedge_prev = torch.cat([torch.zeros(batch_size, 1, n_assets, device=S_paths.device),
                            hedge_seq[:, :-1, :]], dim=1)  # (batch, T, n_assets)
    
    # stock returns: S_t / S_{t-1} - 1
    S_prev = torch.cat([S_paths[:, 0:1, :], S_paths[:, :-1, :]], dim=1)
    stock_ret = S_paths / S_prev - 1   # (batch, T, n_assets)
    
    # P&L from hedge: sum over assets (hedge_prev * S_prev * stock_ret)
    hedge_pnl = torch.sum(hedge_prev * S_prev * stock_ret, dim=2)  # (batch, T)
    
    # Transaction costs
    trade_size = torch.abs(hedge_seq - hedge_prev)  # (batch, T, n_assets)
    tcost = tc * torch.sum(trade_size * S_paths, dim=2)  # (batch, T)
    
    # Option value change: option_values diff? Actually final option value - initial option value
    # But we need to incorporate all cash flows correctly.
    # Better: track cash account.
    # Simplified P&L: final wealth = initial portfolio value + sum(hedge_pnl) - sum(tcost) + (option_value_last - option_value_first)
    # However, option value changes also affect wealth, but the portfolio is exactly the option + hedge.
    # The self-financing condition: V_t = option_value_t + cash_t
    # delta cash = hedge_pnl_t - tcost_t; cash_0 = -option_value_0 - hedge_0*S_0 (assuming borrowed)
    # So final wealth = option_value_T + cash_T, and total P&L = final wealth.
    
    cash_flow = hedge_pnl - tcost
    cash = torch.cumsum(cash_flow, dim=1)
    # initial cash: we start with zero hedge, so cash_0 = -init_value
    # So wealth at each step = option_value + cash + init_value? Let's be precise.
    # Let's define wealth_t = option_value_t + cash_t where cash_0 = -option_value_0.
    # Then wealth_0 = 0, and final wealth = option_value_T + cash_T = option_value_T + sum(hedge_pnl - tcost) - option_value_0
    # So total P&L = wealth_T.
    final_option = option_values[:, -1]
    pnl = final_option - init_value + torch.sum(cash_flow, dim=1)
    return pnl

def cvar_loss(pnl, alpha=0.95):
    """Differentiable CVaR approximation (sorts and takes mean of worst)."""
    sorted_pnl, _ = torch.sort(pnl)
    var_index = int((1 - alpha) * pnl.shape[0])
    cvar = sorted_pnl[:var_index].mean()
    return -cvar  # we want to maximise P&L, so minimise negative CVaR
