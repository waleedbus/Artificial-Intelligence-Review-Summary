import requests
from bs4 import BeautifulSoup
import urllib.parse

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.111 Mobile Safari/537.36"
}

def scrape_noon(product_name):
    base_url = "https://www.noon.com/saudi-en/search"
    params = {"q": product_name}
    search_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {
                "name": "Noon product not found",
                "price": 0.0,
                "link": "#",
                "rating": "N/A"
            }

        soup = BeautifulSoup(response.text, "html.parser")

        product = soup.find('div', {
            'class': 'ProductBoxLinkHandler_linkWrapper__b0qZ9'
        })

        if not product:
            return {
                "name": "Noon product not found",
                "price": 0.0,
                "link": "#",
                "rating": "N/A"
            }

        name_tag = product.find('h2', {'class': 'ProductDetailsSection_title__JorAV'})
        price_tag = product.find('strong', {'class': 'Price_amount__2sXa7'})
        rating_tag = product.find('div', {'class': 'RatingPreviewStar_textCtr__sfsJG'})
        link_tag = product.find('a', {'class': 'ProductBoxLinkHandler_productBoxLink__FPhjp'})

        name = name_tag.text.strip() if name_tag else "N/A"
        link = "https://www.noon.com" + link_tag['href'] if link_tag else "#"
        
        price = 0.0
        if price_tag:
            price_text = price_tag.text.strip().replace(",", "")
            try:
                price = float(price_text)
            except ValueError:
                price = 0.0
        
        rating = rating_tag.text.strip() if rating_tag else "N/A"

        return {
            "name": f"{name} - Noon",
            "price": price,
            "link": link,
            "rating": rating
        }

    except Exception as e:
        return {
            "name": "Error fetching Noon data",
            "price": 0.0,
            "link": "#",
            "rating": f"Error: {str(e)}"
        }
