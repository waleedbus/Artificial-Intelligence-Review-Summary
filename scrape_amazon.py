import requests
from bs4 import BeautifulSoup
import re
import time
import random

def scrape_amazon(product_name):
    search_query = product_name.replace(' ', '+')

    urls = [
        f"https://www.amazon.sa/-/en/s?k={search_query}",
        f"https://www.amazon.sa/s?k={search_query}",
        f"https://www.amazon.sa/-/en/gp/search?k={search_query}"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.amazon.sa/',
        'Cache-Control': 'max-age=0'
    }

    error_message = None

    for url in urls:
        try:
            time.sleep(random.uniform(1, 2))

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                error_message = f"Error: {response.status_code} for url: {url}"
                continue

            soup = BeautifulSoup(response.content, 'html.parser')

            container = soup.select_one('div.s-result-item[data-component-type="s-search-result"]') \
                        or soup.select_one('div.sg-col-4-of-24.sg-col-4-of-12.s-result-item') \
                        or soup.select_one('div.s-result-item')

            if not container:
                continue

            # --- Extract name ---
            name = "N/A"
            name_selectors = [
                'h2 a span',
                '.a-size-medium.a-color-base.a-text-normal',
                '.a-size-base-plus.a-color-base.a-text-normal',
                '.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2', 
                '.a-link-normal.s-underline-text.s-underline-link-text span',
                '.a-link-normal .a-text-normal'
            ]

            for selector in name_selectors:
                name_element = container.select_one(selector)
                if name_element and name_element.text.strip():
                    name = name_element.text.strip()
                    break

            
            link = "#"
            link_element = container.select_one('h2 a') or container.select_one('.a-link-normal')
            if link_element and link_element.has_attr('href'):
                product_link = link_element['href']
                link = "https://www.amazon.sa" + product_link if product_link.startswith('/') else product_link

           
            price = 0.0
            price_element = container.select_one("span.a-price .a-offscreen")
            if price_element:
                price_text = price_element.text.strip()
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        price = float(price_match.group())
                    except ValueError:
                        price = 0.0

            
            rating = "N/A"
            rating_tag = container.select_one("span.a-icon-alt")
            if rating_tag:
                rating = rating_tag.get_text(strip=True)

            
            if name == "N/A" and link != "#":
                name = extract_product_name_from_link(link)
                if name == "N/A":
                    name = f"Amazon Product for '{product_name}'"

            return {
                "name": f"{name} - Amazon",
                "price": price,
                "link": link,
                "rating": rating
            }

        except requests.exceptions.RequestException as e:
            error_message = f"Request Error: {str(e)}"
            continue

        except Exception as e:
            error_message = f"General Error: {str(e)}"
            continue

    return {
        "name": "Error fetching Amazon data",
        "price": 0.0,
        "link": "#",
        "rating": "N/A"
    }

def extract_product_name_from_link(link):
    if not link or link == '#':
        return 'N/A'
    path = link.split('amazon.sa')[-1]
    parts = path.split('/')
    for part in parts:
        if part and part not in ['dp', 'ref', 'sr', '-', 'en'] and not part.startswith('B0'):
            name = ' '.join(word.capitalize() for word in part.split('-'))
            if len(name) > 5:
                return name
    return 'N/A'
