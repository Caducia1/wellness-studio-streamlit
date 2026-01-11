# Wellness Studio

## Objectif du projet
Wellness Studio est une application web développée en Python avec Streamlit.
Elle permet de suivre des habitudes liées au sport et au bien-être, en enregistrant
des sessions d’activité, de sommeil et de ressenti personnel.

L’objectif est de proposer un tableau de bord simple et visuel pour analyser
l’évolution de ses habitudes sur différentes périodes.

---

## Fonctionnalités principales
- Saisie de sessions (activité, durée, intensité, bien-être, sommeil)
- Enregistrement automatique des données dans un fichier CSV
- Filtrage par période, activité et seuil de bien-être
- Calcul d’indicateurs clés (temps d’activité, moyennes, score global)
- Comparaison automatique avec la période précédente
- Visualisation des données sous forme de graphiques et tableaux
- Export des données au format CSV
- Suppression d'une ou plusieurs sessions enregistrées

---

## Technologies utilisées
- Python 3
- Streamlit
- Pandas

---

## ▶️ Lancement de l’application (en local)

1. Se placer dans le dossier du projet :

cd SportApp

Installer les dépendances :
pip install -r requirements.txt

Lancer l’application :
streamlit run app.py

L’application s’ouvre automatiquement dans le navigateur.

📁 Structure du projet
.
├── app.py              # Application Streamlit principale
├── data/
│   └── bienetre.csv    # Données des sessions
├── assets/             # Images de fond
├── requirements.txt    # Dépendances Python
└── README.md
