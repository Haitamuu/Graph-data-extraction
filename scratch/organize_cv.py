import os
import shutil
from pathlib import Path

DEST_DIR = Path(r"c:\Users\hsour\OneDrive\Desktop\Stage\resume-latex")
SRC_DIR = Path(r"c:\Users\hsour\OneDrive\Desktop\Stage")

# Ensure subdirectories exist
(DEST_DIR / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
(DEST_DIR / "sections").mkdir(parents=True, exist_ok=True)
(DEST_DIR / "pdf").mkdir(parents=True, exist_ok=True)

# 1. Preamble
PREAMBLE_CONTENT = r"""% ==============================================================================
% PREAMBLE: PACKAGES, FONTS, COLORS & CUSTOM MACROS
% ==============================================================================

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

% Icons (FontAwesome 5)
\usepackage{fontawesome5}

% Monospace font
\usepackage[scale=0.90,lf]{FiraMono}

% Primary typography: Helvetica-style TeX Gyre Heros
\usepackage{tgheros}
\renewcommand*\familydefault{\sfdefault}

% Custom underline utilities
\usepackage{contour}
\usepackage[normalem]{ulem}
\renewcommand{\ULdepth}{1.8pt}
\contourlength{0.8pt}
\newcommand{\myuline}[1]{%
  \uline{\phantom{#1}}%
  \llap{\contour{white}{#1}}%
}

% Color definitions
\definecolor{light-grey}{gray}{0.83}
\definecolor{dark-grey}{gray}{0.3}
\definecolor{text-grey}{gray}{.08}

\DeclareRobustCommand{\ebseries}{\fontseries{eb}\selectfont}
\DeclareTextFontCommand{\texteb}{\ebseries}

% Header & footer setup
\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Page geometry: adjusted to guarantee a compact 1-page layout
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.6in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-0.9in}
\addtolength{\textheight}{1.8in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Section styling (sans-serif with light horizontal rule)
\titleformat{\section}{
  \bfseries \vspace{-4pt} \raggedright \large
}{}{0em}{}[\color{light-grey} {\titlerule[1.5pt]} \vspace{-6pt}]

% ==============================================================================
% CUSTOM RESUME COMMANDS (optimized spacing)
% ==============================================================================

\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2.5pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-3pt}\item
    \begin{tabular*}{\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & {\color{dark-grey}\small #2}\vspace{1pt}\\
      \textit{#3} & {\color{dark-grey}\small #4}\\
    \end{tabular*}\vspace{-6pt}
}

\newcommand{\resumeProjectHeading}[2]{
  \vspace{-3pt}\item
    \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
      #1 & {\color{dark-grey} #2} \\
    \end{tabular*}\vspace{-6pt}
}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\color{text-grey}

% PDF Metadata
\hypersetup{
  pdftitle={Ourtane Haitam Safouane - CV},
  pdfauthor={Haitam Safouane OURTANE},
  pdfkeywords={Data Science, Machine Learning, Quantitative Research, Software Engineering, Python},
  pdfcreator={LaTeX},
  pdfproducer={pdfLaTeX}
}
"""

# 2. Main modular file
MAIN_CONTENT = r"""\documentclass[letterpaper,11pt]{article}

% Load custom styling, packages, and commands
\input{preamble}

\begin{document}

%---------- HEADING / CONTACT ----------
\input{sections/00_heading}

%---------- EDUCATION ----------
\input{sections/01_education}

%---------- EXPERIENCE ----------
\input{sections/02_experience}

%---------- PROJECTS ----------
\input{sections/03_projects}

%---------- COMPETITIONS ----------
\input{sections/04_competitions}

%---------- SKILLS ----------
\input{sections/05_skills}

\end{document}
"""

# 3. Sections
HEADING_CONTENT = r"""% ==============================================================================
% HEADER / CONTACT INFORMATION
% ==============================================================================

\begin{center}
  \textbf{\Huge Haitam Safouane OURTANE} \\ \vspace{5pt}
  \small
  \faPhone* \href{tel:+33743669375}{\texttt{+33743669375}} \hspace{2pt} $|$ \hspace{2pt}
  \faEnvelope \hspace{2pt} \href{mailto:haitam.safouane.ourtane@gmail.com}{\texttt{haitam.safouane.ourtane@gmail.com}} \hspace{2pt} $|$ \hspace{2pt}
  \faLinkedin \hspace{2pt} \href{https://www.linkedin.com/in/haitam-safouane-ourtane/}{\texttt{LinkedIn}} \hspace{2pt} $|$ \hspace{2pt}
  \faGithub \hspace{2pt} \href{https://github.com/Haitamuu/}{\texttt{GitHub}}
  \\ \vspace{-4pt}
\end{center}
"""

EDUCATION_CONTENT = r"""% ==============================================================================
% EDUCATION
% ==============================================================================

\section{EDUCATION}
\resumeSubHeadingListStart

  \resumeSubheading
    {Mines Saint-Étienne}{Aug 2025 -- Sep 2028}
    {Master of Science in Engineering}{Saint-Étienne, France}
    \resumeItemListStart
      \resumeItem{\textbf{Major}: Data Science}
      \resumeItem{\textbf{Minor}: Paradigms for discrete problem solving, Structured Data Management, Tools and risk analysis, High performance computing, AI and image processing}
      \resumeItem{\textbf{Coursework}: Statistics, Algorithms, Machine Learning, Mathematics, Operational Research}
    \resumeItemListEnd

  \resumeSubheading
    {Université Jean Monnet}{Oct 2025 -- Oct 2026}
    {Final year of Bachelor in Mathematics}{Saint-Étienne, France}
    \resumeItemListStart
      \resumeItem{\textbf{Coursework}: Statistics, Linear Algebra, Probability, Universal Algebra}
    \resumeItemListEnd

  \resumeSubheading
    {Lycée d'Excellence Mohammed VI}{Sep 2023 -- Jun 2025}
    {Preparatory Classes (CPGE)}{Benguerir, Morocco}
    \resumeItemListStart
      \resumeItem{\textbf{Coursework}: Two years intensive program in advanced mathematics (calculus, linear algebra, probability), physics, sciences of engineering}
    \resumeItemListEnd

\resumeSubHeadingListEnd
"""

EXPERIENCE_CONTENT = r"""% ==============================================================================
% EXPERIENCE
% ==============================================================================

\section{EXPERIENCE}
\resumeSubHeadingListStart

  \resumeSubheading
    {Bank Al-Maghrib}{Aug 2026}
    {Data Engineer Intern}{Rabat, Morocco}
    \resumeItemListStart
      \resumeItem{Collaborated with senior data engineers in the Department of Statistics and Data Management.}
      \resumeItem{Automated data extraction workflows from PDF documents by implementing Python machine learning libraries, significantly reducing manual processing time.}
      \resumeItem{Refined and cross-referenced multi-source datasets containing 3000+ records by applying the \textbf{Levenshtein distance} algorithm, boosting data accuracy to 95\% and resolving hundreds of duplicate entries.}
      \resumeItem{Engineered efficient web scraping scripts to harvest and structure critical data from official web pages.}
      \resumeItem{Integrated the Windows API via Python to automate daily system-level tasks, achieving a 100\% reduction in routine data-entry bottlenecks and accelerating pipeline execution.}
    \resumeItemListEnd

\resumeSubHeadingListEnd
"""

PROJECTS_CONTENT = r"""% ==============================================================================
% PROJECTS
% ==============================================================================

\section{PROJECTS}
\resumeSubHeadingListStart

  \resumeProjectHeading
    {\textbf{Automated Curve Extraction Pipeline} $|$ \emph{\small Python, OpenCV, Scikit-Learn, SciPy}}{Sep 2025 -- Nov 2025}
    \resumeItemListStart
      \resumeItem{Built a \textbf{100\% automated} batch computer vision pipeline to extract and digitize multi-curve figures from scanned scientific papers, eliminating 100\% of manual point-clicking overhead.}
      \resumeItem{Calibrated physical axes via \textbf{4x bicubic upscaling}, dual-pass \textbf{EasyOCR}, and a custom \textbf{RANSAC} consensus model ($\le$ \textbf{4\% error tolerance}), eliminating OCR hallucinations and outliers.}
      \resumeItem{Segmented curves using \textbf{MeanShift} on 3000+ pixel samples (cyclical HSV) and 40px morphological kernels; decoupled continuous lines from discrete markers via \textbf{NCC} matching and \textbf{Savitzky-Golay} filtering.}
    \resumeItemListEnd

  \resumeProjectHeading
    {\textbf{Brasse Solidaire}}{Sep 2025 -- Apr 2026}
    \resumeItemListStart
      \resumeItem{Organized a charity sports event in partnership with UNICEF Loire, SEAM (the aquatic club of Saint-Étienne), and the City Council to raise community awareness regarding global children's rights.}
    \resumeItemListEnd

  \resumeProjectHeading
    {\textbf{Pre-Plancks Morocco, Event Manager}}{Dec 2025}
    \resumeItemListStart
      \resumeItem{Partnered with UM6P to successfully coordinate and execute the national preliminaries for the PLANCKS 2026 physics competition.}
      \resumeItem{Directed a partnership with MathsMaroc to provide advanced training, ensuring the winning teams were fully prepared for the international finals in the Netherlands.}
    \resumeItemListEnd

\resumeSubHeadingListEnd
"""

COMPETITIONS_CONTENT = r"""% ==============================================================================
% COMPETITIONS & ACHIEVEMENTS
% ==============================================================================

\section{COMPETITIONS}
\resumeSubHeadingListStart

  \resumeProjectHeading
    {\textbf{PLANCKS 2025}}{May 2025}
    \resumeItemListStart
      \resumeItem{Secured 1st place nationally in Morocco and ranked 25th out of 50 teams globally, successfully outperforming Master's-level competitors as a second-year undergraduate.}
    \resumeItemListEnd

  \resumeProjectHeading
    {\textbf{MMC (Moroccan Mathematics Competition)}}{Aug 2025}
    \resumeItemListStart
      \resumeItem{Competed in a national mathematics competition for college students, tackling advanced, university-level problem-solving under strict time constraints.}
    \resumeItemListEnd

\resumeSubHeadingListEnd
"""

SKILLS_CONTENT = r"""% ==============================================================================
% TECHNICAL & LANGUAGE SKILLS
% ==============================================================================

\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}]
  \small{\item{
    \textbf{Programming Languages}{: Python (top 20\% in the world in Project Euler), Java, SQL (MySQL), R.}\vspace{2pt} \\
    \textbf{Languages}{: French (C1), English (C1), Arabic (Native)}
  }}
\end{itemize}
"""

# 4. Standalone single file (all-in-one)
STANDALONE_CONTENT = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

% Icons (FontAwesome 5)
\usepackage{fontawesome5}

% Monospace font
\usepackage[scale=0.90,lf]{FiraMono}

% Color definitions
\definecolor{light-grey}{gray}{0.83}
\definecolor{dark-grey}{gray}{0.3}
\definecolor{text-grey}{gray}{.08}

\DeclareRobustCommand{\ebseries}{\fontseries{eb}\selectfont}
\DeclareTextFontCommand{\texteb}{\ebseries}

% Custom underline
\usepackage{contour}
\usepackage[normalem]{ulem}
\renewcommand{\ULdepth}{1.8pt}
\contourlength{0.8pt}
\newcommand{\myuline}[1]{%
  \uline{\phantom{#1}}%
  \llap{\contour{white}{#1}}%
}

% Typography: Helvetica-style
\usepackage{tgheros}
\renewcommand*\familydefault{\sfdefault}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Margins tailored for a perfect single-page layout
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.6in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-0.9in}
\addtolength{\textheight}{1.8in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sans-serif sections
\titleformat{\section}{
  \bfseries \vspace{-4pt} \raggedright \large
}{}{0em}{}[\color{light-grey} {\titlerule[1.5pt]} \vspace{-6pt}]

% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2.5pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-3pt}\item
    \begin{tabular*}{\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & {\color{dark-grey}\small #2}\vspace{1pt}\\
      \textit{#3} & {\color{dark-grey}\small #4}\\
    \end{tabular*}\vspace{-6pt}
}

\newcommand{\resumeProjectHeading}[2]{
  \vspace{-3pt}\item
    \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
      #1 & {\color{dark-grey} #2} \\
    \end{tabular*}\vspace{-6pt}
}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\color{text-grey}

\hypersetup{
  pdftitle={Ourtane Haitam Safouane - CV},
  pdfauthor={Haitam Safouane OURTANE},
  pdfkeywords={Data Science, Machine Learning, Quantitative Research, Software Engineering, Python},
  pdfcreator={LaTeX},
  pdfproducer={pdfLaTeX}
}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{document}

%----------HEADING----------
\begin{center}
  \textbf{\Huge Haitam Safouane OURTANE} \\ \vspace{5pt}
  \small
  \faPhone* \href{tel:+33743669375}{\texttt{+33743669375}} \hspace{2pt} $|$ \hspace{2pt}
  \faEnvelope \hspace{2pt} \href{mailto:haitam.safouane.ourtane@gmail.com}{\texttt{haitam.safouane.ourtane@gmail.com}} \hspace{2pt} $|$ \hspace{2pt}
  \faLinkedin \hspace{2pt} \href{https://www.linkedin.com/in/haitam-safouane-ourtane/}{\texttt{LinkedIn}} \hspace{2pt} $|$ \hspace{2pt}
  \faGithub \hspace{2pt} \href{https://github.com/Haitamuu/}{\texttt{GitHub}}
  \\ \vspace{-4pt}
\end{center}

%-----------EDUCATION-----------
\section{EDUCATION}
\resumeSubHeadingListStart
  \resumeSubheading
    {Mines Saint-Étienne}{Aug 2025 -- Sep 2028}
    {Master of Science in Engineering}{Saint-Étienne, France}
    \resumeItemListStart
      \resumeItem{\textbf{Major}: Data Science}
      \resumeItem{\textbf{Minor}: Paradigms for discrete problem solving, Structured Data Management, Tools and risk analysis, High performance computing, AI and image processing}
      \resumeItem{\textbf{Coursework}: Statistics, Algorithms, Machine Learning, Mathematics, Operational Research}
    \resumeItemListEnd

  \resumeSubheading
    {Université Jean Monnet}{Oct 2025 -- Oct 2026}
    {Final year of Bachelor in Mathematics}{Saint-Étienne, France}
    \resumeItemListStart
      \resumeItem{\textbf{Coursework}: Statistics, Linear Algebra, Probability, Universal Algebra}
    \resumeItemListEnd

  \resumeSubheading
    {Lycée d'Excellence Mohammed VI}{Sep 2023 -- Jun 2025}
    {Preparatory Classes (CPGE)}{Benguerir, Morocco}
    \resumeItemListStart
      \resumeItem{\textbf{Coursework}: Two years intensive program in advanced mathematics (calculus, linear algebra, probability), physics, sciences of engineering}
    \resumeItemListEnd
\resumeSubHeadingListEnd

%-----------EXPERIENCE-----------
\section{EXPERIENCE}
\resumeSubHeadingListStart
  \resumeSubheading
    {Bank Al-Maghrib}{Aug 2026}
    {Data Engineer Intern}{Rabat, Morocco}
    \resumeItemListStart
      \resumeItem{Collaborated with senior data engineers in the Department of Statistics and Data Management.}
      \resumeItem{Automated data extraction workflows from PDF documents by implementing Python machine learning libraries, significantly reducing manual processing time.}
      \resumeItem{Refined and cross-referenced multi-source datasets containing 3000+ records by applying the \textbf{Levenshtein distance} algorithm, boosting data accuracy to 95\% and resolving hundreds of duplicate entries.}
      \resumeItem{Engineered efficient web scraping scripts to harvest and structure critical data from official web pages.}
      \resumeItem{Integrated the Windows API via Python to automate daily system-level tasks, achieving a 100\% reduction in routine data-entry bottlenecks and accelerating pipeline execution.}
    \resumeItemListEnd
\resumeSubHeadingListEnd

%-----------PROJECTS-----------
\section{PROJECTS}
\resumeSubHeadingListStart
  \resumeProjectHeading
    {\textbf{Automated Curve Extraction Pipeline} $|$ \emph{\small Python, OpenCV, Scikit-Learn, SciPy}}{Sep 2025 -- Nov 2025}
    \resumeItemListStart
      \resumeItem{Built a \textbf{100\% automated} batch computer vision pipeline to extract and digitize multi-curve figures from scanned scientific papers, eliminating 100\% of manual point-clicking overhead.}
      \resumeItem{Calibrated physical axes via \textbf{4x bicubic upscaling}, dual-pass \textbf{EasyOCR}, and a custom \textbf{RANSAC} consensus model ($\le$ \textbf{4\% error tolerance}), eliminating OCR hallucinations and outliers.}
      \resumeItem{Segmented curves using \textbf{MeanShift} on 3000+ pixel samples (cyclical HSV) and 40px morphological kernels; decoupled continuous lines from discrete markers via \textbf{NCC} matching and \textbf{Savitzky-Golay} filtering.}
    \resumeItemListEnd

  \resumeProjectHeading
    {\textbf{Brasse Solidaire}}{Sep 2025 -- Apr 2026}
    \resumeItemListStart
      \resumeItem{Organized a charity sports event in partnership with UNICEF Loire, SEAM (the aquatic club of Saint-Étienne), and the City Council to raise community awareness regarding global children's rights.}
    \resumeItemListEnd

  \resumeProjectHeading
    {\textbf{Pre-Plancks Morocco, Event Manager}}{Dec 2025}
    \resumeItemListStart
      \resumeItem{Partnered with UM6P to successfully coordinate and execute the national preliminaries for the PLANCKS 2026 physics competition.}
      \resumeItem{Directed a partnership with MathsMaroc to provide advanced training, ensuring the winning teams were fully prepared for the international finals in the Netherlands.}
    \resumeItemListEnd
\resumeSubHeadingListEnd

%-----------COMPETITIONS-----------
\section{COMPETITIONS}
\resumeSubHeadingListStart
  \resumeProjectHeading
    {\textbf{PLANCKS 2025}}{May 2025}
    \resumeItemListStart
      \resumeItem{Secured 1st place nationally in Morocco and ranked 25th out of 50 teams globally, successfully outperforming Master's-level competitors as a second-year undergraduate.}
    \resumeItemListEnd

  \resumeProjectHeading
    {\textbf{MMC (Moroccan Mathematics Competition)}}{Aug 2025}
    \resumeItemListStart
      \resumeItem{Competed in a national mathematics competition for college students, tackling advanced, university-level problem-solving under strict time constraints.}
    \resumeItemListEnd
\resumeSubHeadingListEnd

%-----------PROGRAMMING SKILLS-----------
\section{SKILLS}
\begin{itemize}[leftmargin=0in, label={}]
  \small{\item{
    \textbf{Programming Languages}{: Python (top 20\% in the world in Project Euler), Java, SQL (MySQL), R.}\vspace{2pt} \\
    \textbf{Languages}{: French (C1), English (C1), Arabic (Native)}
  }}
\end{itemize}

\end{document}
"""

# 5. .gitignore
GITIGNORE_CONTENT = r"""# ==============================================================================
# LaTeX auxiliary and build files
# ==============================================================================
*.aux
*.bbl
*.bcf
*.blg
*.dvi
*.fdb_latexmk
*.fls
*.glg
*.glo
*.gls
*.idx
*.ilg
*.ind
*.ist
*.log
*.nav
*.out
*.run.xml
*.snm
*.synctex.gz
*.toc
*.vrb
*.xdv
*.upa
*.upb

# TeX temporary and minted files
_minted*
*.loa
*.lof
*.lot
*.maf
*.mtc*

# OS-specific files
.DS_Store
Thumbs.db
Desktop.ini

# Editor / IDE configs
.vscode/
.idea/
*.swp
*~
"""

# 6. GitHub Actions Workflow
WORKFLOW_CONTENT = r"""name: Build and Release Resume PDF

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build_latex:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Compile LaTeX Document
        uses: xu-cheng/latex-action@v3
        with:
          root_file: main.tex
          latexmk_use_pdflatex: true

      - name: Rename Output PDF
        run: |
          mkdir -p dist
          cp main.pdf dist/Haitam_Safouane_Ourtane_CV.pdf

      - name: Upload PDF Artifact
        uses: actions/upload-artifact@v4
        with:
          name: Haitam_Safouane_Ourtane_CV
          path: dist/Haitam_Safouane_Ourtane_CV.pdf

      - name: Release Latest PDF (on push to main)
        if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
        uses: softprops/action-gh-release@v2
        with:
          tag_name: latest
          name: "Latest CV Release"
          draft: false
          prerelease: false
          files: dist/Haitam_Safouane_Ourtane_CV.pdf
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        continue-on-error: true
"""

# 7. README.md
README_CONTENT = r"""# 📄 Haitam Safouane OURTANE — Curriculum Vitae (LaTeX)

<div align="center">

[![Build Resume](https://github.com/Haitamuu/resume-latex/actions/workflows/compile.yml/badge.svg)](https://github.com/Haitamuu/resume-latex/actions/workflows/compile.yml)
[![Download PDF](https://img.shields.io/badge/Download-PDF-red?logo=adobeacrobatreader&logoColor=white)](./Haitam_Safouane_Ourtane_CV.pdf)
[![LaTeX](https://img.shields.io/badge/LaTeX-pdfLaTeX-blue?logo=latex&logoColor=white)](https://www.latex-project.org/)
[![ATS Friendly](https://img.shields.io/badge/ATS-Optimized-brightgreen)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A modular, modern, single-page Curriculum Vitae written in LaTeX with automated GitHub Actions CI/CD.**

[**📥 Download Latest PDF**](./Haitam_Safouane_Ourtane_CV.pdf) • [**🌐 LinkedIn**](https://www.linkedin.com/in/haitam-safouane-ourtane/) • [**💻 GitHub**](https://github.com/Haitamuu/)

</div>

---

## 🌟 Key Features

- **Modular Architecture**: Separates preamble, macros, and individual CV sections (`education`, `experience`, `projects`, etc.) for clean version control and friction-free updates.
- **ATS-Friendly**: Standard headings, clean tabular alignment, semantic metadata, and selectable text without invisible artifacts.
- **Strict 1-Page Geometry**: Tuned margins, responsive padding, and tight vertical spacing guaranteed to fit on a single page.
- **Automated CI/CD**: Powered by GitHub Actions (`xu-cheng/latex-action`), compiling a fresh PDF and publishing a release on every `push`.
- **Dual Support**: Includes both the modular source (`main.tex` + `sections/`) and a standalone self-contained file (`main_single.tex`) for instant Overleaf compatibility.

---

## 📂 Project Structure

```text
resume-latex/
├── .github/
│   └── workflows/
│       └── compile.yml            # CI/CD: Automated compilation to PDF on push
├── sections/                      # Modular CV components
│   ├── 00_heading.tex             # Name, phone, email, LinkedIn, GitHub
│   ├── 01_education.tex           # Mines Saint-Étienne, Université Jean Monnet, CPGE
│   ├── 02_experience.tex          # Bank Al-Maghrib internship
│   ├── 03_projects.tex            # Curve Extraction, Brasse Solidaire, Pre-Plancks
│   ├── 04_competitions.tex        # PLANCKS 2025, Moroccan Math Competition
│   └── 05_skills.tex              # Programming & natural languages
├── preamble.tex                   # Packages, custom fonts, colors & custom commands
├── main.tex                       # Root LaTeX entry point (modular)
├── main_single.tex                # Standalone single-file version (Overleaf-ready)
├── Haitam_Safouane_Ourtane_CV.pdf # Precompiled PDF preview
├── .gitignore                     # Comprehensive LaTeX auxiliary file filter
├── LICENSE                        # MIT License
└── README.md                      # Documentation & instructions
```

---

## 🚀 How to Use & Compile

### Option 1: Automatic Cloud Build (GitHub Actions)
1. Fork or push this repository to GitHub.
2. Every time you push an update to `main`, GitHub Actions will automatically compile `main.tex` into a PDF.
3. Download your updated PDF from the **Actions** tab artifacts or the **Releases** page!

### Option 2: Overleaf
1. Compress this folder as a `.zip` file (or clone directly via Overleaf Git Integration).
2. Create a new project in [Overleaf](https://www.overleaf.com/) and upload the `.zip`.
3. Set compiler to `pdfLaTeX` (default) and compile `main.tex` (or `main_single.tex`).

### Option 3: Local Compilation
Ensure you have a LaTeX distribution installed (TeX Live, MacTeX, or MiKTeX):

```bash
# Using latexmk (recommended)
latexmk -pdf main.tex

# Or using pdflatex directly
pdflatex main.tex
```

To clean auxiliary files after building:
```bash
latexmk -c
```

---

## 🛠️ Step-by-Step: Pushing to GitHub

To publish this folder to your GitHub account:

```bash
# 1. Navigate to the resume directory
cd resume-latex

# 2. Initialize a git repository
git init

# 3. Add all files
git add .

# 4. Commit your changes
git commit -m "feat: initial commit of modular LaTeX resume with CI/CD"

# 5. Link to your GitHub repository (replace with your repo URL)
git branch -M main
git remote add origin https://github.com/Haitamuu/resume-latex.git

# 6. Push to GitHub
git push -u origin main
```

---

## 📄 License

This template is open-sourced under the [MIT License](LICENSE). You are welcome to customize and use it for your own resume.
"""

# 8. LICENSE (MIT)
LICENSE_CONTENT = r"""MIT License

Copyright (c) 2026 Haitam Safouane OURTANE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Write all files using UTF-8 encoding
files_to_write = {
    DEST_DIR / "preamble.tex": PREAMBLE_CONTENT,
    DEST_DIR / "main.tex": MAIN_CONTENT,
    DEST_DIR / "sections" / "00_heading.tex": HEADING_CONTENT,
    DEST_DIR / "sections" / "01_education.tex": EDUCATION_CONTENT,
    DEST_DIR / "sections" / "02_experience.tex": EXPERIENCE_CONTENT,
    DEST_DIR / "sections" / "03_projects.tex": PROJECTS_CONTENT,
    DEST_DIR / "sections" / "04_competitions.tex": COMPETITIONS_CONTENT,
    DEST_DIR / "sections" / "05_skills.tex": SKILLS_CONTENT,
    DEST_DIR / "main_single.tex": STANDALONE_CONTENT,
    DEST_DIR / ".gitignore": GITIGNORE_CONTENT,
    DEST_DIR / ".github" / "workflows" / "compile.yml": WORKFLOW_CONTENT,
    DEST_DIR / "README.md": README_CONTENT,
    DEST_DIR / "LICENSE": LICENSE_CONTENT,
}

for path, content in files_to_write.items():
    path.write_text(content, encoding="utf-8")
    print(f"Created: {path}")

# Also copy PDF if available
pdf_src = SRC_DIR / "Haitam Safouane Ourtane CV.pdf"
if pdf_src.exists():
    shutil.copy2(pdf_src, DEST_DIR / "Haitam_Safouane_Ourtane_CV.pdf")
    shutil.copy2(pdf_src, DEST_DIR / "pdf" / "Haitam_Safouane_Ourtane_CV.pdf")
    print("Copied CV PDF")

# Also update the original main.tex with the cleaned standalone version to fix character encoding bugs
orig_main = SRC_DIR / "main.tex"
orig_main.write_text(STANDALONE_CONTENT, encoding="utf-8")
print(f"Updated original: {orig_main}")

print("All tasks completed successfully!")
