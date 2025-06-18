import requests
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from collections import deque
import sys
import os
import random
import shutil
import json

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraping.scraper import extract_links, save_article_if_new

# Crawler configuration
ALLOWED_DOMAIN = "www.ilpost.it"
SEED_URLS = [f"https://{ALLOWED_DOMAIN}/"]
MAX_DEPTH = 8 # Maximum depth to avoid excessive crawling, can be modified
MAX_PAGES_TO_CRAWL = 30 # Limit to avoid excessive crawling, can be modified
LIVE_URL_PATTERN = "/live/" # Pattern to identify live pages that are to be managed in a special way
RECRAWL_INTERVAL_SECONDS = 60  # 1 minute for re-crawling live pages (in this usage example, we've kept the wait time low to avoid exceeding the while loop's duration and to ensure at least one re-check occurs; as the number of explored links grows, this time can be increased more reasonably)

# Paths for persisten memori
STATE_FOLDER = "_crawler_state"
FRONTIER_PATH = os.path.join(STATE_FOLDER, "frontier.json")
VISITED_PATH = os.path.join(STATE_FOLDER, "visited.json")
PRIORITY_QUEUE_PATH = os.path.join(STATE_FOLDER, "priority_queue.json")

#Cache for the document index to speed up lookups
INDEX_CACHE = {}

# Load the document index into a cache for fast lookups, needed to speed up the next function (get last modified)
def load_index_cache():
    """Loads the document index into a cache for fast lookups"""
    global INDEX_CACHE
    if os.path.exists("document_list.json"):
        with open("document_list.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Create a cache dictionary with URLs as keys for fast access and alla data as values
                INDEX_CACHE = {item['url']: item for item in data}
            except json.JSONDecodeError:
                INDEX_CACHE = {}

# Function to retrieve the 'Last-Modified' timestamp for a given URL from the cache
def get_last_modified(url: str) -> str | None:
    """Retrieves the 'Last-Modified' server timestamp for a given URL from the cache to ensure freshness"""
    if url in INDEX_CACHE:
        # Return the 'server_last_modified' timestamp from the cache, if available
        return INDEX_CACHE[url].get('metadata', {}).get('server_last_modified')
    return None

#Functions to manage persistent memory ---
def save_state(frontier, visited, priority_queue):
    """Saves the current state of the crawler to JSON files."""
    os.makedirs(STATE_FOLDER, exist_ok=True)
    with open(FRONTIER_PATH, 'w') as f:
        json.dump(list(frontier), f)
    with open(VISITED_PATH, 'w') as f:
        json.dump(list(visited), f)
    with open(PRIORITY_QUEUE_PATH, 'w') as f:
        json.dump(list(priority_queue), f)
    print("\n--- Crawler state saved. ---")

def load_state():
    """Loads the previous state of the crawler from JSON files, if they exist."""
    if os.path.exists(STATE_FOLDER):
        print("Loading previous crawler state...")
        try:
            with open(FRONTIER_PATH, 'r') as f:
                frontier = deque(json.load(f))
            with open(VISITED_PATH, 'r') as f:
                visited = set(json.load(f))
            with open(PRIORITY_QUEUE_PATH, 'r') as f:
                priority_queue = deque(json.load(f))
            return frontier, visited, priority_queue
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading state, starting from scratch.")

    # If there is no saved state, initialize from scratch
    return deque([(url, 0) for url in SEED_URLS]), set(SEED_URLS), deque()


def process_page_and_extract_links(url: str) -> list[str] | None:
    """
    Orchestration function for a single page:
    1. Downloads the HTML, using conditional GET for live pages.
    2. Calls the scraper to save the content (if new/updated).
    3. Calls the scraper to extract links for the frontier.
    """
    print(f"Processing: {url}")
    headers = {'User-Agent': 'MyCoolCrawler/1.0'}

    # NEW: Apply 'If-Modified-Since' check only for live pages
    if LIVE_URL_PATTERN in url:
        last_modified = get_last_modified(url)
        if last_modified:
            headers['If-Modified-Since'] = last_modified

    try:
        # Use requests to download the page content and save it in response + timeout to wait for the server's response
        response = requests.get(url, timeout=10, headers=headers)

        # NEW: Handle "Not Modified" response for live pages
        if response.status_code == 304:
            print(f"   -> Content not modified for {url}. Download skipped.")
            return [] # Return empty list as no new links can be extracted

        if not response.ok:
            print(f"   -> HTTP Error: Status code {response.status_code}")
            return None # Use None to indicate a processing error

        # Extracts the HTML content from the response
        html_content = response.text

        # Attempt to save the content. The scraper function will handle duplicates.
        save_article_if_new(html_content, url, response_headers=response.headers)
        
        # NEW: Reload cache in case the scraper updated the index
        load_index_cache()

        # Always extract links to continue the exploration.
        new_links = extract_links(html_content, url)
        print(f"   -> Found {len(new_links)} links.")
        return new_links

    except requests.RequestException as e:
        print(f"   -> Network error: {e}")
        return None # Use None to indicate a processing error

def main(new: bool = False):
    """
    Main crawler function.

    Args:
        new (bool): If True, deletes all previously crawled data before starting.
    """
    # Checks if the user passed the 'new' argument
    if new:
        print("Fresh start option detected: starting a new session.")

        # Deletes the JSON file if it exists
        if os.path.exists("document_list.json"):
            os.remove("document_list.json")
            print(" -> document_list.json deleted.")

        # Deletes the 'documents' folder and all its content if it exists
        if os.path.exists("documents"):
            shutil.rmtree("documents")
            print(" -> 'documents' folder deleted.")

        # Also cleans the crawler state for a true fresh start
        if os.path.exists(STATE_FOLDER):
            shutil.rmtree(STATE_FOLDER)
            print(" -> Crawler state deleted.")

    # Initializes the state by loading from files or creating from scratch
    exploration_frontier, visited_urls, high_priority_queue = load_state()
    # NEW: Load the index cache at startup
    load_index_cache()
    
    # Counter for processed pages
    pages_processed_count = 0

    # Create a parser to read the robots.txt file
    robot_parser = RobotFileParser()
    # Tells the parser where to find the robots.txt file it's interested in
    robot_parser.set_url(f"https://{ALLOWED_DOMAIN}/robots.txt")
    # Downloads and reads the content of the robots.txt file
    robot_parser.read()
    
    print("\n--- Starting Integrated Web Crawler ---")
    
    try:
        # while loop: 1. there are still pages to explore in the queues 2. check against the processed page limit
        while (exploration_frontier or high_priority_queue) and pages_processed_count < MAX_PAGES_TO_CRAWL:

            # 1. check high-priority queue (freshness policy) (checks if there are live pages with an expired re-crawl time)
            if high_priority_queue and high_priority_queue[0][1] <= time.time():
                # Takes the first expired live page to be re-checked and saves its URL
                url_to_recrawl, _ = high_priority_queue.popleft()
                print(f"Re-crawling live page for freshness: {url_to_recrawl}")

                # process it again
                new_links = process_page_and_extract_links(url_to_recrawl)
                # update the counter only if page was actually processed (not 304)
                if new_links is not None: pages_processed_count += 1

                # calculate a new future time for the next re-check
                next_crawl_time = time.time() + RECRAWL_INTERVAL_SECONDS
                # re-adds the URL to the queue
                high_priority_queue.append((url_to_recrawl, next_crawl_time))

            # 2. process normal frontier (exploration policy)
            elif exploration_frontier:
                # extracts the first available url and its depth
                current_url, current_depth = exploration_frontier.popleft()

                # check that the crawler has not gone too deep
                if current_depth >= MAX_DEPTH:
                    continue

                # check that robots.txt allows access to this url
                if not robot_parser.can_fetch("*", current_url):
                    print(f"SKIPPED (as per robots.txt): {current_url}")
                    continue

                # if the checks pass, it calls the function to download the page, passes it to the scraper for saving, and returns a list of all new links found inside.
                new_links = process_page_and_extract_links(current_url)
                if new_links is not None: pages_processed_count += 1

                # for loop that examines the new links found
                if new_links:
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

            # non-uniform delay to avoid getting blocked
            delay = 1 + random.uniform(0, 2)
            print(f"   -> Pausing for {delay:.2f} seconds...") # Formats the number for a cleaner printout
            time.sleep(delay)
    finally:
        # This block is always executed, whether the crawler finishes normally
        # or is interrupted (e.g., with Ctrl+C), ensuring the state is saved.
        save_state(exploration_frontier, visited_urls, high_priority_queue)

    print("\n--- Crawling Complete ---")
    print(f"Total pages processed: {pages_processed_count}, Unique URLs discovered: {len(visited_urls)}")


if __name__ == "__main__":
    # This block is executed only when the script is run directly.
    # It checks for a '--new' command-line argument to trigger a fresh start.
    should_start_new = "--new" in sys.argv
    main(new=should_start_new)
