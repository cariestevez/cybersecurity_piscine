import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse

DEFAULT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

# This script ONLY processes the STATIC HTML content received from the server!
# modern websites use JavaScript to load images or links dynamically after the initial HTML is rendered
# headless browsers (Selenium or Playwright) which render the page fully, including any JavaScript-loaded content have to be used

# problem: some URLs might not be images
# solution: check the content type of the response before downloading the image
# problem: The script might download the same image multiple times if it appears on multiple pages
# solution: Use a set to store previously saved image-URLs and avoid duplicates or check if file(name) already exists
def download_images(image_urls, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for url in image_urls:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            if response.headers["Content-Type"].startswith("image"):
                filename = os.path.join(output_dir, os.path.basename(url))
                # add condition to check if the file already exists
                with open(filename, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"Downloaded: {filename}")
            else:
                print(f"Skipping: {url} (Not an image)")
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")

# problem: Images or links might be stored in attributes other than <img src> or <a href>
# solution: Extract images from custom attributes like data-src, div style or CSS styles
def extract_image_urls(soup, base_url, image_formats):
    image_urls = []
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")
        if src and any(src.lower().endswith(ext) for ext in image_formats):
            full_url = urljoin(base_url, src)
            image_urls.append(full_url)
    
    for div in soup.find_all("div", style=True):
        style = div.get("style")
        if "background-image" in style:
            url = style.split("url(")[1].split(")")[0].strip("'\"")
            image_urls.append(urljoin(base_url, url))

    return image_urls

# problem: some attributes might contain invalid URLs, incorrectly formatted URLs like missing protocol or domain
# problem: The script might get stuck in an infinite loop if the website has circular links
# solution: Keep track of visited URLs and avoid revisiting them
# problem: some links might not be in the link tag <a href> but in JavaScript code or CSS or the page might not be HTML
# URLs must start with http:// or https://, else requests.get() will raise an exception
# solution: use regex to find all URLs in the response text and crawl them
def crawl_page(url, output_dir, image_formats, visited, depth, max_depth):
    if depth > max_depth or url in visited:
        return []

    visited.add(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return []

    print(f"Crawling: {url} (Depth {depth})")
    image_urls = extract_image_urls(soup, url, image_formats)

    for link_tag in soup.find_all("a", href=True):
        href = link_tag.get("href")
        next_url = urljoin(url, href)

        if urlparse(next_url).netloc == urlparse(url).netloc:
            image_urls.extend(crawl_page(next_url, output_dir, image_formats, visited, depth + 1, max_depth))

    return image_urls

def main():
    parser = argparse.ArgumentParser(description="Spider to download images from a website.")
    parser.add_argument("url", help="The URL to start crawling from.")
    parser.add_argument("-r", action="store_true", help="Enable recursive crawling.")
    parser.add_argument("-l", type=int, default=5, help="Maximum depth level for recursive crawling (default: 5).")
    parser.add_argument("-p", type=str, default="./data", help="Path to save downloaded images (default: ./data).")

    args = parser.parse_args()

    url = args.url
    recursive = args.r
    max_depth = args.l
    output_dir = args.p

    visited = set()
    image_urls = crawl_page(url, output_dir, DEFAULT_EXTENSIONS, visited, 0, max_depth if recursive else 0)

    print(f"Found {len(image_urls)} images. Downloading...")
    download_images(set(image_urls), output_dir)

if __name__ == "__main__":
    main()
