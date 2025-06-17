import requests
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from collections import deque
import sys
import os
import random

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


def process_page_and_extract_links(url: str) -> list[str]:
    """
    Orchestration function for a single page:
    1. Downloads the HTML.
    2. Calls the scraper to save the content (if new).
    3. Calls the scraper to extract links for the frontier.
    """
    print(f"Processing: {url}")
    try:
        # Use requests to download the page content and save it in response + timeout to wait for the server's response
        response = requests.get(url, timeout=10)
        if not response.ok:
            print(f"   -> HTTP Error: Status code {response.status_code}")
            return []

        # Extracts the HTML content from the response
        html_content = response.text

        # Attempt to save the content. The scraper function will handle duplicates.
        save_article_if_new(html_content, url)

        # Always extract links to continue the exploration.
        new_links = extract_links(html_content, url)
        print(f"   -> Found {len(new_links)} links.")
        return new_links

    except requests.RequestException as e:
        print(f"   -> Network error: {e}")
        return []

def main():
    """ Main crawler function """
    print("--- Starting Integrated Web Crawler ---")
    
    # Create the URL exploration frontier starting from the seeds, each URL is a tuple with the starting URL's depth (0)
    exploration_frontier = deque([(url, 0) for url in SEED_URLS])

    # Create a set to keep track of already visited URLs, initially containing only the seeds
    visited_urls = set(SEED_URLS)

    # Special queue for live pages with a freshness policy
    high_priority_queue = deque()

    # Counter for processed pages
    pages_processed_count = 0

    # Create a parser to read the robots.txt file
    robot_parser = RobotFileParser()
    # Tells the parser where to find the robots.txt file it's interested in
    robot_parser.set_url(f"https://{ALLOWED_DOMAIN}/robots.txt")
    # Downloads and reads the content of the robots.txt file
    robot_parser.read()
    
    # while loop: 1. there are still pages to explore in the queues 2. check against the processed page limit
    while (exploration_frontier or high_priority_queue) and pages_processed_count < MAX_PAGES_TO_CRAWL:
        
        # 1. check high-priority queue (freshness policy) (checks if there are live pages with an expired re-crawl time)
        if high_priority_queue and high_priority_queue[0][1] <= time.time():
            # Takes the first expired live page to be re-checked and saves its URL
            url_to_recrawl, _ = high_priority_queue.popleft()
            print(f"Re-crawling live page for freshness: {url_to_recrawl}")
            
            # process it again
            process_page_and_extract_links(url_to_recrawl)
            # update the counter
            pages_processed_count += 1 
            
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
            pages_processed_count += 1

            # for loop that examines the new links found
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
