import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json

# DeepSeek API
DEEPSEEK_API_KEY = "sk-7179a0c490934f77a8d5da89875b3603"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def extract_amazon_reviews(product_url, num_reviews=10):
    #Extract reviews from an Amazon product page
    if product_url == "#" or not product_url:
        return ["Unable to find product reviews"]
    
    reviews_url = product_url
    if "/dp/" in product_url:
        asin_match = re.search(r'/dp/([A-Z0-9]+)', product_url)
        if asin_match:
            asin = asin_match.group(1)
            reviews_url = f"https://www.amazon.sa/-/en/product-reviews/{asin}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Referer': 'https://www.amazon.sa/'
    }
    
    reviews = []
    page = 1
    max_pages = 3  # Try up to 3 pages of reviews
    
    try:
        while len(reviews) < num_reviews and page <= max_pages:
            # Construct page URL
            page_url = reviews_url
            if page > 1:
                if '?' in page_url:
                    page_url += f"&pageNumber={page}"
                else:
                    page_url += f"?pageNumber={page}"
            
           
            time.sleep(random.uniform(1, 2))  #delay
            response = requests.get(page_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
               
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            #selectors to find reviews
            selectors = [
                '.review-text-content span',  
                '[data-hook="review-body"] span',  
                '.a-row.a-spacing-small.review-data',  
                '.review-data',  
                'div[data-hook="review"] .a-size-base.review-text',  
                'span.review-text' 
            ]
            
            found_reviews_on_page = False
            for selector in selectors:
                review_elements = soup.select(selector)
                if review_elements:
                    for review_element in review_elements:
                        review_text = review_element.get_text(strip=True)
                        if review_text and len(review_text) > 5: #filter short reviews
                            reviews.append(review_text)
                            found_reviews_on_page = True
                            if len(reviews) >= num_reviews:
                                break
                
                if len(reviews) >= num_reviews:
                    break
            
            # if doesnt work
            if not found_reviews_on_page:
            
                review_containers = soup.select('.review') or soup.select('div[data-hook="review"]')
                for container in review_containers:
                    review_section = container.select_one('.review-data') or container.select_one('[data-hook="review-body"]')
                    if review_section:
                        review_text = review_section.get_text(strip=True)
                    else:
                        review_text = container.get_text(strip=True)
                    
                    if review_text and len(review_text) > 10:
                        reviews.append(review_text)
                        found_reviews_on_page = True
                        if len(reviews) >= num_reviews:
                            break
            
            if not found_reviews_on_page:
                break
                
            page += 1
        
        if not reviews:
            return ["No reviews found for this product"]
            
       
        
        return reviews[:num_reviews]  # Limit to requested number
        
    except Exception as e:
        print(f"Error fetching reviews: {str(e)}")
        return [f"Error fetching reviews: {str(e)}"]

def generate_review_summary(reviews):
    if not reviews or (isinstance(reviews[0], str) and reviews[0].startswith(("Unable", "No reviews", "Error"))):
        return "No reviews available to generate summary"
    
    try:
        combined_reviews = "\n".join([f"Review {i+1}: {review}" for i, review in enumerate(reviews)])
        
        prompt = f"""Please analyze these product reviews and provide a concise summary (3-5 sentences) tell what is most feel about this product without
retyping the orginal reviews your only allowed to retype the negative ones

Reviews:
{combined_reviews}"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }

       
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        summary = result['choices'][0]['message']['content'].strip()
        
        return summary
        
    except Exception as e:
        return f"Could not generate summary: {str(e)}"

def search_amazon_product(product_name):
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

    for url in urls:
        try:
            print(f"Searching URL: {url}")
            time.sleep(random.uniform(1, 2))  # delay
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Failed with status code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')

            containers = soup.select('div.s-result-item[data-component-type="s-search-result"]') or \
                         soup.select('div.sg-col-4-of-24.sg-col-4-of-12.s-result-item') or \
                         soup.select('div.s-result-item')
            
            if not containers:
                print("No product containers found, trying alternative approach")
                containers = soup.select('div[data-asin]')
            
            for container in containers:
                rating_count = container.select_one('.a-size-base.s-underline-text') or \
                               container.select_one('span.a-size-base:contains("reviews")')
                
                link_element = container.select_one('h2 a') or container.select_one('.a-link-normal')
                if not link_element or not link_element.has_attr('href'):
                    continue
                    
                product_link = link_element['href']
                link = "https://www.amazon.sa" + product_link if product_link.startswith('/') else product_link
                
                name_element = container.select_one('h2 a span') or container.select_one('.a-size-medium.a-color-base.a-text-normal')
                product_name = name_element.text.strip() if name_element else "Found product"
                
                if rating_count:
                    print(f"Found product with reviews: {product_name}")
                    return link
            
            if containers and len(containers) > 0:
                first_container = containers[0]
                link_element = first_container.select_one('h2 a') or first_container.select_one('.a-link-normal')
                if link_element and link_element.has_attr('href'):
                    product_link = link_element['href']
                    link = "https://www.amazon.sa" + product_link if product_link.startswith('/') else product_link
                    
                    name_element = first_container.select_one('h2 a span') or first_container.select_one('.a-size-medium.a-color-base.a-text-normal')
                    product_name = name_element.text.strip() if name_element else "Found product"
                    
                    print(f"Found product: {product_name}")
                    return link

        except Exception as e:
            print(f"Error during search: {str(e)}")
            continue

    print("No products found in search results")
    return None

def summarize_amazon_reviews(product_name=None, product_url=None):
    if product_name and not product_url:
        product_url = search_amazon_product(product_name)
        
    if not product_url:
        return "Unable to find product on Amazon"
        
    reviews = extract_amazon_reviews(product_url)
    
    if isinstance(reviews[0], str) and reviews[0].startswith(("Unable", "Error", "No reviews")):
        return reviews[0]
        
    summary = generate_review_summary(reviews)
    return reviews, summary



if __name__ == "__main__":
    main()