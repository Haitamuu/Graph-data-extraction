import markdown
import win32com.client
import os
import sys

def convert_md_to_pdf(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Create HTML
    html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
    # Add simple CSS for better looks
    html = f"""<html>
<head>
<meta charset='utf-8'>
<style>
    body {{ font-family: 'Segoe UI', Calibri, Arial, sans-serif; line-height: 1.5; padding: 2em; }}
    h1 {{ color: #14233C; }}
    h2 {{ color: #1F9E9A; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
    h3 {{ color: #E88A1A; }}
    code {{ font-family: Consolas, monospace; background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
    pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    pre code {{ background-color: transparent; padding: 0; }}
</style>
</head>
<body>
{html}
</body>
</html>"""
    
    html_path = os.path.abspath("temp_explication.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Use Word to convert HTML to PDF
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(html_path)
        doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17) # 17 is wdFormatPDF
        doc.Close()
        word.Quit()
        print(f"Saved PDF to {pdf_path}")
    except Exception as e:
        print("Error during Word conversion:", e)
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)

if __name__ == "__main__":
    convert_md_to_pdf(
        r"C:\Users\hsour\.gemini\antigravity\brain\530f1d87-a205-4254-8c38-3e12bf4bad44\explication_technique_main.md",
        "explication_technique.pdf"
    )
