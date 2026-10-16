# Extraction Automatique de Courbes Expérimentales

Projet Technique - 2ème Année Ingénieur Civil des Mines (Mines Saint-Étienne).

Pipeline automatisé en Python permettant d'extraire, calibrer et numériser des courbes scientifiques et tracés expérimentaux à partir de figures scannées ou capturées.

---

## 📁 Structure du Projet

```text
pro tech/
│
├── main.py                     # Script principal d'exécution par lot
├── requirements.txt            # Dépendances Python requises
├── README.md                   # Documentation générale du projet
│
├── images/                     # Dossier d'entrée : figures et graphiques scannés
│   ├── Curve_points.png
│   ├── Data_points.png
│   ├── image082.png
│   └── test_graph.png
│
├── data/                       # Dossier de sortie : données extraites et vérifications
│   ├── *_donnees.xlsx          # Tableaux Excel (colonnes X et Y côte à côte)
│   └── *_verification.png      # Comparatif côte à côte (original vs données extraites)
│
├── docs/                       # Documentation technique et rapports
│   └── explication_technique.pdf
│
├── presentation/               # Supports de soutenance et scripts de génération
│   ├── build_pptx.py           # Générateur automatique des diapositives
│   └── Extraction_automatique_de_courbes_v*.pptx
│
├── scratch/                    # Scripts de test, visualisations intermédiaires et debug
└── archives/                   # Anciennes versions, prototypes et historiques
```

---

## 🚀 Installation & Utilisation

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Exécution du traitement

Traitement automatique de toutes les images contenues dans `images/` :

```bash
python main.py
```

Options disponibles pour spécifier d'autres répertoires :

```bash
python main.py --input images/ --output data/
```

---

## ⚙️ Architecture du Pipeline (`main.py`)

1. **Prétraitement & OCR des axes :**
   - Détection des graduations textuelles et numériques via EasyOCR.
   - Régression linéaire robuste (RANSAC) pour calibrer la transformation pixels $\to$ unités physiques.
   - Gestion des replis automatiques en cas d'absence de graduations lisibles.

2. **Extraction des légendes :**
   - Localisation des pastilles et libellés textuels.
   - Appariement glouton couleur pastille $\leftrightarrow$ courbe par distance euclidienne RGB.

3. **Segmentation des courbes :**
   - Courbes colorées : clustering non supervisé (MeanShift sur composantes HSV cycliques).
   - Courbes achromatiques (noir/gris) : filtrage morphologique soustractif éliminant les axes, grilles et textes.

4. **Découplage Modèle Continu / Mesures Expérimentales :**
   - **Nuages de points purs :** détection par analyse de compacité et centroids.
   - **Courbes continues :** profil moyen $y = f(x)$.
   - **Courbes mixtes (modèle fitting + marqueurs superposés) :**
     - Détection exhaustive des marqueurs via template matching guidé et analyse morphologique.
     - Soustraction locale des marqueurs pour éviter toute déformation de la ligne continue.
     - Lissage Savitzky-Golay adapté préservant les bornes physiques ($Y \in [0, 1]$).

5. **Export & Contrôle :**
   - Tableur Excel (`*_donnees.xlsx`) avec colonnes $X$ immédiatement adjacentes aux colonnes $Y$.
   - Figure de contrôle (`*_verification.png`) superposant l'image originale et le tracé reconstitué.
