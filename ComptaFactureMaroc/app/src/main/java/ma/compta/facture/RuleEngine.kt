package ma.compta.facture

import kotlin.math.roundToLong

/**
 * Moteur de règles : à partir de la saisie, produit l'écriture comptable
 * selon le CGNC et les remarques fiscales selon le CGI (règles DGI).
 */
object RuleEngine {

    private const val PLAFOND_ESPECES_ACHAT = 5_000.0
    private const val PLAFOND_ESPECES_VENTE = 20_000.0

    fun comptabiliser(s: Saisie): Ecriture {
        val cat = s.categorie
        val taux = if (cat.horsChampTva) 0 else s.tauxTva
        val t = taux / 100.0

        val ht: Double
        val tva: Double
        if (taux == 0) {
            ht = arrondi(s.montant)
            tva = 0.0
        } else if (s.montantEstTtc) {
            ht = arrondi(s.montant / (1 + t))
            tva = arrondi(s.montant - ht)
        } else {
            ht = arrondi(s.montant)
            tva = arrondi(ht * t)
        }
        val ttc = arrondi(ht + tva)

        val lignes = mutableListOf<Ligne>()
        val notes = mutableListOf<String>()
        notes += cat.notes

        val contrepartie = contrepartie(s)

        if (s.sens == Sens.ACHAT) {
            // TVA non déductible => la charge/l'immobilisation est comptabilisée TTC.
            val tvaRecuperable = cat.tvaDeductible && tva > 0
            val montantCompte = if (tvaRecuperable) ht else ttc
            lignes += Ligne(cat.compte, cat.compteLabel, debit = montantCompte)
            if (tvaRecuperable) {
                val compteTva = if (cat.isImmobilisation) "34551" else "34552"
                val labelTva = if (cat.isImmobilisation)
                    "État – TVA récupérable sur immobilisations"
                else
                    "État – TVA récupérable sur charges"
                lignes += Ligne(compteTva, labelTva, debit = tva)
            }
            lignes += Ligne(contrepartie.first, contrepartie.second, credit = ttc)

            if (!cat.tvaDeductible && tva > 0) {
                // La note explicative figure déjà dans la catégorie.
            }
            if (tvaRecuperable) {
                notes += "TVA récupérable de ${Format.montant(tva)} DH à porter sur la déclaration de TVA (art. 101 et s. CGI). Conditions : facture régulière (ICE, IF, montant de la taxe) et paiement justifié."
            }
        } else {
            lignes += Ligne(contrepartie.first, contrepartie.second, debit = ttc)
            lignes += Ligne(cat.compte, cat.compteLabel, credit = ht)
            if (tva > 0) {
                lignes += Ligne("4455", "État – TVA facturée", credit = tva)
            }
            if (tva > 0) {
                notes += "TVA facturée de ${Format.montant(tva)} DH à déclarer (mensuelle si CA ≥ 1 MDH, sinon trimestrielle — art. 108 CGI). Exigibilité : encaissement par défaut, ou débits sur option (art. 95)."
            }
        }

        // Règles sur le règlement en espèces.
        if (s.reglement == Reglement.ESPECES) {
            if (s.sens == Sens.ACHAT && ttc > PLAFOND_ESPECES_ACHAT) {
                notes += "⚠️ Règlement en espèces de ${Format.montant(ttc)} DH : la déduction (charges/amortissements) est limitée à 5 000 DH TTC par jour et par fournisseur, dans la limite de 50 000 DH TTC par mois et par fournisseur (art. 11-II CGI). La TVA déductible est plafonnée dans les mêmes conditions (art. 106-II CGI). Privilégiez chèque barré non endossable, virement ou carte."
            }
            if (s.sens == Sens.VENTE && ttc >= PLAFOND_ESPECES_VENTE) {
                notes += "⚠️ Encaissement en espèces ≥ 20 000 DH : amende de 6 % du montant encaissé (art. 193 CGI). Exigez un chèque barré non endossable, un virement ou un moyen de paiement électronique."
            }
        }

        if (s.reglement != Reglement.CREDIT) {
            notes += "Bonne pratique : enregistrer d'abord la facture au journal des ${if (s.sens == Sens.ACHAT) "achats (contrepartie 4411)" else "ventes (contrepartie 3421)"}, puis le règlement au journal de trésorerie. L'écriture unique ci-dessus est une simplification admise pour les règlements au comptant."
        }

        notes += "Mentions obligatoires de la facture (art. 145 CGI) : identité et ICE des deux parties, IF, n° de facture, date, désignation, prix HT, taux et montant de la TVA, modalités de paiement."
        notes += "⚠️ Outil pédagogique : vérifiez le traitement auprès d'un expert-comptable et des textes en vigueur (CGNC, CGI, notes circulaires DGI)."

        val journal = when {
            s.reglement == Reglement.ESPECES -> "JOURNAL DE CAISSE"
            s.reglement == Reglement.BANQUE -> "JOURNAL DE BANQUE"
            s.sens == Sens.ACHAT -> "JOURNAL DES ACHATS"
            else -> "JOURNAL DES VENTES"
        }

        val tiers = s.tiers.ifBlank { if (s.sens == Sens.ACHAT) "Fournisseur" else "Client" }
        val numf = s.numFacture.ifBlank { "…" }
        val libelle = (if (s.sens == Sens.ACHAT) "Facture n° $numf – $tiers – ${cat.label}"
        else "Facture n° $numf – $tiers – ${cat.label}")

        return Ecriture(
            journal = journal,
            libelle = libelle,
            lignes = lignes,
            ht = ht, tva = tva, ttc = ttc, tauxTva = taux,
            notes = notes,
        )
    }

    /** Compte de contrepartie (crédit pour un achat, débit pour une vente). */
    private fun contrepartie(s: Saisie): Pair<String, String> = when (s.reglement) {
        Reglement.ESPECES -> "5161" to "Caisses"
        Reglement.BANQUE -> "5141" to "Banques"
        Reglement.CREDIT ->
            if (s.sens == Sens.ACHAT) {
                if (s.categorie.isImmobilisation)
                    "4481" to "Dettes sur acquisitions d'immobilisations"
                else
                    "4411" to "Fournisseurs"
            } else {
                "3421" to "Clients"
            }
    }

    private fun arrondi(v: Double): Double = (v * 100).roundToLong() / 100.0
}
