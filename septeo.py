"""Conversion d'un export d'écritures Septeo au format d'import Pennylane."""

from __future__ import annotations

import io
import re
from datetime import date
from pathlib import Path

import pandas as pd

import config
from converter import COLONNES_PENNYLANE, Resultat, _par_prefixe, taux_tva


def _texte(valeur) -> str:
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return ""
    texte = str(valeur).strip()
    # un compte lu comme nombre par Excel : "707000.0" -> "707000"
    return texte[:-2] if texte.endswith(".0") and texte[:-2].isdigit() else texte


def _montant(valeur) -> float:
    if isinstance(valeur, (int, float)):
        return 0.0 if pd.isna(valeur) else round(float(valeur), 2)
    texte = _texte(valeur).replace(" ", "").replace(" ", "").replace(",", ".")
    return round(float(texte), 2) if texte else 0.0


def _date(valeur) -> date | None:
    if isinstance(valeur, (pd.Timestamp, date)):
        return pd.Timestamp(valeur).date()
    texte = _texte(valeur)
    if texte.isdigit() and len(texte) in (6, 8):  # JJMMAA / JJMMAAAA
        return pd.to_datetime(texte, format="%d%m%y" if len(texte) == 6 else "%d%m%Y").date()
    date_lue = pd.to_datetime(texte, dayfirst=True, errors="coerce")
    return None if pd.isna(date_lue) else date_lue.date()


def lire_fichier(contenu: bytes, nom: str) -> pd.DataFrame:
    """Lit un export Septeo (Excel ou CSV/texte) sans en-tête imposé : colonnes A à G."""
    if Path(nom).suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        df = pd.read_excel(io.BytesIO(contenu), header=None, dtype=object)
    else:
        for encodage in ("utf-8-sig", "cp1252"):
            try:
                texte = contenu.decode(encodage)
                break
            except UnicodeDecodeError:
                continue
        premiere_ligne = texte.splitlines()[0] if texte else ""
        separateur = next((sep for sep in (";", "\t", ",") if sep in premiere_ligne), ";")
        df = pd.read_csv(io.StringIO(texte), header=None, dtype=str, sep=separateur)
    df = df.iloc[:, : len(config.SEPTEO_COLONNES)]
    df.columns = config.SEPTEO_COLONNES[: df.shape[1]]
    return df


def libelle_compte(libelle: str) -> str:
    """Libellé sans le code dossier en tête (7 caractères) ; inchangé s'il n'y en a pas."""
    if re.match(config.SEPTEO_CODE_DOSSIER, libelle):
        return libelle[config.SEPTEO_CARACTERES_A_RETIRER:].strip()
    return libelle


def _regrouper(ecritures: list[dict]) -> list[list[dict]]:
    """Pièces : même journal + n° de pièce + date ; sans n° de pièce, lignes consécutives
    du même journal jusqu'à équilibre débit = crédit."""
    pieces: dict[tuple, list[dict]] = {}
    courante, solde = None, 0.0
    for i, e in enumerate(ecritures):
        if e["piece"]:
            pieces.setdefault((e["journal"], e["piece"], e["date"]), []).append(e)
            continue
        if courante is None or courante[0] != e["journal"]:
            courante, solde = (e["journal"], "", i), 0.0
        pieces.setdefault(courante, []).append(e)
        solde += e["debit"] - e["credit"]
        if abs(solde) < 0.005:
            courante = None
    return list(pieces.values())


def convertir_compte(compte: str) -> str:
    if compte.startswith(config.SEPTEO_COMPTES_INCHANGES):
        return compte
    return compte.ljust(config.LONGUEUR_COMPTE or 0, "0")


def convertir(contenu: bytes, nom: str) -> Resultat:
    brut = lire_fichier(contenu, nom)
    alertes: list[str] = []
    ecritures = []
    for i, ligne in brut.iterrows():
        date_ecriture = _date(ligne["date"])
        compte = _texte(ligne["compte"])
        if date_ecriture is None or not compte:
            # ligne d'en-tête, de total ou vide
            if any(_texte(v) for v in ligne) and i > 0:
                alertes.append(f"Ligne {i + 1} ignorée (date ou compte illisible) : {' | '.join(_texte(v) for v in ligne)}")
            continue
        debit, credit = _montant(ligne["debit"]), _montant(ligne["credit"])
        ecritures.append({
            "journal": _texte(ligne["journal"]),
            "date": date_ecriture,
            "piece": _texte(ligne["piece"]),
            "compte": compte,
            "libelle": _texte(ligne["libelle"]),
            # format attendu par taux_tva : montant positif + sens
            "sens": "D" if debit - credit >= 0 else "C",
            "montant": f"{abs(debit - credit):.2f}",
            "debit": debit,
            "credit": credit,
        })

    pieces = _regrouper(ecritures)
    compteurs: dict[str, int] = {}
    lignes = []
    for piece in pieces:
        journal_septeo = piece[0]["journal"]
        journal = config.SEPTEO_JOURNAUX.get(journal_septeo, journal_septeo)
        numero = piece[0]["piece"]
        if not numero:
            cle = f"{journal}-{piece[0]['date']:%y%m}"
            compteurs[cle] = compteurs.get(cle, 0) + 1
            numero = f"{cle}-{compteurs[cle]:03d}"
        debit = sum(e["debit"] for e in piece)
        credit = sum(e["credit"] for e in piece)
        if abs(debit - credit) >= 0.005:
            alertes.append(
                f"Pièce {numero} (journal {journal_septeo} du {piece[0]['date']:%d/%m/%Y}) déséquilibrée : "
                f"débit {debit:.2f} / crédit {credit:.2f}"
            )
        taux, taux_incoherent = taux_tva(piece, config.SEPTEO_COMPTES_TVA, config.SEPTEO_COMPTES_SOUMIS_TVA)
        if taux_incoherent:
            alertes.append(f"Pièce {numero} : taux de TVA incohérent ({taux or 'HT nul'}), à vérifier")

        for e in piece:
            compte = convertir_compte(e["compte"])
            if len(compte) > (config.LONGUEUR_COMPTE or len(compte)) and not compte.startswith(config.SEPTEO_COMPTES_INCHANGES):
                alertes.append(f"Compte {compte} (pièce {numero}) : plus de {config.LONGUEUR_COMPTE} caractères")
            lignes.append({
                "Date": e["date"],
                "Code Journal": journal,
                "Numéro de compte": compte,
                "Libellé de compte": libelle_compte(e["libelle"]),
                "Libellé de ligne": e["libelle"],
                "Taux de TVA du compte": taux if e["compte"].startswith(config.SEPTEO_COMPTES_SOUMIS_TVA) else "",
                "Code pays du compte": "",
                "Libellé de pièce": e["libelle"],
                "Numéro de pièce": numero,
                "Débit et/ou Crédit": e["debit"],
                "Crédit": e["credit"],
                "Famille de catégories": "",
                "Catégorie": "",
                "Identifiant de ligne": "",
                "Identifiant de lettrage": "",
            })

    df = pd.DataFrame(lignes, columns=COLONNES_PENNYLANE)
    return Resultat(ecritures=df, alertes=alertes, nb_pieces=len(pieces))
