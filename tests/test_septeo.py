import io
from datetime import datetime

from openpyxl import Workbook

import septeo

LIGNES = [
    ["Journal", "Date", "Pièce", "Compte", "Libellé", "Débit", "Crédit"],
    ["VE", datetime(2026, 7, 2), "F001", "411DUPONT", "220205 DUPONT SARL", 120, None],
    ["VE", datetime(2026, 7, 2), "F001", "44571", "220205 DUPONT SARL", None, 20],
    ["VE", datetime(2026, 7, 2), "F001", 706, "220205 DUPONT SARL", None, 100],
    ["AC", datetime(2026, 7, 3), "A12", "401FOUR", "S150125 FOURNISSEUR X", None, 60],
    ["AC", datetime(2026, 7, 3), "A12", "44566", "S150125 FOURNISSEUR X", 10, None],
    ["AC", datetime(2026, 7, 3), "A12", "6064", "S150125 FOURNISSEUR X", 50, None],
    ["BQ", datetime(2026, 7, 4), "B1", "512", "220205 DUPONT SARL", 120, None],
    ["BQ", datetime(2026, 7, 4), "B1", "411DUPONT", "220205 DUPONT SARL", None, 120],
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
    assert df.iloc[0]["Libellé de compte"] == "DUPONT SARL"
    assert df.iloc[0]["Libellé de ligne"] == df.iloc[0]["Libellé de pièce"] == "220205 DUPONT SARL"
    assert df.iloc[0]["Numéro de pièce"] == "F001"
    assert str(df.iloc[0]["Date"]) == "2026-07-02"
    assert (df.iloc[0]["Débit et/ou Crédit"], df.iloc[0]["Crédit"]) == (120, 0)
    # TVA : ventes (collectée) et achats (déductible)
    assert df.iloc[2]["Taux de TVA du compte"] == "20 %"
    assert df.iloc[5]["Taux de TVA du compte"] == "20 %"
    assert df.iloc[0]["Taux de TVA du compte"] == ""


def test_format_reel_csv():
    csv = (
        # facture : honoraires + débours soumis à TVA (46711) + débours non soumis (46701)
        "VE;20/07/2026;261587;70601000;260341 CARPE DIEM;0,00;180,00\n"
        "VE;20/07/2026;261587;46711006;260341 CARPE DIEM;0,00;70,49\n"
        "VE;20/07/2026;261587;46701000;260341 CARPE DIEM;0,00;5,90\n"
        "VE;20/07/2026;261587;44571000;260341 CARPE DIEM;0,00;50,10\n"
        "VE;20/07/2026;261587;4110007906;260341 CARPE DIEM;306,49;0,00\n"
        # même n° de pièce en banque, deux règlements à des dates différentes
        "BQ;24/07/2026;261587;58200000;260341 CARPE DIEM;100,00;0,00\n"
        "BQ;24/07/2026;261587;4110007906;260341 CARPE DIEM;0,00;100,00\n"
        "BQ;01/09/2026;261587;58200000;260341 CARPE DIEM;206,49;0,00\n"
        "BQ;01/09/2026;261587;4110007906;260341 CARPE DIEM;0,00;206,49\n"
        # achats sans n° de pièce
        "AC;20/07/2026;;46710004;DROIT DE PLAIDOIRIE - CNBF;13,00;0,00\n"
        "AC;20/07/2026;;40100000;DROIT DE PLAIDOIRIE - CNBF;0,00;13,00\n"
        "AC;20/07/2026;;46710004;DROIT DE PLAIDOIRIE - CNBF;13,00;0,00\n"
        "AC;20/07/2026;;40100000;DROIT DE PLAIDOIRIE - CNBF;0,00;13,00\n"
        "ACH;04/09/2026;000005;70601000;R180129 SCI ARNAUD;0,00;10,00\n"
        "ACH;04/09/2026;000005;4110004894;R180129 SCI ARNAUD;10,00;0,00\n"
    ).encode("utf-8")
    r = septeo.convertir(csv, "ExportEcrituresComptable.csv")
    df = r.ecritures
    assert r.alertes == []
    assert r.nb_pieces == 6
    assert list(df.iloc[0:4]["Taux de TVA du compte"]) == ["20\u00a0%", "20\u00a0%", "", ""]
    assert df.iloc[4]["Numéro de compte"] == "4110007906"
    assert list(df.iloc[9:13]["Numéro de pièce"]) == ["HA-2607-001"] * 2 + ["HA-2607-002"] * 2
    assert df.iloc[9]["Libellé de compte"] == "DROIT DE PLAIDOIRIE - CNBF"
    assert df.iloc[13]["Code Journal"] == "ACH"
    assert df.iloc[13]["Libellé de compte"] == "SCI ARNAUD"


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
