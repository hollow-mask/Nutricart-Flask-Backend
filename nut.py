import requests
from decimal import Decimal, getcontext
from functools import lru_cache
# import requests

# def search_top10_nutriscores(product_name):
#     """
#     Search Open Food Facts for a product name and fetch Nutri-Score
#     for the top 10 search results.
#     """
#     url = "https://world.openfoodfacts.org/cgi/search.pl"
#     params = {
#         "search_terms": product_name,
#         "search_simple": 1,
#         "action": "process",
#         "json": 1,
#         "page_size": 10  # Get top 10 results
#     }
#     response = requests.get(url, params=params)

#     if response.status_code == 200:
#         data = response.json()
#         products = data.get('products', [])

#         if not products:
#             return "No products found for your search."

#         results = []
#         for i, product in enumerate(products, 1):
#             name = product.get('product_name', 'Unknown Product')
#             nutriscore = product.get('nutriscore_grade', 'unknown').upper()
#             nova = product.get('nova_group', 'unknown')
#             results.append(f"{i}. {name}\n   Nutri-Score: {nutriscore}, NOVA: {nova}")

#         return "\n".join(results)

#     else:
#         return f"Error: API returned status code {response.status_code}"


# print(search_top10_nutriscores("avocado"))


nutrition_cache = {}


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class NutritionScorer:
    """
    Scores food items in real-time using macro and micro nutrients from Open Food Facts API.
    """

    def __init__(self):
        self.api_base = "https://world.openfoodfacts.org"
    

    
    def fetch_nutrients(self, product_name, s):
        """
        Search Open Food Facts API for a product name and return nutrient data for the first match.
        """
        search_url = f"{self.api_base}/cgi/search.pl"
        params = {
            "search_terms": product_name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 1  # Only get top result for now
        }

        # response = requests.get(search_url, params=params)
        response = s.get(search_url, params=params)
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code}")

        data = response.json()
        products = data.get('products', [])
        if not products:
            raise Exception(f"No product found for '{product_name}'")

        return products[0].get('nutriments', {}), products[0].get('product_name', 'Unknown Product')

    def calculate_score(self, nutrients):
        """
        Calculate nutrition score based on macro and micro nutrients.
        """
        score = 0

        # ----------------------------
        # ✅ Positive Macronutrients
        # ----------------------------
        # protein = nutrients.get('proteins_100g', 0)
        # fiber = nutrients.get('fiber_100g', 0)
        protein = safe_float(nutrients.get('proteins_100g'))
        fiber = safe_float(nutrients.get('fiber_100g'))

        score += min((protein // 5) * 1, 10)  # +1 per 5g protein
        score += min((fiber // 2) * 2, 10)    # +2 per 2g fiber

        # ----------------------------
        # ❌ Negative Macronutrients
        # ----------------------------
        # sat_fat = nutrients.get('saturated-fat_100g', 0)
        # sugars = nutrients.get('sugars_100g', 0)
        # sodium = nutrients.get('sodium_100g', 0)
        sat_fat = safe_float(nutrients.get('saturated-fat_100g'))
        sugars = safe_float(nutrients.get('sugars_100g'))
        sodium = safe_float(nutrients.get('sodium_100g'))

        score -= min((sat_fat // 2) * 1, 10)     # -1 per 2g sat fat
        score -= min((sugars // 5) * 1, 10)      # -1 per 5g sugars
        score -= min((sodium // 400) * 1, 10)    # -1 per 400mg sodium

        # ----------------------------
        # ✅ Positive Micronutrients
        # ----------------------------
        
        vitamin_c = safe_float(nutrients.get('vitamin-c_100g'))
        calcium = safe_float(nutrients.get('calcium_100g'))
        iron = safe_float(nutrients.get('iron_100g'))
        potassium = safe_float(nutrients.get('potassium_100g'))
        # vitamin_c = nutrients.get('vitamin-c_100g', 0)
        # calcium = nutrients.get('calcium_100g', 0)
        # iron = nutrients.get('iron_100g', 0)
        # potassium = nutrients.get('potassium_100g', 0)

        if vitamin_c >= 10: score += 1
        if calcium >= 10:   score += 1
        if iron >= 10:      score += 1
        if potassium >= 300: score += 1

        # ----------------------------
        # 🔄 Normalize Score (0–100)
        # ----------------------------
        normalized_score = min(100, max(0, int((score + 30) * (100 / 50))))
        return normalized_score

    def score_food(self, product_name, s):
        """
        Fetch nutrient data for a product and return its nutrition score.
        """
        key = product_name.strip().lower()
        if key in nutrition_cache:
            return nutrition_cache[key]
        nutrients, name = self.fetch_nutrients(product_name, s)
        score = self.calculate_score(nutrients)
        nutrition_cache[key] = {"product": name, "score": score}
        return {"product": name, "score": score}

class Food:
    def __init__(self,name, price, quantity, nutrition_score):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.nutrition_score = nutrition_score
        # foods.append(self)
        
    def total_price(self):
        return self.price * self.quantity
    
#left of here trying to store foods into shoppping cart and calculate budget   
class ShoppingCart:
    def __init__(self, budget):
       self.budget = budget
       self.cart =[]
       self.bill = 0
       
    # def calc_bill(self, price):
    #     getcontext().prec = 4 # Example: 4 significant digits
    #     new_bill = self.bill + price
    #     number = Decimal(new_bill)
    #     fixed_bill = number.quantize(Decimal('0.00')) # Quantize to two decimal places
    #     return fixed_bill
       
    def add_to_cart(self, food):
        self.cart.append(food)
        
        self.bill += food.total_price()
        
            
if __name__ == "__main__":
    
    # import csv

    
    # foods = []
    
    # scorer = NutritionScorer()
    # shopping_cart = ShoppingCart(500)
    # with open("grocery_list.csv", "r", encoding="utf-8") as csv_file:
    #     csv_reader = csv.reader(csv_file)

    #     next(csv_reader)

    #     for line in csv_reader:
            
            
    #         result = scorer.score_food(str(line[0]))
    #         f = Food(line[0], float(line[1]), float(line[2]), result['score'])
    #         shopping_cart.add_to_cart(f)
            # print(f"{line[3]}\n")
    
    
    # bill = 0
    # for i in foods:
    #     bill += i.total_price()
    
    # print(f"your grocery bill is {shopping_cart.bill:.2f}$ dollars")
    
    
    scorer = NutritionScorer()
    #Score Avocado
    result = scorer.score_food("raw chicken tenderloins")
    print(f"{result['product']}: Nutrition Score = {result['score']}/100 {int(result['score'])}")
    
    #Score Coca-Cola
    result = scorer.score_food("Coca-Cola")
    print(f"{result['product']}: Nutrition Score = {result['score']}/100")



