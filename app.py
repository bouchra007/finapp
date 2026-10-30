from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fin'App - ERP Gestion & Facturation", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p {
        color: #F8FAFC !important;
    }
    div.stMetric, div[data-testid="stForm"] {
        background-color: #1E293B;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        border: 1px solid #334155;
    }
    h1, h2, h3 {
        color: #F8FAFC !important;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        color: white;
    }
    .welcome-banner {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #475569;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

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
            montant_ht REAL,
            montant_ttc REAL,
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
            montant_ht REAL,
            montant_ttc REAL,
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
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN compte TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE tiers ADD COLUMN compte_auxiliaire TEXT")
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
            st.markdown("Plateforme Auto-entrepreneur : Trésorerie, Factures & Devis, Tiers et Stocks.")
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Trésorerie", "Saisie des Flux", "Devis & Facturation", "Échéances & Gestion", "Annuaire Tiers", "Stocks & Articles"])
        else:
            st.markdown("Plateforme ERP Pro : Trésorerie, Facturation, Annuaire Tiers et Stocks.")
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Trésorerie", "Saisie des Flux", "Échéances & Gestion", "Annuaire Tiers", "Stocks & Articles"])
    else:
        st.markdown("Suivi du budget personnel.")
        tab1, tab2, tab3 = st.tabs(["Trésorerie & Budget", "Saisie des Flux", "Échéances & Gestion"])

    conn = sqlite3.connect("finapp.db")
    raw_df = pd.read_sql_query("SELECT id, libelle, type, montant_ht, montant_ttc, date, echeance, statut, compte FROM transactions WHERE email = ?", conn, params=(st.session_state.user_email,))
    
    if not raw_df.empty:
        raw_df["date_obj"] = pd.to_datetime(raw_df["date"], errors="coerce")
        raw_df["echeance_obj"] = pd.to_datetime(raw_df["echeance"], errors="coerce")
        raw_df = raw_df.sort_values(by="date_obj", ascending=True)
        
        raw_df["Date"] = raw_df["date_obj"].dt.strftime("%d/%m/%Y")
        raw_df["Échéance"] = raw_df["echeance_obj"].dt.strftime("%d/%m/%Y")
        
        if is_pro:
            df_factures = raw_df[["id", "libelle", "type", "montant_ht", "montant_ttc", "Date", "Échéance", "statut", "compte"]].rename(columns={
                "libelle": "Libellé / Tiers",
                "type": "Type",
                "montant_ht": "Montant HT",
                "montant_ttc": "Montant TTC",
                "statut": "Statut",
                "compte": "N° Compte"
            })
        else:
            df_factures = raw_df[["id", "libelle", "type", "montant_ttc", "Date", "Échéance", "statut"]].rename(columns={
                "libelle": "Libellé / Tiers",
                "type": "Type",
                "montant_ttc": "Montant",
                "statut": "Statut"
            })
        df_factures = df_factures.dropna(subset=["Libellé / Tiers"])
        df_factures = df_factures[df_factures["Libellé / Tiers"].astype(str).str.strip() != ""]
        df_factures = df_factures.reset_index(drop=True)
        df_factures.index = range(1, len(df_factures) + 1)
    else:
        if is_pro:
            df_factures = pd.DataFrame(columns=["id", "Libellé / Tiers", "Type", "Montant HT", "Montant TTC", "Date", "Échéance", "Statut", "N° Compte"])
        else:
            df_factures = pd.DataFrame(columns=["id", "Libellé / Tiers", "Type", "Montant", "Date", "Échéance", "Statut"])

    df_devis = pd.read_sql_query("SELECT id, num_devis as 'Numéro Devis', client as 'Client', montant_ht as 'Montant HT', montant_ttc as 'Montant TTC', date as 'Date', statut as 'Statut' FROM devis WHERE email = ? ORDER BY date", conn, params=(st.session_state.user_email,))
    if not df_devis.empty:
        df_devis = df_devis.reset_index(drop=True)
        df_devis.index = range(1, len(df_devis) + 1)

    df_tiers = pd.read_sql_query("SELECT id, nom as 'Nom', role as 'Rôle', email_tiers as 'Email / Numéro', ville as 'Ville', compte_auxiliaire as 'N° Compte' FROM tiers WHERE email = ? ORDER BY role, nom", conn, params=(st.session_state.user_email,))
    if not df_tiers.empty:
        df_tiers = df_tiers.reset_index(drop=True)
        df_tiers.index = range(1, len(df_tiers) + 1)

    df_stocks = pd.read_sql_query("SELECT id, reference as 'Article / Référence', categorie as 'Catégorie', quantite as 'Quantité', prix_ht as 'Prix unitaire HT (€)' FROM stocks WHERE email = ? ORDER BY reference", conn, params=(st.session_state.user_email,))
    if not df_stocks.empty:
        df_stocks = df_stocks.reset_index(drop=True)
        df_stocks.index = range(1, len(df_stocks) + 1)
    else:
        df_stocks = pd.DataFrame(columns=["id", "Article / Référence", "Catégorie", "Quantité", "Prix unitaire HT (€)"])

    conn.close()

    with tab1:
        st.subheader(f"Indicateurs Clés - {st.session_state.profil}")
        col_montant_col = "Montant TTC" if is_pro else "Montant"
        total_revenus = df_factures[df_factures["Type"].isin(["Revenu", "Vente de Produits", "Prestation de Services", "Loyers perçus (SCI)"])][col_montant_col].sum() if not df_factures.empty else 0
        total_charges = df_factures[df_factures["Type"] == "Charge / Dépense"][col_montant_col].sum() if not df_factures.empty else 0
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
                    df_del_trans = df_del_trans[["Supprimer", "libelle", "type", "montant_ht", "montant_ttc", "Date", "Échéance", "statut", "compte", "id"]].rename(columns={
                        "libelle": "Libellé / Tiers", "type": "Type", "montant_ht": "Montant HT", "montant_ttc": "Montant TTC", "statut": "Statut", "compte": "N° Compte"
                    })
                else:
                    df_del_trans = df_del_trans[["Supprimer", "libelle", "type", "montant_ttc", "Date", "Échéance", "statut", "id"]].rename(columns={
                        "libelle": "Libellé / Tiers", "type": "Type", "montant_ttc": "Montant", "statut": "Statut"
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
                montant_saisi = st.number_input("Montant HT (€)" if is_pro else "Montant (€)", min_value=0.0, step=10.0, format="%.2f")
            with col_b:
                if is_pro:
                    if is_auto_entrepreneur:
                        st.info("Auto-entrepreneur : Franchise en base de TVA (0%)")
                        tva = 0.0
                    else:
                        tva = st.selectbox("Taux de TVA", [0.0, 5.5, 10.0, 20.0])
                else:
                    tva = 0.0
                
                date_facture = st.date_input("Date de la transaction", date.today())
                echeance_facture = st.date_input("Date d'échéance", date.today())
            
            submitted = st.form_submit_button("Enregistrer la transaction")

            if submitted:
                if libelle.strip() == "":
                    st.warning("Veuillez renseigner le libellé.")
                else:
                    montant_ttc = montant_saisi * (1 + tva / 100)
                    conn = sqlite3.connect("finapp.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO transactions (email, libelle, type, montant_ht, montant_ttc, date, echeance, statut, compte)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (st.session_state.user_email, libelle, type_flux, montant_saisi, montant_ttc, str(date_facture), str(echeance_facture), statut_pait, compte_auto))
                    conn.commit()
                    conn.close()
                    
                    st.session_state.form_key += 1
                    st.success(f"Transaction '{libelle}' ({montant_ttc:.2f} €) enregistrée avec succès (Compte {compte_auto}) !")
                    st.rerun()

    if is_auto_entrepreneur:
        with tab3:
            st.subheader("Gestion des Devis (Auto-entrepreneur)")
            st.markdown("Créez et suivez vos devis avant transformation en facture.")
            with st.form(f"form_devis_{st.session_state.form_key}"):
                col1, col2 = st.columns(2)
                with col1:
                    num_devis = st.text_input("Numéro de devis (ex: DEV-2026-001)", value="DEV-2026-001")
                    client_devis = st.text_input("Nom du client")
                with col2:
                    montant_ht_devis = st.number_input("Montant HT du devis (€)", min_value=0.0, step=10.0, format="%.2f")
                    date_devis = st.date_input("Date du devis", date.today())
                
                statut_devis = st.selectbox("Statut du devis", ["Accepté", "Payé", "Envoyé", "Brouillon"])
                btn_devis = st.form_submit_button("Enregistrer le devis")

                if btn_devis:
                    if client_devis.strip() == "":
                        st.warning("Veuillez renseigner le nom du client.")
                    else:
                        montant_ttc_devis = montant_ht_devis
                        conn = sqlite3.connect("finapp.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO devis (email, num_devis, client, montant_ht, montant_ttc, date, statut)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (st.session_state.user_email, num_devis, client_devis, montant_ht_devis, montant_ttc_devis, str(date_devis), statut_devis))
                        conn.commit()
                        conn.close()
                        st.session_state.form_key += 1
                        st.success(f"Devis '{num_devis}' enregistré avec succès !")
                        st.rerun()

            st.markdown("### Liste des Devis")
            conn_d = sqlite3.connect("finapp.db")
            raw_devis = pd.read_sql_query("SELECT id, num_devis, client, montant_ht, montant_ttc, date, statut FROM devis WHERE email = ?", conn_d, params=(st.session_state.user_email,))
            conn_d.close()
            
            if not raw_devis.empty:
                df_del_devis = raw_devis.copy()
                df_del_devis.insert(0, "Supprimer", False)
                df_del_devis = df_del_devis.rename(columns={
                    "num_devis": "Numéro Devis", "client": "Client", "montant_ht": "Montant HT", "montant_ttc": "Montant TTC", "date": "Date", "statut": "Statut"
                })
                df_del_devis = df_del_devis.reset_index(drop=True)
                df_del_devis.index = range(1, len(df_del_devis) + 1)
                
                edited_devis_table = st.data_editor(df_del_devis, use_container_width=True, hide_index=True)
                if st.button("Supprimer les devis cochés"):
                    ids_to_del = edited_devis_table[edited_devis_table["Supprimer"] == True]["id"].tolist()
                    if ids_to_del:
                        conn = sqlite3.connect("finapp.db")
                        cursor = conn.cursor()
                        cursor.executemany("DELETE FROM devis WHERE id = ?", [(i,) for i in ids_to_del])
                        conn.commit()
                        conn.close()
                        st.success("Devis sélectionnés supprimés !")
                        st.rerun()
                    else:
                        st.warning("Aucun devis coché.")
            else:
                st.info("Aucun devis enregistré pour le moment.")

    if is_auto_entrepreneur:
        target_tab_ech = tab4
        target_tab_tiers = tab5
        target_tab_stocks = tab6
    elif is_pro:
        target_tab_ech = tab3
        target_tab_tiers = tab4
        target_tab_stocks = tab5
    else:
        target_tab_ech = tab3

    with target_tab_ech:
        st.subheader("Système de Rappels, Alertes & Gestion dynamique des Échéances")
        if not df_factures.empty:
            a_payer = df_factures[df_factures["Statut"] == "À payer"]
            
            if len(a_payer) > 0:
                plural_pay = "s" if len(a_payer) > 1 else ""
                st.warning(f"Attention : Vous avez {len(a_payer)} élément{plural_pay} à payer !")
                for index, row in a_payer.iterrows():
                    montant_affichage = row["Montant TTC"] if is_pro else row["Montant"]
                    st.markdown(f"- **{row['Libellé / Tiers']}** ({row['Type']}) : `{montant_affichage:.2f} €` (À payer | **{row['Échéance']}**)")
            else:
                st.success("Aucun élément en attente de paiement !")
        else:
            st.info("Aucune donnée disponible.")

    if is_pro:
        with target_tab_tiers:
            st.subheader("Gestion des Tiers (Classés par catégorie)")
            with st.form(f"form_tiers_{st.session_state.form_key}"):
                col1, col2 = st.columns(2)
                with col1:
                    nom_tiers = st.text_input("Nom du Tiers (Client, Fournisseur ou Banque ex: BNP, Caisse d'Épargne)")
                    role_tiers = st.selectbox("Rôle", ["Client", "Fournisseur", "Établissement de crédit"])
                with col2:
                    email_tiers = st.text_input("Adresse e-mail / Numéro")
                    ville_tiers = st.text_input("Ville / Localisation")
                
                compte_aux_saisi = st.text_input("N° Compte (laisser vide pour attribution automatique ex: 41100001 ou 40100001)")
                
                btn_tiers = st.form_submit_button("Ajouter le Tiers")
                if btn_tiers:
                    if nom_tiers.strip() == "":
                        st.warning("Veuillez renseigner le nom.")
                    else:
                        conn = sqlite3.connect("finapp.db")
                        cursor = conn.cursor()
                        
                        cursor.execute("SELECT compte_auxiliaire FROM tiers WHERE email = ? AND nom = ?", (st.session_state.user_email, nom_tiers))
                        existing_tier = cursor.fetchone()
                        
                        if existing_tier and existing_tier[0]:
                            compte_aux = existing_tier[0]
                        elif compte_aux_saisi.strip() != "":
                            compte_aux = compte_aux_saisi.strip()
                        else:
                            if role_tiers == "Fournisseur":
                                cursor.execute("SELECT COUNT(*) FROM tiers WHERE email = ? AND role = 'Fournisseur'", (st.session_state.user_email,))
                                count_role = cursor.fetchone()[0] + 1
                                compte_aux = f"4010000{count_role}"
                            elif role_tiers == "Client":
                                cursor.execute("SELECT COUNT(*) FROM tiers WHERE email = ? AND role = 'Client'", (st.session_state.user_email,))
                                count_role = cursor.fetchone()[0] + 1
                                compte_aux = f"4110000{count_role}"
                            elif role_tiers == "Établissement de crédit":
                                compte_aux = "512"

                        cursor.execute("""
                            INSERT INTO tiers (email, nom, role, email_tiers, ville, compte_auxiliaire)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (st.session_state.user_email, nom_tiers, role_tiers, email_tiers, ville_tiers, compte_aux))
                        conn.commit()
                        conn.close()
                        st.session_state.form_key += 1
                        st.success(f"Tiers '{nom_tiers}' ajouté avec succès (Compte auxiliaire {compte_aux}) !")
                        st.rerun()

            st.markdown("### Liste des Tiers (Triés par rôle)")
            conn_t = sqlite3.connect("finapp.db")
            raw_tiers = pd.read_sql_query("SELECT id, nom, role, email_tiers, ville, compte_auxiliaire FROM tiers WHERE email = ? ORDER BY role, nom", conn_t, params=(st.session_state.user_email,))
            conn_t.close()
            
            if not raw_tiers.empty:
                df_del_tiers = raw_tiers.copy()
                df_del_tiers.insert(0, "Supprimer", False)
                df_del_tiers = df_del_tiers.rename(columns={
                    "nom": "Nom", "role": "Rôle", "email_tiers": "Email / Numéro", "ville": "Ville", "compte_auxiliaire": "N° Compte"
                })
                df_del_tiers = df_del_tiers.drop(columns=["id"])
                df_del_tiers = df_del_tiers.reset_index(drop=True)
                df_del_tiers.index = range(1, len(df_del_tiers) + 1)
                
                edited_tiers_table = st.data_editor(df_del_tiers, use_container_width=True, hide_index=True)
                if st.button("Supprimer les tiers cochés"):
                    noms_to_del = edited_tiers_table[edited_tiers_table["Supprimer"] == True]["Nom"].tolist()
                    if noms_to_del:
                        conn = sqlite3.connect("finapp.db")
                        cursor = conn.cursor()
                        cursor.executemany("DELETE FROM tiers WHERE email = ? AND nom = ?", [(st.session_state.user_email, n) for n in noms_to_del])
                        conn.commit()
                        conn.close()
                        st.success("Tiers sélectionnés supprimés !")
                        st.rerun()
                    else:
                        st.warning("Aucun tiers coché.")
            else:
                st.info("Aucun tiers enregistré pour le moment.")

        with target_tab_stocks:
            st.subheader("Gestion des Stocks & Articles")
            with st.form(f"form_stock_{st.session_state.form_key}"):
                col1, col2 = st.columns(2)
                with col1:
                    ref_article = st.text_input("Référence ou nom de l'article")
                    cat_article = st.text_input("Catégorie")
                with col2:
                    qte_article = st.number_input("Quantité", min_value=0, step=1, value=10)
                    prix_article = st.number_input("Prix unitaire HT (€)", min_value=0.0, step=5.0, format="%.2f")
                
                btn_stock = st.form_submit_button("Ajouter au stock")
                if btn_stock:
                    if ref_article.strip() == "":
                        st.warning("Veuillez renseigner la référence.")
                    else:
                        conn = sqlite3.connect("finapp.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO stocks (email, reference, categorie, quantite, prix_ht)
                            VALUES (?, ?, ?, ?, ?)
                        """, (st.session_state.user_email, ref_article, cat_article, qte_article, prix_article))
                        conn.commit()
                        conn.close()
                        st.session_state.form_key += 1
                        st.success(f"Article '{ref_article}' ajouté au stock !")
                        st.rerun()

            st.markdown("### État du Stock (Classé alphabétiquement & numéroté à partir de 1)")
            conn_s = sqlite3.connect("finapp.db")
            raw_stocks = pd.read_sql_query("SELECT id, reference, categorie, quantite, prix_ht FROM stocks WHERE email = ? ORDER BY reference", conn_s, params=(st.session_state.user_email,))
            conn_s.close()
            
            if not raw_stocks.empty:
                df_del_stocks = raw_stocks.copy()
                df_del_stocks.insert(0, "Supprimer", False)
                df_del_stocks.rename(columns={
                    "reference": "Article / Référence", "categorie": "Catégorie", "quantite": "Quantité", "prix_ht": "Prix unitaire HT (€)"
                }, inplace=True)
                df_del_stocks = df_del_stocks.reset_index(drop=True)
                df_del_stocks.index = range(1, len(df_del_stocks) + 1)
                
                edited_stocks_table = st.data_editor(df_del_stocks, use_container_width=True, hide_index=True)
                if st.button("Supprimer les articles cochés"):
                    ids_to_del = edited_stocks_table[edited_stocks_table["Supprimer"] == True]["id"].tolist()
                    if ids_to_del:
                        conn = sqlite3.connect("finapp.db")
                        cursor = conn.cursor()
                        cursor.executemany("DELETE FROM stocks WHERE id = ?", [(i,) for i in ids_to_del])
                        conn.commit()
                        conn.close()
                        st.success("Articles sélectionnés supprimés !")
                        st.rerun()
                    else:
                        st.warning("Aucun article coché.")
            else:
                st.info("Stock vide.")
