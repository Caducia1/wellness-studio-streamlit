import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from base64 import b64encode

# ============================================================
# 01) CONFIGURATION DE L'APP
# ============================================================
APP_NAME = "Wellness Studio"
st.set_page_config(page_title=APP_NAME, page_icon="🧘", layout="wide")

# ============================================================
# 02) DOSSIERS / FICHIERS
# ============================================================
DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)
ASSETS = Path("assets"); ASSETS.mkdir(exist_ok=True)
CSV_FILE = DATA_DIR / "bienetre.csv"

# ============================================================
# 03) COLONNES ATTENDUES DANS LE CSV
# ============================================================
COLS = ["date", "activite", "duree_min", "intensite", "humeur", "sommeil_h", "commentaire"]


# ============================================================
# 04) RENDU HTML (évite affichage en bloc de code)
# ============================================================
def md_html(html: str):
    html = "\n".join(line.lstrip() for line in html.splitlines())
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# 05) ASSETS (récupérer un fichier s'il existe)
# ============================================================
def pick_asset(*names):
    for n in names:
        p = ASSETS / n
        if p.exists():
            return p
        p2 = Path(n)
        if p2.exists():
            return p2
    return None


# ============================================================
# 06) CSS BACKGROUND (image + voile)
# ============================================================
def css_bg(bg_path: Path, veil: float, dark: bool):
    mime = "png" if bg_path.suffix.lower() == ".png" else "jpeg"
    b64 = b64encode(bg_path.read_bytes()).decode()
    overlay = (
        f"linear-gradient(180deg, rgba(0,0,0,{veil}) 0%, rgba(0,0,0,{min(veil+0.15,0.95)}) 100%)"
        if dark
        else f"linear-gradient(180deg, rgba(255,255,255,{veil}) 0%, rgba(255,255,255,{min(veil+0.15,0.95)}) 100%)"
    )
    return f"""
    .stApp {{
      background-image: {overlay}, url("data:image/{mime};base64,{b64}");
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
    }}
    """


# ============================================================
# 07) CHARGEMENT DU CSV + NETTOYAGE (robuste)
# ============================================================
def load_df():
    """
    Charge le fichier CSV des sessions.
    - Si le CSV n'existe pas, on le crée vide avec les bonnes colonnes.
    - On force les types (date, int, float, str) pour éviter les bugs.
    """
    if not CSV_FILE.exists():
        df = pd.DataFrame(columns=COLS)
        df.to_csv(CSV_FILE, index=False)
        return df

    df = pd.read_csv(CSV_FILE)

    for c in COLS:
        if c not in df.columns:
            df[c] = "" if c == "commentaire" else 0

    df = df[COLS].copy()

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        df = df.dropna(subset=["date"])

        df["duree_min"] = pd.to_numeric(df["duree_min"], errors="coerce").fillna(0).astype(int)
        df["intensite"] = pd.to_numeric(df["intensite"], errors="coerce").fillna(0).astype(int)
        df["humeur"] = pd.to_numeric(df["humeur"], errors="coerce").fillna(0).astype(int)
        df["sommeil_h"] = pd.to_numeric(df["sommeil_h"], errors="coerce").fillna(0).astype(float)

        df["commentaire"] = df["commentaire"].fillna("").astype(str)

    return df


# ============================================================
# 08) AJOUT D'UNE SESSION (append)
# ============================================================
def save_append(row: dict):
    df = load_df()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)


# ============================================================
# 09) SAUVEGARDE D'UN DF COMPLET (utile après suppression)
# ============================================================
def save_df(df: pd.DataFrame):
    for c in COLS:
        if c not in df.columns:
            df[c] = "" if c == "commentaire" else 0
    df = df[COLS].copy()
    df.to_csv(CSV_FILE, index=False)


# ============================================================
# 10) OUTILS DE CALCUL (score, tendance, filtres)
# ============================================================
def clamp(x, a, b):
    return max(a, min(b, x))

def streak_days(df):
    if df.empty:
        return 0
    days = sorted(set(df["date"]))
    if not days:
        return 0
    s = 1
    for i in range(len(days) - 1, 0, -1):
        if (days[i] - days[i - 1]).days == 1:
            s += 1
        else:
            break
    return s

def global_score(h, sl, mins, streak):
    s_h  = (h / 5) * 35
    s_sl = clamp(sl / 8, 0, 1) * 35
    s_m  = clamp(mins / 600, 0, 1) * 20
    s_st = clamp(streak / 10, 0, 1) * 10
    return int(round(s_h + s_sl + s_m + s_st))

def score_status(s):
    if s >= 85: return "Excellence"
    if s >= 70: return "Très satisfaisant"
    if s >= 55: return "Satisfaisant"
    if s >= 40: return "À renforcer"
    return "Priorité récupération"

def delta(cur, prev):
    if prev is None:
        return None
    try:
        return cur - prev
    except Exception:
        return None

def delta_chip(v, unit="", positive_is_good=True):
    if v is None:
        return ""
    arrow = "↑" if v > 0 else ("↓" if v < 0 else "•")
    good = (v >= 0) if positive_is_good else (v <= 0)
    cls = "ok" if good else "warn"
    if isinstance(v, float):
        label = f"{'+' if v >= 0 else ''}{v:.2f}{unit}"
    else:
        label = f"{'+' if v >= 0 else ''}{v}{unit}"
    return f"<span class='delta {cls}'>{arrow} {label}</span>"

def window(df, start, end):
    if df.empty:
        return df
    return df[(df["date"] >= start) & (df["date"] <= end)].copy()


# ============================================================
# 11) SIDEBAR : PARAMÈTRES + SAISIE
# ============================================================
st.sidebar.title("Paramétrage")
theme = st.sidebar.selectbox("Thème", ["Clair", "Sombre"], index=0)
dark = theme == "Sombre"

period_days = st.sidebar.selectbox("Périmètre d’analyse", [7, 14, 30, 90, 365], index=2)

st.sidebar.markdown("#### Arrière-plan")
veil = st.sidebar.slider("Voile", 0.06, 0.90, 0.14 if not dark else 0.60, 0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("Saisie d’une session")

with st.sidebar.form("add", clear_on_submit=True):
    d = st.date_input("Date", value=date.today())
    act = st.selectbox("Activité", ["Marche", "Course", "Yoga / Pilates", "Musculation", "Vélo", "Natation", "Autre"])
    mins = st.number_input("Durée (min)", 0, 600, 30, 5)
    inten = st.slider("Intensité", 1, 5, 3)
    mood = st.slider("Bien-être", 1, 5, 4)
    sleep = st.number_input("Sommeil (h)", 0.0, 24.0, 7.0, 0.5)
    com = st.text_area("Commentaire", height=80)
    ok = st.form_submit_button("Enregistrer")

if ok:
    if mins == 0 and sleep == 0:
        st.sidebar.error("Renseignez une durée d’activité ou de sommeil.")
    else:
        save_append({
            "date": d,
            "activite": act,
            "duree_min": int(mins),
            "intensite": int(inten),
            "humeur": int(mood),
            "sommeil_h": float(sleep),
            "commentaire": com.strip() if com else ""
        })
        st.sidebar.success("Session enregistrée.")
        st.rerun()


# ============================================================
# 12) STYLE (CSS)
# ============================================================
bg = pick_asset("background.png", "background2.png")

palette = """
:root{
  --ink:#0b1412;
  --muted:rgba(11,20,18,.62);
  --line:rgba(11,20,18,.12);

  --maskA:rgba(255,255,255,.62);
  --maskB:rgba(255,255,255,.50);

  --okBg:rgba(15,91,69,.14); --okInk:#0f5b45;
  --warnBg:rgba(225,120,0,.14); --warnInk:#b75a00;

  --accent:#23b9ad;
  --btn1:#0f5b45;
  --btn2:#23b9ad;

  --maskTint1: rgba(35,185,173,.14);
  --maskTint2: rgba(15,91,69,.12);
}
""" if not dark else """
:root{
  --ink:#eef7f4;
  --muted:rgba(238,247,244,.72);
  --line:rgba(238,247,244,.14);

  --maskA:rgba(8,14,13,.54);
  --maskB:rgba(8,14,13,.44);

  --okBg:rgba(126,224,196,.18); --okInk:#bff7ea;
  --warnBg:rgba(255,166,77,.18); --warnInk:#ffd1a3;

  --accent:#7dd3fc;
  --btn1:#7ee0c4;
  --btn2:#7dd3fc;

  --maskTint1: rgba(125,211,252,.14);
  --maskTint2: rgba(126,224,196,.10);
}
"""

md_html(f"""
<style>
{palette}
{css_bg(bg, veil, dark) if bg else ""}

header[data-testid="stHeader"]{{background:transparent!important;}}
.block-container{{max-width:1180px;padding-top:1.1rem!important;padding-bottom:1.2rem!important;}}
.stCaption, small{{color:var(--muted)!important;}}

section[data-testid="stSidebar"]{{
  background: rgba(255,255,255,.55);
  {"background: rgba(8,14,13,.42);" if dark else ""}
  border-right: 1px solid var(--line);
  backdrop-filter: blur(10px);
}}

/* MASQUES COLORÉS */
.mask{{
  background: linear-gradient(135deg, var(--maskTint1), var(--maskTint2)), var(--maskA);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 16px 18px;
  margin-bottom: 16px;
  backdrop-filter: blur(12px);
}}
.mask-mini{{
  background: linear-gradient(135deg, var(--maskTint1), rgba(255,255,255,.10));
  {"background: linear-gradient(135deg, var(--maskTint1), rgba(8,14,13,.08));" if dark else ""}
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 8px 10px;
  margin-bottom: 10px;
  backdrop-filter: blur(8px);
}}
.mask-mini b{{font-size:13px;color:var(--ink);}}
.mask-mini .sub{{margin-top:2px;font-size:12px;color:var(--muted);font-weight:750;}}

/* Boutons */
div[data-testid="stButton"] > button{{
  border: none !important;
  border-radius: 999px !important;
  padding: .80rem 1.10rem !important;
  font-weight: 950 !important;
  color: white !important;
  background: linear-gradient(90deg, var(--btn1), var(--btn2)) !important;
  box-shadow: 0 12px 26px rgba(0,0,0,.16) !important;
  transition: transform .14s ease, filter .14s ease, box-shadow .14s ease !important;
}}
div[data-testid="stButton"] > button:hover{{
  transform: translateY(-1px) !important;
  filter: brightness(1.03) !important;
  box-shadow: 0 16px 34px rgba(0,0,0,.20) !important;
}}

/* Download buttons */
div[data-testid="stDownloadButton"] > button{{
  border: none !important;
  border-radius: 999px !important;
  padding: .80rem 1.10rem !important;
  font-weight: 950 !important;
  color: white !important;
  background: linear-gradient(90deg, var(--btn1), var(--btn2)) !important;
  box-shadow: 0 12px 26px rgba(0,0,0,.16) !important;
  transition: transform .14s ease, filter .14s ease, box-shadow .14s ease !important;
}}
div[data-testid="stDownloadButton"] > button:hover{{
  transform: translateY(-1px) !important;
  filter: brightness(1.03) !important;
  box-shadow: 0 16px 34px rgba(0,0,0,.20) !important;
}}
div[data-testid="stDownloadButton"] > button:disabled{{
  opacity: .55 !important;
  filter: grayscale(.15) !important;
}}

/* Header sans masque */
.logoRow{{display:flex;align-items:flex-start;gap:18px;margin-bottom:16px;}}
.logoIcon{{
  width:96px;height:96px;border-radius:22px;
  display:flex;align-items:center;justify-content:center;
  background:
    radial-gradient(circle at 30% 25%, rgba(255,255,255,.28), transparent 60%),
    linear-gradient(135deg, var(--accent), rgba(15,91,69,.92));
  {"background: radial-gradient(circle at 30% 25%, rgba(255,255,255,.14), transparent 60%), linear-gradient(135deg, var(--accent), rgba(126,224,196,.55));" if dark else ""}
  box-shadow: 0 18px 44px rgba(0,0,0,.20);
  border: 1px solid rgba(255,255,255,.18);
  flex: 0 0 auto;
}}
.logoW{{font-size:40px;font-weight:950;color:white;line-height:1;text-shadow:0 12px 22px rgba(0,0,0,.28);letter-spacing:-0.03em;}}
.h1{{font-size:44px;font-weight:950;letter-spacing:-0.02em;color:var(--ink);margin:0;line-height:1.05;}}

.pills{{display:flex;gap:12px;flex-wrap:wrap;margin-top:10px;margin-bottom:10px;}}
.pill{{
  display:inline-flex;align-items:center;gap:10px;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,.10);
  {"border: 1px solid rgba(255,255,255,.14);" if dark else ""}
  font-weight: 950;
  color: rgba(0,0,0,.80);
  box-shadow: 0 10px 22px rgba(0,0,0,.10);
}}
.pills .pill:nth-child(1){{background: linear-gradient(135deg, rgba(35,185,173,.35), rgba(15,91,69,.20));}}
.pills .pill:nth-child(2){{background: linear-gradient(135deg, rgba(125,211,252,.40), rgba(35,185,173,.22));}}
.pills .pill:nth-child(3){{background: linear-gradient(135deg, rgba(255,166,77,.38), rgba(125,211,252,.20));}}
.pill svg{{width:18px;height:18px;stroke:rgba(0,0,0,.78);stroke-width:2;fill:none;opacity:.95;}}
{" .pill svg{stroke:rgba(10,14,13,.92);} " if dark else ""}

.goalLine{{
  margin-top: 8px;
  color: rgba(0,0,0,.80);
  {"color: rgba(255,255,255,.86);" if dark else ""}
  font-weight: 900;
  font-size: 18px;
  line-height: 1.45;
}}

.analyseTitle{{display:flex;align-items:center;gap:10px;margin-top:10px;margin-bottom:6px;font-size:26px;font-weight:950;color:var(--ink);}}
.analyseTitle svg{{width:22px;height:22px;stroke:var(--ink);stroke-width:2;fill:none;opacity:.95;}}
.analyseText{{color: rgba(0,0,0,.78);{"color: rgba(255,255,255,.86);" if dark else ""}font-weight:850;font-size:16px;line-height:1.6;margin-bottom:10px;}}

.ico{{width:30px;height:30px;border-radius:10px;border:1px solid var(--line);
  background: rgba(255,255,255,.22);
  {"background: rgba(8,14,13,.24);" if dark else ""}
  display:flex;align-items:center;justify-content:center;backdrop-filter: blur(10px);flex:0 0 auto;
}}
.ico svg{{width:18px;height:18px;stroke:var(--ink);stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round;opacity:.95;}}

.kpi{{background:var(--maskB);border:1px solid var(--line);border-radius:16px;padding:12px 14px;height:132px;
  display:flex;flex-direction:column;justify-content:space-between;margin-bottom:16px;backdrop-filter: blur(12px);
}}
.kTop{{display:flex;align-items:center;justify-content:space-between;gap:10px;}}
.kLeft{{display:flex;align-items:center;gap:10px;min-width:0;}}
.klabel{{font-size:10px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);white-space:nowrap;}}
.kval{{font-size:32px;font-weight:950;color:var(--ink);line-height:1.0;}}
.ksub{{font-weight:800;font-size:13px;color:rgba(0,0,0,.60);{"color: rgba(255,255,255,.74);" if dark else ""}}}

.delta{{display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:999px;border:1px solid var(--line);font-weight:900;font-size:11px;}}
.delta.ok{{background:var(--okBg);color:var(--okInk);}}
.delta.warn{{background:var(--warnBg);color:var(--warnInk);}}

.anaDates{{
  margin-top: 8px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,.22);
  {"background: rgba(8,14,13,.20);" if dark else ""}
  color: rgba(0,0,0,.78);
  {"color: rgba(255,255,255,.86);" if dark else ""}
  font-weight: 900;
  font-size: 14px;
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap: wrap;
}}
.anaDates .tag{{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;border:1px solid var(--line);
  background: rgba(255,255,255,.18);
  {"background: rgba(8,14,13,.20);" if dark else ""}
  font-weight: 900;
}}
.anaDates .tag svg{{width:16px;height:16px;stroke:var(--ink);stroke-width:2;fill:none;opacity:.95;}}
.anaDates .val{{font-weight:950;color:var(--ink);}}

.sTitle{{display:flex;align-items:center;gap:10px;font-size:18px;font-weight:950;color:var(--ink);margin-bottom:8px;}}
.sTitle .ico{{width:34px;height:34px;border-radius:12px;}}
.sList li{{margin-top:8px;color:var(--muted);font-weight:850;}}

.footer{{margin-top:14px;color: rgba(0,0,0,.72);{"color: rgba(255,255,255,.80);" if dark else ""}font-weight:950;font-size:18px;padding:0 2px;}}
.footer strong{{color:var(--ink);font-size:20px;}}
</style>
""")


# ============================================================
# 13) SVG ICONS
# ============================================================
def svg_icon(name: str) -> str:
    icons = {
        "calendar": """<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4.5" width="18" height="16" rx="3"/><path d="M8 3v3"/><path d="M16 3v3"/><path d="M3 9h18"/></svg>""",
        "timer": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 2h4"/><path d="M12 14v-4"/><path d="M12 22a8 8 0 1 0-8-8"/></svg>""",
        "smile": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 14.5c1 1.2 2.2 2 3.5 2s2.5-.8 3.5-2"/><path d="M9 10h.01"/><path d="M15 10h.01"/><circle cx="12" cy="12" r="9"/></svg>""",
        "moon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 13a8.5 8.5 0 1 1-10-10 7 7 0 0 0 10 10z"/></svg>""",
        "fire": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22c4 0 7-3 7-7 0-3-2-5-4-7 0 2-1 3-2 4-1-2-2-3-2-6C7 8 5 11 5 15c0 4 3 7 7 7z"/></svg>""",
        "flag": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3v18"/><path d="M5 4h12l-2 4 2 4H5"/></svg>""",
        "trend": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 16l6-6 4 4 6-8"/><path d="M20 7v5h-5"/></svg>""",
        "alert": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 9v5"/><path d="M12 17h.01"/><path d="M10.3 4.2l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-2.8l-8-14a2 2 0 0 0-3.4 0z"/></svg>""",
        "bolt": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2L3 14h7l-1 8 12-14h-7l-1-6z"/></svg>""",
        "eye": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>""",
        "sync": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12a9 9 0 0 1-15.36 6.36"/><path d="M3 12a9 9 0 0 1 15.36-6.36"/><path d="M21 3v6h-6"/><path d="M3 21v-6h6"/></svg>""",
        "info": """<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 10v7"/><path d="M12 7h.01"/></svg>""",
    }
    return icons.get(name, icons["info"])

def ico(name: str) -> str:
    return f"<div class='ico'>{svg_icon(name)}</div>"


# ============================================================
# 14) HEADER (logo WS + titre)
# ============================================================
md_html(f"""
<div class="logoRow">
  <div class="logoIcon"><div class="logoW">WS</div></div>
  <div style="flex:1;min-width:0;">
    <div class="h1">{APP_NAME}</div>

    <div class="pills">
      <span class="pill">{svg_icon("bolt")} Boost ton énergie</span>
      <span class="pill">{svg_icon("eye")} Suis tes habitudes</span>
      <span class="pill">{svg_icon("sync")} Compare tes tendances</span>
    </div>

    <div class="goalLine">
      Pilotage simple de l’activité, du sommeil et du bien-être.
      <span style="opacity:.88;">Ce qui s’améliore, ce qui baisse : tout est visible.</span>
    </div>
  </div>
</div>
""")


# ============================================================
# 15) DONNÉES + FILTRES PAGE
# ============================================================
df_all = load_df()

md_html("<div class='mask-mini'><b>Filtres</b><div class='sub'>Période, activités et seuil de bien-être.</div></div>")

c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    period_days_page = st.selectbox("Période", [7, 14, 30, 90, 365], index=[7, 14, 30, 90, 365].index(period_days))
with c2:
    activities_all = sorted(df_all["activite"].unique()) if not df_all.empty else []
    selected_acts = st.multiselect("Activités", options=activities_all, default=activities_all)
with c3:
    min_mood = st.slider("Seuil bien-être", 1, 5, 1)

if df_all.empty:
    md_html("<div class='mask'>Aucune donnée. Ajoute une session dans la barre latérale.</div>")
    st.stop()

end_cur = df_all["date"].max()
start_cur = end_cur - timedelta(days=period_days_page - 1)
end_prev = start_cur - timedelta(days=1)
start_prev = end_prev - timedelta(days=period_days_page - 1)

df_cur = window(df_all, start_cur, end_cur)
df_prev = window(df_all, start_prev, end_prev)

if selected_acts:
    df_cur = df_cur[df_cur["activite"].isin(selected_acts)]
    df_prev = df_prev[df_prev["activite"].isin(selected_acts)]

df_cur = df_cur[df_cur["humeur"] >= min_mood]
df_prev = df_prev[df_prev["humeur"] >= min_mood]

if df_cur.empty:
    md_html("<div class='mask'>Aucune donnée avec ces filtres. Ajuste les critères ou ajoute une session.</div>")
    st.stop()


# ============================================================
# 16) CALCUL DES KPI + COMPARAISON
# ============================================================
total = len(df_cur)
minutes = int(df_cur["duree_min"].sum())
h_m = float(df_cur["humeur"].mean())
sl_m = float(df_cur["sommeil_h"].mean())
streak = streak_days(df_cur)
score = global_score(h_m, sl_m, minutes, streak)
status = score_status(score)

prev_minutes = int(df_prev["duree_min"].sum()) if not df_prev.empty else None
prev_hm = float(df_prev["humeur"].mean()) if not df_prev.empty else None
prev_slm = float(df_prev["sommeil_h"].mean()) if not df_prev.empty else None
prev_streak = streak_days(df_prev) if not df_prev.empty else None
prev_score = global_score(prev_hm, prev_slm, prev_minutes, prev_streak) if not df_prev.empty else None

d_minutes = delta(minutes, prev_minutes)
d_hm = delta(h_m, prev_hm)
d_slm = delta(sl_m, prev_slm)
d_score = delta(score, prev_score)


# ============================================================
# 17) BLOC "ANALYSE" (principe + périodes)
# ============================================================
md_html(f"""
<div class="analyseTitle">
  {svg_icon("info")} Analyse
</div>
<div class="analyseText">
  <b>Principe :</b> tu saisis tes sessions (activité, intensité, bien-être, sommeil).
  Le tableau de bord calcule les indicateurs sur la période filtrée, puis compare la période sélectionnée
  à la période précédente de même durée (<b>↑ / ↓</b>) pour visualiser les tendances.
</div>
""")

md_html(f"""
<div class="anaDates">
  <span class="tag">{svg_icon("calendar")} Période analysée</span>
  <span class="val">{start_cur.strftime('%d/%m/%Y')} → {end_cur.strftime('%d/%m/%Y')}</span>
  <span style="opacity:.55;">|</span>
  <span class="tag">{svg_icon("trend")} Comparaison</span>
  <span class="val">{start_prev.strftime('%d/%m/%Y')} → {end_prev.strftime('%d/%m/%Y')}</span>
</div>
""")


# ============================================================
# 18) KPI (cartes)
# ============================================================
r1 = st.columns(3, gap="large")
r1[0].markdown(
    f"""
    <div class='kpi'>
      <div class='kTop'>
        <div class='kLeft'>{ico("calendar")}<div class='klabel'>VOLUME</div></div>
      </div>
      <div class='kval'>{total}</div>
      <div class='ksub'>Sessions</div>
    </div>
    """,
    unsafe_allow_html=True
)
r1[1].markdown(
    f"""
    <div class='kpi'>
      <div class='kTop'>
        <div class='kLeft'>{ico("timer")}<div class='klabel'>ACTIVITÉ</div></div>
      </div>
      <div class='kval'>{minutes} min</div>
      <div class='ksub'>Cumul {delta_chip(d_minutes,' min')}</div>
    </div>
    """,
    unsafe_allow_html=True
)
r1[2].markdown(
    f"""
    <div class='kpi'>
      <div class='kTop'>
        <div class='kLeft'>{ico("smile")}<div class='klabel'>BIEN-ÊTRE</div></div>
      </div>
      <div class='kval'>{h_m:.2f}</div>
      <div class='ksub'>Moyenne {delta_chip(d_hm)}</div>
    </div>
    """,
    unsafe_allow_html=True
)

r2 = st.columns(3, gap="large")
r2[0].markdown(
    f"""
    <div class='kpi'>
      <div class='kTop'>
        <div class='kLeft'>{ico("moon")}<div class='klabel'>SOMMEIL</div></div>
      </div>
      <div class='kval'>{sl_m:.2f} h</div>
      <div class='ksub'>Moyenne {delta_chip(d_slm,' h')}</div>
    </div>
    """,
    unsafe_allow_html=True
)
r2[1].markdown(
    f"""
    <div class='kpi'>
      <div class='kTop'>
        <div class='kLeft'>{ico("fire")}<div class='klabel'>RÉGULARITÉ</div></div>
      </div>
      <div class='kval'>{streak}</div>
      <div class='ksub'>Streak (jours)</div>
    </div>
    """,
    unsafe_allow_html=True
)
r2[2].markdown(
    f"""
    <div class='kpi'>
      <div class='kTop'>
        <div class='kLeft'>{ico("flag")}<div class='klabel'>SCORE GLOBAL</div></div>
      </div>
      <div class='kval'>{score}</div>
      <div class='ksub'>{status} {delta_chip(d_score)}</div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 19) POINTS FORTS / ATTENTION + NOTE
# ============================================================
forts, att = [], []

if d_minutes is not None:
    if d_minutes >= 60: forts.append("Activité en nette hausse (volume en progression).")
    if d_minutes <= -60: att.append("Activité en retrait (relance recommandée).")

if d_slm is not None:
    if d_slm >= 0.25: forts.append("Sommeil en amélioration.")
    if d_slm <= -0.25: att.append("Sommeil en baisse (risque sur énergie / récupération).")

if d_hm is not None:
    if d_hm >= 0.25: forts.append("Bien-être en progression.")
    if d_hm <= -0.25: att.append("Bien-être en baisse (surveiller charge / récupération).")

if d_score is not None:
    if d_score >= 5: forts.append("Score global en amélioration nette.")
    if d_score <= -5: att.append("Score global en baisse (actions à prioriser).")

if prev_score is None:
    forts = ["Base de comparaison : première période exploitable en cours de constitution."]
    att = ["Ajoutez quelques sessions pour fiabiliser les tendances."]

forts = forts[:3] or ["Indicateurs globalement stables."]
att = att[:3] or ["Aucun point d’attention majeur détecté."]

syn1 = f"Score global : {score}/100 ({status})."
if d_score is None:
    syn2 = "Évolution : non disponible (pas de période précédente). Priorités : activité & sommeil."
else:
    trend = "en progression" if d_score > 0 else ("stable" if d_score == 0 else "en repli")
    syn2 = f"Évolution : {('+' if d_score>=0 else '')}{d_score} point(s) vs période précédente ({trend}). Priorités : activité & sommeil."

cL, cR = st.columns([1.15, 1], gap="large")

with cL:
    forts_li = "".join([f"<li>{x}</li>" for x in forts])
    att_li = "".join([f"<li>{x}</li>" for x in att])
    md_html(f"""
    <div class='mask'>
      <div class="sTitle">{ico("trend")} Points forts</div>
      <ul class="sList" style="margin:0 0 10px 18px;padding:0;">{forts_li}</ul>

      <div style="height:10px"></div>
      <div style="height:1px;background:var(--line);"></div>
      <div style="height:10px"></div>

      <div class="sTitle">{ico("alert")} Points d’attention</div>
      <ul class="sList" style="margin:0 0 0 18px;padding:0;">{att_li}</ul>
    </div>
    """)

with cR:
    md_html(f"""
    <div class='mask'>
      <div class="sTitle">{ico("flag")} Synthèse</div>
      <div style="margin-top:6px;font-size:26px;font-weight:950;color:var(--ink);line-height:1.15">{syn1}</div>
      <div style="margin-top:10px;color:var(--muted);font-weight:850;line-height:1.55;font-size:14px">{syn2}</div>
    </div>
    """)

    show_note = st.button("📌 Ouvrir la note de synthèse (copier / exporter)", use_container_width=True)

    note_txt = (
        f"SYNTHÈSE — {APP_NAME}\n"
        f"Période analysée : {start_cur.strftime('%d/%m/%Y')} → {end_cur.strftime('%d/%m/%Y')}\n"
        f"Période de comparaison : {start_prev.strftime('%d/%m/%Y')} → {end_prev.strftime('%d/%m/%Y')}\n\n"
        f"{syn1}\n{syn2}\n\n"
        f"POINTS FORTS\n- " + "\n- ".join(forts) +
        f"\n\nPOINTS D’ATTENTION\n- " + "\n- ".join(att)
    )
    if show_note:
        st.text_area("Note synthèse", value=note_txt, height=260)


# ============================================================
# 20) ONGLETS (Activité / Bien-être & sommeil / Données)
# ============================================================
tab1, tab2, tab3 = st.tabs(["Activité", "Bien-être & sommeil", "Données"])

with tab1:
    d1 = df_cur.copy()
    d1["date"] = pd.to_datetime(d1["date"])
    st.line_chart(d1.groupby("date")["duree_min"].sum().sort_index(), use_container_width=True)

with tab2:
    d2 = df_cur.copy()
    d2["date"] = pd.to_datetime(d2["date"])
    cA, cB = st.columns(2, gap="large")
    with cA:
        st.line_chart(d2.set_index("date")["humeur"], use_container_width=True)
    with cB:
        st.line_chart(d2.set_index("date")["sommeil_h"], use_container_width=True)

with tab3:
    # Données : pas de recommandations ici
    df_for_table = df_all.copy()
    df_for_table["row_id"] = df_for_table.index
    df_for_table = df_for_table.sort_values("date", ascending=False).reset_index(drop=True)

    st.dataframe(df_for_table.drop(columns=["row_id"]), use_container_width=True, hide_index=True)

    rep = df_cur.groupby("activite")["duree_min"].sum().sort_values(ascending=False)
    st.bar_chart(rep, use_container_width=True)

    st.markdown("### Suppression de données")

    labels = []
    for _, r in df_for_table.iterrows():
        labels.append(
            f"[{int(r['row_id'])}] {r['date']} — {r['activite']} — {int(r['duree_min'])} min — bien-être {int(r['humeur'])}"
        )

    mode = st.radio(
        "Choisir le mode",
        ["Supprimer 1 ligne", "Supprimer plusieurs lignes", "Tout supprimer"],
        horizontal=True
    )

    if mode == "Supprimer 1 ligne":
        choice = st.selectbox("Sélectionner la ligne", labels)
        confirm = st.checkbox("Je confirme la suppression")
        if st.button("🗑️ Supprimer", disabled=not confirm):
            rid = int(choice.split("]")[0].replace("[", ""))
            df_new = df_all.drop(index=rid, errors="ignore").reset_index(drop=True)
            save_df(df_new)
            st.success("Ligne supprimée ✅")
            st.rerun()

    elif mode == "Supprimer plusieurs lignes":
        choices = st.multiselect("Sélectionner les lignes", labels)
        confirm = st.checkbox("Je confirme la suppression multiple")
        if st.button("🗑️ Supprimer la sélection", disabled=(not confirm or not choices)):
            rids = [int(c.split("]")[0].replace("[", "")) for c in choices]
            df_new = df_all.drop(index=rids, errors="ignore").reset_index(drop=True)
            save_df(df_new)
            st.success(f"{len(rids)} ligne(s) supprimée(s) ✅")
            st.rerun()

    else:
        st.warning("Action irréversible.")
        txt = st.text_input("Tapez SUPPRIMER TOUT pour confirmer")
        if st.button("🔥 Tout supprimer", disabled=(txt != "SUPPRIMER TOUT")):
            save_df(pd.DataFrame(columns=COLS))
            st.success("Toutes les données ont été supprimées ✅")
            st.rerun()

    e1, e2 = st.columns(2, gap="large")
    with e1:
        st.download_button(
            "Télécharger — période courante",
            data=df_cur.to_csv(index=False).encode("utf-8"),
            file_name=f"{APP_NAME.lower().replace(' ','_')}_export_{start_cur.strftime('%Y%m%d')}_{end_cur.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    with e2:
        if df_prev.empty:
            st.download_button(
                "Télécharger — période précédente",
                data=b"",
                file_name="prev.csv",
                mime="text/csv",
                disabled=True
            )
        else:
            st.download_button(
                "Télécharger — période précédente",
                data=df_prev.to_csv(index=False).encode("utf-8"),
                file_name=f"{APP_NAME.lower().replace(' ','_')}_export_prev_{start_prev.strftime('%Y%m%d')}_{end_prev.strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )


# ============================================================
# 21) RECOMMANDATIONS (hors onglet Données)
# ============================================================
reco = []
if minutes < 120:
    reco.append(("Priorité", "Planifier 2 sessions courtes (20–30 min) cette semaine."))
else:
    reco.append(("Maintien", "Alterner intensités (léger / modéré) pour soutenir la régularité."))
if sl_m < 7:
    reco.append(("Sommeil", "Stabiliser l’heure de coucher pour améliorer la récupération."))
if h_m <= 3:
    reco.append(("Bien-être", "Ajouter une séance douce + exposition extérieure (≥15 min)."))

reco_html = "".join(
    [f"<li style='margin-top:8px;color:var(--muted);font-weight:900'><b>✅ {t}</b> — {x}</li>" for t, x in reco[:4]]
)

md_html(f"""
<div class="mask">
  <div class="sTitle">{ico("trend")} Recommandations</div>
  <ul style="margin:0 0 0 18px;padding:0;">
    {reco_html}
  </ul>
</div>
""")


# ============================================================
# 22) FOOTER
# ============================================================
md_html(f"""
<div class="footer">
  <strong>{APP_NAME}</strong> — pilotage des habitudes & consolidation des indicateurs.
  <span style="float:right;">© {APP_NAME}</span>
</div>
""")
