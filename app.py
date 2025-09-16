from flask import Flask, render_template, request, session
from scrape_amazon import scrape_amazon
from scrape_noon import scrape_noon
from scrape_aliexpress import scrape_aliexpress
from amazon_summarizer import summarize_amazon_reviews as summarize_reviews


app = Flask(__name__)
app.secret_key = "price_compare_app_secret_key"  # for session management

# --- Coloring  ---
def color_prices(data):
    prices = [item["price"] for item in data]
    min_price = min(prices)
    max_price = max(prices)
    for item in data:
        if item["price"] == min_price:
            item["color"] = "green"
        elif item["price"] == max_price:
            item["color"] = "red"
        else:
            item["color"] = "white"
    return data

# --- Home page ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Handle product search ---
@app.route('/search', methods=["POST"])
def search():
    product = request.form['product']

    # scrapers
    amazon_result = scrape_amazon(product)
    noon_result = scrape_noon(product)
    ali_result = scrape_aliexpress(product)

    results = [amazon_result, noon_result, ali_result]
    results = color_prices(results)


    session['results'] = results
    session['query'] = product

    for item in results:
        item["query"] = product  

    return render_template('results.html', results=results, query=product)

# --- Review summarizer  ---
@app.route('/summarize', methods=['POST'])
def summarize():
    site = request.form['site']
    link = request.form['link']
    product = request.form.get('query', "Your product")
    
    
    summary = summarize_reviews(site, link)
    
  
    results = session.get('results', [])
    query = session.get('query', product)
    
    
    for item in results:
        if item["name"] == site:
            item["summary"] = summary
    
    # default 
    if not results:
        results = [
            {"name": site, "price": 0.0, "link": link, "color": "white", "rating": "N/A", "summary": summary}
        ]

    return render_template("results.html", results=results, query=query)

# --- Run the app ---
if __name__ == '__main__':
    app.run(debug=True)