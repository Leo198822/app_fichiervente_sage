# Conversion → Pennylane

Application Streamlit qui transforme des exports comptables en fichier
d'import d'écritures au format Pennylane (`.xlsx`).

## Utilisation

1. Choisir le **type d'import** en haut de la page : `Import fichier Sage` ou `Import fichier Septeo`.
2. Déposer les fichiers demandés :
   - Sage : l'export des **écritures** (`.pnm` / `.txt`) et l'export des **clients** (`.pnc` / `.txt`) ;
   - Septeo : l'export des **écritures** (`.xlsx` / `.csv` / `.txt`).
3. Vérifier les totaux et les éventuelles alertes, puis cliquer sur **Télécharger le fichier Pennylane**.

## Règles de conversion Sage

Toutes les règles sont dans [`config.py`](config.py) :

| Sage | Pennylane |
|---|---|
| Compte client `41100000` + code client `0385` | `411038500` (`411` + code client + `00`) |
| Journal `VTE` / `VE` | `VT` |
| Journaux `BQ1`, `BQ3`…, `CAI`, `OD` | `SAGE` |
| Comptes `512…` | `582000000` |
| Compte `5311…` | `531000000` |
| Compte `44571120` | `445710000` |
| Autres comptes généraux (`70702000`) | complétés à 9 chiffres (`707020000`) |

- **Libellé de ligne** et **libellé de pièce** : nom du client concerné par la pièce
  (issu du fichier clients), sur toutes les lignes de la pièce.
- **Libellé de compte** : nom du client pour les comptes clients,
  libellé par défaut selon la racine du compte pour les autres.
- **Code pays** : laissé vide.
- **Taux de TVA** : calculé pour chaque pièce (TVA collectée / montant HT, arrondi au taux légal
  le plus proche) et indiqué sur les lignes de produits et de charges (classes 6 et 7) :
  `20 %`, `10 %`, `5,5 %`… ou `pas de TVA`. Un taux incohérent (pièce mêlant plusieurs taux) est signalé.
- **Numéro de pièce** : numéro de facture (`FA…` / `FR…`) quand il figure dans le libellé,
  sinon `JOURNAL-AAMM-nnn`. Les lignes d'une pièce sont regroupées jusqu'à équilibre débit = crédit.
- L'application signale les pièces déséquilibrées et les codes clients introuvables.

## Règles de conversion Septeo

Colonnes du fichier Septeo : A = journal, B = date, C = pièce, D = compte, E = libellé,
F = débit, G = crédit (une ligne d'en-tête éventuelle est ignorée).

| Septeo | Pennylane |
|---|---|
| Journal `VE` | `VT` |
| Journal `AC` | `HA` |
| Journal `ACH` (ventes) | `VT` |
| Journal `BQ` et autres | inchangés |
| Comptes commençant par `411` | inchangés (`4110004465`) |
| Autres comptes (`70601000`) | complétés à 10 caractères (`7060100000`) |

- **Libellé de compte** : libellé de l'écriture sans ses 7 premiers caractères quand ils forment
  un code dossier (`220205 MARC JOEL` → `MARC JOEL`, `S150125 VILLE DE PLERIN` → `VILLE DE PLERIN`) ;
  libellé complet sinon (`DROIT DE PLAIDOIRIE - CNBF`).
- **Libellé de ligne** et **libellé de pièce** : libellé de l'écriture.
- **Pièces** : lignes de même journal, n° de pièce (colonne C) et date. Sans n° de pièce (journal AC),
  lignes consécutives regroupées jusqu'à équilibre, avec un numéro généré `HA-AAMM-nnn`.
- **Taux de TVA** : TVA (`4456` / `4457`) ÷ base HT (comptes 6, 7 et débours soumis à TVA `46711…`),
  indiqué sur les lignes de la base HT.

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests : `pip install pytest && pytest`

## Déploiement sur Streamlit Community Cloud

1. Se connecter sur <https://share.streamlit.io> avec le compte GitHub.
2. **Create app** → choisir ce dépôt, la branche, et `app.py` comme fichier principal.
3. Cliquer sur **Deploy** : l'URL obtenue peut être partagée.

> Les exports Sage contiennent des données clients : ne pas les déposer dans le dépôt
> (les extensions `.pnm` / `.pnc` sont ignorées par git).
