package ma.compta.facture

import android.content.ClipData
import android.content.ClipboardManager
import android.os.Bundle
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.HorizontalScrollView
import android.widget.RadioButton
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var etDescription: EditText
    private lateinit var spSens: Spinner
    private lateinit var spCategorie: Spinner
    private lateinit var etMontant: EditText
    private lateinit var rbHt: RadioButton
    private lateinit var rbTtc: RadioButton
    private lateinit var spTaux: Spinner
    private lateinit var spReglement: Spinner
    private lateinit var etTiers: EditText
    private lateinit var etNumFacture: EditText
    private lateinit var tvResultat: TextView
    private lateinit var tvNotes: TextView

    private val tauxValeurs = listOf(20, 14, 10, 7, 0)
    private val tauxLibelles = listOf(
        "20 % (taux normal)", "14 %", "10 %", "7 %", "0 % / exonéré / hors champ",
    )

    private var categoriesCourantes: List<Categorie> = Categories.achats
    private var derniereEcriture: Ecriture? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        etDescription = findViewById(R.id.etDescription)
        spSens = findViewById(R.id.spSens)
        spCategorie = findViewById(R.id.spCategorie)
        etMontant = findViewById(R.id.etMontant)
        rbHt = findViewById(R.id.rbHt)
        rbTtc = findViewById(R.id.rbTtc)
        spTaux = findViewById(R.id.spTaux)
        spReglement = findViewById(R.id.spReglement)
        etTiers = findViewById(R.id.etTiers)
        etNumFacture = findViewById(R.id.etNumFacture)
        tvResultat = findViewById(R.id.tvResultat)
        tvNotes = findViewById(R.id.tvNotes)

        spSens.adapter = adapter(
            listOf(getString(R.string.sens_achat), getString(R.string.sens_vente)),
        )
        spTaux.adapter = adapter(tauxLibelles)
        spReglement.adapter = adapter(
            listOf(
                getString(R.string.reglement_credit),
                getString(R.string.reglement_especes),
                getString(R.string.reglement_banque),
            ),
        )

        spSens.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {
                majCategories(if (pos == 0) Sens.ACHAT else Sens.VENTE)
            }

            override fun onNothingSelected(p: AdapterView<*>?) {}
        }
        majCategories(Sens.ACHAT)

        spCategorie.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {
                selectionnerTaux(categoriesCourantes[pos].tauxSuggere)
            }

            override fun onNothingSelected(p: AdapterView<*>?) {}
        }

        findViewById<Button>(R.id.btnAnalyser).setOnClickListener { analyserDescription() }
        findViewById<Button>(R.id.btnGenerer).setOnClickListener { genererEcriture() }
        findViewById<Button>(R.id.btnCopier).setOnClickListener { copierEcriture() }
    }

    private fun adapter(items: List<String>): ArrayAdapter<String> =
        ArrayAdapter(this, android.R.layout.simple_spinner_item, items).apply {
            setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }

    private fun majCategories(sens: Sens) {
        categoriesCourantes = Categories.pour(sens)
        spCategorie.adapter = adapter(categoriesCourantes.map { it.label })
    }

    private fun selectionnerTaux(taux: Int) {
        val idx = tauxValeurs.indexOf(taux)
        if (idx >= 0) spTaux.setSelection(idx)
    }

    private fun analyserDescription() {
        val texte = etDescription.text.toString().trim()
        if (texte.isEmpty()) {
            Toast.makeText(this, R.string.analyse_vide, Toast.LENGTH_SHORT).show()
            return
        }
        val s = TextAnalyzer.analyser(texte)

        s.sens?.let { spSens.setSelection(if (it == Sens.ACHAT) 0 else 1) }
        val sensEffectif = s.sens ?: sensCourant()
        majCategories(sensEffectif)

        s.categorieId?.let { id ->
            val idx = categoriesCourantes.indexOfFirst { it.id == id }
            if (idx >= 0) {
                spCategorie.setSelection(idx)
                selectionnerTaux(categoriesCourantes[idx].tauxSuggere)
            }
        }
        s.montant?.let { etMontant.setText(if (it == it.toLong().toDouble()) it.toLong().toString() else it.toString()) }
        s.montantEstTtc?.let { if (it) rbTtc.isChecked = true else rbHt.isChecked = true }
        s.tauxTva?.let { selectionnerTaux(it) }
        s.reglement?.let {
            spReglement.setSelection(
                when (it) {
                    Reglement.CREDIT -> 0
                    Reglement.ESPECES -> 1
                    Reglement.BANQUE -> 2
                },
            )
        }
        Toast.makeText(this, R.string.analyse_ok, Toast.LENGTH_SHORT).show()
    }

    private fun sensCourant(): Sens =
        if (spSens.selectedItemPosition == 0) Sens.ACHAT else Sens.VENTE

    private fun genererEcriture() {
        val montant = etMontant.text.toString().replace(',', '.').toDoubleOrNull()
        if (montant == null || montant <= 0) {
            Toast.makeText(this, R.string.err_montant, Toast.LENGTH_SHORT).show()
            return
        }
        val pos = spCategorie.selectedItemPosition.coerceIn(categoriesCourantes.indices)
        val saisie = Saisie(
            sens = sensCourant(),
            categorie = categoriesCourantes[pos],
            montant = montant,
            montantEstTtc = rbTtc.isChecked,
            tauxTva = tauxValeurs[spTaux.selectedItemPosition],
            reglement = when (spReglement.selectedItemPosition) {
                1 -> Reglement.ESPECES
                2 -> Reglement.BANQUE
                else -> Reglement.CREDIT
            },
            tiers = etTiers.text.toString().trim(),
            numFacture = etNumFacture.text.toString().trim(),
            date = "",
        )

        val ecriture = RuleEngine.comptabiliser(saisie)
        derniereEcriture = ecriture

        tvResultat.text = Format.ecriture(ecriture)
        tvNotes.text = Format.notes(ecriture)

        listOf(
            R.id.tvTitreEcriture, R.id.hsvResultat, R.id.btnCopier,
            R.id.tvTitreNotes, R.id.tvNotes,
        ).forEach { findViewById<View>(it).visibility = View.VISIBLE }

        findViewById<HorizontalScrollView>(R.id.hsvResultat).post {
            findViewById<View>(R.id.tvTitreEcriture).requestFocus()
        }
    }

    private fun copierEcriture() {
        val e = derniereEcriture ?: return
        val texte = Format.ecriture(e) + "\n\n" + Format.notes(e)
        val cm = getSystemService(CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("ecriture", texte))
        Toast.makeText(this, R.string.copie_ok, Toast.LENGTH_SHORT).show()
    }
}
