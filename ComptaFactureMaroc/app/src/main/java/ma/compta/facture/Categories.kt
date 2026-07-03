package ma.compta.facture

/**
 * Catalogue des catégories d'opérations, avec les comptes du CGNC
 * (plan comptable général des entreprises marocain) et les règles
 * fiscales usuelles issues du CGI (Code Général des Impôts).
 */
object Categories {

    val achats: List<Categorie> = listOf(
        Categorie(
            id = "marchandises",
            label = "Achat de marchandises (revente en l'état)",
            compte = "6111", compteLabel = "Achats de marchandises",
            sens = Sens.ACHAT,
        ),
        Categorie(
            id = "matieres_premieres",
            label = "Matières premières",
            compte = "6121", compteLabel = "Achats de matières premières",
            sens = Sens.ACHAT,
        ),
        Categorie(
            id = "fournitures",
            label = "Fournitures consommables / bureau",
            compte = "6122", compteLabel = "Achats de matières et fournitures consommables",
            sens = Sens.ACHAT,
        ),
        Categorie(
            id = "eau_electricite",
            label = "Eau / Électricité",
            compte = "61251", compteLabel = "Achats de fournitures non stockables (eau, électricité)",
            sens = Sens.ACHAT,
            notes = listOf(
                "Taux en convergence (LF 2024) : eau vers 10 %, électricité vers 20 % à l'horizon 2026. Reprenez le taux exact figurant sur la facture (ONEE, Lydec, Redal, Amendis…).",
            ),
        ),
        Categorie(
            id = "carburant_tourisme",
            label = "Carburant – véhicule de tourisme",
            compte = "61225", compteLabel = "Achats de combustibles (carburants)",
            sens = Sens.ACHAT,
            tvaDeductible = false,
            notes = listOf(
                "TVA NON déductible sur les carburants utilisés dans des véhicules de tourisme (art. 106 CGI) : la TVA est incorporée au coût, la charge est comptabilisée TTC.",
            ),
        ),
        Categorie(
            id = "gasoil_transport",
            label = "Gasoil – véhicules d'exploitation (transport)",
            compte = "61225", compteLabel = "Achats de combustibles (gasoil)",
            sens = Sens.ACHAT,
            notes = listOf(
                "TVA déductible sur le gasoil utilisé pour les besoins d'exploitation des véhicules de transport routier de marchandises ou de personnes (art. 106 CGI). Conservez les justificatifs kilométriques.",
            ),
        ),
        Categorie(
            id = "loyer",
            label = "Loyer local professionnel",
            compte = "6131", compteLabel = "Locations et charges locatives",
            sens = Sens.ACHAT,
            notes = listOf(
                "Location nue à usage professionnel : souvent hors champ de TVA ; location de locaux équipés/meublés : TVA 20 %. Vérifiez la facture.",
                "Loyer versé à une personne physique : retenue à la source IR sur revenus fonciers (10 % si loyer annuel ≤ 120 000 DH, 15 % au-delà — art. 160 bis CGI), à opérer par l'entreprise locataire personne morale.",
            ),
        ),
        Categorie(
            id = "entretien",
            label = "Entretien et réparations",
            compte = "6133", compteLabel = "Entretien et réparations",
            sens = Sens.ACHAT,
            notes = listOf(
                "Si la dépense prolonge la durée de vie ou augmente la valeur du bien (grosse réparation), il peut s'agir d'une immobilisation (classe 2) et non d'une charge.",
            ),
        ),
        Categorie(
            id = "assurance",
            label = "Primes d'assurance",
            compte = "6134", compteLabel = "Primes d'assurances",
            sens = Sens.ACHAT,
            horsChampTva = true,
            tauxSuggere = 0,
            notes = listOf(
                "Les primes d'assurance sont soumises à la taxe sur les contrats d'assurance, pas à la TVA : aucune TVA récupérable — comptabilisez le montant total en charge.",
            ),
        ),
        Categorie(
            id = "honoraires",
            label = "Honoraires (avocat, comptable, notaire, consultant…)",
            compte = "61365", compteLabel = "Honoraires",
            sens = Sens.ACHAT,
            notes = listOf(
                "Retenue à la source sur les rémunérations allouées à des tiers (LF 2023) : 5 % si les honoraires sont versés à une personne morale soumise à l'IS ; 10 % ou 30 % selon la situation fiscale de la personne physique. Vérifiez le cas exact avec votre conseil.",
                "Exigez une facture avec ICE et IF du prestataire : condition de déductibilité (art. 145 et 146 CGI).",
            ),
        ),
        Categorie(
            id = "transport",
            label = "Transport / fret sur achats-ventes",
            compte = "6142", compteLabel = "Transports",
            sens = Sens.ACHAT,
            tauxSuggere = 14,
            notes = listOf(
                "Transport : taux historique de 14 % en cours de convergence vers 20 % (LF 2024). Reprenez le taux figurant sur la facture.",
            ),
        ),
        Categorie(
            id = "missions",
            label = "Déplacements, missions, réceptions (hôtel, restaurant…)",
            compte = "6143", compteLabel = "Déplacements, missions et réceptions",
            sens = Sens.ACHAT,
            tvaDeductible = false,
            notes = listOf(
                "TVA NON déductible sur les frais de mission, de réception et de déplacement (art. 106-I CGI) : la charge est comptabilisée TTC.",
            ),
        ),
        Categorie(
            id = "publicite",
            label = "Publicité et communication",
            compte = "6144", compteLabel = "Publicité, publications et relations publiques",
            sens = Sens.ACHAT,
        ),
        Categorie(
            id = "cadeaux",
            label = "Cadeaux à la clientèle",
            compte = "61446", compteLabel = "Cadeaux à la clientèle",
            sens = Sens.ACHAT,
            tvaDeductible = false,
            notes = listOf(
                "TVA NON déductible sur les cadeaux (art. 106 CGI) : charge comptabilisée TTC.",
                "Déductible à l'IS uniquement si la valeur unitaire ≤ 100 DH TTC et si l'objet porte le nom/sigle ou la marque de la société (art. 10 CGI). Sinon : réintégration extra-comptable.",
            ),
        ),
        Categorie(
            id = "telecom",
            label = "Téléphone / Internet",
            compte = "61455", compteLabel = "Frais de téléphone et Internet",
            sens = Sens.ACHAT,
        ),
        Categorie(
            id = "services_bancaires",
            label = "Services et commissions bancaires",
            compte = "6147", compteLabel = "Services bancaires",
            sens = Sens.ACHAT,
            tauxSuggere = 10,
            notes = listOf(
                "Opérations de banque : TVA au taux de 10 % (art. 99 CGI). La TVA est déductible sur relevé/avis bancaire mentionnant la taxe.",
            ),
        ),
        // ---- Immobilisations ----
        Categorie(
            id = "materiel",
            label = "Immobilisation : matériel et outillage",
            compte = "2332", compteLabel = "Matériel et outillage",
            sens = Sens.ACHAT, isImmobilisation = true,
            notes = listOf(
                "Bien durable (> 1 exercice) : à immobiliser puis amortir selon les taux d'usage admis par la DGI (ex. matériel : 10 à 15 %).",
            ),
        ),
        Categorie(
            id = "vehicule_utilitaire",
            label = "Immobilisation : véhicule utilitaire / de transport",
            compte = "2340", compteLabel = "Matériel de transport",
            sens = Sens.ACHAT, isImmobilisation = true,
            notes = listOf(
                "TVA déductible pour les véhicules utilitaires affectés à l'exploitation. Amortissement usuel : 20 à 25 %.",
            ),
        ),
        Categorie(
            id = "vehicule_tourisme",
            label = "Immobilisation : véhicule de tourisme",
            compte = "2340", compteLabel = "Matériel de transport (véhicule de tourisme)",
            sens = Sens.ACHAT, isImmobilisation = true,
            tvaDeductible = false,
            notes = listOf(
                "TVA NON déductible sur les véhicules de tourisme (art. 106 CGI) : le véhicule est immobilisé pour son montant TTC.",
                "Amortissement fiscalement déductible plafonné : base maximale de 300 000 DH TTC au taux maximal de 20 % (5 ans) — art. 10-I-F CGI. L'excédent est à réintégrer.",
            ),
        ),
        Categorie(
            id = "informatique",
            label = "Immobilisation : matériel informatique",
            compte = "2355", compteLabel = "Matériel informatique",
            sens = Sens.ACHAT, isImmobilisation = true,
            notes = listOf(
                "Amortissement usuel du matériel informatique : 20 à 25 % (mode linéaire ; dégressif possible sur option, art. 10 CGI).",
            ),
        ),
        Categorie(
            id = "mobilier",
            label = "Immobilisation : mobilier de bureau",
            compte = "2351", compteLabel = "Mobilier de bureau",
            sens = Sens.ACHAT, isImmobilisation = true,
            notes = listOf("Amortissement usuel du mobilier : 10 %."),
        ),
        Categorie(
            id = "logiciel",
            label = "Immobilisation : logiciel / licence perpétuelle",
            compte = "2220", compteLabel = "Brevets, marques, droits et valeurs similaires (logiciels)",
            sens = Sens.ACHAT, isImmobilisation = true,
            notes = listOf(
                "Les abonnements périodiques (SaaS, licences annuelles) sont des charges (ex. 6136 – rémunérations d'intermédiaires / redevances), pas des immobilisations.",
            ),
        ),
        Categorie(
            id = "construction",
            label = "Immobilisation : construction / local",
            compte = "2321", compteLabel = "Bâtiments",
            sens = Sens.ACHAT, isImmobilisation = true,
            notes = listOf(
                "Amortissement usuel des constructions : 4 à 5 %. Prévoir droits d'enregistrement et conservation foncière en sus (à immobiliser dans le coût d'acquisition).",
            ),
        ),
        Categorie(
            id = "terrain",
            label = "Immobilisation : terrain",
            compte = "2311", compteLabel = "Terrains",
            sens = Sens.ACHAT, isImmobilisation = true,
            horsChampTva = true, tauxSuggere = 0,
            notes = listOf(
                "L'acquisition d'un terrain est généralement hors champ de TVA ; elle supporte des droits d'enregistrement. Les terrains ne s'amortissent pas.",
            ),
        ),
    )

    val ventes: List<Categorie> = listOf(
        Categorie(
            id = "vente_marchandises",
            label = "Vente de marchandises (négoce)",
            compte = "7111", compteLabel = "Ventes de marchandises au Maroc",
            sens = Sens.VENTE,
        ),
        Categorie(
            id = "vente_produits",
            label = "Vente de produits finis (production)",
            compte = "7121", compteLabel = "Ventes de produits finis",
            sens = Sens.VENTE,
        ),
        Categorie(
            id = "prestation_services",
            label = "Prestation de services",
            compte = "7124", compteLabel = "Ventes de services",
            sens = Sens.VENTE,
            notes = listOf(
                "Pour les prestations de services, la TVA est exigible à l'encaissement (régime de droit commun, art. 95 CGI), sauf option pour le régime des débits.",
            ),
        ),
        Categorie(
            id = "vente_export",
            label = "Vente à l'export",
            compte = "7113", compteLabel = "Ventes de marchandises à l'étranger",
            sens = Sens.VENTE,
            horsChampTva = true, tauxSuggere = 0,
            notes = listOf(
                "Exportations exonérées de TVA avec droit à déduction (art. 92 CGI). Conservez les justificatifs douaniers (DUM) et de rapatriement des devises.",
            ),
        ),
    )

    fun pour(sens: Sens): List<Categorie> = if (sens == Sens.ACHAT) achats else ventes

    fun parId(id: String): Categorie? = (achats + ventes).firstOrNull { it.id == id }
}
