import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class DeepHedgingLab:
    def __init__(self, n_samples=5000):
        """
        INITIALISATION: 
        Nous simulons le marché avec un Mouvement Brownien Géométrique (GBM).
        C'est le standard académique pour simuler les prix des actifs.
        """
        np.random.seed(42)
        # Simulation des rendements (loi normale)
        returns = np.random.normal(0.0005, 0.02, n_samples)
        # Simulation des prix (Prix = Prix_initial * exp(somme des rendements))
        prices = 100 * np.exp(np.cumsum(returns))
        self.df = pd.DataFrame({'Returns': returns, 'Price': prices})

    def run_descriptive_analysis(self):
        """
        CHAPITRE 2 DU RAPPORT: Analyse Exploratoire (EDA)
        Nous calculons les moments de la distribution pour démontrer
        l'asymétrie (Skewness) et l'aplatissement (Kurtosis).
        """
        # Calcul des statistiques clés
        stats = self.df['Returns'].agg(['mean', 'median', 'std', 'skew', 'kurt'])
        # Calcul de l'IQR (Interquartile Range) pour mesurer la dispersion robuste
        q75, q25 = np.percentile(self.df['Returns'], [75, 25])
        stats['IQR'] = q75 - q25
        return stats

    def visualize_data(self):
        """Visualisation pour le rapport."""
        fig, ax = plt.subplots(1, 2, figsize=(14, 5))
        
        # Graphique 1: Trajectoire des prix
        ax[0].plot(self.df['Price'], color='blue', lw=1)
        ax[0].set_title("Trajectoire de l'Actif (Simulation)")
        
        # Graphique 2: Histogramme des rendements
        ax[1].hist(self.df['Returns'], bins=50, color='green', alpha=0.7)
        ax[1].set_title("Distribution des Rendements")
        
        return fig

# --- EXÉCUTION ---
lab = DeepHedgingLab()
print("--- ANALYSE DESCRIPTIVE ---")
print(lab.run_descriptive_analysis())

import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

class FinancialQuantLab:
    def __init__(self, n_samples=5000):
        # Simulation (Phase 1)
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, n_samples)
        prices = 100 * np.exp(np.cumsum(returns))
        self.df = pd.DataFrame({'Returns': returns, 'Price': prices})

    def run_descriptive_analysis(self):
        """(Phase 1 déjà réalisée)"""
        return self.df['Returns'].agg(['mean', 'median', 'std', 'skew', 'kurt'])

    # --- PHASE 2: INFÉRENCE STATISTIQUE ---
    
    def run_inference_tests(self):
        """
        CHAPITRE 3: Inférence Statistique
        On utilise le test de Jarque-Bera pour tester la normalité (Loi Khi-deux).
        C'est la preuve scientifique que le marché est 'complexe'.
        """
        jb_stat, p_val = stats.jarque_bera(self.df['Returns'])
        return {"JB_Statistic": jb_stat, "P_Value": p_val, "Normal_Hypothesis": p_val > 0.05}

    def run_confidence_intervals(self, confidence=0.95):
        """
        CHAPITRE 3 (Suite): Estimation par Intervalle
        On calcule l'intervalle de confiance pour valider la précision 
        de nos estimateurs de rendement (Loi de Student).
        """
        n = len(self.df['Returns'])
        mean = self.df['Returns'].mean()
        std = self.df['Returns'].std()
        
        # Utilisation de la loi de Student (t-distribution) pour l'intervalle
        t_crit = stats.t.ppf((1 + confidence) / 2, df=n-1)
        margin_of_error = t_crit * (std / np.sqrt(n))
        
        return {"Lower_Bound": mean - margin_of_error, "Upper_Bound": mean + margin_of_error}

# --- EXÉCUTION PHASE 2 ---
lab = FinancialQuantLab()

print("--- 1. TEST DE NORMALITÉ (JACQUE-BERA) ---")
print(lab.run_inference_tests())

print("\n--- 2. INTERVALLES DE CONFIANCE (STUDENT) ---")
print(lab.run_confidence_intervals())

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from sklearn.neural_network import MLPRegressor

class FinancialQuantLab:
    def __init__(self, n_samples=5000):
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, n_samples)
        prices = 100 * np.exp(np.cumsum(returns))
        self.df = pd.DataFrame({'Returns': returns, 'Price': prices})

    # --- PHASE 3: LE BENCHMARK LINÉAIRE (OLS) ---
    
    def run_benchmark_regression(self):
        """
        CHAPITRE 4: Analyse Comparative & Baseline
        Nous utilisons la Régression Linéaire (Ordinary Least Squares - OLS).
        C'est notre modèle de référence. Il suppose une relation linéaire
        entre le prix passé et le prix futur (hypothèse de marché efficace).
        """
        # On définit X (la variable explicative : Prix t-1)
        # On ajoute une constante (l'ordonnée à l'origine)
        X = sm.add_constant(self.df['Price'].shift(1).fillna(100))
        y = self.df['Price']
        
        # Ajustement du modèle OLS
        model = sm.OLS(y, X).fit()
        return model

# --- EXÉCUTION PHASE 3 ---
lab = FinancialQuantLab()
ols_model = lab.run_benchmark_regression()

# Affichage du rapport statistique complet
print("--- 3. RÉSULTATS RÉGRESSION LINÉAIRE (BENCHMARK) ---")
print(ols_model.summary())

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

class FinancialQuantLab:
    def __init__(self, n_samples=5000):
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, n_samples)
        prices = 100 * np.exp(np.cumsum(returns))
        self.df = pd.DataFrame({'Returns': returns, 'Price': prices})
        self.scaler = StandardScaler()

    # --- PHASE 4: LE DEEP HEDGING ---
    
    def run_deep_hedging_model(self):
        """
        CHAPITRE 5: Deep Learning pour le Hedging Dynamique
        Nous utilisons un Réseau de Neurones (MLP) pour approximer la fonction 
        de couverture (Delta). 
        
        ACADEMIC NOTE:
        Contrairement à l'OLS, le MLP capture les relations non-linéaires 
        entre le prix de l'actif et les rendements. 
        Architecture : 3 couches cachées (128, 64, 32) pour 
        gérer la complexité de la surface de volatilité.
        """
        # Préparation des données (Normalisation cruciale pour les réseaux de neurones)
        X = self.scaler.fit_transform(self.df[['Price']])
        y = self.df['Returns'].values
        
        # Split Train/Test (Pour valider la performance hors échantillon)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Initialisation du Réseau de Neurones
        mlp = MLPRegressor(
            hidden_layer_sizes=(128, 64, 32), 
            max_iter=1000, 
            activation='relu', 
            solver='adam'
        )
        
        # Entraînement
        mlp.fit(X_train, y_train)
        
        # Évaluation (R2 score pour comparer avec l'OLS)
        score = mlp.score(X_test, y_test)
        return score, mlp

# --- EXÉCUTION PHASE 4 ---
lab = FinancialQuantLab()
accuracy, model = lab.run_deep_hedging_model()

print(f"\n--- 4. PERFORMANCE DEEP HEDGING (R2 Score) ---")
print(f"R2 Score du Modèle IA : {accuracy:.4f}")

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

class FinancialQuantLab:
    def __init__(self, n_samples=5000):
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, n_samples)
        prices = 100 * np.exp(np.cumsum(returns))
        self.df = pd.DataFrame({'Returns': returns, 'Price': prices})
        self.scaler = StandardScaler()

    # --- PHASE 4: LE DEEP HEDGING ---
    
    def run_deep_hedging_model(self):
        """
        CHAPITRE 5: Deep Learning pour le Hedging Dynamique
        Nous utilisons un Réseau de Neurones (MLP) pour approximer la fonction 
        de couverture (Delta). 
        
        ACADEMIC NOTE:
        Contrairement à l'OLS, le MLP capture les relations non-linéaires 
        entre le prix de l'actif et les rendements. 
        Architecture : 3 couches cachées (128, 64, 32) pour 
        gérer la complexité de la surface de volatilité.
        """
        # Préparation des données (Normalisation cruciale pour les réseaux de neurones)
        X = self.scaler.fit_transform(self.df[['Price']])
        y = self.df['Returns'].values
        
        # Split Train/Test (Pour valider la performance hors échantillon)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Initialisation du Réseau de Neurones
        mlp = MLPRegressor(
            hidden_layer_sizes=(128, 64, 32), 
            max_iter=1000, 
            activation='relu', 
            solver='adam'
        )
        
        # Entraînement
        mlp.fit(X_train, y_train)
        
        # Évaluation (R2 score pour comparer avec l'OLS)
        score = mlp.score(X_test, y_test)
        return score, mlp

# --- EXÉCUTION PHASE 4 ---
lab = FinancialQuantLab()
accuracy, model = lab.run_deep_hedging_model()

print(f"\n--- 4. PERFORMANCE DEEP HEDGING (R2 Score) ---")
print(f"R2 Score du Modèle IA : {accuracy:.4f}")

