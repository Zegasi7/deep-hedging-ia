package ma.compta.facture

import java.text.DecimalFormat
import java.text.DecimalFormatSymbols
import java.util.Locale

object Format {

    private val symbols = DecimalFormatSymbols(Locale.FRENCH).apply {
        groupingSeparator = ' '
        decimalSeparator = ','
    }
    private val df = DecimalFormat("#,##0.00", symbols)

    fun montant(v: Double): String = df.format(v)

    /** Rend l'écriture sous forme de texte monospace aligné. */
    fun ecriture(e: Ecriture): String {
        val sb = StringBuilder()
        val sep = "─".repeat(46)
        sb.appendLine(e.journal)
        sb.appendLine(e.libelle)
        sb.appendLine(sep)
        for (l in e.lignes) {
            val dc = if (l.debit != null) "D" else "C"
            val compte = l.compte.padEnd(6)
            val label = tronque(l.intitule, 24).padEnd(24)
            val montant = montant(l.debit ?: l.credit ?: 0.0).padStart(12)
            val indent = if (l.credit != null) "  " else ""
            sb.appendLine("$indent$dc $compte $label $montant")
        }
        sb.appendLine(sep)
        sb.append("HT : ${montant(e.ht)}")
        if (e.tva > 0) sb.append("   TVA ${e.tauxTva} % : ${montant(e.tva)}")
        sb.append("   TTC : ${montant(e.ttc)}")
        return sb.toString()
    }

    fun notes(e: Ecriture): String =
        e.notes.joinToString("\n\n") { "• $it" }

    private fun tronque(s: String, max: Int): String =
        if (s.length <= max) s else s.substring(0, max - 1) + "…"
}
