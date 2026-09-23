# Conversion Sage → Pennylane

Application Streamlit qui transforme les exports Sage (écritures + clients) en fichier
d'import d'écritures au format Pennylane (`.xlsx`).

## Utilisation

1. Déposer l'export des **écritures** Sage (`.pnm`, `.txt`…).
2. Déposer l'export des **clients** Sage (`.pnc`, `.txt`…).
3. Vérifier les totaux et les éventuelles alertes, puis cliquer sur **Télécharger le fichier Pennylane**.

## Règles de conversion

Toutes les règles sont dans [`config.py`](config.py) :

| Sage | Pennylane |
|---|---|
| Compte client `41100000` + code client `3184` | `411003184` (`41100` + code client) |
| Journal `VTE` / `VE` | `VT` |
| Journaux `BQ1`, `BQ3`…, `CAI`, `OD` | `SAGE` |
| Comptes `512…` | `582000000` |
| Compte `5311…` | `531` |
| Autres comptes généraux (`44571120`) | complétés à 9 chiffres (`445711200`) |

- **Libellé de ligne** et **libellé de pièce** : nom du client concerné par la pièce
  (issu du fichier clients), sur toutes les lignes de la pièce.
- **Libellé de compte** : nom du client pour les comptes clients,
  libellé par défaut selon la racine du compte pour les autres.
- **Code pays** : laissé vide.
- **Numéro de pièce** : numéro de facture (`FA…` / `FR…`) quand il figure dans le libellé,
  sinon `JOURNAL-AAMM-nnn`. Les lignes d'une pièce sont regroupées jusqu'à équilibre débit = crédit.
- L'application signale les pièces déséquilibrées et les codes clients introuvables.

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
