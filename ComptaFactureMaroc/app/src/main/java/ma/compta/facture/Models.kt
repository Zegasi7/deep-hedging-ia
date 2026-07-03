package ma.compta.facture

/** Sens de la facture : achat (facture fournisseur) ou vente (facture client). */
enum class Sens { ACHAT, VENTE }

/** Mode de règlement de la facture. */
enum class Reglement { CREDIT, ESPECES, BANQUE }

/**
 * Une catégorie d'opération, associée à un compte du plan comptable
 * marocain (CGNC) et aux règles fiscales (CGI / DGI) qui s'y appliquent.
 */
data class Categorie(
    val id: String,
    val label: String,
    val compte: String,
    val compteLabel: String,
    val sens: Sens,
    val isImmobilisation: Boolean = false,
    val tvaDeductible: Boolean = true,
    val tauxSuggere: Int = 20,
    val horsChampTva: Boolean = false,
    val notes: List<String> = emptyList(),
) {
    override fun toString(): String = label
}

/** Une ligne d'écriture comptable (un compte est soit débité, soit crédité). */
data class Ligne(
    val compte: String,
    val intitule: String,
    val debit: Double? = null,
    val credit: Double? = null,
)

/** L'écriture comptable proposée, avec le journal et les remarques fiscales. */
data class Ecriture(
    val journal: String,
    val libelle: String,
    val lignes: List<Ligne>,
    val ht: Double,
    val tva: Double,
    val ttc: Double,
    val tauxTva: Int,
    val notes: List<String>,
)

/** Données saisies par l'utilisateur. */
data class Saisie(
    val sens: Sens,
    val categorie: Categorie,
    val montant: Double,
    val montantEstTtc: Boolean,
    val tauxTva: Int,
    val reglement: Reglement,
    val tiers: String,
    val numFacture: String,
    val date: String,
)
