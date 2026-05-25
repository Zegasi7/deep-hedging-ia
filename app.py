import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.callbacks import Callback
from sklearn.model_selection import train_test_split

# --- Configuration de la page ---
st.set_page_config(page_title="Deep Hedging - Live Dashboard", layout="wide")
st.title("🧠 Application : Deep Learning & Couverture Dynamique")
st.markdown("### Projet de Statistique Appliquée à la Finance")

# --- Session State ---
if 'ia_entrainee' not in st.session_state:
    st.session_state.ia_entrainee = False

# --- Callback Customisé pour afficher l'entraînement en direct ---
class StreamlitCallback(Callback):
    def __init__(self, progress_bar, status_text, total_epochs):
        self.progress_bar = progress_bar
        self.status_text = status_text
        self.total_epochs = total_epochs

    def on_epoch_end(self, epoch, logs=None):
        progress = (epoch + 1) / self.total_epochs
        self.progress_bar.progress(progress)
        self.status_text.markdown(f"**Époque {epoch + 1}/{self.total_epochs}** | Erreur (Loss) : `{logs['loss']:.5f}` | Validation : `{logs['val_loss']:.5f}`")

# --- Barre latérale ---
st.sidebar.header("1. Paramètres de Marché")
mu = st.sidebar.slider("Tendance (Drift - μ)", -0.20, 0.20, 0.05, 0.01)
sigma = st.sidebar.slider("Volatilité (Écart-type - σ)", 0.01, 0.80, 0.20, 0.01)
T = st.sidebar.slider("Maturité (T en années)", 0.5, 5.0, 1.0, 0.5)

st.sidebar.header("2. Paramètres de l'IA")
epochs = st.sidebar.slider("Époques d'entraînement", 10, 100, 30, 5)
n_samples = st.sidebar.selectbox("Taille de l'échantillon", [2000, 5000, 10000])

# --- Section 1 : Environnement Stochastique ---
st.subheader("1. Mouvement Brownien Géométrique (Simulation)")
S0 = 100.0
dt = 1/252
num_steps = int(T / dt)
Z = np.random.standard_normal(num_steps)
path = np.zeros(num_steps + 1)
path[0] = S0
for t in range(1, num_steps + 1):
    path[t] = path[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z[t-1])

fig1, ax1 = plt.subplots(figsize=(12, 3))
ax1.plot(path, color='#1f77b4', linewidth=1.5)
ax1.set_xlabel("Jours de trading")
ax1.set_ylabel("Prix de l'actif")
st.pyplot(fig1)

# --- Section 2 : Entraînement de l'IA ---
st.subheader("2. Apprentissage du Réseau de Neurones")

if st.button("🚀 Lancer l'entraînement en direct", type="primary"):
    st.markdown("#### L'IA réfléchit (Progression en direct) :")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    np.random.seed(42)
    S_train = np.random.uniform(50, 150, n_samples)
    T_train = np.random.uniform(0.1, 1.0, n_samples)
    K = 100.0
    r = 0.05
    
    def bs_delta(S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return norm.cdf(d1)
        
    y_target = bs_delta(S_train, K, T_train, r, sigma)
    X = np.column_stack((S_train, T_train))
    X_train, X_test, y_train, y_test = train_test_split(X, y_target, test_size=0.2, random_state=42)
    
    model = Sequential([
        Dense(32, input_dim=2, activation='relu'),
        Dense(64, activation='relu'),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='mse')
    
    history = model.fit(
        X_train, y_train, 
        epochs=epochs, 
        batch_size=64, 
        validation_split=0.2, 
        verbose=0,
        callbacks=[StreamlitCallback(progress_bar, status_text, epochs)]
    )
    
    predictions = model.predict(X_test).flatten()
    
    st.session_state.ia_entrainee = True
    st.session_state.train_loss = history.history['loss']
    st.session_state.val_loss = history.history['val_loss']
    st.session_state.y_test = y_test
    st.session_state.predictions = predictions

# --- Affichage des Résultats Finaux ---
if st.session_state.ia_entrainee:
    st.success("✅ Entraînement terminé ! L'IA a trouvé la corrélation mathématique.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Convergence Statistique**")
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.plot(st.session_state.train_loss, label='Apprentissage')
        ax2.plot(st.session_state.val_loss, label='Validation')
        ax2.legend()
        st.pyplot(fig2)
        
    with col2:
        st.markdown("**Prédiction IA vs Théorie**")
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        ax3.scatter(st.session_state.y_test, st.session_state.predictions, alpha=0.3, color='green')
        ax3.plot([0, 1], [0, 1], color='red', linestyle='--')
        st.pyplot(fig3)
