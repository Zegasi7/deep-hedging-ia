"""
Streamlit app: Deep Learning for Dynamic Hedging of Options Portfolio
Aligns with "Méthodes Statistiques Appliquée à la Finance"
"""
import streamlit as st
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import plotly.graph_objects as go
from scipy.stats import norm, t as t_dist
from arch import arch_model
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(layout="wide")
st.title("📊 Deep Hedging of Options Portfolio with Statistical Methods")

# -------------------------------
# 1. Sidebar – User Controls
# -------------------------------
st.sidebar.header("Portfolio Configuration")
assets = st.sidebar.multiselect("Underlyings", ['AAPL', 'MSFT', 'SPY', 'GOOGL', 'AMZN'],
                                 default=['AAPL', 'MSFT'])
n_assets = len(assets)
if n_assets < 1:
    st.error("Select at least one asset.")
    st.stop()

st.sidebar.subheader("Options Portfolio")
option_list = []
for i, ticker in enumerate(assets):
    with st.sidebar.expander(f"{ticker} options"):
        pos_call = st.selectbox(f"Call position ({ticker})", [0, 1, -1], key=f"call_{ticker}")
        strike_call = st.number_input(f"Strike Call ({ticker})", value=100.0, step=5.0, key=f"Kc_{ticker}")
        pos_put = st.selectbox(f"Put position ({ticker})", [0, 1, -1], key=f"put_{ticker}")
        strike_put = st.number_input(f"Strike Put ({ticker})", value=100.0, step=5.0, key=f"Kp_{ticker}")
        if pos_call != 0:
            option_list.append({'underlying': i, 'type': 'call', 'K': strike_call, 'pos': pos_call})
        if pos_put != 0:
            option_list.append({'underlying': i, 'type': 'put', 'K': strike_put, 'pos': pos_put})

if not option_list:
    st.error("Add at least one option.")
    st.stop()

st.sidebar.header("Market Simulator Parameters")
garch_p = st.sidebar.slider("GARCH p", 1, 3, 1)
garch_q = st.sidebar.slider("GARCH q", 1, 3, 1)
use_gjr = st.sidebar.checkbox("Use GJR-GARCH", True)
copula_type = st.sidebar.selectbox("Copula", ["t-copula", "Gaussian"])

st.sidebar.header("Deep Hedging Model")
hidden_dim = st.sidebar.slider("LSTM hidden dim", 32, 256, 64)
num_layers = st.sidebar.slider("LSTM layers", 1, 3, 2)
epochs = st.sidebar.number_input("Training epochs", 10, 200, 50)
lr = st.sidebar.number_input("Learning rate", 1e-5, 1e-2, 1e-3, format="%.4f")
tc = st.sidebar.number_input("Transaction cost (bps)", 0.0, 50.0, 10.0) / 10000
cvar_alpha = st.sidebar.slider("CVaR confidence", 0.90, 0.99, 0.95)
horizon_days = st.sidebar.slider("Backtest horizon (days)", 20, 252, 60)
sim_paths = st.sidebar.number_input("Simulated training paths", 1000, 20000, 5000)
st.sidebar.info("Training uses simulated paths. Backtest runs on real historical data.")

# -------------------------------
# 2. Data Fetching & GARCH fitting
# -------------------------------
@st.cache_data
def load_data(tickers, lookback=504):
    end = datetime.today()
    start = end - timedelta(days=lookback*2)
    data = yf.download(tickers, start=start, end=end)['Adj Close']
    returns = np.log(data / data.shift(1)).dropna()
    return data, returns

data, returns = load_data(assets)
st.write("### Historical Prices")
st.line_chart(data.tail(252))

# -------------------------------
# 3. GARCH & Copula fitting
# -------------------------------
@st.cache_resource
def fit_models(returns, p, q, use_gjr, cop_type):
    n = returns.shape[1]
    models = []
    std_resid = np.zeros_like(returns)
    dfs = []
    for i in range(n):
        vol = 'Garch' if not use_gjr else 'Garch'
        dist = 'skewt' if cop_type == 't-copula' else 'normal'
        am = arch_model(returns.iloc[:, i], vol=vol, p=p, q=q, o=int(use_gjr), dist=dist)
        res = am.fit(disp='off')
        models.append(res)
        std_resid[:, i] = res.std_resid
        if cop_type == 't-copula':
            df_est = res.params['nu']
        else:
            df_est = 100  # large for Gaussian
        dfs.append(df_est)

    # Copula fit
    u = np.zeros_like(std_resid)
    for i in range(n):
        u[:, i] = t_dist.cdf(std_resid[:, i], df=dfs[i])
    z = np.sqrt(2) * np.erfinv(2 * u - 1)
    R = np.corrcoef(z.T)
    R = (R + R.T) / 2
    if cop_type == 't-copula':
        nu_cop = np.mean(dfs) if n > 0 else 5
    else:
        nu_cop = 1e9  # huge df -> Gaussian
    return models, R, nu_cop, dfs

models, cop_R, cop_nu, dfs = fit_models(returns, garch_p, garch_q, use_gjr, copula_type)
st.success("GARCH + Copula fitted.")

# -------------------------------
# 4. Simulate training paths
# -------------------------------
def simulate_paths(models, R, nu_cop, dfs, S0, n_paths, horizon):
    n_assets = len(models)
    # unconditional variance
    omega = np.array([m.params['omega'] for m in models])
    alpha = np.array([m.params['alpha[1]'] for m in models])
    gamma = np.array([m.params.get('gamma[1]', 0) for m in models])
    beta = np.array([m.params['beta[1]'] for m in models])
    var_uncond = np.maximum(omega / (1 - alpha - gamma/2 - beta), 1e-8)

    # simulate copula
    T = horizon
    n_total = n_paths * T
    # t-copula simulation
    from scipy.stats import multivariate_t
    mvt = multivariate_t(shape=R, df=nu_cop) if nu_cop < 50 else multivariate_t(shape=R, df=1e9)
    samples = mvt.rvs(n_total)
    u = t_dist.cdf(samples, df=nu_cop)
    innov = np.zeros_like(u)
    for i in range(n_assets):
        innov[:, i] = t_dist.ppf(u[:, i], df=dfs[i])
    innov = innov.reshape(n_paths, T, n_assets)

    prices = np.zeros((n_paths, T+1, n_assets))
    vols = np.zeros((n_paths, T, n_assets))
    prices[:, 0, :] = S0
    var = np.tile(var_uncond, (n_paths, 1))
    for t in range(T):
        ret = np.sqrt(np.maximum(var, 1e-8)) * innov[:, t, :]
        prices[:, t+1, :] = prices[:, t, :] * np.exp(ret)
        vols[:, t, :] = np.sqrt(var)
        neg_ret = np.minimum(ret, 0)
        var = omega + alpha * ret**2 + gamma * neg_ret**2 + beta * var
        var = np.maximum(var, 1e-8)
    return prices, vols

S0 = data.iloc[-1].values
st.write(f"Initial prices: {dict(zip(assets, S0))}")
sim_prices, sim_vols = simulate_paths(models, cop_R, cop_nu, dfs, S0, sim_paths, horizon_days)

# -------------------------------
# 5. Portfolio & Greeks (vectorised)
# -------------------------------
class Portfolio:
    def __init__(self, opts, S0, r=0.05):
        self.opts = opts
        self.n_assets = len(S0)
        self.r = r

    def price(self, S, T, sigma):
        val = 0.0
        for o in self.opts:
            i = o['underlying']
            vol = sigma[i]
            d1 = (np.log(S[i]/o['K']) + (self.r + 0.5*vol**2)*T) / (vol*np.sqrt(T))
            d2 = d1 - vol*np.sqrt(T)
            if o['type'] == 'call':
                val += o['pos'] * (S[i]*norm.cdf(d1) - o['K']*np.exp(-self.r*T)*norm.cdf(d2))
            else:
                val += o['pos'] * (o['K']*np.exp(-self.r*T)*norm.cdf(-d2) - S[i]*norm.cdf(-d1))
        return val

    def delta(self, S, T, sigma):
        deltas = np.zeros(self.n_assets)
        for o in self.opts:
            i = o['underlying']
            vol = sigma[i]
            d1 = (np.log(S[i]/o['K']) + (self.r + 0.5*vol**2)*T) / (vol*np.sqrt(T))
            if o['type'] == 'call':
                deltas[i] += o['pos'] * norm.cdf(d1)
            else:
                deltas[i] += o['pos'] * (norm.cdf(d1) - 1)
        return deltas

pf = Portfolio(option_list, S0)
r = 0.05
T_init = horizon_days / 252  # approximate

# -------------------------------
# 6. Deep Hedging Model Definition
# -------------------------------
class DeepHedger(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim),
            nn.Tanh()
        )
        self.scale = nn.Parameter(torch.ones(output_dim))

    def forward(self, x, hidden=None):
        out, hidden = self.lstm(x, hidden)
        out = self.fc(out[:, -1, :]) * self.scale
        return out, hidden

# -------------------------------
# 7. Training
# -------------------------------
def train_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    st.info(f"Using device: {device}")

    # Prepare state features: S_t, T_remaining, implied vol (here use GARCH vol)
    n_paths, T, n_assets = sim_vols.shape
    T_rem = np.linspace(T_init, T_init/T, T)  # approx
    features = np.zeros((n_paths, T, 2*n_assets+1))
    for t in range(T):
        features[:, t, :n_assets] = sim_prices[:, t, :]
        features[:, t, n_assets:2*n_assets] = sim_vols[:, t, :]
        features[:, t, -1] = T_rem[t]
    features = torch.tensor(features, dtype=torch.float32)
    S_tensor = torch.tensor(sim_prices[:, :-1, :], dtype=torch.float32)
    vol_tensor = torch.tensor(sim_vols, dtype=torch.float32)
    T_rem_tensor = torch.tensor(T_rem, dtype=torch.float32)

    input_dim = features.shape[2]
    model = DeepHedger(input_dim, hidden_dim, num_layers, n_assets).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    batch_size = 256

    dataset = torch.utils.data.TensorDataset(features, S_tensor, vol_tensor, T_rem_tensor)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    loss_history = []
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_feat, batch_S, batch_vol, batch_T in loader:
            batch_feat = batch_feat.to(device)
            batch_S = batch_S.to(device)
            batch_vol = batch_vol.to(device)
            batch_T = batch_T.to(device)
            bs = batch_feat.shape[0]
            # Forward: we need hedge sequence; we'll loop over time
            hidden = None
            hedge_seq = []
            for t in range(T):
                # At time t, state is batch_feat[:, t, :] but we need sequential info.
                # Use LSTM iteratively:
                x_t = batch_feat[:, t:t+1, :]
                hed, hidden = model(x_t, hidden)
                hedge_seq.append(hed)
            hedge_seq = torch.stack(hedge_seq, dim=1)  # (bs, T, n_assets)

            # Compute P&L
            hedge_prev = torch.cat([torch.zeros(bs, 1, n_assets, device=device),
                                    hedge_seq[:, :-1, :]], dim=1)
            S_prev = torch.cat([batch_S[:, 0:1, :], batch_S[:, :-1, :]], dim=1)
            stock_ret = batch_S / S_prev - 1
            hedge_pnl = torch.sum(hedge_prev * S_prev * stock_ret, dim=2)  # (bs, T)
            trade_size = torch.abs(hedge_seq - hedge_prev)
            tcost = tc * torch.sum(trade_size * batch_S, dim=2)

            # Option values
            opt_vals = []
            for b in range(bs):
                vals_b = []
                for t in range(T):
                    S_np = batch_S[b, t].cpu().numpy()
                    vol_np = batch_vol[b, t].cpu().numpy()
                    vals_b.append(pf.price(S_np, batch_T[t].item(), vol_np))
                opt_vals.append(torch.tensor(vals_b, dtype=torch.float32, device=device))
            opt_vals = torch.stack(opt_vals)  # (bs, T)
            init_val = torch.tensor([pf.price(batch_S[i,0].cpu().numpy(), batch_T[0].item(), batch_vol[i,0].cpu().numpy()) for i in range(bs)], device=device)

            final_opt = opt_vals[:, -1]
            pnl = final_opt - init_val + torch.sum(hedge_pnl - tcost, dim=1)

            # CVaR loss
            sorted_pnl, _ = torch.sort(pnl)
            var_idx = int((1 - cvar_alpha) * bs)
            cvar = sorted_pnl[:var_idx].mean()
            loss = -cvar

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * bs
        epoch_loss /= n_paths
        loss_history.append(epoch_loss)
        if (epoch+1) % 10 == 0:
            st.write(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f}")
    return model, loss_history

if st.sidebar.button("Train Deep Hedging Model"):
    with st.spinner("Training..."):
        model, loss_hist = train_model()
        st.session_state['model'] = model
        st.session_state['loss_hist'] = loss_hist
        st.success("Training complete!")
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(y=loss_hist, mode='lines', name='Loss'))
        fig_loss.update_layout(title="Training Loss", xaxis_title="Epoch")
        st.plotly_chart(fig_loss)

# -------------------------------
# 8. Backtesting on real data
# -------------------------------
if 'model' in st.session_state:
    st.subheader("Backtest on Historical Data")
    model = st.session_state['model']
    model.eval()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Use last 60 days of real data as out-of-sample
    backtest_days = min(horizon_days, len(data)-1)
    hist_data = data.iloc[-backtest_days-1:]
    hist_returns = returns.iloc[-backtest_days:]

    # We need volatility forecasts: use rolling GARCH predictions (simplified: constant sigma from last GARCH)
    sigma_forecast = np.array([m.conditional_volatility.iloc[-1] for m in models])
    # For simplicity, use constant vol for backtest
    S_hist = hist_data.values
    T_rem_hist = np.linspace(T_init, 0, backtest_days+1)[:backtest_days]  # from T_init to 0 in backtest_days steps
    hedge_positions = np.zeros((backtest_days, n_assets))
    pnl_daily = []

    # Deep hedging loop
    hidden = None
    cash = 0.0
    current_hedge = np.zeros(n_assets)
    for t in range(backtest_days):
        S_t = S_hist[t]
        # Option price at start (before rebalance)
        opt_val = pf.price(S_t, T_rem_hist[t], sigma_forecast)
        if t == 0:
            # initial cash = - opt_val (buy portfolio)
            cash = -opt_val
        else:
            # P&L from previous hedge
            S_prev = S_hist[t-1]
            hedge_pnl = np.dot(current_hedge, S_t - S_prev)
            cash += hedge_pnl
            # transaction cost from previous rebalance already accounted

        # Prepare state
        state = np.concatenate([S_t, sigma_forecast, [T_rem_hist[t]]])
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)  # (1,1,feat)
        with torch.no_grad():
            hedge_out, hidden = model(state_tensor, hidden)
        new_hedge = hedge_out.cpu().numpy().flatten()

        # Transaction cost
        trade = new_hedge - current_hedge
        tcost_t = tc * np.sum(np.abs(trade) * S_t)
        cash -= tcost_t
        current_hedge = new_hedge
        hedge_positions[t, :] = current_hedge

        # Daily P&L = option value change + cash change
        if t > 0:
            opt_val_prev = pf.price(S_hist[t-1], T_rem_hist[t-1], sigma_forecast)
            daily_pnl = (opt_val - opt_val_prev) + (cash - cash_prev)
        else:
            daily_pnl = 0.0
        cash_prev = cash
        pnl_daily.append(daily_pnl)
    # Final liquidation
    opt_val_final = pf.price(S_hist[-1], 0.0, sigma_forecast)
    final_pnl = opt_val_final + cash
    pnl_daily.append(final_pnl - (pnl_daily[-1] if pnl_daily else 0))  # rough

    cumulative_pnl = np.cumsum(pnl_daily)

    # Delta hedging benchmark (daily rebalance)
    delta_positions = np.zeros((backtest_days, n_assets))
    pnl_delta = []
    hedge_delta = np.zeros(n_assets)
    cash_d = 0.0
    for t in range(backtest_days):
        S_t = S_hist[t]
        opt_val_t = pf.price(S_t, T_rem_hist[t], sigma_forecast)
        if t == 0:
            cash_d = -opt_val_t
        else:
            hedge_pnl_d = np.dot(hedge_delta, S_t - S_hist[t-1])
            cash_d += hedge_pnl_d
        new_delta = pf.delta(S_t, T_rem_hist[t], sigma_forecast)
        trade_d = new_delta - hedge_delta
        tcost_d = tc * np.sum(np.abs(trade_d) * S_t)
        cash_d -= tcost_d
        hedge_delta = new_delta
        delta_positions[t] = hedge_delta
        daily_d = (opt_val_t - pf.price(S_hist[t-1], T_rem_hist[t-1], sigma_forecast)) + (cash_d - cash_d_prev) if t>0 else 0
        cash_d_prev = cash_d
        pnl_delta.append(daily_d)
    opt_final_d = pf.price(S_hist[-1], 0.0, sigma_forecast)
    final_d = opt_final_d + cash_d
    pnl_delta.append(final_d - (pnl_delta[-1] if pnl_delta else 0))
    cum_delta = np.cumsum(pnl_delta)

    # Plot
    fig_pnl = go.Figure()
    fig_pnl.add_trace(go.Scatter(y=cumulative_pnl, mode='lines', name='Deep Hedging'))
    fig_pnl.add_trace(go.Scatter(y=cum_delta, mode='lines', name='Delta Hedging'))
    fig_pnl.update_layout(title="Cumulative Hedged P&L", xaxis_title="Days")
    st.plotly_chart(fig_pnl)

    # Metrics
    st.write("### Performance Metrics")
    deep_sharpe = np.mean(pnl_daily[1:]) / np.std(pnl_daily[1:]) * np.sqrt(252)
    delta_sharpe = np.mean(pnl_delta[1:]) / np.std(pnl_delta[1:]) * np.sqrt(252)
    col1, col2 = st.columns(2)
    col1.metric("Deep Sharpe", f"{deep_sharpe:.3f}")
    col2.metric("Delta Sharpe", f"{delta_sharpe:.3f}")

    # Statistical tests
    from scipy.stats import chi2
    def kupiec_test(pnl_series, var, alpha=0.99):
        exceptions = (pnl_series < -var).sum()
        total = len(pnl_series)
        p_hat = exceptions / total
        if p_hat == 0:
            return 0.0, 1.0
        lr = -2 * np.log(((1 - alpha)**(total - exceptions) * alpha**exceptions) /
                         ((1 - p_hat)**(total - exceptions) * p_hat**exceptions))
        p_val = 1 - chi2.cdf(lr, 1)
        return lr, p_val

    var_deep = np.quantile(pnl_daily[1:], 0.01)
    lr_deep, p_deep = kupiec_test(np.array(pnl_daily[1:]), var_deep)
    st.write(f"Deep Hedging VaR(99%) backtest: LR={lr_deep:.2f}, p-value={p_deep:.3f}")

    # Diebold-Mariano test (simplified)
    errors_deep = np.array(pnl_daily[1:])
    errors_delta = np.array(pnl_delta[1:])
    d = np.abs(errors_deep) - np.abs(errors_delta)
    se = np.std(d) / np.sqrt(len(d))
    dm_stat = np.mean(d) / se if se != 0 else 0
    from scipy.stats import norm as norm_dist
    p_dm = 2 * (1 - norm_dist.cdf(np.abs(dm_stat)))
    st.write(f"Diebold-Mariano test (abs errors): DM={dm_stat:.3f}, p-value={p_dm:.3f}")

    st.write("Negative DM statistic means deep hedging errors are smaller (better).")
