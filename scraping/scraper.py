import json
import os
import re
import sys
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Definiamo i percorsi come costanti globali per coerenza
INDEX_PATH = "document_list.json"
DOCUMENTS_FOLDER = "documents"
MIN_ARTICLE_WORDS = 150 # Soglia minima di parole per considerare una pagina un articolo


def extract_links(html_content: str, base_url: str) -> list[str]:
    """
    Estrae tutti i link puliti da un contenuto HTML.
    Questa funzione viene chiamata dal crawler per scoprire nuove pagine.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    raw_links = [a.get('href') for a in soup.find_all('a', href=True)]
    cleaned_links = []
    for link in raw_links:
        full_url = urljoin(base_url, link).split('#')[0]
        cleaned_links.append(full_url)
    return cleaned_links


def extract_main_text(html: str) -> (str, str):
    """
    Funzione per estrarre e pulire il testo principale e il titolo da una pagina HTML.
    """
    page = BeautifulSoup(html, 'html.parser')
    
    # Se presente, estrae il titolo della pagina. Altrimenti "No Title"
    title = page.title.string.strip() if page.title else "No Title"
    
    # Rimuove elementi non utili che non contengono testo rilevante:
    # script, style (codice non visibile)
    # nav, footer, header, aside (menu, pubblicità, ecc)

    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()

    main_content_div = page.find('div', class_='entry-content')
    if main_content_div:
        text = main_content_div.get_text(separator='\n', strip=True)
        return text, title

    main_tag = page.find('main')
    if main_tag:
        text = main_tag.get_text(separator='\n', strip=True)
        return text, title
        
    body_tag = page.find('body')
    text = body_tag.get_text(separator='\n', strip=True) if body_tag else ""
    return text, title


def is_article_url(url: str) -> bool:
    """
    EURISTICA URL: Controlla se l'URL ha la struttura tipica di un articolo.
    """
    path = urlparse(url).path

    is_standard_article = re.search(r'/\d{4}/\d{2}/\d{2}/', path)
    is_live_page = '/live/' in path
    
    return is_standard_article or is_live_page


def extract_metadata_from_url(url: str) -> (str, str):
    """
    Estrae automaticamente categoria e data dall'URL del Post.
    """
    parts = urlparse(url).path.strip('/').split('/')
    date = datetime.now().strftime("%Y-%m-%d")
    category = 'generale'

    try:
        if len(parts) >= 3 and all(p.isdigit() for p in parts[0:3]):
            date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
            datetime.strptime(date_str, "%Y-%m-%d")
            date = date_str
            if len(parts) > 3:
                category = parts[3]
    except (ValueError, IndexError):
        pass
    return category, date


def get_next_filename() -> (str, str):
    """
    Calcola il nome del prossimo file da salvare in modo progressivo.
    """
    os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)
    files = [f for f in os.listdir(DOCUMENTS_FOLDER) if f.startswith("articolo_") and f.endswith(".txt")]
    nums = [int(re.search(r'(\d+)', f).group(1)) for f in files if re.search(r'(\d+)', f)]
    next_num = max(nums) + 1 if nums else 1
    filename = f"articolo_{next_num:03d}.txt"
    return filename, os.path.join(DOCUMENTS_FOLDER, filename)


def save_article_if_new(html_content: str, url: str) -> bool:
    """
    Orchestra estrazione, filtraggio e salvataggio.
    Ora gestisce sia la creazione di nuovi articoli che l'aggiornamento di quelli esistenti (es. pagine live).
    """
    if not is_article_url(url):
        print(f"   -> URL non sembra un articolo, skippato: {url.split('/')[-2] if '/' in url else url}")
        return False

    text, title = extract_main_text(html_content)
    word_count = len(text.split())

    if word_count < MIN_ARTICLE_WORDS:
        print(f"   -> Contenuto troppo corto ({word_count} parole), probabilmente non un articolo. Skippato.")
        return False

    # Carica l'indice JSON
    index_data = []
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Attenzione: {INDEX_PATH} corrotto. Verrà creato un nuovo file.")
            index_data = []
    
    # Cerca se esiste già un record per questo URL
    existing_record = next((record for record in index_data if record.get("url") == url), None)
    
    # --- NUOVA LOGICA DI AGGIORNAMENTO O CREAZIONE ---
    
    if existing_record:
        # **CASO 2: L'ARTICOLO ESISTE (Aggiorna il file .txt)**
        filename = existing_record['filename']
        filepath = os.path.join(DOCUMENTS_FOLDER, filename)
        
        # Sovrascrive il file esistente con il nuovo contenuto
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{text}")
        
        print(f"   ->Aggiornato contenuto di {filename} ({word_count} parole)")
        # Non è necessario modificare il JSON, quindi non lo salviamo
        return True # Ritorna True per indicare che l'operazione ha avuto successo

    else:
        # **CASO 1: L'ARTICOLO È NUOVO (Crea nuovo file e nuovo record JSON)**
        category, date = extract_metadata_from_url(url)
        filename, filepath = get_next_filename()
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{text}")

        new_record = {
            "filename": filename,
            "title": title,
            "url": url,
            "metadata": {"category": category, "date": date}
        }

        index_data.append(new_record)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"   -> Creato {filename} ({word_count} parole) e aggiornato {INDEX_PATH}")
        return True


def download_html(url):
    """
    Funzione per scaricare il contenuto HTML di una pagina web da un URL.
    """
    try:
        # Scarica la pagina con timeout di 10 secondi
        response = requests.get(url, timeout=10)
        # Lancia eccezione se la risposta HTTP non è OK (ad esempio 404)
        response.raise_for_status()
        # Restituisce il contenuto HTML come stringa
        return response.text
    
    except requests.RequestException as e:
        # Stampa errore in caso di problemi di rete o URL e restituisce stringa vuota
        print(f"Errore durante il download: {e}")
        return None


def main_standalone():
    """
    Funzione principale per gestire l'esecuzione da riga di comando.
    """
    if len(sys.argv) != 2:
        print("Uso: python -m scraping.scraper <URL>")
        sys.exit(1)

    url = sys.argv[1]

    if not (url.startswith("http://") or url.startswith("https://")):
        print("Errore: l'argomento fornito non è un URL valido.")
        sys.exit(1)
        
    print(f"Download e processamento di: {url}")
    html = download_html(url)
    
    if html:
        # Chiama la stessa funzione usata dal crawler
        save_article_if_new(html, url)
    else:
        print("Download fallito. Impossibile processare la pagina.")


if __name__ == "__main__":
    # Questa parte viene eseguita solo quando lo script è lanciato direttamente
    # da riga di comando, non quando viene importato dal crawler.
    main_standalone()