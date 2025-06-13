# main.py
# Estrazione del contenuto principale (testo) da pagine HTML.
# Usa la libreria python BeautifulSoup per rimuovere elementi non utili come menu, pubblicità, script, ecc.
# Viene usato insieme a un crawler su HTML già scaricati (funziona meglio con pagine statiche).

import requests
from bs4 import BeautifulSoup
import sys
import os

def extract_main_text(html):
    """
    Funzione per estrarre il testo principale da una pagina HTML, rimuovendo elementi non informativi.

    Parametri:
    - html (str): contenuto HTML della pagina.

    Ritorna:
    - str: testo pulito.
    """
    if not html:
        return "" # Restituisce una stringa vuota
    
    page = BeautifulSoup(html, 'html.parser')

    # Con 'decompose', rimuove:
    # script, style: codice invisibile
    # nav, footer, header, aside: menù, intestazione, pubblicità, ecc.
    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()


    # Cerca il contenuto principale, <main>
    possible_main = page.find('main')
    
    if possible_main:
        text = possible_main.get_text()
        # Se trova <main>, prende solo quel testo.
    else:
        text = page.get_text()
        # Se non lo trova, prende tutto il testo della pagina.


    # Pulisce gli spazi in più
    text = ' '.join(text.split())
    return text # Restituzione del testo pulito


def download_html(url):
    """ Funzione per caricare HTML da un URL. """
    try:
        # Usa la libreria 'request' per scaricare il contenuto della pagina. Aspetta massimo 10 secondo per ricevere risposta.
        response = requests.get(url, timeout=10)
        # Controlla se la richiesta è andata a buon fine
        response.raise_for_status()
        return response.text
    
    except Exception as e:
        print(f"Errore durante il download: {e}")
        return ""

# Esempio per testare il file
# python main.py pagina.html
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python scraping/main_scrap.py <URL o percorso file>")
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

    clean_text = extract_main_text(html)
    print(clean_text)