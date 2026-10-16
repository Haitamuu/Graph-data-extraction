from pathlib import Path

bat_content = """@echo off
echo ===================================================
echo   Push Resume to GitHub
echo ===================================================
echo.
set /p REPO_URL="Enter your GitHub repository URL (e.g., https://github.com/Haitamuu/resume-latex.git): "
if "%REPO_URL%"=="" (
    echo Repository URL cannot be empty.
    pause
    exit /b 1
)

echo.
echo Initializing Git repository...
git init
git add .
git commit -m "feat: initial commit of modular LaTeX resume with automated CI/CD"
git branch -M main
git remote remove origin 2>nul
git remote add origin %REPO_URL%
echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo ===================================================
echo Done! Your resume is now live on GitHub.
echo ===================================================
pause
"""

Path(r"c:\Users\hsour\OneDrive\Desktop\Stage\resume-latex\push_to_github.bat").write_text(bat_content, encoding="utf-8")
print("Created push_to_github.bat")
