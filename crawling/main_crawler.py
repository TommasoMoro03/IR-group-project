# Crawler web per il progetto di Information Retrieval.
#
# Funzionalità implementate:
# - Crawling focalizzato: Oopera solo sul dominio specificato (il post).
# - Politeness: Rispetta robots.txt e attende tra una richiesta e l'altra (REQUEST_DELAY_SECONDS).
# - Robustezza: Limita l'esplorazione a una profondità massima (MAX_DEPTH) per evitare trappole.
# - Gestione della 'freshness'': implementa una politica di re-crawling per pagine "live" (articoli in aggiornamento costante).
#   identificate da un pattern (LIVE_URL_PATTERN) per mantenere i contenuti aggiornati.

import requests
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from collections import deque

# Dominio su cui il crawler deve rimanere
ALLOWED_DOMAIN = "www.ilpost.it"

# URL iniziali da cui il crawler comincia la sua esplorazione
SEED_URLS = [f"https://{ALLOWED_DOMAIN}/"]

# Limite di profondità massima da esplorare a partire dai seed
MAX_DEPTH = 10

# Numero massimo di pagine da scaricare per evitare crawling troppo lunghi
MAX_PAGES_TO_CRAWL = 100

# Secondi di attesa tra una richiesta HTTP e la successiva
REQUEST_DELAY_SECONDS = 2

# Pattern testuale per identificare URL di pagine "live" o ad alta priorità
# es: https://www.ilpost.it/live/bombardamento-israele-iran-nucleare/?homepagePosition=0
LIVE_URL_PATTERN = "/live/"

# Intervallo in secondi per rivisitare le pagine ad alta priorità
RECRAWL_INTERVAL_SECONDS = 60 * 5  # Ogni 5 minuti

def scrape_links_from_html(html_content: str, base_url: str) -> list[str]:
    """
    Funzione di scraping per estrarre tutti i link da un contenuto HTML.
    INPUT:
    - html_content: stringa contenente il codice HTML della pagina.
    - base_url: URL di base per risolvere i link relativi.
    OUTPUT:
    - Lista di URL puliti estratti dalla pagina.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Libreria BeautifulSoup4 non trovata. Eseguo uno scraping semplificato.")
        print("Per un parsing corretto, installa BeautifulSoup: pip install beautifulsoup4 lxml")
        import re
        # Se beautifulsup non è disponibile non usa il dom ma ricerca semplicemente oggetti assimilabili a href
        raw_links = re.findall(r'href=[\'"]?([^\'" >]+)', html_content)
    else:
        #Trasforma il testo HTML e lo trasforma in un oggetto navigabile (albero che rappresenta la struttura della pagina, DOM)
        soup = BeautifulSoup(html_content, 'lxml')
        # Naviga il dom e trova tutti i tag <a> con attributo href + per ogni tag <a> estrae il valore dell'attributo href
        raw_links = [a.get('href') for a in soup.find_all('a', href=True)]

    # Pulizia e normalizzazione dei link
    cleaned_links = []
    for link in raw_links:
        # Trasforma link relativi in assoluti e rimuove i frammenti (#)
        full_url = urljoin(base_url, link).split('#')[0]
        cleaned_links.append(full_url)
    return cleaned_links

def process_page(url: str) -> list[str]:
    """
    Funzione helper per scaricare e processare una singola pagina.
    Restituisce i nuovi link trovati o una lista vuota in caso di errore.
    INPUT:
    - url: URL della pagina da processare.
    OUTPUT:
    - Lista di URL estratti dalla pagina, o una lista vuota in caso di errore.
    """
    try:
        print(f"Visitando: {url}")
        # Fetch
        response = requests.get(url, timeout=10)
        
        if not response.ok:
            print(f"   -> Errore HTTP: Status code {response.status_code}")
            return []
        
        # In un sistema completo, qui il contenuto verrebbe salvato su disco
        # o passato al modulo di scraping per l'estrazione del testo pulito.
        html_content = response.text
        
        new_links = scrape_links_from_html(html_content, url)
        print(f"Trovati {len(new_links)} link.")
        return new_links

    except requests.RequestException as e:
        print(f"Errore di rete: {e}")
        return []

def main():
    """
    Funzione principale che avvia e gestisce il processo di crawling.
    """
    
    # coda di frontiera per l'esplorazione standard (contiene tuple: url, profondità)
    exploration_frontier = deque([(url, 0) for url in SEED_URLS])
    # Set per non visitare due volte lo stesso link durante l'esplorazione
    visited_urls = set(SEED_URLS)
    
    # Coda ad alta priorità per la politica di freshness (contiene tuple: url, timestamp del prossimo re-crawl)
    high_priority_queue = deque()
    
    pages_crawled_count = 0
    
    robot_parser = RobotFileParser()
    #lettura del robots.txt 
    robot_parser.set_url(f"https://{ALLOWED_DOMAIN}/robots.txt")
    robot_parser.read()

    # Il ciclo continua finché c'è lavoro da fare in una delle due code o non si raggiunge il limite
    while (exploration_frontier or high_priority_queue) and pages_crawled_count < MAX_PAGES_TO_CRAWL:
        
        # 1. prima check sulla coda ad alta priorità
        # Se la coda prioritaria non è vuota e il primo elemento è "scaduto" (pronto per il re-crawl)
        if high_priority_queue and high_priority_queue[0][1] <= time.time():
            url_to_recrawl, _ = high_priority_queue.popleft()
            print(f"Re-crawling pagina live per freschezza: {url_to_recrawl}")
            
            # Processa la pagina ma ignora i link restituiti per non ri-esplorare da una pagina live
            process_page(url_to_recrawl)
            pages_crawled_count += 1
            
            # Riprogramma il prossimo controllo per questa stessa pagina
            next_crawl_time = time.time() + RECRAWL_INTERVAL_SECONDS
            high_priority_queue.append((url_to_recrawl, next_crawl_time))
            
        # 2. elabora ora la frontiera normale
        elif exploration_frontier:
            current_url, current_depth = exploration_frontier.popleft()
            
            if current_depth >= MAX_DEPTH:
                print(f"SKIPPATO (profondità massima {current_depth}): {current_url}")
                continue

            if not robot_parser.can_fetch("*", current_url):
                print(f"SKIPPATO (da robots.txt): {current_url}")
                continue
                
            new_links = process_page(current_url)
            pages_crawled_count += 1

            for link in new_links:
                if link not in visited_urls and urlparse(link).netloc == ALLOWED_DOMAIN:
                    visited_urls.add(link)
                    
                    # Identifica se il nuovo link è una pagina "live" e quindi ad alta priorità
                    if LIVE_URL_PATTERN in link:
                        next_crawl_time = time.time() + RECRAWL_INTERVAL_SECONDS
                        high_priority_queue.append((link, next_crawl_time))
                    else:
                        exploration_frontier.append((link, current_depth + 1))
        
        # 3. Se la frontiera di esplorazione è vuota ma ci sono re-crawl futuri, attendi.
        else:
            print("Frontiera di esplorazione vuota, in attesa di re-crawl schedulati...")
            time.sleep(5)
            continue

        # Pausa tra ogni ciclo per non sovraccaricare il server
        print(f"Attesa di {REQUEST_DELAY_SECONDS} secondi...")
        time.sleep(REQUEST_DELAY_SECONDS)

    print("\n--- Crawling Completato ---")
    print(f"Limite di pagine raggiunto o code esaurite.")
    print(f"Pagine totali processate (incl. re-crawl): {pages_crawled_count}")
    print(f"URL unici scoperti: {len(visited_urls)}")
    print("----------------------------")

if __name__ == "__main__":
    # pip install requests beautifulsoup4 lxml
    main()