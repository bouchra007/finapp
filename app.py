from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fin'App",
    page_icon="📊",
    layout="centered"
)

# Forcer le mode clair et ajouter des bordures nettes autour des cases
st.markdown("""
    <style>
    /* Fond principal blanc et texte noir */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #000000 !important;
    }
    /* Garde le fond blanc et AJOUTE une bordure bien visible autour des cases */
    input, select, textarea, div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 2px solid #555555 !important;
        border-radius: 6px !important;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- TITRE DANS LA BARRE DE GAUCHE ---
st.sidebar.title("Mon Application Financière")
st.sidebar.caption("Plateforme de gestion financière")
st.sidebar.divider()

def init_db():
    conn = sqlite3.connect("finapp.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            profil TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            libelle TEXT,
            type TEXT,
            montant REAL,
            date TEXT,
            echeance TEXT,
            statut TEXT,
            compte TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            num_devis TEXT,
            client TEXT,
            montant REAL,
            date TEXT,
            statut TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            nom TEXT,
            role TEXT,
            email_tiers TEXT,
            ville TEXT,
            compte_auxiliaire TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            reference TEXT,
            categorie TEXT,
            quantite INTEGER,
            prix_ht REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emprunts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            libelle TEXT,
            banque TEXT,
            montant_total REAL,
            taux REAL,
            duree_mois INTEGER,
            mensualite REAL,
            date_debut TEXT
        )
    """)
    
    # Migrations automatiques pour éviter les erreurs si la base existait déjà
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN compte TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE tiers ADD COLUMN compte_auxiliaire TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN montant REAL")
        cursor.execute("UPDATE transactions SET montant = montant_ttc WHERE montant IS NULL AND montant_ttc IS NOT NULL")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE devis ADD COLUMN montant REAL")
        cursor.execute("UPDATE devis SET montant = montant_ttc WHERE montant IS NULL AND montant_ttc IS NOT NULL")
    except:
        pass

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
    st.markdown("""
        <div class="welcome-banner">
            <h1 style="margin-top: 0; color: #60A5FA;">Bienvenue sur Fin'App</h1>
            <p style="font-size: 1.1rem; line-height: 1.6; color: #E2E8F0;">
                Votre solution de gestion financière, inspirée des meilleurs outils du marché. 
                Connectez-vous ou créez un compte pour retrouver votre espace personnel.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    auth_mode = st.radio("Choisissez une option :", ["Connexion", "Inscription"])
    
    if auth_mode == "Connexion":
        with st.form("form_login"):
            identifiant_login = st.text_input("Adresse e-mail ou identifiant")
            password_login = st.text_input("Mot de passe", type="password")
            btn_login = st.form_submit_button("Se connecter")
            
            if btn_login:
                conn = sqlite3.connect("finapp.db")
                cursor = conn.cursor()
                cursor.execute("SELECT profil FROM users WHERE email = ? AND password = ?", (identifiant_login, password_login))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state.user_email = identifiant_login
                    st.session_state.profil = user[0]
                    st.session_state.logged_in = True
                    st.success("Connexion réussie ! Redirection en cours...")
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect. Veuillez vérifier vos informations.")
    else:
        st.markdown("### Choix de la catégorie socio-professionnelle")
        categorie_choisie = st.selectbox("Sélectionnez votre profil :", ["Étudiant", "Salarié", "Auto-entrepreneur", "Société", "Autre"])
        
        sous_cat = ""
        if categorie_choisie == "Étudiant":
            sous_cat = st.selectbox("Précisez votre statut :", ["Boursier", "Alternant", "Classique"])
            profil_final = f"Étudiant ({sous_cat})"
        elif categorie_choisie == "Société":
            sous_cat = st.selectbox("Sélectionnez votre forme sociale :", ["SAS", "SARL", "EURL", "Autre"])
            profil_final = f"Société ({sous_cat})"
        else:
            profil_final = categorie_choisie

        with st.form("form_signup"):
            email_signup = st.text_input("Adresse e-mail (identifiant)")
            password_signup = st.text_input("Créer un mot de passe", type="password")
            
            btn_signup = st.form_submit_button("S'inscrire et créer le compte")
            
            if btn_signup:
                if email_signup.strip() == "":
                    st.warning("Veuillez renseigner une adresse e-mail valide.")
                else:
                    conn = sqlite3.connect("finapp.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT email FROM users WHERE email = ?", (email_signup,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        st.warning("Cet e-mail est déjà associé à un compte existant.")
                        conn.close()
                    else:
                        cursor.execute("INSERT INTO users (email, password, profil) VALUES (?, ?, ?)", (email_signup, password_signup, profil_final))
                        conn.commit()
                        conn.close()
                        
                        st.session_state.user_email = email_signup
                        st.session_state.profil = profil_final
                        st.session_state.logged_in = True
                        st.success("Compte créé avec succès ! Bienvenue sur Fin'App.")
                        st.rerun()
else:
    st.sidebar.header("Mon Compte")
    st.sidebar.info(f"Utilisateur : {st.session_state.user_email}\n\nProfil : {st.session_state.profil}")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()
    st.sidebar.markdown("---")

    st.title("Fin'App")

    is_pro = not ("Étudiant" in st.session_state.profil or "Salarié" in st.session_state.profil or "Autre" in st.session_state.profil)
    is_auto_entrepreneur = "Auto-entrepreneur" == st.session_state.profil

    if is_pro:
        if is_auto_entrepreneur:
            st.markdown("Plateforme Auto-entrepreneur : Trésorerie, Factures & Devis, Tiers, Stocks, TVA & Emprunts.")
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Trésorerie", "Saisie des Flux", "Devis & Facturation", "Échéances & Gestion", "Annuaire Tiers", "Stocks & Articles", "TVA", "Emprunts"])
        else:
            st.markdown("Plateforme ERP Pro : Trésorerie, Facturation, Annuaire Tiers, Stocks, TVA & Emprunts.")
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Trésorerie", "Saisie des Flux", "Échéances & Gestion", "Annuaire Tiers", "Stocks & Articles", "TVA", "Emprunts"])
    else:
        st.markdown("Suivi du budget personnel.")
        tab1, tab2, tab3 = st.tabs(["Trésorerie & Budget", "Saisie des Flux", "Échéances & Gestion"])

    conn = sqlite3.connect("finapp.db")
    raw_df = pd.read_sql_query("SELECT id, libelle, type, montant, date, echeance, statut, compte FROM transactions WHERE email = ?", conn, params=(st.session_state.user_email,))
    
    if not raw_df.empty:
        raw_df["date_obj"] = pd.to_datetime(raw_df["date"], errors="coerce")
        raw_df["echeance_obj"] = pd.to_datetime(raw_df["echeance"], errors="coerce")
        raw_df = raw_df.sort_values(by="date_obj", ascending=True)
        
        raw_df["Date"] = raw_df["date_obj"].dt.strftime("%d/%m/%Y")
        raw_df["Échéance"] = raw_df["echeance_obj"].dt.strftime("%d/%m/%Y")
        
        if is_pro:
            df_factures = raw_df[["id", "libelle", "type", "montant", "Date", "Échéance", "statut", "compte"]].rename(columns={
                "libelle": "Libellé / Tiers",
                "type": "Type",
                "montant": "Montant (€)",
                "statut": "Statut",
                "compte": "N° Compte"
            })
        else:
            df_factures = raw_df[["id", "libelle", "type", "montant", "Date", "Échéance", "statut"]].rename(columns={
                "libelle": "Libellé / Tiers",
                "type": "Type",
                "montant": "Montant (€)",
                "statut": "Statut"
            })
        df_factures = df_factures.dropna(subset=["Libellé / Tiers"])
        df_factures = df_factures[df_factures["Libellé / Tiers"].astype(str).str.strip() != ""]
        df_factures = df_factures.reset_index(drop=True)
        df_factures.index = range(1, len(df_factures) + 1)
    else:
        if is_pro:
            df_factures = pd.DataFrame(columns=["id", "Libellé / Tiers", "Type", "Montant (€)", "Date", "Échéance", "Statut", "N° Compte"])
        else:
            df_factures = pd.DataFrame(columns=["id", "Libellé / Tiers", "Type", "Montant (€)", "Date", "Échéance", "Statut"])

    df_devis = pd.read_sql_query("SELECT id, num_devis as 'Numéro Devis', client as 'Client', montant as 'Montant (€)', date as 'Date', statut as 'Statut' FROM devis WHERE email = ? ORDER BY date", conn, params=(st.session_state.user_email,))
    if not df_devis.empty:
        df_devis = df_devis.reset_index(drop=True)
        df_devis.index = range(1, len(df_devis) + 1)

    df_tiers = pd.read_sql_query("SELECT id, nom as 'Nom', role as 'Rôle', email_tiers as 'Email / Numéro', ville as 'Ville', compte_auxiliaire as 'N° Compte' FROM tiers WHERE email = ? ORDER BY role, nom", conn, params=(st.session_state.user_email,))
    if not df_tiers.empty:
        df_tiers = df_tiers.reset_index(drop=True)
        df_tiers.index = range(1, len(df_tiers) + 1)

    df_stocks = pd.read_sql_query("SELECT id, reference as 'Article / Référence', categorie as 'Catégorie', quantite as 'Quantité', prix_ht as 'Prix unitaire (€)' FROM stocks WHERE email = ? ORDER BY reference", conn, params=(st.session_state.user_email,))
    if not df_stocks.empty:
        df_stocks = df_stocks.reset_index(drop=True)
        df_stocks.index = range(1, len(df_stocks) + 1)
    else:
        df_stocks = pd.DataFrame(columns=["id", "Article / Référence", "Catégorie", "Quantité", "Prix unitaire (€)"])

    conn.close()

    with tab1:
        st.subheader(f"Indicateurs Clés - {st.session_state.profil}")
        total_revenus = df_factures[df_factures["Type"].isin(["Revenu", "Vente de Produits", "Prestation de Services", "Loyers perçus (SCI)"])]["Montant (€)"].sum() if not df_factures.empty else 0
        total_charges = df_factures[df_factures["Type"] == "Charge / Dépense"]["Montant (€)"].sum() if not df_factures.empty else 0
        solde_net = total_revenus - total_charges

        if solde_net > 50:
            color_solde = "#22C55E"
        elif solde_net >= -50:
            color_solde = "#F59E0B"
        else:
            color_solde = "#EF4444"

        col1, col2, col3 = st.columns(3)
        if is_pro:
            col1.metric("Total des entrées", f"{total_revenus:,.2f} €")
            col2.metric("Total des charges", f"{total_charges:,.2f} €")
            col3.markdown(f"""
                <div style="background-color: #1E293B; padding: 20px; border-radius: 10px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);">
                    <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 5px;">Solde</p>
                    <p style="color: {color_solde}; font-size: 1.8rem; font-weight: bold; margin: 0;">{solde_net:,.2f} €</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            col1.metric("Revenus", f"{total_revenus:,.2f} €")
            col2.metric("Achats", f"{total_charges:,.2f} €")
            col3.markdown(f"""
                <div style="background-color: #1E293B; padding: 20px; border-radius: 10px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);">
                    <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 5px;">Solde restant</p>
                    <p style="color: {color_solde}; font-size: 1.8rem; font-weight: bold; margin: 0;">{solde_net:,.2f} €</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        if is_pro:
            st.subheader("Historique global des transactions & Comptes comptables (Compte unique 512)")
            if not raw_df.empty:
                df_del_trans = raw_df.copy()
                df_del_trans.insert(0, "Supprimer", False)
                df_del_trans["Date"] = pd.to_datetime(df_del_trans["date"]).dt.strftime("%d/%m/%Y")
                df_del_trans["Échéance"] = pd.to_datetime(df_del_trans["echeance"]).dt.strftime("%d/%m/%Y")
                
                if is_pro:
                    df_del_trans = df_del_trans[["Supprimer", "libelle", "type", "montant", "Date", "Échéance", "statut", "compte", "id"]].rename(columns={
                        "libelle": "Libellé / Tiers", "type": "Type", "montant": "Montant (€)", "statut": "Statut", "compte": "N° Compte"
                    })
                else:
                    df_del_trans = df_del_trans[["Supprimer", "libelle", "type", "montant", "Date", "Échéance", "statut", "id"]].rename(columns={
                        "libelle": "Libellé / Tiers", "type": "Type", "montant": "Montant (€)", "statut": "Statut"
                    })
                
                df_del_trans = df_del_trans.reset_index(drop=True)
                df_del_trans.index = range(1, len(df_del_trans) + 1)
                
                edited_trans_table = st.data_editor(df_del_trans, use_container_width=True, hide_index=True)
                if st.button("Supprimer les transactions cochées"):
                    ids_to_del = edited_trans_table[edited_trans_table["Supprimer"] == True]["id"].tolist()
                    if ids_to_del:
                        conn = sqlite3.connect("finapp.db")
                        cursor = conn.cursor()
                        cursor.executemany("DELETE FROM transactions WHERE id = ?", [(i,) for i in ids_to_del])
                        conn.commit()
                        conn.close()
                        st.success("Transactions sélectionnées supprimées !")
                        st.rerun()
                    else:
                        st.warning("Aucune transaction cochée.")
            else:
                st.info("Aucune transaction enregistrée pour le moment.")
        else:
            st.subheader("Analyse & Synthèse financière")
            if not df_factures.empty:
                st.markdown(f"""
                <div style="background-color: #1E293B; padding: 25px; border-radius: 10px; border: 1px solid #334155; line-height: 2;">
                    <p style="font-size: 1.14rem; color: #E2E8F0; margin-bottom: 12px;">
                        Sur cette période :
                    </p>
                    <p style="font-size: 1.14rem; color: #E2E8F0; margin-bottom: 12px;">
                        Vos revenus s'élèvent à <span style="color: #22C55E; font-weight: bold;">{total_revenus:,.2f} €</span>.
                    </p>
                    <p style="font-size: 1.14rem; color: #E2E8F0; margin-bottom: 12px;">
                        Tandis que vos achats et dépenses atteignent <span style="color: #EF4444; font-weight: bold;">{total_charges:,.2f} €</span>.
                    </p>
                    <p style="font-size: 1.14rem; color: #E2E8F0; margin: 0;">
                        Votre solde restant s'est établi ainsi à <span style="color: {color_solde}; font-weight: bold;">{solde_net:,.2f} €</span>.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Aucune transaction enregistrée pour le moment.")

    with tab2:
        st.subheader("Saisir une nouvelle Facture ou Transaction")
        if is_pro:
            if "SCI" in st.session_state.profil:
                options_flux = ["Charge / Dépense", "Loyers perçus (SCI)"]
            else:
                options_flux = ["Charge / Dépense", "Vente de Produits", "Prestation de Services"]
        else:
            options_flux = ["Charge / Dépense", "Revenu"]

        statut_pait = st.selectbox("Statut du paiement", ["Payé", "Reçu", "À recevoir", "À payer"], key="statut_select_flux")
        
        client_fournisseur_choisi = ""
        compte_lie_tiers = ""
        if is_pro:
            tiers_df = df_tiers[df_tiers["Rôle"].isin(["Client", "Fournisseur"])] if not df_tiers.empty else pd.DataFrame()
            tiers_list = tiers_df["Nom"].tolist() if not tiers_df.empty else []
            if tiers_list:
                client_fournisseur_choisi = st.selectbox("Client / Fournisseur (depuis l'annuaire tiers) :", tiers_list)
                match_row = tiers_df[tiers_df["Nom"] == client_fournisseur_choisi]
                if not match_row.empty:
                    compte_lie_tiers = match_row["N° Compte"].values[0]

        compte_auto = "512" if is_pro else ""
        if is_pro and compte_lie_tiers:
            compte_auto = f"{compte_lie_tiers} / 512"
        st.info(f"Règle comptable associée : Compte **{compte_auto}**")

        with st.form(f"form_facture_{st.session_state.form_key}"):
            col_a, col_b = st.columns(2)
            with col_a:
                libelle_defaut = client_fournisseur_choisi if is_pro else ""
                libelle = st.text_input("Libellé / Nom de la facture ou transaction", value=libelle_defaut)
                type_flux = st.selectbox("Type de flux", options_flux)
                montant_saisi = st.number_input("Montant (€)", min_value=0.0, step=10.0, format="%.2f")
            with col_b:
                date_facture = st.date_input("Date de la transaction", date.today())
                echeance_facture = st.date_input("Date d'échéance", date.today())
            
            submitted = st.form_submit_button("Enregistrer la transaction")

            if submitted:
                if libelle.strip() == "":
                    st.warning("Veuillez renseigner le libellé.")
                else:
                    montant_final = montant_saisi
                    conn = sqlite3.connect("finapp.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO transactions (email, libelle, type, montant, date, echeance, statut, compte)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (st.session_state.user_email, libelle, type_flux, montant_final, str(date_facture), str(echeance_facture), statut_pait, compte_
                          
