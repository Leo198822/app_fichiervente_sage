"""Règles de conversion Sage -> Pennylane.

Ce fichier regroupe tous les paramètres métier : modifiez-le pour ajuster
la conversion sans toucher au reste du code.
"""

# Encodage des exports Sage (format DOS)
ENCODAGE_SAGE = "cp850"

# Compte client Pennylane = PREFIXE_COMPTE_CLIENT + code client, complété par des 0
# à droite jusqu'à LONGUEUR_COMPTE (ex. 0385 -> 411038500, 3184 -> 411318400)
PREFIXE_COMPTE_CLIENT = "411"

# Longueur des numéros de compte généraux (complétés par des 0 à droite).
# Mettre None pour conserver les numéros Sage tels quels.
LONGUEUR_COMPTE = 9

# Remplacement des codes journaux (préfixe du code Sage -> code Pennylane).
# Le préfixe le plus long l'emporte ; un journal absent de la liste est conservé.
JOURNAUX = {
    "VTE": "VT",   # journal de ventes
    "VE": "VT",
    "BQ": "SAGE",  # BQ1, BQ3... -> SAGE
    "CAI": "SAGE",
    "OD": "SAGE",
}

# Remplacement de comptes généraux (préfixe du compte Sage -> compte Pennylane).
COMPTES_REMPLACES = {
    "512": "582000000",
    "5311": "531000000",
    "44571120": "445710000",
}

# Libellés des comptes généraux (préfixe du compte -> libellé).
# Le préfixe le plus long l'emporte.
LIBELLES_COMPTES = {
    "411": "Clients",
    "44571": "TVA collectée",
    "512": "Banque",
    "531": "Caisse",
    "582": "Virements internes",
    "658": "Charges diverses de gestion courante",
    "666": "Pertes de change",
    "706": "Prestations de services",
    "707": "Ventes de marchandises",
    "708": "Produits des activités annexes",
    "758": "Produits divers de gestion courante",
    "766": "Gains de change",
}

# Taux de TVA : calculé pour chaque pièce (TVA collectée / montant HT) puis arrondi
# au taux légal le plus proche. Il est indiqué sur les lignes de produits et de charges.
TAUX_TVA = [20, 10, 5.5, 2.1]
COMPTES_TVA_COLLECTEE = ("4457",)
COMPTES_SOUMIS_TVA = ("6", "7")
LIBELLE_SANS_TVA = "pas de TVA"


# ---------------------------------------------------------------------------
# Import Septeo
# ---------------------------------------------------------------------------

# Colonnes du fichier Septeo (A = 1re colonne)
SEPTEO_COLONNES = ["journal", "date", "piece", "compte", "libelle", "debit", "credit"]

# Remplacement des codes journaux (préfixe du code Septeo -> code Pennylane)
SEPTEO_JOURNAUX = {
    "VE": "VT",
    "AC": "HA",
    # BQ : inchangé
}

# Comptes commençant par ces préfixes : conservés tels quels (pas de mise à 9 caractères)
SEPTEO_COMPTES_INCHANGES = ("411",)

# Libellé de compte = libellé de l'écriture sans ses N premiers caractères
SEPTEO_CARACTERES_A_RETIRER = 7

# TVA collectée (ventes) et déductible (achats) pour le calcul du taux
SEPTEO_COMPTES_TVA = ("4456", "4457")
