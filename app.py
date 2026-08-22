from flask import Flask, jsonify, request
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import requests
import logic
import nut
import json
import os

app = Flask(__name__)
CORS(app)
# Mock recipe data

s = requests.Session()

price_cache = {}

prices = [
    {"name": "chicken", "price": 3.00},
    {"name": "pasta spaghetti", "price": 2.34},
    {"name": "cream", "price": 2.89},
    {"name": "broccoli", "price": 1.67},
    {"name": "carrot", "price": 1.89},
    {"name": "soy sauce", "price": 3.56},
    {"name": "beef", "price": 3.45},
    {"name": "tortilla", "price": 6.97},
    {"name": "cheddar cheese", "price": 4.78},
    {"name": "salmon", "price": 8.90},
    {"name": "lettuce", "price": 1.50},
    {"name": "organic avocado", "price": 1.00},
    {"name": "jeff's rib eye Steak", "price": 7.00},
    {"name": "tony's ceaser ranch", "price": 7.00},
    {"name": "fresh eggplant", "price": 2.30},
    {"name": "fresh eggplant", "price": 2.30},
    {"name": "salmon", "price": 4.46},
    {"name": "spinach", "price": 2.56},
    {"name": "ranch dressing", "price": 6.96},
    {"name": "quinoa", "price": 7.77},
    {"name": "tofu", "price": 6.21},
    {"name": "carrot", "price": 9.45},
    {"name": "mushroom", "price": 3.86},
    {"name": "tomato", "price": 2.47},
    {"name": "soy sauce", "price": 6.12},
    {"name": "onion", "price": 3.18},
    {"name": "cucumber", "price": 3.0},
    {"name": "lettuce", "price": 1.77},
    {"name": "zucchini", "price": 4.05},
    {"name": "broccoli", "price": 7.77},
    {"name": "turkey", "price": 3.0},
    {"name": "eggplant", "price": 2.03},
    {"name": "pasta", "price": 2.81},
    {"name": "chicken breast", "price": 7.28},
    {"name": "potato", "price": 8.59},
    {"name": "beef", "price": 4.88},
    {"name": "steak", "price": 3.19},
    {"name": "avocado", "price": 6.02},
    {"name": "bell pepper", "price": 7.55},
    {"name": "garlic", "price": 4.28},
    {"name": "cheese", "price": 2.11},
]


def get_price_ingredient(ingredient):
    product = logic.fuzzy_match(ingredient, prices)
    if product:
        # print(f"{product["name"]} and  {product["price"]}\n")
        return product
    return {"error": "Ingredient not found"}


def calc_health_score(recipe, s, ingredient_scores):
    # scorer = nut.NutritionScorer()
    # ingredient_ct = len(recipe["ingredients"])
    # score = 0
    # for ings in recipe["ingredients"]:
    #     result = scorer.score_food(ings, s)
    #     score += int(result['score'])

    # meal_health_score = score / ingredient_ct
    # return meal_health_score
    scorer = nut.NutritionScorer()
    ingredients = recipe["ingredients"]

    def score_ing(ing):
        try:
            result = scorer.score_food(ing, s)
            ingredient_scores[ing] = int(result["score"])
            return int(result["score"])
        except:
            return 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        scores = list(executor.map(score_ing, ingredients))

    total_score = sum(scores)
    return total_score / len(ingredients)


def calc_recipe_price(recipe):
    ingredients = recipe["ingredients"]

    def fetch_price(ingredient):
        if ingredient in price_cache:
            return price_cache[ingredient]
        try:

            # response = requests.get(f"http://127.0.0.1:5000/price/{ingredient}")
            # print(f"UTGJYVUGJHK><NBKCLU>KJBVUY>JUHKHCGTCJHUYCUJHKB:IUVHKJB\n")
            response = get_price_ingredient(ingredient)
            # print(f"AHHHHHHHHHHHHHHHHHHHHHHH {response}\n")
            if "error" in response:
                raise Exception("Ingredient not found")
            else:
                price_cache[ingredient] = response["price"]
                return response["price"]
        except:
            pass
        return 0.0

    with ThreadPoolExecutor(max_workers=5) as executor:
        prices = list(executor.map(fetch_price, ingredients))
    return sum(prices)


recipes_by_diet_combo = defaultdict(list)


with open("recipe_data.json", "r") as f:
    data = json.load(f)
    for recipe in data:
        ingredient_socres = defaultdict(int)
        diet_combo = frozenset(recipe["diet"])  # Use frozenset so it can be a dict key

        score = calc_health_score(recipe, s, ingredient_socres)
        price = calc_recipe_price(recipe)

        recipe["price"] = round(price, 2)
        # print(f"recipe: {recipe["name"]} and price: {recipe["price"]}\n")
        recipe["score"] = round((score / price), 2)
        recipe["ingredient_scores"] = ingredient_socres
        recipes_by_diet_combo[diet_combo].append(recipe)
    for rec in recipes_by_diet_combo:
        sorted(recipes_by_diet_combo[rec], key=lambda r: r["score"], reverse=True)


recipes = [
    {
        "id": 1,
        "name": "Chicken Alfredo",
        "calories": 600,
        "ingredients": ["chicken breasts", "pasta", "cream"],
        "diet": ["high protein"],
    },
    {
        "id": 2,
        "name": "Veggie Stir Fry",
        "calories": 400,
        "ingredients": ["broccoli", "carrot", "soy sauce"],
        "diet": ["low fat"],
    },
    {
        "id": 3,
        "name": "Beef Tacos",
        "calories": 500,
        "ingredients": ["beef", "tortilla", "cheese"],
        "diet": ["high protein"],
    },
    {
        "id": 4,
        "name": "Salmon Salad",
        "calories": 350,
        "ingredients": ["salmon", "lettuce", "avocado"],
        "diet": ["high protein"],
    },
    {
        "id": 5,
        "name": "Steak Salad",
        "calories": 350,
        "ingredients": ["Ribeye Steak", "lettuce", "avocado"],
        "diet": ["high protein"],
    },
    {
        "id": 6,
        "name": "Ceaser Salad",
        "calories": 300,
        "ingredients": ["lettuce", "avocado", "crutons", "ranch"],
        "diet": ["vegetarian"],
    },
    {
        "id": 7,
        "name": "eggplant parmesean",
        "calories": 430,
        "ingredients": [
            "eggplant",
            "marinara sauce",
            "panko breadcrumbs",
            "parmesan cheese",
        ],
        "diet": ["vegetarian", "low carb"],
    },
]

# prices = [
#     {"chicken" : 3.00},
#     {"pasta spaghetti": 2.34},
#     {"cream": 2.89},
#     {"broccoli": 1.67},
#     {"carrot": 1.89},
#     {"soy sauce": 3.56},
#     {"beef": 3.45},
#     {"tortilla": 6.97},
#     {"cheddar cheese": 4.78},
#     {"salmon": 8.90},
#     {"lettuce": 1.50},
#     {"organic avocado": 1.00},
#     {"jeff's rib eye Steak"}
# ]


@app.route("/recipes", methods=["GET"])
def get_recipes():
    """Return all recipes, optionally filtered by ingredients"""
    ingredients_param = request.args.get("ingredients")

    if ingredients_param:
        # Split user-supplied ingredients and lowercase them
        ingredients = [i.strip().lower() for i in ingredients_param.split(",")]

        # Filter recipes that include ANY of the requested ingredients (partial match)
        filtered_recipes = [
            recipe
            for recipe in recipes
            if any(
                ingredient in [ing.lower() for ing in recipe["ingredients"]]
                for ingredient in ingredients
            )
        ]
        return jsonify(filtered_recipes)

    # Return all recipes if no filter
    return jsonify(recipes)


@app.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    """Return a single recipe by ID"""
    recipe = next((r for r in recipes if r["id"] == recipe_id), None)
    if recipe:
        return jsonify(recipe)
    return jsonify({"error": "Recipe not found"}), 404


@app.route("/recipes", methods=["POST"])
def add_recipe():
    """Add a new recipe"""
    new_recipe = request.get_json()
    new_recipe["id"] = len(recipes) + 1
    recipes.append(new_recipe)
    return jsonify(new_recipe), 201


@app.route("/price/<ingredient>", methods=["GET"])
def get_ingredient_price(ingredient):
    product = logic.fuzzy_match(ingredient, prices)
    if product:

        return jsonify(product), 200
    return jsonify({"error": "Ingredient not found"}), 404


# def calc_health_score(recipe, s):
# scorer = nut.NutritionScorer()
# ingredient_ct = len(recipe["ingredients"])
# score = 0
# for ings in recipe["ingredients"]:
#     result = scorer.score_food(ings, s)
#     score += int(result['score'])

# meal_health_score = score / ingredient_ct
# return meal_health_score
# scorer = nut.NutritionScorer()
# ingredients = recipe["ingredients"]

# def score_ing(ing):
#     try:
#         result = scorer.score_food(ing, s)
#         return int(result['score'])
#     except:
#         return 0

# with ThreadPoolExecutor(max_workers=5) as executor:
#     scores = list(executor.map(score_ing, ingredients))

# total_score = sum(scores)
# return total_score / len(ingredients)

# def calc_recipe_price(recipe):

# ings = recipe["ingredients"]
# total_price=0
# for ingredient in ings:

#     response = get_ingredient_price(ingredient)
#     if response.status_code != 200:
#         raise Exception(f"API request failed: {response.status_code}")

#     price = response.json()
#     total_price += price["price"]

# return total_price
# ings = recipe["ingredients"]
# total_price = 0

# for ingredient in ings:
#     try:
#         response = requests.get(f"http://127.0.0.1:5000/price/{ingredient}")
#         if response.status_code != 200:
#             raise Exception(f"API request failed: {response.status_code}")
#         price_data = response.json()
#         total_price += price_data["price"]
#     except Exception as e:
#         print(f"Error fetching price for {ingredient}: {e}")
# return total_price
# ingredients = recipe["ingredients"]

# def fetch_price(ingredient):
#     if ingredient in price_cache:
#         return price_cache[ingredient]
#     try:
#         response = requests.get(f"http://127.0.0.1:5000/price/{ingredient}")
#         if response.status_code == 200:
#             price_cache[ingredient] = response.json()["price"]
#             return response.json()["price"]
#     except:
#         pass
#     return 0.0

# with ThreadPoolExecutor(max_workers=5) as executor:
#     prices = list(executor.map(fetch_price, ingredients))

# return sum(prices)


# left off here test this end point with react frontend
@app.route("/mealplan", methods=["GET"])
def get_mealplan():

    lf = request.args.get("lowfat")
    hp = request.args.get("highprotein")
    v = request.args.get("vegetarian")
    lc = request.args.get("lowcarb")
    budget = request.args.get("budget")

    diet_pref = []

    if int(lf):
        diet_pref.append("low fat")
    if int(hp):
        diet_pref.append("high protein")
    if int(v):
        diet_pref.append("vegetarian")
    if int(lc):
        diet_pref.append("low carb")
    # print("lowfat:", lf)
    # print("lowcarb:", lc)
    # print("highprotein:", hp)
    # print("vegetarian:", v)

    recipe_data = []

    if len(diet_pref) == 0:
        diet_pref = [
            "low fat",
            "high protein",
        ]  # no diet preference selsected jsut use fall back of low fat and high protein meals

    diet_pref_set = frozenset(diet_pref)

    data = recipes_by_diet_combo[diet_pref_set]
    # print(f"im looking for{diet_pref_set} meals\n")
    max_recipe_query = 0
    meal_plan_total = 0
    for recipe in data:

        if max_recipe_query == 30:
            break

        # print(recipe["name"])
        if meal_plan_total + recipe["price"] > float(budget):
            break
        else:
            meal_plan_total += recipe["price"]
        recipe_data.append(recipe)
        max_recipe_query += 1

    if not recipe_data:
        return (
            jsonify(
                {
                    "error": "No recipes with your criteria found Possibly try choosing less dietary restrictions"
                }
            ),
            404,
        )

    # for rec in recipe_data:
    #     score = calc_health_score(rec, s)
    #     price = calc_recipe_price(rec)

    #     rec["price"] = round(price, 2)
    #     rec["score"] = round ((score / price), 2)

    # sorted(recipe_data, key = lambda recipe: recipe["score"], reverse=True)
    # #print(recipe_data)
    # meal_plan = []
    # for rec in recipe_data:
    #     if meal_plan_total + rec["price"] > float(budget):
    #         break
    #     meal_plan_total += rec["price"]
    #     meal_plan.append(rec)

    return jsonify({"plan_price": round(meal_plan_total, 2), "meals": recipe_data})


if __name__ == "__main__":
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
