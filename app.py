import streamlit as st
import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Quant Lab - Deep Hedging", layout="wide")
st.title("📊 Laboratoire de Recherche Quantitative : Deep Hedging")

# --- CLASSE DU LABO (ARCHITECTURE PRO) ---
class FinancialQuantLab:
    def __init__(self, n_samples=5000):
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, n_samples)
        prices = 100 * np.exp(np.cumsum(returns))
        self.df = pd.DataFrame({'Returns': returns, 'Price': prices})
        self.scaler = StandardScaler()

    def get_descriptive_stats(self):
        stats_data = self.df['Returns'].agg(['mean', 'median', 'std', 'skew', 'kurt'])
        q75, q25 = np.percentile(self.df['Returns'], [75, 25])
        stats_data['IQR'] = q75 - q25
        return stats_data

    def get_inference(self):
        jb_stat, p_val = stats.jarque_bera(self.df['Returns'])
        return jb_stat, p_val

    def get_ols_summary(self):
        X = sm.add_constant(self.df['Price'].shift(1).fillna(100))
        y = self.df['Price']
        return sm.OLS(y, X).fit()

    def run_deep_hedging(self):
        X = self.scaler.fit_transform(self.df[['Price']])
        y = self.df['Returns'].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        mlp = MLPRegressor(hidden_layer_sizes=(128, 64, 32), max_iter=1000, activation='relu', solver='adam')
        mlp.fit(X_train, y_train)
        return mlp.score(X_test, y_test), mlp.loss_curve_

# --- APPLICATION INTERFACE (STREAMLIT) ---
lab = FinancialQuantLab()
tab1, tab2, tab3, tab4 = st.tabs(["1. Data Mining", "2. Inférence", "3. Benchmark OLS", "4. Deep Hedging"])

with tab1:
    st.subheader("Analyse Exploratoire des Données")
    st.table(lab.get_descriptive_stats())
    fig, ax = plt.subplots()
    ax.hist(lab.df['Returns'], bins=50, color='green')
    st.pyplot(fig)

with tab2:
    st.subheader("Validation Statistique")
    jb, p = lab.get_inference()
    st.write(f"**Test de Jarque-Bera :** {jb:.2f}")
    st.write(f"**P-value :** {p:.4f}")
    st.info("Si la P-value < 0.05, les données ne suivent pas une loi normale (Fondement du Deep Hedging).")

with tab3:
    st.subheader("Régression Linéaire (Baseline)")
    model = lab.get_ols_summary()
    st.text(model.summary())

with tab4:
    st.subheader("Modèle de Deep Hedging")
    score, loss = lab.run_deep_hedging()
    st.metric("Performance R2 Score", f"{score:.4f}")
    fig, ax = plt.subplots()
    ax.plot(loss)
    ax.set_title("Convergence (Loss Curve)")
    st.pyplot(fig)
