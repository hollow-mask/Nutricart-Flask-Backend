import requests
from rapidfuzz import process, fuzz
from unidecode import unidecode

def normalize_ingredient(name):
    """
    Clean and normalize ingredient names for better matching.
    """
    name = name.lower()
    name = unidecode(name)  # remove accents
    blacklist = ["fresh", "organic", "chopped", "diced", "sliced", 
    "minced","fresh", "frozen", "organic", "cooked", "pre-cooked", "pre-cut", "pre-washed",
    "dried", "canned", "bottled", "powdered", "concentrated", "unsweetened", "sweetened",
    "salted", "unsalted", "low-sodium", "reduced-fat", "full-fat", "whole", "skim",
    "lean", "fat-free", "extra-virgin"]
    words = [w for w in name.split() if w not in blacklist]
    return " ".join(words)

def search_open_food_facts(ingredient, page_size=26):
    """
    Query Open Food Facts API for a given ingredient with filters.
    Returns a list of matching products.
    """
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        # "search_terms": ingredient,
        # "categories": "",  # Optional: add category here (e.g., "raw chicken")
        "countries": "united-states",
        # "states": "",
        # "sort_by": "popularity",
        # "page_size": page_size,
        "fields": "product_name,code",
        # "action": "process",
        # "json": 1
        "search_terms": ingredient,
        # "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size  # Only get top result for now
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("products", [])

# def fuzzy_match(ingredient, products):
#     """
#     Find the best fuzzy match for ingredient in the API product names.
#     """
#     product_names = [p["product_name"] for p in products if "product_name" in p]
#     if not product_names:
#         return None
#     best_match, score, idx = process.extractOne(
#         ingredient, product_names, scorer=fuzz.WRatio
#     )
#     return products[idx] if score > 75 else None  # Threshold 75%
def fuzzy_match(ingredient, products):
    """
    Find the best fuzzy match for ingredient in a list of product dicts.
    Each product dict contains at least 'name' and 'price' keys.
    Returns the best matching product dict if similarity > 75%, else None.
    """
    product_names = [p["name"] for p in products if "name" in p]
    if not product_names:
        return None  # No products to compare

    best_match, score, idx = process.extractOne(
        ingredient, product_names, scorer=fuzz.WRatio
    )

    # Debug output (optional)
    print(f"🔍 Ingredient: {ingredient}")
    print(f"Best match: {best_match} (Score: {score}%)")

    # Return the full product dict if similarity is above threshold
    return products[idx] if score > 75 else None

def get_price_from_open_prices(barcode):
    """
    Query Open Prices API for the barcode.
    Returns the latest price if available.
    """
    price_url = f"https://prices.openfoodfacts.org/api/v1/entry?code={barcode}"
    response = requests.get(price_url)
    if response.status_code != 200:
        return None
    data = response.json()
    entries = data.get("entries", [])
    if not entries:
        return None
    # Take most recent price
    latest_entry = sorted(entries, key=lambda x: x["date"], reverse=True)[0]
    return latest_entry.get("price")

def find_ingredient_prices(ingredients):
    """
    Main function: takes list of ingredients, finds matching barcodes & prices.
    """
    results = []
    for ingredient in ingredients:
        print(f"🔎 Searching for: {ingredient}")
        normalized = normalize_ingredient(ingredient)
        products = search_open_food_facts(normalized)

        if not products:
            print(f"⚠️ No products found for '{ingredient}' in OFF.")
            results.append({"ingredient": ingredient, "barcode": None, "price": None})
            continue

        best_product = fuzzy_match(normalized, products) or products[0]

        barcode = best_product.get("code")
        product_name = best_product.get("product_name")
        print(f"✅ Matched to: {product_name} (Barcode: {barcode})")

        price = get_price_from_open_prices(barcode)
        if price:
            print(f"💲 Price found: ${price:.2f}")
        else:
            print(f"⚠️ No price data found for barcode {barcode}")

        results.append({
            "ingredient": ingredient,
            "matched_product": product_name,
            "barcode": barcode,
            "price": price
        })

    return results
