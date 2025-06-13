import requests
from bs4 import BeautifulSoup
import sys
import json
import os

def extract_main_text(html):
    page = BeautifulSoup(html, 'html.parser')

    title = page.title.string if page.title else "No Title"

    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    possible_main = page.find('main')
    
    if possible_main:
        text = possible_main.get_text()
    else:
        text = page.get_text()

    text = ' '.join(text.split())
    return text, title

def download_html(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Errore durante il download: {e}")
        return ""

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python main.py <URL o file>")
        sys.exit(1)

    arg = sys.argv[1]

    if arg.startswith("http://") or arg.startswith("https://"):
        html = download_html(arg)
    elif os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        print("Errore: l'argomento non è un URL valido né un file esistente.")
        sys.exit(1)

    clean_text, title = extract_main_text(html)

    # Dai un nome univoco al file (es. basato su numero o timestamp)
    os.makedirs("documents", exist_ok=True)
    filename = f"articolo_{len(os.listdir('documents')) + 1}.txt"
    filepath = os.path.join("documents", filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # Costruisci l’entry per Tommy
    record = {
        "filename": filename,
        "title": title,
        "url": arg,
        "metadata": {}
    }

    index_file = "index.json"
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
    else:
        index_data = []

    index_data.append(record)

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Salvato {filename} e aggiornato index.json")