import json
import os
import re
import sys
import requests
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Definiamo i percorsi come costanti globali per coerenza
INDEX_PATH = "document_list.json"
DOCUMENTS_FOLDER = "documents"
MIN_ARTICLE_WORDS = 50 # Soglia minima di parole per considerare una pagina un articolo


def extract_links(html_content: str, base_url: str) -> list[str]:
    """
    Estrae tutti i out-link puliti da un contenuto HTML.
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
    title = page.title.string.strip() if page.title else "No Title"
    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()
    main_content_div = page.find('div', class_='entry-content')
    if main_content_div:
        return main_content_div.get_text(separator='\n', strip=True), title
    main_tag = page.find('main')
    if main_tag:
        return main_tag.get_text(separator='\n', strip=True), title
    body_tag = page.find('body')
    return (body_tag.get_text(separator='\n', strip=True) if body_tag else ""), title


def is_article_url(url: str) -> bool:
    """
    EURISTICA URL: Controlla se l'URL ha la struttura di un articolo o di una pagina live (to ensure quality property).
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
    Calcola il nome del prossimo file da salvare in modo progressivo,
    garantendo la continuità della numerazione se la cartella non viene cancellata.
    """
    os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)
    files = [f for f in os.listdir(DOCUMENTS_FOLDER) if f.startswith("articolo_") and f.endswith(".txt")]
    nums = [int(re.search(r'(\d+)', f).group(1)) for f in files if re.search(r'(\d+)', f)]
    next_num = max(nums) + 1 if nums else 1
    filename = f"articolo_{next_num:03d}.txt"
    return filename, os.path.join(DOCUMENTS_FOLDER, filename)


def save_article_if_new(html_content: str, url: str, response_headers: dict = None) -> bool:
    """
    Orchestra estrazione, filtraggio e salvataggio, ora con controllo checksum per duplicati esatti.
    """
    if not is_article_url(url):
        print(f"   -> URL non sembra un articolo, skippato.")
        return False

    text, title = extract_main_text(html_content)
    word_count = len(text.split())
    if word_count < MIN_ARTICLE_WORDS:
        print(f"   -> Contenuto troppo corto ({word_count} parole), skippato.")
        return False

    # <-- 2. CALCOLA IL CHECKSUM DEL CONTENUTO -->
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

    index_data = []
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except json.JSONDecodeError:
            index_data = []
            
    existing_record_by_url = next((record for record in index_data if record.get("url") == url), None)
    
    current_timestamp = datetime.now().isoformat()
    server_last_modified = response_headers.get('Last-Modified') if response_headers else None

    if existing_record_by_url:
        # L'ARTICOLO ESISTE GIA' (STESSO URL).
        is_live_page = '/live/' in url
        if is_live_page:
            filename = existing_record_by_url['filename']
            filepath = os.path.join(DOCUMENTS_FOLDER, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"{title}\n\n{text}")
            
            existing_record_by_url['metadata']['last_crawled_at'] = current_timestamp
            existing_record_by_url['metadata']['content_hash'] = content_hash # Aggiorna anche l'hash
            if server_last_modified:
                existing_record_by_url['metadata']['server_last_modified'] = server_last_modified
            
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

            print(f"   -> Aggiornato contenuto e timestamp di {filename} (pagina live)")
            return True
        else:
            print(f"   -> Articolo standard già esistente, skippato: {url}")
            return False
    else:
        # L'ARTICOLO È NUOVO (URL NUOVO). ORA CONTROLLIAMO SE IL CONTENUTO È UN DUPLICATO.
        
        # <-- 3. CONTROLLO DUPLICATI BASATO SUL CHECKSUM -->
        existing_record_by_hash = next((record for record in index_data if record.get('metadata', {}).get("content_hash") == content_hash), None)
        if existing_record_by_hash:
            print(f"   -> Trovato contenuto duplicato. URL: {url} (duplicato di {existing_record_by_hash['url']})")
            return False

        # Se non è un duplicato, procedi con il salvataggio
        category, date = extract_metadata_from_url(url)
        filename, filepath = get_next_filename()
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{text}")

        new_record = {
            "filename": filename, "title": title, "url": url,
            "metadata": {
                "category": category, "date": date,
                "last_crawled_at": current_timestamp,
                "server_last_modified": server_last_modified,
                "content_hash": content_hash # <-- 4. SALVA L'HASH NEI METADATI
            }
        }
        index_data.append(new_record)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        print(f"   ->Creato {filename} e aggiornato {INDEX_PATH}")
        return True


def download_html(url):
    """
    Funzione per scaricare il contenuto HTML di una pagina web da un URL.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Errore durante il download: {e}")
        return None


def main_standalone():
    """
    Funzione principale per gestire l'esecuzione da riga di comando.
    """
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m scraping.scraper <URL>")
    url = sys.argv[1]
    if not (url.startswith("http://") or url.startswith("https://")):
        sys.exit("Errore: l'argomento fornito non è un URL valido.")
    
    print(f"Download e processamento di: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        save_article_if_new(response.text, url, response.headers)
    except requests.RequestException as e:
        print(f"Download fallito: {e}")

if __name__ == "__main__":
    main_standalone()
