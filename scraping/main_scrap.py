import requests
from bs4 import BeautifulSoup
import sys
import json
import os

def extract_main_text(html):
    page = BeautifulSoup(html, 'html.parser')

    # Se presente, estrae il titolo della pagina. Altrimenti "No Title"
    title = page.title.string if page.title else "No Title"

    # Rimuove elementi non utili che non contengono testo rilevante:
    # script, style (codice non visibile)
    # nav, footer, header, aside (menu, pubblicità, ecc)
    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    # Cerchiamo il <main>
    possible_main = page.find('main')
    
    if possible_main:
        # Se trova <main>, prende solo il testo al suo interno
        text = possible_main.get_text()
    else:
        # Altrimenti prende tutto il testo della pagina (potrebbe includere rumore)
        text = page.get_text()

    # Se ci sono spazi multipli e newline, li rimuove, sostituendoli con uno spazio singolo
    text = ' '.join(text.split())

    # Restituisce il testo pulito e il titolo
    return text, title


def download_html(url):
    """
    Funzione per scaricare il contenuto HTML di una pagina web da un URL
    """
    try:
        # Scarica la pagina con timeout di 10 secondi
        response = requests.get(url, timeout=10)
        # Lancia eccezione se la risposta HTTP non è OK (ad esempio 404)
        response.raise_for_status()
        # Restituisce il contenuto HTML come stringa
        return response.text
    
    except Exception as e:
        # Stampa errore in caso di problemi di rete o URL e restituisce stringa vuota
        print(f"Errore durante il download: {e}")
        return ""
    

def main():
    # Controlla che l'utente abbia passato esattamente un argomento (URL o file)
    if len(sys.argv) != 2:
        print("Uso: python main.py <URL o file>")
        sys.exit(1)

    arg = sys.argv[1]

    # Se l'argomento è un URL (http o https), scarica l'HTML
    if arg.startswith("http://") or arg.startswith("https://"):
        html = download_html(arg)

    # Altrimenti, se è un file esistente, lo legge
    elif os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            html = f.read()

    else:
        # Se non è URL né file, esce con errore
        print("Errore: l'argomento non è un URL valido né un file esistente.")
        sys.exit(1)

    # Estrae testo pulito e titolo dalla pagina HTML
    clean_text, title = extract_main_text(html)

    # Crea la cartella 'documents' se non esiste, dove salvare i testi
    os.makedirs("documents", exist_ok=True)

    # Crea un nome file univoco basato sul numero di file già presenti
    filename = f"articolo_{len(os.listdir('documents')) + 1}.txt"
    filepath = os.path.join("documents", filename)

    # Salva il testo pulito nel file appena creato
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # Costruisce il record da inserire nell'indice JSON
    record = {
        "filename": filename,
        "title": title,
        "url": arg,
        "metadata": {}
    }

    index_file = "index.json"
    # Se esiste già un file index.json, lo carica, altrimenti crea una lista vuota
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
    else:
        index_data = []

    # Aggiungi il nuovo record all'indice
    index_data.append(record)

    # Riscrivi index.json con il record aggiornato
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Salvato {filename} e aggiornato index.json")


if __name__ == "__main__":
    main()