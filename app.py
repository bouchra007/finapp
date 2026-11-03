from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fin'App", page_icon="📊", layout="centered")

st.sidebar.title("Mon Application Financière")
st.sidebar.caption("Plateforme de gestion financière")
st.sidebar.divider()

def init_db():
    conn = sqlite3.connect("finapp.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, profil TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, libelle TEXT, type TEXT, montant REAL, date TEXT, echeance TEXT, statut TEXT, compte TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS devis (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, num_devis TEXT, client TEXT, montant REAL, date TEXT, statut TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tiers (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, nom TEXT, role TEXT, email_tiers TEXT, ville TEXT, compte_auxiliaire TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS stocks (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, reference TEXT, categorie TEXT, quantite INTEGER, prix_ht REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS emprunts (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, libelle TEXT, banque TEXT, montant_total REAL, taux REAL, duree_mois INTEGER, mensualite REAL, date_debut TEXT)")
    conn.commit()
    conn.close()

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "profil" not in st.session_state:
    st.session_state.profil = "Salarié"
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if not st.session_state.logged_in:
    st.title("Bienvenue sur Fin'App")
    auth_mode = st.radio("Choisissez une option :", ["Connexion", "Inscription"])
    
    if auth_mode == "Connexion":
        with st.form("form_login"):
            identifiant_login = st.text_input("Adresse e-mail ou identifiant")
            password_login = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                conn = sqlite3.connect("finapp.db")
                cursor = conn.cursor()
                cursor.execute("SELECT profil FROM users WHERE email = ? AND password = ?", (identifiant_login, password_login))
                user = cursor.fetchone()
                conn.close()
                if user:
                    st.session_state.user_email = identifiant_login
                    st.session_state.profil = user[0]
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
    else:
        profil_final = st.selectbox("Sélectionnez votre profil :", ["Étudiant", "Salarié", "Auto-entrepreneur", "Société"])
        with st.form("form_signup"):
            email_signup = st.text_input("Adresse e-mail")
            password_signup = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("S'inscrire"):
                if email_signup.strip():
                    conn = sqlite3.connect("finapp.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO users (email, password, profil) VALUES (?, ?, ?)", (email_signup, password_signup, profil_final))
                    conn.commit()
                    conn.close()
                    st.session_state.user_email = email_signup
                    st.session_state.profil = profil_final
                    st.session_state.logged_in = True
                    st.rerun()
else:
    if st.sidebar.button("Se déconnecter"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("Fin'App - Tableau de Bord")
    is_pro = "Auto-entrepreneur" in st.session_state.profil or "Société" in st.session_state.profil

    tab1, tab2, tab3 = st.tabs(["Trésorerie", "Saisie des Flux", "Échéances"])

    conn = sqlite3.connect("finapp.db")
    raw_df = pd.read_sql_query("SELECT id, libelle, type, montant, date, echeance, statut, compte FROM transactions WHERE email = ?", conn, params=(st.session_state.user_email,))
    conn.close()

    with tab1:
        st.subheader("Historique des transactions")
        if not raw_df.empty:
            st.dataframe(raw_df, use_container_width=True)
        else:
            st.info("Aucune transaction pour le moment.")

    with tab2:
        st.subheader("Saisir une Transaction")
        with st.form(f"form_facture_{st.session_state.form_key}"):
            libelle = st.text_input("Libellé")
            type_flux = st.selectbox("Type de flux", ["Revenu", "Charge / Dépense"])
            montant_saisi = st.number_input("Montant (€)", min_value=0.0, step=10.0)
            date_facture = st.date_input("Date", date.today())
            echeance_facture = st.date_input("Échéance", date.today())
            statut_pait = st.selectbox("Statut", ["Payé", "À payer"])
            
            if st.form_submit_button("Enregistrer"):
                if libelle.strip():
                    conn = sqlite3.connect("finapp.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO transactions (email, libelle, type, montant, date, echeance, statut, compte) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (st.session_state.user_email, libelle, type_flux, montant_saisi, str(date_facture), str(echeance_facture), statut_pait, "512")
                    )
                    conn.commit()
                    conn.close()
                    st.session_state.form_key += 1
                    st.success("Enregistré avec succès !")
                    st.rerun()

    with tab3:
        st.subheader("Échéances")
        if not raw_df.empty and "statut" in raw_df.columns:
            a_payer = raw_df[raw_df["statut"] == "À payer"]
            if not a_payer.empty:
                st.warning(f"Vous avez {len(a_payer)} élément(s) à payer.")
            else:
                st.success("Aucun élément à payer.")
        else:
            st.info("Aucune donnée.")
            
