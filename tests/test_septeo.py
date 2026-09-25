import io
from datetime import datetime

from openpyxl import Workbook

import septeo

LIGNES = [
    ["Journal", "Date", "Pièce", "Compte", "Libellé", "Débit", "Crédit"],
    ["VE", datetime(2026, 7, 2), "F001", "411DUPONT", "F001 - Dupont SARL", 120, None],
    ["VE", datetime(2026, 7, 2), "F001", "44571", "F001 - Dupont SARL", None, 20],
    ["VE", datetime(2026, 7, 2), "F001", 706, "F001 - Dupont SARL", None, 100],
    ["AC", datetime(2026, 7, 3), "A12", "401FOUR", "A12    Fournisseur X", None, 60],
    ["AC", datetime(2026, 7, 3), "A12", "44566", "A12    Fournisseur X", 10, None],
    ["AC", datetime(2026, 7, 3), "A12", "6064", "A12    Fournisseur X", 50, None],
    ["BQ", datetime(2026, 7, 4), "B1", "512", "B1     Virement", 120, None],
    ["BQ", datetime(2026, 7, 4), "B1", "411DUPONT", "B1     Virement", None, 120],
]


def excel(lignes):
    wb = Workbook()
    for ligne in lignes:
        wb.active.append(ligne)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_conversion_excel():
    r = septeo.convertir(excel(LIGNES), "export.xlsx")
    df = r.ecritures
    assert r.alertes == []
    assert len(df) == 8 and r.nb_pieces == 3
    assert list(df["Code Journal"].unique()) == ["VT", "HA", "BQ"]
    assert list(df["Numéro de compte"]) == [
        "411DUPONT", "445710000", "706000000", "401FOUR00", "445660000", "606400000", "512000000", "411DUPONT",
    ]
    assert df.iloc[0]["Libellé de compte"] == "Dupont SARL"
    assert df.iloc[0]["Libellé de ligne"] == df.iloc[0]["Libellé de pièce"] == "F001 - Dupont SARL"
    assert df.iloc[0]["Numéro de pièce"] == "F001"
    assert str(df.iloc[0]["Date"]) == "2026-07-02"
    assert (df.iloc[0]["Débit et/ou Crédit"], df.iloc[0]["Crédit"]) == (120, 0)
    # TVA : ventes (collectée) et achats (déductible)
    assert df.iloc[2]["Taux de TVA du compte"] == "20 %"
    assert df.iloc[5]["Taux de TVA du compte"] == "20 %"
    assert df.iloc[0]["Taux de TVA du compte"] == ""


def test_conversion_csv_et_alertes():
    csv = (
        "VE;02/07/2026;F002;411X;F002 - Client;100,50;\n"
        "VE;02/07/2026;F002;706;F002 - Client;;90\n"
        "Total;;;;;;\n"
    ).encode("cp1252")
    r = septeo.convertir(csv, "export.csv")
    assert len(r.ecritures) == 2
    assert r.ecritures.iloc[0]["Débit et/ou Crédit"] == 100.5
    assert any("déséquilibrée" in a for a in r.alertes)
    assert any("Ligne 3 ignorée" in a for a in r.alertes)
