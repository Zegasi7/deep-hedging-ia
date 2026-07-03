package ma.compta.facture

import java.text.Normalizer

/** Résultat de l'analyse du texte libre décrivant la facture. */
data class Suggestion(
    val sens: Sens?,
    val categorieId: String?,
    val montant: Double?,
    val montantEstTtc: Boolean?,
    val tauxTva: Int?,
    val reglement: Reglement?,
)

/**
 * Analyse naïve par mots-clés d'une description de facture en français,
 * pour pré-remplir le formulaire. C'est une suggestion, pas un verdict.
 */
object TextAnalyzer {

    private val motsVente = listOf(
        "vente", "vendu", "client", "facture de vente", "j'ai facture", "encaisse", "prestation rendue",
    )
    private val motsAchat = listOf("achat", "achete", "fournisseur", "recu une facture", "paye")

    // Ordre important : le premier motif qui matche gagne.
    private val motsCategoriesAchat: List<Pair<String, List<String>>> = listOf(
        "vehicule_utilitaire" to listOf("camion", "utilitaire", "fourgon", "tricycle"),
        "vehicule_tourisme" to listOf("voiture", "vehicule de tourisme", "citadine", "berline", "dacia", "clio"),
        "gasoil_transport" to listOf("gasoil camion", "gasoil transport"),
        "carburant_tourisme" to listOf("carburant", "essence", "gasoil", "diesel", "station", "afriquia", "shell", "total", "winxo"),
        "eau_electricite" to listOf("electricite", "lydec", "redal", "amendis", "onee", "eau"),
        "telecom" to listOf("telephone", "internet", "iam", "maroc telecom", "inwi", "orange", "fibre", "forfait mobile"),
        "honoraires" to listOf("honoraire", "avocat", "notaire", "comptable", "expert", "consultant", "conseil juridique", "audit"),
        "loyer" to listOf("loyer", "location du local", "bail", "location bureau"),
        "assurance" to listOf("assurance", "prime d'assurance", "wafa assurance", "rma", "sanad", "axa"),
        "services_bancaires" to listOf("frais bancaire", "commission bancaire", "agios", "banque", "tenue de compte"),
        "missions" to listOf("hotel", "restaurant", "mission", "deplacement", "voyage", "reception", "billet d'avion", "riad"),
        "cadeaux" to listOf("cadeau"),
        "publicite" to listOf("publicite", "pub", "annonce", "flyer", "sponsoring", "communication"),
        "transport" to listOf("transport", "fret", "livraison", "messagerie", "ctm", "coursier"),
        "informatique" to listOf("ordinateur", "pc portable", "laptop", "imprimante", "serveur", "informatique", "ecran"),
        "logiciel" to listOf("logiciel", "licence", "software", "erp", "sage"),
        "mobilier" to listOf("mobilier", "bureau (meuble)", "chaise", "armoire", "meuble"),
        "materiel" to listOf("machine", "outillage", "equipement", "materiel industriel"),
        "construction" to listOf("construction", "local commercial", "appartement", "immeuble", "batiment"),
        "terrain" to listOf("terrain"),
        "entretien" to listOf("entretien", "reparation", "maintenance", "vidange", "peinture", "plombier"),
        "matieres_premieres" to listOf("matiere premiere", "matieres premieres", "tissu", "farine", "ciment"),
        "fournitures" to listOf("fourniture", "papeterie", "consommable", "ramette", "stylo"),
        "marchandises" to listOf("marchandise", "revente", "negoce", "stock"),
    )

    private val motsCategoriesVente: List<Pair<String, List<String>>> = listOf(
        "vente_export" to listOf("export", "etranger", "international"),
        "prestation_services" to listOf("prestation", "service", "honoraire", "formation", "developpement", "maintenance", "conseil"),
        "vente_produits" to listOf("produit fini", "production", "fabrique"),
        "vente_marchandises" to listOf("marchandise", "vente", "negoce"),
    )

    fun analyser(texte: String): Suggestion {
        val t = normaliser(texte)

        val sens = when {
            motsVente.any { t.contains(it) } && motsAchat.none { t.contains(it) } -> Sens.VENTE
            motsAchat.any { t.contains(it) } -> Sens.ACHAT
            motsVente.any { t.contains(it) } -> Sens.VENTE
            else -> null
        }
        val sensEffectif = sens ?: Sens.ACHAT

        val dico = if (sensEffectif == Sens.VENTE) motsCategoriesVente else motsCategoriesAchat
        val categorieId = dico.firstOrNull { (_, mots) -> mots.any { t.contains(it) } }?.first

        val reglement = when {
            listOf("espece", "cash", "liquide").any { t.contains(it) } -> Reglement.ESPECES
            listOf("cheque", "virement", "carte", "tpe", "par banque").any { t.contains(it) } -> Reglement.BANQUE
            listOf("credit", "a terme", "60 jours", "90 jours", "30 jours", "non paye", "pas encore paye").any { t.contains(it) } -> Reglement.CREDIT
            else -> null
        }

        val taux = Regex("\\b(20|14|10|7)\\s*%").find(t)?.groupValues?.get(1)?.toIntOrNull()

        val montantEstTtc = when {
            t.contains("ttc") -> true
            t.contains(" ht") || t.startsWith("ht") || t.contains("hors taxe") -> false
            else -> null
        }

        return Suggestion(
            sens = sens,
            categorieId = categorieId,
            montant = extraireMontant(t),
            montantEstTtc = montantEstTtc,
            tauxTva = taux,
            reglement = reglement,
        )
    }

    /** Extrait le montant le plus plausible (de préférence suivi de dh/dhs/mad). */
    private fun extraireMontant(t: String): Double? {
        val regex = Regex("(\\d{1,3}(?:[\\s.]\\d{3})+(?:,\\d{1,2})?|\\d+(?:[.,]\\d{1,2})?)\\s*(dh|dhs|mad)?")
        var meilleur: Double? = null
        var meilleurAvecDevise = false
        for (m in regex.findAll(t)) {
            val brut = m.groupValues[1]
            val avecDevise = m.groupValues[2].isNotEmpty()
            // Ignore les nombres qui font partie d'un pourcentage.
            val apres = t.getOrNull(m.range.last + 1)
            if (apres == '%') continue
            val v = parseNombre(brut) ?: continue
            if (v < 1) continue
            val gagne = when {
                avecDevise && !meilleurAvecDevise -> true
                avecDevise == meilleurAvecDevise -> meilleur == null || v > meilleur!!
                else -> false
            }
            if (gagne) {
                meilleur = v
                meilleurAvecDevise = avecDevise
            }
        }
        return meilleur
    }

    private fun parseNombre(brut: String): Double? {
        var s = brut.replace(" ", "")
        s = if (s.contains(',')) {
            s.replace(".", "").replace(',', '.')
        } else if (s.count { it == '.' } > 1 || Regex("\\.\\d{3}$").containsMatchIn(s)) {
            s.replace(".", "")
        } else s
        return s.toDoubleOrNull()
    }

    private fun normaliser(s: String): String {
        val lower = s.lowercase()
        return Normalizer.normalize(lower, Normalizer.Form.NFD)
            .replace(Regex("\\p{Mn}+"), "")
    }
}
