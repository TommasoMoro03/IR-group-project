import requests
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from collections import deque
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraping.scraper import extract_links, save_article_if_new

# --- CRAWLER CONFIGURATION ---
ALLOWED_DOMAIN = "www.ilpost.it"
SEED_URLS = [f"https://{ALLOWED_DOMAIN}/"]
MAX_DEPTH = 5
MAX_PAGES_TO_CRAWL = 30
REQUEST_DELAY_SECONDS = 2
LIVE_URL_PATTERN = "/live/"
RECRAWL_INTERVAL_SECONDS = 60 * 5

def process_page_and_extract_links(url: str) -> list[str]:
    """
    Orchestration function for a single page:
    1. Downloads the HTML.
    2. Calls the scraper to save the content (if new).
    3. Calls the scraper to extract links for the frontier.
    """
    print(f"Processing: {url}")
    try:
        response = requests.get(url, timeout=10)
        if not response.ok:
            print(f"   -> HTTP Error: Status code {response.status_code}")
            return []

        html_content = response.text

        # 1. Attempt to save the content. The scraper function will handle duplicates.
        save_article_if_new(html_content, url)

        # 2. Always extract links to continue the exploration.
        new_links = extract_links(html_content, url)
        print(f"   -> Found {len(new_links)} links.")
        return new_links

    except requests.RequestException as e:
        print(f"   -> Network error: {e}")
        return []

def main():
    """ Main crawler function """
    print("--- Starting Integrated Web Crawler ---")
    
    exploration_frontier = deque([(url, 0) for url in SEED_URLS])
    visited_urls = set(SEED_URLS)
    high_priority_queue = deque()
    pages_processed_count = 0
    
    robot_parser = RobotFileParser()
    robot_parser.set_url(f"https://{ALLOWED_DOMAIN}/robots.txt")
    robot_parser.read()

    while (exploration_frontier or high_priority_queue) and pages_processed_count < MAX_PAGES_TO_CRAWL:
        
        # 1. CHECK HIGH-PRIORITY QUEUE (FRESHNESS POLICY)
        if high_priority_queue and high_priority_queue[0][1] <= time.time():
            url_to_recrawl, _ = high_priority_queue.popleft()
            print(f"Re-crawling live page for freshness: {url_to_recrawl}")
            
            process_page_and_extract_links(url_to_recrawl) # We process it again
            pages_processed_count += 1
            
            next_crawl_time = time.time() + RECRAWL_INTERVAL_SECONDS
            high_priority_queue.append((url_to_recrawl, next_crawl_time))
            
        # 2. PROCESS NORMAL FRONTIER (EXPLORATION POLICY)
        elif exploration_frontier:
            current_url, current_depth = exploration_frontier.popleft()
            
            if current_depth >= MAX_DEPTH:
                continue

            if not robot_parser.can_fetch("*", current_url):
                print(f"SKIPPED (as per robots.txt): {current_url}")
                continue
                
            new_links = process_page_and_extract_links(current_url)
            pages_processed_count += 1

            for link in new_links:
                # Add to the frontier only if it's a valid link and not yet discovered
                if urlparse(link).netloc == ALLOWED_DOMAIN and link not in visited_urls:
                    visited_urls.add(link)
                    
                    if LIVE_URL_PATTERN in link:
                        print(f"Live page found! Adding to priority queue: {link}")
                        high_priority_queue.append((link, time.time() + RECRAWL_INTERVAL_SECONDS))
                    else:
                        exploration_frontier.append((link, current_depth + 1))
        else:
            print("Frontier empty, waiting for scheduled re-crawls...")
            time.sleep(5)
            continue

        print(f"   -> Pausing for {REQUEST_DELAY_SECONDS} seconds...")
        time.sleep(REQUEST_DELAY_SECONDS)

    print("\n--- Crawling Complete ---")
    print(f"Total pages processed: {pages_processed_count}, Unique URLs discovered: {len(visited_urls)}")

# This part is useless for the whole process but can be useful if you want to call only the crawler separately.
if __name__ == "__main__":
    # Make sure the scraping/ directory with scraper.py exists
    # and that this script is run from the project's root directory.
    if not os.path.exists("scraping"):
        print("Error: The 'scraping' directory is not present.")
        print("Please ensure you have the correct directory structure: crawling/, scraping/")
    else:
        main()
