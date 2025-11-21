import os
import requests
from bs4 import BeautifulSoup
import time
import csv
import random
from urllib.parse import urljoin, unquote, urlparse
from datetime import datetime

# Folder to save articles
ARTICLES_FOLDER = "wikipedia_articles"
os.makedirs(ARTICLES_FOLDER, exist_ok=True)

# CSV log for downloaded articles
LOG_FILE = os.path.join(ARTICLES_FOLDER, "download_log.csv")
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Folder", "URL", "Timestamp"])

# Headers to make requests look like a browser
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Function to make a filename safe
def safe_filename(title):
    return title.replace(" ", "_").replace("/", "_")

# Function to check if article is already downloaded
def is_downloaded(title):
    folder_path = os.path.join(ARTICLES_FOLDER, safe_filename(title))
    if os.path.exists(folder_path):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == title:
                    return True, folder_path
    return False, folder_path

# Function to log downloaded article
def log_article(title, folder_path, url):
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([title, folder_path, url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

# Function to download a file (image or media)
def download_file(file_url, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    parsed_url = urlparse(file_url)
    file_name = unquote(os.path.basename(parsed_url.path))
    file_path = os.path.join(save_folder, file_name)
    try:
        r = requests.get(file_url, headers=HEADERS)
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)
    except Exception as e:
        print(f"Failed to download file {file_url}: {e}")

# Function to download all images in the article
def download_images(content_div, images_folder):
    os.makedirs(images_folder, exist_ok=True)
    for img in content_div.find_all("img"):
        img_url = img.get("src")
        if not img_url:
            continue
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        download_file(img_url, images_folder)

# Function to download tables as CSV
def save_tables(content_div, folder_path):
    tables = content_div.find_all("table", {"class": "wikitable"})
    for i, table in enumerate(tables, start=1):
        table_file = os.path.join(folder_path, f"table_{i}.csv")
        rows = table.find_all("tr")
        with open(table_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in rows:
                cells = row.find_all(["th", "td"])
                writer.writerow([cell.get_text(strip=True) for cell in cells])

# Function to download linked media files (PDF, MP3, etc.)
def download_linked_files(content_div, media_folder):
    os.makedirs(media_folder, exist_ok=True)
    for link in content_div.find_all("a", href=True):
        href = link['href']
        if href.lower().endswith((".pdf", ".mp3", ".ogg", ".wav", ".mp4")):
            file_url = urljoin("https://en.wikipedia.org/", href)
            download_file(file_url, media_folder)

# Function to save references and external links
def save_references(content_div, folder_path):
    # References
    references = content_div.find_all("ol", {"class": "references"})
    with open(os.path.join(folder_path, "references.txt"), "w", encoding="utf-8") as f:
        for ref_list in references:
            for li in ref_list.find_all("li"):
                f.write(li.get_text(strip=True) + "\n\n")

    # External links
    external_links = content_div.find("span", {"id": "External_links"})
    with open(os.path.join(folder_path, "external_links.txt"), "w", encoding="utf-8") as f:
        if external_links:
            ul = external_links.find_next("ul")
            if ul:
                for li in ul.find_all("li"):
                    a = li.find("a", href=True)
                    if a:
                        f.write(a['href'] + " - " + li.get_text(strip=True) + "\n")

# Main infinite loop to download random English Wikipedia articles
while True:
    try:
        url = "https://en.wikipedia.org/wiki/Special:Random"
        r = requests.get(url, headers=HEADERS, timeout=10)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # Get page title
        page_title = soup.find("h1", {"id": "firstHeading"}).text
        downloaded, folder_path = is_downloaded(page_title)
        if downloaded:
            print(f"Already downloaded: {page_title}")
            time.sleep(1)
            continue

        os.makedirs(folder_path, exist_ok=True)

        # Main content
        content_div = soup.find("div", {"id": "mw-content-text"})
        if not content_div:
            print(f"No content for {page_title}")
            time.sleep(1)
            continue

        # Extract sections and paragraphs
        current_heading = "Introduction"
        section_text = []
        article_lines = []

        for element in content_div.find_all(["h2", "h3", "p"]):
            if element.name in ["h2", "h3"]:
                if section_text:
                    article_lines.append(f"\n=== {current_heading} ===\n")
                    article_lines.extend(section_text)
                    section_text = []
                heading = element.get_text(strip=True).replace("[edit]", "")
                current_heading = heading
            elif element.name == "p":
                text = element.get_text(strip=True)
                if text:
                    section_text.append(text)

        if section_text:
            article_lines.append(f"\n=== {current_heading} ===\n")
            article_lines.extend(section_text)

        # Save article text
        txt_file = os.path.join(folder_path, f"{safe_filename(page_title)}.txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            for line in article_lines:
                f.write(line + "\n")

        # Download images
        download_images(content_div, os.path.join(folder_path, "images"))

        # Save tables
        save_tables(content_div, folder_path)

        # Download linked media files
        download_linked_files(content_div, os.path.join(folder_path, "media"))

        # Save references and external links
        save_references(content_div, folder_path)

        # Log the article
        log_article(page_title, folder_path, r.url)

        print(f"Downloaded: {page_title} text, images, tables, media, references")

        # Polite delay
        time.sleep(random.uniform(2, 5))

    except Exception as e:
        print("Error:", e)
        time.sleep(5)