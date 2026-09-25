"""Application Streamlit : conversion d'exports comptables au format d'import Pennylane."""

from pathlib import Path

import streamlit as st

import config
import septeo
from converter import Resultat, convertir, vers_excel

st.set_page_config(page_title="Import Pennylane", page_icon="📒", layout="wide")

IMPORT_SAGE = "Import fichier Sage"
IMPORT_SEPTEO = "Import fichier Septeo"


def afficher_resultat(resultat: Resultat, nom_source: str) -> None:
    df = resultat.ecritures
    total_debit = df["Débit et/ou Crédit"].sum()
    total_credit = df["Crédit"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Lignes", len(df))
    m2.metric("Pièces", resultat.nb_pieces)
    m3.metric("Total débit", f"{total_debit:,.2f} €".replace(",", " "))
    m4.metric("Total crédit", f"{total_credit:,.2f} €".replace(",", " "))

    if resultat.alertes:
        with st.expander(f"⚠️ {len(resultat.alertes)} point(s) à vérifier", expanded=True):
            for alerte in resultat.alertes:
                st.warning(alerte)
    else:
        st.success("Aucune anomalie détectée : toutes les pièces sont équilibrées.")

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Télécharger le fichier Pennylane",
        data=vers_excel(df),
        file_name=f"pennylane_{Path(nom_source).stem}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def page_sage() -> None:
    st.write(
        "Déposez l'export des **écritures** et l'export des **clients** issus de Sage. "
        "L'application génère le fichier d'import des écritures au format Pennylane."
    )

    with st.sidebar:
        st.header("Règles appliquées")
        st.markdown(
            f"- Compte client : `{config.PREFIXE_COMPTE_CLIENT}` + code client + `00`\n"
            + "".join(f"- Journal `{k}…` → `{v}`\n" for k, v in config.JOURNAUX.items())
            + "".join(f"- Comptes `{k}…` → `{v}`\n" for k, v in config.COMPTES_REMPLACES.items())
            + (f"- Comptes généraux complétés à {config.LONGUEUR_COMPTE} chiffres\n" if config.LONGUEUR_COMPTE else "")
        )
        st.caption("Ces règles se modifient dans le fichier `config.py`.")

    col1, col2 = st.columns(2)
    # Aucun filtre d'extension : les exports Sage sont en .pnm, .pnc, .txt...
    fichier_ecritures = col1.file_uploader("Fichier des écritures (.pnm / .txt)")
    fichier_clients = col2.file_uploader("Fichier des clients (.pnc / .txt)")

    if not (fichier_ecritures and fichier_clients):
        st.info("En attente des deux fichiers.")
        return
    try:
        resultat = convertir(fichier_ecritures.getvalue(), fichier_clients.getvalue())
    except Exception as erreur:  # fichier inattendu : message lisible plutôt qu'une trace
        st.error(f"Impossible de lire les fichiers : {erreur}. Vérifiez que les fichiers ne sont pas inversés.")
        return
    afficher_resultat(resultat, fichier_ecritures.name)


def page_septeo() -> None:
    st.write(
        "Déposez l'export des écritures Septeo (Excel ou CSV) : colonnes A à G = journal, date, "
        "pièce, compte, libellé, débit, crédit. L'application génère le fichier d'import Pennylane."
    )

    with st.sidebar:
        st.header("Règles appliquées")
        st.markdown(
            "".join(f"- Journal `{k}…` → `{v}`\n" for k, v in config.SEPTEO_JOURNAUX.items())
            + "- Autres journaux inchangés\n"
            + f"- Comptes complétés à {config.LONGUEUR_COMPTE} caractères, "
            + "sauf " + ", ".join(f"`{p}…`" for p in config.SEPTEO_COMPTES_INCHANGES) + " (inchangés)\n"
            + f"- Libellé de compte = libellé sans les {config.SEPTEO_CARACTERES_A_RETIRER} premiers caractères\n"
        )
        st.caption("Ces règles se modifient dans le fichier `config.py`.")

    fichier = st.file_uploader("Fichier des écritures Septeo (.xlsx / .csv / .txt)")
    if not fichier:
        st.info("En attente du fichier.")
        return
    try:
        resultat = septeo.convertir(fichier.getvalue(), fichier.name)
    except Exception as erreur:  # fichier inattendu : message lisible plutôt qu'une trace
        st.error(f"Impossible de lire le fichier : {erreur}.")
        return
    afficher_resultat(resultat, fichier.name)


st.title("Conversion des écritures → Pennylane")
choix = st.radio("Type d'import", [IMPORT_SAGE, IMPORT_SEPTEO], horizontal=True)
st.divider()

if choix == IMPORT_SAGE:
    page_sage()
else:
    page_septeo()
