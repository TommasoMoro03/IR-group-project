import json
import os
import re
import sys
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Global constants for file paths and thresholds
INDEX_PATH = "document_list.json"         # JSON index file to track saved articles metadata
DOCUMENTS_FOLDER = "documents"            # Folder where article text files are stored
MIN_ARTICLE_WORDS = 50                    # Minimum words to consider a page as a valid article


def extract_links(html_content: str, base_url: str) -> list[str]:
    """
    Extracts all hyperlinks from the given HTML content,
    normalizing them to absolute URLs
    and removing any fragment identifiers (#).
    """
    
    # Parse the raw HTML content with BeautifulSoup using the 'lxml' parser
    soup = BeautifulSoup(html_content, 'lxml')
    # Extract all href attributes from <a> tags that have an href attribute
    raw_links = [a.get('href') for a in soup.find_all('a', href=True)]

    cleaned_links = []
    for link in raw_links:
        # Build absolute URL and remove anything after '#' to avoid duplicates pointing to sections within the page
        full_url = urljoin(base_url, link).split('#')[0]
        cleaned_links.append(full_url)
    return cleaned_links


def extract_main_text(html: str) -> (str, str):
    """
    Extracts the main text content and title from an HTML page.
    Removes non-textual or navigation elements to isolate relevant content.
    """
    page = BeautifulSoup(html, 'html.parser')
    # Extract the page title if available
    title = page.title.string.strip() if page.title else "No Title"
    # Remove unwanted tags to clean the main text
    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()
    # Look for common article container div
    main_content_div = page.find('div', class_='entry-content')
    if main_content_div:
        return main_content_div.get_text(separator='\n', strip=True), title
    # If not found, try <main> tag
    main_tag = page.find('main')
    if main_tag:
        return main_tag.get_text(separator='\n', strip=True), title
    # As fallback, return all text inside <body>
    body_tag = page.find('body')
    return (body_tag.get_text(separator='\n', strip=True) if body_tag else ""), title


def is_article_url(url: str) -> bool:
    """
    Simple heuristic to determine if a URL is likely an article.
    Checks for date patterns (/YYYY/MM/DD/) or presence of '/live/' in the path.
    """
    path = urlparse(url).path
    is_standard_article = re.search(r'/\d{4}/\d{2}/\d{2}/', path)  # Blog-like date pattern
    is_live_page = '/live/' in path                                # Live page indicator
    return is_standard_article or is_live_page


def extract_metadata_from_url(url: str) -> (str, str):
    """
    Extracts category and date from the URL if present in the expected format.
    If not found, returns default values.
    """
    parts = urlparse(url).path.strip('/').split('/')
    date = datetime.now().strftime("%Y-%m-%d")   # Default to current date
    category = 'generale'                        # Default category
    try:
        # If first three segments are numeric, interpret as year, month, day
        if len(parts) >= 3 and all(p.isdigit() for p in parts[0:3]):
            date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
            datetime.strptime(date_str, "%Y-%m-%d")  # Validate date format
            date = date_str
            if len(parts) > 3:
                category = parts[3]  # Fourth segment as category
    except (ValueError, IndexError):
        pass  # Keep defaults if parsing fails
    return category, date


def get_next_filename() -> tuple[str, str]:
    """
    Returns the next filename to use for saving an article,
    ensuring progressive numbering and no overwriting of existing files.
    """
    os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)  # Create folder if missing
    files = [f for f in os.listdir(DOCUMENTS_FOLDER) if f.startswith("articolo_") and f.endswith(".txt")]
    # Extract numbers from existing filenames
    nums = [int(re.search(r'(\d+)', f).group(1)) for f in files if re.search(r'(\d+)', f)]
    next_num = max(nums) + 1 if nums else 1          # Start at 1 if none found
    filename = f"articolo_{next_num:03d}.txt"        # Zero-padded filename (e.g. articolo_001.txt)
    return filename, os.path.join(DOCUMENTS_FOLDER, filename)


def save_article_if_new(html_content: str, url: str, response_headers: dict = None) -> bool:
    """
    Main function that manages:
    - Validating the URL as an article
    - Extracting text and title
    - Filtering out too short articles
    - Calculating hash to detect duplicates
    - Saving the file only if new or live page updated
    - Updating the JSON index with metadata and status
    """
    # Skip if the URL doesn't appear to be an article (based on heuristic)
    if not is_article_url(url):
        print("   -> URL does not look like an article, skipping.")
        return False

    # Extract the main article text and title from the HTML content
    text, title = extract_main_text(html_content)
    word_count = len(text.split())

    # Discard articles that are too short
    if word_count < MIN_ARTICLE_WORDS:
        print(f"   -> Content too short ({word_count} words), skipping.")
        return False


    # Compute hash of the text to identify exact duplicates
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

    index_data = []
    # Load existing index if present
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except json.JSONDecodeError:
            index_data = []

    # Check if this URL has already been processed and is in the index
    existing_record_by_url = next((record for record in index_data if record.get("url") == url), None)

    current_timestamp = datetime.now().isoformat()
    server_last_modified = response_headers.get('Last-Modified') if response_headers else None


    # If article already present with this URL
    if existing_record_by_url:
        is_live_page = '/live/' in url
        if is_live_page:
            # For live pages, update content and timestamp
            filename = existing_record_by_url['filename']
            filepath = os.path.join(DOCUMENTS_FOLDER, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"{title}\n\n{text}")

            # Update metadata in index
            existing_record_by_url['metadata']['last_crawled_at'] = current_timestamp
            existing_record_by_url['metadata']['content_hash'] = content_hash
            if server_last_modified:
                existing_record_by_url['metadata']['server_last_modified'] = server_last_modified

            # Save updated index to disk
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

            print(f"   -> Updated content and timestamp of {filename} (live page)")
            return True
        else:
            # Standard article already saved, skip saving again
            print(f"   -> Standard article already exists, skipping: {url}")
            return False
    else:
        # New URL: check for duplicates via content hash
        existing_record_by_hash = next((record for record in index_data if record.get('metadata', {}).get("content_hash") == content_hash), None)
        if existing_record_by_hash:
            print(f"   -> Duplicate content found. URL: {url} (duplicate of {existing_record_by_hash['url']})")
            return False

        # If new and not duplicate, save article to file
        category, date = extract_metadata_from_url(url)
        filename, filepath = get_next_filename()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{text}")

        # Prepare a dictionary (record) with all relevant metadata about the article
        new_record = {
            "filename": filename,            # Name of the saved text file
            "title": title,                  # Extracted title of the article
            "url": url,                      # Original URL of the article
            "metadata": {
                "category": category,        # Article category (from URL or default)
                "date": date,                # Article date (from URL or current date)
                "last_crawled_at": current_timestamp,       # When it was last processed
                "server_last_modified": server_last_modified,  # Last-Modified header from server (if any)
                "content_hash": content_hash   # SHA-256 hash of the content for deduplication
            }
        }
        # Append the new record to the index list
        index_data.append(new_record)
        # Save the updated index back to the JSON file
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"   -> Created {filename} and updated {INDEX_PATH}")
        return True


def download_html(url):
    """
    Downloads the HTML content of a given URL using requests.
    Handles network errors and timeouts gracefully.
    """
    try:
        # Download the page content with a timeout of 10 seconds
        response = requests.get(url, timeout=10)
        # Raises exception for non-200 status
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error during download: {e}")
        return None


def main_standalone():
    """
    Main entry point if run from the command line.
    Accepts a URL argument, downloads and processes the page.
    """
    # Check if exactly one argument (the URL) is provided on the command line
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m scraping.scraper <URL>")
    url = sys.argv[1]
    if not (url.startswith("http://") or url.startswith("https://")):
        sys.exit("Error: the argument provided is not a valid URL.")
    
    print(f"Downloading and processing: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        save_article_if_new(response.text, url, response.headers)
    except requests.RequestException as e:
        print(f"Download failed: {e}")


if __name__ == "__main__":
    main_standalone()