"""Règles de conversion Sage -> Pennylane.

Ce fichier regroupe tous les paramètres métier : modifiez-le pour ajuster
la conversion sans toucher au reste du code.
"""

# Encodage des exports Sage (format DOS)
ENCODAGE_SAGE = "cp850"

# Compte client Pennylane = PREFIXE_COMPTE_CLIENT + code client (ex. 3184 -> 411003184)
PREFIXE_COMPTE_CLIENT = "41100"

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
    "5311": "531",
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
