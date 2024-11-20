import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
import re

DEFAULT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

# This script ONLY processes the STATIC HTML content received from the server!
# for modern websites that use JavaScript to load images or links dynamically after the initial HTML is rendered
# headless browsers (Selenium or Playwright) which render the page fully, including any JavaScript-loaded content have to be used

# Update extract_links_from_json to also check for image extensions
def extract_links_from_json(data, base_url=None):
    urls = []
    if isinstance(data, dict):
        for key, value in data.items():
            urls.extend(extract_links_from_json(value, base_url))
    elif isinstance(data, list):
        for item in data:
            urls.extend(extract_links_from_json(item, base_url))
    elif isinstance(data, str):
        if data.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            urls.append(urljoin(base_url, data) if base_url else data)
        elif data.startswith(('http://', 'https://')):
            urls.append(urljoin(base_url, data) if base_url else data)
    return urls

# problem: some URLs might not be images
# solution: check the content type of the response before downloading the image
# problem: The script might download the same image multiple times if it appears on multiple pages
# solution: check if file(name) already exists to avoid duplicates
def download_images(image_urls, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for url in image_urls:
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            if response.headers["Content-Type"].startswith("image"):
                filename = os.path.join(output_dir, os.path.basename(url))
                if os.path.exists(filename):
                    print(f"File already exists, skipping: {filename}")
                    continue
                with open(filename, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"Downloaded: {filename}")
            else:
                print(f"Skipping: {url} (Not an image)")
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")

# problem: Images or links might be stored in attributes other than <img src>
# solution: Extract images from custom attributes like data-src, div style, CSS styles...
def is_valid_image_url(url, image_formats):
    return url and any(url.lower().endswith(ext) for ext in image_formats)

def extract_image_urls(soup, base_url, image_formats):
    image_urls = []
    
    def process_and_add(url):
        full_url = urljoin(base_url, url)
        if is_valid_image_url(full_url, image_formats):
            image_urls.append(full_url)
    
    # Standard <img> tags
    for img_tag in soup.find_all("img"):
        process_and_add(img_tag.get("src"))
    
    # <source> in <picture> or <video>
    for source in soup.find_all('source', srcset=True):
        process_and_add(source['srcset'])
    
    # Meta og:image
    for meta in soup.find_all('meta', property="og:image", content=True):
        process_and_add(meta['content'])
    
    # Link icons
    for link in soup.find_all('link', href=True):
        process_and_add(link['href'])
    
    # Inline styles
    for div in soup.find_all("div", style=True):
        style = div.get("style")
        if "background-image" in style:
            url = style.split("url(")[1].split(")")[0].strip("'\"")
            process_and_add(url)
    
    # Custom attributes
    for tag in soup.find_all(attrs={"data-src": True}):
        process_and_add(tag['data-src'])
    
    return image_urls

# subject specifies: URLs must start with http:// or https://. else requests.get() will raise an exception otherwise
# problem: The script might get stuck in an infinite loop if the website has circular links
# solution: Keep track of visited URLs and avoid revisiting them
# problem: some links might not be in the link tag <a href> but in JavaScript code or CSS or the page might not be HTML
# solution: use bautifulsoup(for html; including alternative link tags) AND regex to find all URLs in the response text and crawl them
# problem: some links might lead to external domains -> crawling unintended websites, wasting resources, or violating website terms of use
# solution: use netloc to compare the domain of the next URL with the base URL
def crawl_page(url, output_dir, image_formats, visited, depth, max_depth):
    if depth > max_depth or url in visited:
        return []

    visited.add(url)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return []

    print(f"Crawling: {url} (Depth {depth})")
    image_urls = []

    if "text/html" in content_type:
        soup = BeautifulSoup(response.text, "html.parser")
        image_urls.extend(extract_image_urls(soup, url, image_formats))
        for link_tag in soup.find_all("a", href=True):
            next_url = urljoin(url, link_tag["href"])
            if urlparse(next_url).netloc == urlparse(url).netloc:
                image_urls.extend(crawl_page(next_url, output_dir, image_formats, visited, depth + 1, max_depth))
        for script_tag in soup.find_all("script", src=True):
            next_url = urljoin(url, script_tag["src"])
            if urlparse(next_url).netloc == urlparse(url).netloc:
                image_urls.extend(crawl_page(next_url, output_dir, image_formats, visited, depth + 1, max_depth))
        for link_tag in soup.find_all("link", href=True):
            next_url = urljoin(url, link_tag["href"])
            if urlparse(next_url).netloc == urlparse(url).netloc:
                image_urls.extend(crawl_page(next_url, output_dir, image_formats, visited, depth + 1, max_depth))

    elif "text/plain" in content_type:
        text_content = response.text
        url_regex = r'https?://[^\s"]+'
        found_links = re.findall(url_regex, text_content)
        image_regex = r'https?://[^\s"]+\.(jpg|jpeg|png|gif|bmp)'
        image_urls.extend(re.findall(image_regex, text_content))
        for next_url in found_links:
            if urlparse(next_url).netloc == urlparse(url).netloc:
                image_urls.extend(crawl_page(next_url, output_dir, image_formats, visited, depth + 1, max_depth))

    elif "application/json" in content_type:
        try:
            data = response.json()
            found_links = extract_links_from_json(data, base_url=url)
            image_urls.extend([link for link in found_links if link.endswith(tuple(image_formats))])
            for next_url in found_links:
                if urlparse(next_url).netloc == urlparse(url).netloc:
                    image_urls.extend(crawl_page(next_url, output_dir, image_formats, visited, depth + 1, max_depth))
        except Exception as e:
            print(f"Error processing JSON at {url}: {e}")

    elif content_type.startswith("image/"):
        print(f"Direct image found: {url}")
        image_urls.append(url)

    else:
        print(f"Unhandled Content-Type: {content_type}")

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

    print(f"Found {len(image_urls)} potential image urls. Downloading...")
    download_images(set(image_urls), output_dir)

if __name__ == "__main__":
    main()
