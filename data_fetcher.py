import yfinance as yf
import pandas as pd
import numpy as np

def fetch_stock_data(tickers, start, end):
    """Download adjusted close prices and compute log returns."""
    data = yf.download(tickers, start=start, end=end)['Adj Close']
    returns = np.log(data / data.shift(1)).dropna()
    return data, returns
