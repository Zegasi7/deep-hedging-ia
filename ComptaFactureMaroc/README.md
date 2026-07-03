# Compta Facture Maroc 🇲🇦

Application Android (hors ligne) qui vous aide à **comptabiliser une facture selon le plan comptable marocain (CGNC)** et qui signale les **règles fiscales de la DGI** (Code Général des Impôts).

## Fonctionnement

1. Décrivez la facture en texte libre (ex. : *« facture d'honoraires avocat 12 000 dh TTC payée par virement »*) et appuyez sur **Analyser** — ou remplissez directement le formulaire (achat/vente, nature, montant HT/TTC, taux de TVA, mode de règlement).
2. L'application génère **l'écriture comptable** (comptes CGNC débit/crédit, calcul HT/TVA/TTC) et les **remarques fiscales** applicables.

## Règles couvertes (extraits)

- Plan comptable CGNC : classes 2 (immobilisations), 3/4 (TVA 3455/4455, tiers 3421/4411/4481), 5 (trésorerie), 6 (charges), 7 (produits).
- TVA : taux 20 / 14 / 10 / 7 / 0 %, TVA récupérable sur charges (34552) et immobilisations (34551), TVA facturée (4455).
- TVA non déductible (art. 106 CGI) : carburant des véhicules de tourisme, frais de mission/réception, cadeaux, véhicules de tourisme.
- Plafond des règlements en espèces (art. 11-II et 106-II CGI) et amende de 6 % sur encaissements en espèces ≥ 20 000 DH (art. 193 CGI).
- Retenues à la source : honoraires (LF 2023), loyers versés à des personnes physiques (art. 160 bis CGI).
- Amortissement plafonné des véhicules de tourisme (300 000 DH TTC, art. 10 CGI), mentions obligatoires des factures (art. 145 CGI), exonération des exportations (art. 92 CGI).

## Obtenir l'APK

L'APK est compilé automatiquement par GitHub Actions (workflow **Build APK**) :

1. Ouvrez l'onglet **Actions** du dépôt → workflow *Build APK (Compta Facture Maroc)* → dernière exécution.
2. Téléchargez l'artefact **ComptaFactureMaroc-debug-apk** (fichier `app-debug.apk`).
3. Installez-le sur votre téléphone (autorisez l'installation de sources inconnues). Android 8.0+ requis.

Pour compiler localement : `cd ComptaFactureMaroc && ./gradlew assembleDebug` (Android SDK requis).

## ⚠️ Avertissement

Outil **pédagogique**. Les règles fiscales évoluent (lois de finances annuelles, convergence des taux de TVA prévue par la LF 2024). Vérifiez toujours le traitement auprès d'un expert-comptable et des textes en vigueur (CGNC, CGI, notes circulaires DGI).
