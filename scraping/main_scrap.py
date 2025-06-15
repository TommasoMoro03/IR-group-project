import sys
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def extract_main_text(html):
    """
    Funzione per estrarre e pulire il testo principale e il titolo da una pagina HTML.
    """
    page = BeautifulSoup(html, 'html.parser')

    # Se presente, estrae il titolo della pagina. Altrimenti "No Title"
    title = page.title.string if page.title else "No Title"

    # Rimuove elementi non utili che non contengono testo rilevante:
    # script, style (codice non visibile)
    # nav, footer, header, aside (menu, pubblicità, ecc)
    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    # Cerca il <main>
    possible_main = page.find('main')
    
    # Estrae tutti i paragrafi dal <main>, se presente
    if possible_main:
        paragraphs = possible_main.find_all('p')
    else:
        paragraphs = page.find_all('p')

    # Pulisce ogni paragrafo e li mette su righe separate
    clean_paragraphs = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]

    # Unisce i paragrafi con una newline
    text = '\n\n'.join(clean_paragraphs)

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
    

def get_category():
    """
    Chiede all'utente di inserire una categoria valida non vuota.
    """
    while True:
        category = input("Categoria dell'articolo (es: politica, esteri, scienza...): ").strip()
        if category:
            return category
        print("Inserisci una categoria valida.")


def get_date():
    """
    Chiede all'utente di inserire una data valida nel formato YYYY-MM-DD.
    """
    while True:
        date = input("Data dell'articolo (formato YYYY-MM-DD): ").strip()
        try:
            # Prova a convertire la stringa in una data vera
            datetime.strptime(date, "%Y-%m-%d")
            # Se la data è valida, esce dal ciclo e restituisce la data
            return date
        except ValueError:   
            # Se la data non è valida, ripete il ciclo
            print("Formato data non valido, riprova.")


def get_next_filename(folder="documents", prefix="articolo_", ext=".txt"):
    """
    Calcola il nome del prossimo file da salvare in modo progressivo e senza duplicati.
    """
    os.makedirs(folder, exist_ok=True)  # crea la cartella se non esiste

    # Lista file nella cartella che rispettano il formato nome
    files = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(ext)]

    # Estrai numeri progressivi dai nomi file
    nums = []
    for f in files:
        num_part = f[len(prefix):-len(ext)]
        if num_part.isdigit():
            nums.append(int(num_part))

    next_num = max(nums) + 1 if nums else 1
    filename = f"{prefix}{next_num:03d}{ext}"
    return filename


def main():
    """
    Funzione principale che gestisce il flusso del programma:
    gestisce input URL/file, estrae testo e titolo, salva file e aggiorna indice JSON.
    """
    # Controlla che l'utente abbia passato esattamente un argomento (URL o file)
    if len(sys.argv) != 2:
        print("Uso: python main.py <URL o file>")
        sys.exit(1)

    arg = sys.argv[1]

    # Se l'argomento è un URL (http o https), scarica l'HTML
    if arg.startswith("http://") or arg.startswith("https://"):
        html = download_html(arg)
        url = arg

    # Se invece è un file esistente, lo legge
    elif os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            html = f.read()
        url = "file://" + os.path.abspath(arg)

    # Altrimenti se non è URL né file, esce con errore
    else:
        print("Errore: l'argomento non è un URL valido né un file esistente.")
        sys.exit(1)

    # Estrae testo pulito e titolo dalla pagina HTML
    clean_text, title = extract_main_text(html)

    # Chiede category e date all’utente
    category = get_category()
    date = get_date()

    # Crea la cartella 'documents' se non esiste, dove salvare i testi
    folder = "documents"
    filename = get_next_filename(folder=folder)
    filepath = os.path.join(folder, filename)

     # File dove vengono salvati tutti i record, cioè l’indice degli articoli
    index_path = "index.json"

    # Carica l'indice JSON se esiste
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)
    else:
        index_data = []

    # Controllo duplicati URL nell'indice (per non salvare più volte lo stesso articolo)
    if any(r.get("url") == url for r in index_data):
        print("Articolo già presente nell'indice. Nessun nuovo salvataggio effettuato.")
        return

    # Salva il testo pulito nel file appena creato
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # Costruisce il record da inserire nell'indice JSON
    record = {
        "filename": filename,  # nome .txt con cui è salvato nella cartella
        "title": title,        # preso dal tag <title> html
        "url": url,            # url o file a cui si riferisce
        "metadata": {
            "category": category,  # categoria presa in input dall'utente
            "date": date           # data presa in input dall'utente
        }
    }

    # Aggiunge il nuovo record alla lista e riscrive index.json
    index_data.append(record)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    # Conferma all'utente che il file è stato salvato
    print(f"Salvato {filename} e aggiornato index.json")


if __name__ == "__main__":
    main()