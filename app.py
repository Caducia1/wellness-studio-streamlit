import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from base64 import b64encode

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Wellness Studio – Suivi Sport & Bien-être",
    page_icon="🧘",
    layout="wide",
)

# -------------------------------------------------
# Sidebar toggle
# -------------------------------------------------
st.sidebar.markdown("## 🎨 Apparence")
mode_nuit = st.sidebar.toggle("Mode nuit zen", value=False)

# -------------------------------------------------
# CSS (premium)
# -------------------------------------------------
base_css = """
<style>
* { font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif; }

/* Palette */
:root{
  --ink: #1f2d28;
  --muted: #4b5b55;
  --brand: #1B4332;
  --accent: #52B788;
  --card: rgba(255,255,255,0.90);
  --card2: rgba(255,255,255,0.82);
  --border: rgba(27,67,50,0.14);
}

/* Animation douce */
.fade-in { animation: fadeIn .7s ease-in-out; }
@keyframes fadeIn { from { opacity:0; transform: translateY(6px);} to { opacity:1; transform: translateY(0);} }

/* Titres */
h1 { letter-spacing: -0.02em; line-height: 1.05; margin-bottom: .2rem; }
h2, h3 { letter-spacing: -0.01em; }
small, .stCaption { color: var(--muted) !important; font-size: .95rem !important; }

/* Sidebar */
section[data-testid="stSidebar"]{
  border-right: 1px solid var(--border);
}

/* Inputs */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stDateInput>div>div>input,
.stTextArea textarea,
.stSelectbox>div>div{
  border-radius: 14px !important;
  border: 1px solid var(--border) !important;
  background: rgba(255,255,255,0.93) !important;
}

/* Labels widgets */
label, .stSelectbox label, .stSlider label, .stNumberInput label, .stDateInput label{
  font-weight: 600 !important;
  color: var(--ink) !important;
}

/* Boutons */
.stButton>button{
  border-radius: 999px;
  padding: .55rem 1.35rem;
  font-weight: 700;
  border: none;
  transition: all .25s ease;
}
.stButton>button:hover{ transform: translateY(-1px) scale(1.02); }

/* KPI cards */
.kpi-card{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 18px;
  text-align: left;
  box-shadow: 0 4px 18px rgba(0,0,0,.06);
  backdrop-filter: blur(6px);
}
.kpi-top{
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom: 6px;
}
.kpi-label{
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .10em;
  color: var(--muted);
  font-weight: 800;
}
.kpi-number{
  font-size: 34px;
  font-weight: 900;
  color: var(--brand);
}
.kpi-sub{
  font-size: 13px;
  color: var(--muted);
}

/* Section cards */
.section-card{
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px 18px 10px 18px;
  margin: 12px 0 18px 0;
  box-shadow: 0 4px 18px rgba(0,0,0,.06);
  backdrop-filter: blur(7px);
}
.section-title{
  display:flex; align-items:center; gap:12px;
  margin: 0 0 10px 0;
}
.section-dot{
  width:10px; height:10px; border-radius:999px;
  background: var(--accent);
  box-shadow: 0 0 0 4px rgba(82,183,136,0.18);
}

/* Badge */
.badge{
  display:inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,.85);
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

/* Dataframe */
.stDataFrame { border-radius: 16px; overflow: hidden; }
</style>
"""

light_css = """
<style>
.stApp { background: linear-gradient(120deg, rgba(227,253,253,0.88), rgba(203,241,245,0.88)); }

.block-container{
  padding-top: 1.4rem;
  background-color: rgba(255,255,255,0.78);
  border-radius: 26px;
  margin: 1.1rem;
  padding-bottom: 1.4rem;
}

h1, h2, h3, h4 { color: #1B4332 !important; }

section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #E9FFD9 0%, #DEFDE0 100%);
}

.stButton>button{
  background: linear-gradient(90deg, #74C69D, #52B788);
  color: white;
}
</style>
"""

dark_css = """
<style>
.stApp { background: linear-gradient(160deg, #0b1726 0%, #13293D 50%, #08141f 100%); }

.block-container{
  padding-top: 1.4rem;
  background-color: rgba(7, 18, 30, 0.62);
  border-radius: 26px;
  margin: 1.1rem;
  padding-bottom: 1.4rem;
}

h1, h2, h3, h4 { color: #B5F3FF !important; }

section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #051725 0%, #0B2538 100%);
  border-right: 1px solid rgba(173,232,244,0.18);
}

.stButton>button{
  background: linear-gradient(90deg, #00B4D8, #48CAE4);
  color: #01161E;
}

.kpi-card{
  background: rgba(10, 25, 47, 0.80);
  border: 1px solid rgba(173,232,244,0.14);
}
.kpi-number{ color:#ADE8F4; }
.kpi-label, .kpi-sub{ color:#B5F3FF; }
.badge{
  border: 1px solid rgba(173,232,244,0.14);
  background: rgba(10, 25, 47, 0.60);
  color:#B5F3FF;
}
</style>
"""

st.markdown(base_css, unsafe_allow_html=True)
st.markdown(dark_css if mode_nuit else light_css, unsafe_allow_html=True)

# -------------------------------------------------
# Background image (base64) – guaranteed
# -------------------------------------------------
img_path = Path("background.png")
if img_path.exists():
    img_base64 = b64encode(img_path.read_bytes()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            filter: saturate(0.95) brightness(1.05);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.warning("Image de fond introuvable : background.png (mets-la à la racine du dossier SportApp)")

# -------------------------------------------------
# Title
# -------------------------------------------------
st.markdown(
    "<h1 class='fade-in'>Wellness Studio <span class='badge'>Suivi Sport & Bien-être</span></h1>",
    unsafe_allow_html=True,
)
st.caption("Suivi doux de tes séances, de ton humeur et de ton sommeil.")

# -------------------------------------------------
# Data storage
# -------------------------------------------------
DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)
CSV_FILE = DATA_PATH / "bienetre.csv"

def charger_donnees() -> pd.DataFrame:
    if CSV_FILE.exists():
        df_ = pd.read_csv(CSV_FILE)
        if not df_.empty:
            df_["date"] = pd.to_datetime(df_["date"]).dt.date
        return df_
    return pd.DataFrame(columns=["date","activite","duree_min","intensite","humeur","sommeil_h","commentaire"])

def enregistrer_seance(enr: dict) -> None:
    df_ = charger_donnees()
    df_ = pd.concat([df_, pd.DataFrame([enr])], ignore_index=True)
    df_.to_csv(CSV_FILE, index=False)

# -------------------------------------------------
# Sidebar form
# -------------------------------------------------
st.sidebar.markdown("## 📝 Nouvelle séance")
with st.sidebar.form("form_seance", clear_on_submit=True):
    date_seance = st.date_input("Date", value=date.today())
    activite = st.selectbox("Activité", ["Marche", "Course", "Yoga / Pilate", "Musculation", "Vélo", "Natation", "Autre"])
    duree_min = st.number_input("Durée (minutes)", min_value=0, max_value=600, value=30, step=5)
    intensite = st.slider("Intensité (1 à 5)", 1, 5, 3)
    humeur = st.slider("Humeur (1 à 5)", 1, 5, 4)
    sommeil_h = st.number_input("Sommeil (heures)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
    commentaire = st.text_area("Commentaire (optionnel)", height=80)
    submit = st.form_submit_button("Enregistrer")

if submit:
    if duree_min == 0 and sommeil_h == 0:
        st.sidebar.error("Indique au moins une durée de séance ou une durée de sommeil.")
    else:
        enr = {
            "date": date_seance,
            "activite": activite,
            "duree_min": int(duree_min),
            "intensite": int(intensite),
            "humeur": int(humeur),
            "sommeil_h": float(sommeil_h),
            "commentaire": commentaire.strip() if commentaire else "",
        }
        enregistrer_seance(enr)
        st.sidebar.success("Séance enregistrée ✅")

# -------------------------------------------------
# Dashboard
# -------------------------------------------------
df = charger_donnees()

if df.empty:
    st.info("Aucune donnée pour le moment. Ajoute une séance avec le formulaire à gauche.")
else:
    ref_today = df["date"].max()

    # Filters
    st.markdown(
        '<div class="section-card fade-in"><div class="section-title"><div class="section-dot"></div><h2>Filtres</h2></div>',
        unsafe_allow_html=True
    )
    cfil1, cfil2, cfil3 = st.columns(3)
    with cfil1:
        periode = st.selectbox("Période", ["7 derniers jours", "30 derniers jours", "Tout l'historique"], index=1)
    with cfil2:
        activites_sel = st.multiselect(
            "Activités",
            options=sorted(df["activite"].unique()),
            default=list(sorted(df["activite"].unique()))
        )
    with cfil3:
        humeur_min = st.slider("Humeur minimale", 1, 5, 1)
    st.markdown("</div>", unsafe_allow_html=True)

    df_filtre = df.copy()

    if periode == "7 derniers jours":
        df_filtre = df_filtre[df_filtre["date"] >= (ref_today - timedelta(days=7))]
    elif periode == "30 derniers jours":
        df_filtre = df_filtre[df_filtre["date"] >= (ref_today - timedelta(days=30))]

    df_filtre = df_filtre[df_filtre["activite"].isin(activites_sel)]
    df_filtre = df_filtre[df_filtre["humeur"] >= humeur_min]

    if df_filtre.empty:
        st.warning("Aucune donnée ne correspond aux filtres. Essaie d’élargir la période ou de sélectionner plus d’activités.")
    else:
        total_seances = len(df_filtre)
        total_minutes = int(df_filtre["duree_min"].sum())
        humeur_moy = round(df_filtre["humeur"].mean(), 2)
        sommeil_moy = round(df_filtre["sommeil_h"].mean(), 2)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(
                f"""
                <div class="kpi-card fade-in">
                  <div class="kpi-top">
                    <div class="kpi-label">Séances</div>
                    <span class="badge">{periode}</span>
                  </div>
                  <div class="kpi-number">{total_seances}</div>
                  <div class="kpi-sub">Nombre total de séances</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"""
                <div class="kpi-card fade-in">
                  <div class="kpi-top">
                    <div class="kpi-label">Activité</div>
                    <span class="badge">minutes</span>
                  </div>
                  <div class="kpi-number">{total_minutes}</div>
                  <div class="kpi-sub">Temps total d’activité</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:
            st.markdown(
                f"""
                <div class="kpi-card fade-in">
                  <div class="kpi-top">
                    <div class="kpi-label">Humeur</div>
                    <span class="badge">/5</span>
                  </div>
                  <div class="kpi-number">{humeur_moy}</div>
                  <div class="kpi-sub">Moyenne sur la période</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c4:
            st.markdown(
                f"""
                <div class="kpi-card fade-in">
                  <div class="kpi-top">
                    <div class="kpi-label">Sommeil</div>
                    <span class="badge">heures</span>
                  </div>
                  <div class="kpi-number">{sommeil_moy}</div>
                  <div class="kpi-sub">Moyenne par nuit</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Tabs
        tab1, tab2, tab3 = st.tabs(["Activité", "Humeur & Sommeil", "Détails"])

        with tab1:
            st.markdown(
                '<div class="section-card fade-in"><div class="section-title"><div class="section-dot"></div><h2>Activité dans le temps</h2></div>',
                unsafe_allow_html=True
            )
            d1 = df_filtre.copy()
            d1["date"] = pd.to_datetime(d1["date"])
            par_jour = d1.groupby("date")["duree_min"].sum().sort_index()
            st.line_chart(par_jour, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown(
                '<div class="section-card fade-in"><div class="section-title"><div class="section-dot"></div><h2>Humeur & sommeil</h2></div>',
                unsafe_allow_html=True
            )
            d2 = df_filtre.copy()
            d2["date"] = pd.to_datetime(d2["date"])
            colA, colB = st.columns(2)
            with colA:
                st.markdown("**Humeur**")
                st.line_chart(d2.set_index("date")["humeur"], use_container_width=True)
            with colB:
                st.markdown("**Sommeil (heures)**")
                st.line_chart(d2.set_index("date")["sommeil_h"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown(
                '<div class="section-card fade-in"><div class="section-title"><div class="section-dot"></div><h2>Tableau détaillé</h2></div>',
                unsafe_allow_html=True
            )
            st.dataframe(df_filtre.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

            st.markdown("**Répartition du temps par activité**")
            rep = df_filtre.groupby("activite")["duree_min"].sum().sort_values(ascending=False)
            st.bar_chart(rep, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Tips
        st.markdown(
            '<div class="section-card fade-in"><div class="section-title"><div class="section-dot"></div><h2>Conseils bien-être</h2></div>',
            unsafe_allow_html=True
        )
        conseils = []
        if total_minutes < 60:
            conseils.append("Tu bouges peu sur la période : vise 2 séances courtes de 20–30 minutes.")
        else:
            conseils.append("Très bien : garde un rythme régulier (2 à 3 séances / semaine).")
        if sommeil_moy < 7:
            conseils.append("Sommeil un peu bas : essaie de te coucher 30 minutes plus tôt et limite les écrans.")
        if humeur_moy <= 3:
            conseils.append("Humeur moyenne/basse : privilégie des séances douces (marche, yoga) + sorties nature.")
        for c in conseils:
            st.write("•", c)
        st.markdown("</div>", unsafe_allow_html=True)

        # Export
        st.markdown(
            '<div class="section-card fade-in"><div class="section-title"><div class="section-dot"></div><h2>Export</h2></div>',
            unsafe_allow_html=True
        )
        st.download_button(
            "Télécharger les données filtrées (CSV)",
            data=df_filtre.to_csv(index=False).encode("utf-8"),
            file_name="bienetre_filtre.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)
