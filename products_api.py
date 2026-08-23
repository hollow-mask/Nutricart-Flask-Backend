from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
from requests.auth import HTTPBasicAuth
from collections import defaultdict
from sentence_transformers import SentenceTransformer
import hnswlib
import numpy as np
from rapidfuzz import fuzz
import math
from Productfilter import (
    IMPORTANT_TOKENS,
    INGREDIENT_CONVERSIONS_GRAMS,
    UNIFORM_INGREDIENT_CONVERSION_GRAMS,
)

# activate virtual eniorment: .\Scripts\Activate

app = Flask(__name__)
CORS(app)

# === Step 1: Authenticate and get access token ===
# TODO find away to not hard code your API key dummy probaly willl need to be environment variable
CLIENT_ID = "nutricartbudgetingapp-bbc89mg5"
CLIENT_SECRET = "l0o4WZOnlyNjK05u4dKJNaCBFda1g5FH-hz66Dmd"  # re-type manually


def get_access_token():
    url = "https://api.kroger.com/v1/connect/oauth2/token"
    data = {"grant_type": "client_credentials", "scope": "product.compact"}
    response = requests.post(
        url, data=data, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    )
    response.raise_for_status()
    return response.json()["access_token"]


# === Step 2: Find nearest Kroger location by ZIP code ===
def get_location_id(access_token, zip_code):
    url = "https://api.kroger.com/v1/locations"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"filter.zipCode.near": zip_code}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json().get("data", [])
    if not data:
        raise ValueError("No Kroger locations found near that ZIP code.")

    # Take the first (nearest) location
    location = data[0]
    location_id = location["locationId"]
    name = location["name"]
    print(f"✅ Nearest Kroger: {name} (ID: {location_id})")
    return location_id


# fucntion to extract quantity as a float from string
def extract_float_quantity(size):
    return


class IngredientCluster:
    def __init__(self, cluster_id, canonical_name, embedding, attributes):
        self.cluster_id = cluster_id
        self.canonical_name = canonical_name
        self.embedding = embedding
        self.attributes = attributes  # 👈 NEW
        self.aliases = set()
        self.kroger_cache = None


clusters = {}  # cluster_id -> IngredientCluster
ingredient_to_cluster = {}  # alias string -> cluster_id


# sentance tarnsformer model initialiozation
model = SentenceTransformer("all-MiniLM-L6-v2")


# function to turn ingredients into vectors
# reshape emebedding since ANN expects 2d vectors
def embed_text(text: str) -> list[float]:
    return model.encode(text, convert_to_numpy=True)


# initilaizing ANN index
DIM = model.get_sentence_embedding_dimension()  # embedding dimension
MAX_CLUSTERS = 10_000

index = hnswlib.Index(space="cosine", dim=DIM)
index.init_index(max_elements=MAX_CLUSTERS, ef_construction=200, M=16)
index.set_ef(50)

# normalization Algorithm
# SIMILARITY_THRESHOLD = 0.85
SIMILARITY_THRESHOLD = 0.75


# important add extra logic in normalization function to make sure that cooked versios of raw ingredients to not get put in the same cluster
# will probally need a generate cannonical namde function
def extract_attributes(name: str):
    name_lower = name.lower()

    attrs = {
        "state": None,  # raw / cooked / canned
        "fat": None,  # nonfat / lowfat / full
    }

    # STATE
    if any(x in name_lower for x in ["raw", "uncooked"]):
        attrs["state"] = "raw"
    if any(x in name_lower for x in ["canned", "in water", "in oil"]):
        attrs["state"] = "canned"
    elif any(
        x in name_lower
        for x in [
            "cooked",
            "grilled",
            "baked",
            "roasted",
            "grilled",
            "baked",
            "roasted",
            "broiled",
            "smoked",
            "fried",
            "deep fried",
            "air fried",
            "sauteed",
            "seared",
            "braised",
            "steamed",
            "poached",
        ]
    ):
        attrs["state"] = "cooked"

    # FAT
    if any(
        x in name_lower
        for x in [
            "nonfat",
            "fat free",
            "low fat",
            "low-fat",
            "lowfat",
            "reduced fat",
            "reduced-fat",
            "skim",
            "lean",
        ]
    ):
        attrs["fat"] = "lowfat"
    elif any(
        x in name_lower
        for x in [
            "whole",
            "full fat",
            "fullfat",
            "full-fat",
            "full-milk",
            "whole milk greek",
            "whole milk",
        ]
    ):
        attrs["fat"] = "fullfat"

    return attrs


# function for getting base name of ongredients removes descripters reffering to foods cooked state and fat contenet/ processing
def get_base_name(name: str):
    remove_words = [
        "cooked",
        "grilled",
        "baked",
        "roasted",
        "grilled",
        "raw",
        "uncooked",
        "baked",
        "roasted",
        "broiled",
        "smoked",
        "fried",
        "deep fried",
        "air fried",
        "sauteed",
        "seared",
        "braised",
        "steamed",
        "poached",
        "nonfat",
        "fat free",
        "low fat",
        "low-fat",
        "lowfat",
        "reduced fat",
        "reduced-fat",
        "skim",
        "lean",
        "whole",
        "full fat",
        "fullfat",
        "full-fat",
        "full-milk",
        "whole milk greek",
        "whole milk",
    ]

    tokens = re.split(r"[,\s]+", name.lower())
    filtered = [t for t in tokens if t not in remove_words]

    return " ".join(filtered)


def normalize_ingredient(ingredient_name: str):
    # 1. Extract attributes
    attrs = extract_attributes(ingredient_name)

    # 2. Normalize base name
    base_name = get_base_name(ingredient_name)

    # 3. Embed ONLY base
    embedding = embed_text(base_name)
    vec = np.array(embedding, dtype=np.float32)

    # 4. Filter candidate clusters by attributes
    candidate_ids = [cid for cid, c in clusters.items() if c.attributes == attrs]

    # 5. ANN search ONLY on candidates
    if candidate_ids:
        # build temporary vectors for candidates
        candidate_vectors = np.array([clusters[cid].embedding for cid in candidate_ids])

        # brute force on small filtered set (fast + simple)
        sims = np.dot(candidate_vectors, vec) / (
            np.linalg.norm(candidate_vectors, axis=1) * np.linalg.norm(vec)
        )

        best_idx = np.argmax(sims)
        similarity = sims[best_idx]
        best_cluster_id = candidate_ids[best_idx]

        print(f"DEBUG similarity {similarity} for {ingredient_name}")

        if similarity >= SIMILARITY_THRESHOLD:
            cluster = clusters[best_cluster_id]
            cluster.aliases.add(ingredient_name)
            ingredient_to_cluster[ingredient_name] = best_cluster_id
            return cluster.canonical_name

    # 6. CREATE NEW CLUSTER
    cluster_id = len(clusters)

    canonical_name = base_name.title()

    print(f"NEW CLUSTER: {canonical_name} | attrs={attrs}")

    cluster = IngredientCluster(cluster_id, canonical_name, vec, attrs)
    cluster.aliases.add(ingredient_name)

    clusters[cluster_id] = cluster
    ingredient_to_cluster[ingredient_name] = cluster_id

    index.add_items(vec, np.array([cluster_id]))
    aliases = list(cluster.aliases)
    return (canonical_name, aliases[0])


# takes amount of ingredient for recipie(ing_size) and the kroger product and calculates how much of the product you need to buy and return cost
# def pice_ingredient(ing_size, product):
#     return

# out of the filtered kroger product api results picks which one is the best price wise to pick
# def get_best_product_match(products, quantity):
#    #finish this function and strt testing functions together. Also create a price meal plane function etc..!!!!!
#     # convert product and ingredient quantities to grams here
#     if quantity == "N/A":
#         sorted_products = sorted(products, key=lambda x: x["price"])
#         return sorted_products[0]
#     return products[0]


# =========================================================
# Calculates actual purchase cost for an ingredient
# =========================================================
# TODO 8/16/26 price ingredient neees to handle
# products/ingredients with unit = "whole"
# TODO price ingredient needs to handle unit being N/A or unresolved
def price_ingredient(required_grams, product):

    # ----------------------------
    # Missing data handling
    # ----------------------------
    if (
        product.get("price") == "N/A"
        or product.get("size") == "N/A"
        or (product.get("size_unit") != "g" and product.get("size_unit") != "whole")
    ):

        return {
            "product": product,
            "total_cost": float("inf"),
            "packages_needed": None,
            "cost_per_gram": None,
            "leftover_grams": None,
        }

    package_size_grams = product["size"]
    package_price = product["price"]

    # Safety checks
    if package_size_grams <= 0:
        return {
            "product": product,
            "total_cost": float("inf"),
            "packages_needed": None,
            "cost_per_gram": None,
            "leftover_grams": None,
        }

    # ----------------------------
    # Core calculations
    # ----------------------------

    cost_per_gram = package_price / package_size_grams

    packages_needed = math.ceil(required_grams / package_size_grams)

    total_cost = packages_needed * package_price

    leftover_grams = (packages_needed * package_size_grams) - required_grams

    return {
        "product": product,
        "total_cost": round(total_cost, 2),
        "packages_needed": packages_needed,
        "cost_per_gram": round(cost_per_gram, 4),
        "leftover_grams": round(leftover_grams, 2),
    }


# =========================================================
# Chooses best Kroger product for ingredient
# =========================================================
# TODO implament test case hwere user enters whole ingredient but all
# the products returned which DO match the search term are sold by unit as aopposed to whole
def get_best_product_match(products, required_quantity):

    if not products:
        return None

    scored_products = []

    for product in products:

        pricing_data = price_ingredient(required_quantity, product)

        # Skip invalid products
        if pricing_data["total_cost"] == float("inf"):
            continue

        match_score = product.get("match_score", 0.5)

        # =================================================
        # FINAL SCORE
        #
        # Lower is better
        #
        # We slightly reward semantic match quality
        # while mostly optimizing for actual total cost
        # =================================================

        adjusted_score = pricing_data["total_cost"] - (match_score * 0.25)

        scored_products.append(
            {"product": product, "pricing": pricing_data, "final_score": adjusted_score}
        )

    if not scored_products:
        return None

    # =====================================================
    # Sort best -> worst
    # =====================================================

    scored_products.sort(key=lambda x: x["final_score"])

    best = scored_products[0]

    # =====================================================
    # DEBUG PRINTS
    # =====================================================

    print("\n===== BEST PRODUCT ANALYSIS =====")

    for item in scored_products:

        p = item["product"]
        pr = item["pricing"]

        print(f"""
            PRODUCT: {p["name"]}
            price: ${p["price"]}
            size(g): {p["size"]}
            match_score: {p.get("match_score")}

            packages_needed: {pr["packages_needed"]}
            cost_per_gram: {pr["cost_per_gram"]}
            leftover_g: {pr["leftover_grams"]}

            TOTAL COST: ${pr["total_cost"]}
            FINAL SCORE: {item["final_score"]}
            """)

    print("=================================\n")

    return best


# =========================================================
# MEAL PLAN OPTIMIZATION FUNCTIONS
# =========================================================


def get_recipe_ingredient_dict(recipe):
    # """
    # Converts a recipe's ingredient list into:

    #     {
    #         normalized_name: total_quantity_in_grams
    #     }

    # Assumes ingredients have already been normalized and
    # converted to grams.
    # """

    ingredients = defaultdict(float)

    for ingredient in recipe:

        name = ingredient["normalized_name"]
        quantity = ingredient["quantity"]

        # Ignore ingredients whose quantity could not be converted
        if quantity == "N/A":
            continue

        if ingredient["unit"] != "g":
            continue

        ingredients[name] += quantity

    return dict(ingredients)


def aggregate_recipe_ingredients(recipes):
    # """
    # Combines all ingredient quantities across a group of recipes.

    # Example:

    #     Recipe A:
    #         chicken = 400g
    #         rice = 200g

    #     Recipe B:
    #         chicken = 300g
    #         rice = 100g

    # Returns:

    #     {
    #         "Chicken": 700,
    #         "Rice": 300
    #     }
    # """

    aggregated = defaultdict(float)

    for recipe in recipes:

        ingredients = get_recipe_ingredient_dict(recipe)

        for ingredient_name, quantity in ingredients.items():
            aggregated[ingredient_name] += quantity

    return dict(aggregated)


def calculate_recipe_individual_cost(recipe):
    # """
    # Calculates the grocery cost of a recipe by itself.

    # This is useful as a baseline for determining how much
    # aggregation savings a recipe receives.
    # """

    total_cost = 0.0

    ingredients = get_recipe_ingredient_dict(recipe)

    for ingredient_name, quantity in ingredients.items():

        product = get_kroger_product(ingredient_name, quantity)

        if product is None:
            return float("inf")

        if isinstance(product, dict) and "pricing" in product:
            total_cost += product["pricing"]["total_cost"]
        else:
            return float("inf")

    return round(total_cost, 2)


def calculate_aggregated_cost(aggregated_ingredients):
    # """
    # Calculates the grocery cost of an entire aggregated
    # grocery list.

    # aggregated_ingredients:

    #     {
    #         "Chicken": 850,
    #         "Rice": 500,
    #         "Broccoli": 300
    #     }

    # Returns:

    #     {
    #         "total_cost": ...,
    #         "ingredients": {...}
    #     }
    # """

    total_cost = 0.0
    priced_ingredients = {}

    for ingredient_name, quantity in aggregated_ingredients.items():

        product = get_kroger_product(ingredient_name, quantity)

        if product is None:
            return {"total_cost": float("inf"), "ingredients": priced_ingredients}

        if not isinstance(product, dict):
            return {"total_cost": float("inf"), "ingredients": priced_ingredients}

        if "pricing" not in product:
            return {"total_cost": float("inf"), "ingredients": priced_ingredients}

        pricing = product["pricing"]

        total_cost += pricing["total_cost"]

        priced_ingredients[ingredient_name] = {
            "required_grams": quantity,
            "product": product["product"],
            "packages_needed": pricing["packages_needed"],
            "cost": pricing["total_cost"],
            "leftover_grams": pricing["leftover_grams"],
        }

    return {"total_cost": round(total_cost, 2), "ingredients": priced_ingredients}


def calculate_incremental_cost(current_ingredients, candidate_recipe):
    # """
    # Determines how much additional money is required to add
    # candidate_recipe to the current grocery plan.

    # IMPORTANT:

    # This does NOT simply price the candidate recipe.

    # It compares:

    #     current grocery cost

    # against:

    #     grocery cost after adding candidate recipe

    # Therefore existing ingredients and package sizes are
    # automatically taken into account.
    # """

    # Cost of current grocery cart
    current_result = calculate_aggregated_cost(current_ingredients)

    if current_result["total_cost"] == float("inf"):
        return None

    current_cost = current_result["total_cost"]

    # Get candidate's ingredients
    candidate_ingredients = get_recipe_ingredient_dict(candidate_recipe)

    # Create copy so current cart isn't modified
    new_ingredients = defaultdict(float)

    for ingredient_name, quantity in current_ingredients.items():
        new_ingredients[ingredient_name] += quantity

    # Add candidate recipe
    for ingredient_name, quantity in candidate_ingredients.items():
        new_ingredients[ingredient_name] += quantity

    # Calculate new grocery cost
    new_result = calculate_aggregated_cost(dict(new_ingredients))

    if new_result["total_cost"] == float("inf"):
        return None

    new_cost = new_result["total_cost"]

    incremental_cost = new_cost - current_cost

    return {
        "incremental_cost": round(incremental_cost, 2),
        "current_cost": current_cost,
        "new_cost": new_cost,
        "current_ingredients": dict(current_ingredients),
        "new_ingredients": dict(new_ingredients),
        "new_pricing": new_result,
    }


def calculate_aggregation_savings(candidate_recipe, current_ingredients):
    # """
    # Measures how much cheaper a recipe becomes because of
    # ingredients already present in the grocery plan.

    # Example:

    #     Recipe alone = $12
    #     Incremental cost = $7

    #     savings = $5
    #     savings ratio = 41.7%
    # """

    individual_cost = calculate_recipe_individual_cost(candidate_recipe)

    incremental_result = calculate_incremental_cost(
        current_ingredients, candidate_recipe
    )

    if incremental_result is None:
        return None

    incremental_cost = incremental_result["incremental_cost"]

    if individual_cost == float("inf"):
        return None

    savings = individual_cost - incremental_cost

    if individual_cost > 0:
        savings_ratio = savings / individual_cost
    else:
        savings_ratio = 0

    return {
        "individual_cost": round(individual_cost, 2),
        "incremental_cost": round(incremental_cost, 2),
        "savings": round(savings, 2),
        "savings_ratio": round(savings_ratio, 4),
    }


def calculate_recipe_overlap(candidate_recipe, current_ingredients):
    # """
    # Calculates what percentage of the candidate recipe's
    # required ingredient quantity is already represented in
    # the current grocery plan.

    # This is quantity-weighted rather than simply counting
    # ingredient names.

    # Example:

    #     Candidate:
    #         chicken = 500g
    #         rice = 300g
    #         tomatoes = 200g

    #     Current plan:
    #         chicken
    #         rice

    #     Coverage is based on quantities rather than:

    #         2 / 3 ingredients
    # """

    candidate_ingredients = get_recipe_ingredient_dict(candidate_recipe)

    if not candidate_ingredients:
        return 0.0

    total_candidate_grams = sum(candidate_ingredients.values())

    if total_candidate_grams == 0:
        return 0.0

    overlapping_grams = 0.0

    for ingredient_name, quantity in candidate_ingredients.items():

        if ingredient_name in current_ingredients:

            existing_quantity = current_ingredients[ingredient_name]

            # Only count the amount that already exists
            covered_quantity = min(quantity, existing_quantity)

            overlapping_grams += covered_quantity

    return overlapping_grams / total_candidate_grams


def score_candidate_recipe(candidate_recipe, current_ingredients, remaining_budget):
    # """
    # Produces all useful metrics for a candidate recipe.

    # Incremental cost is the primary metric.

    # Overlap and aggregation savings are secondary metrics
    # that help distinguish otherwise similar candidates.
    # """

    incremental_result = calculate_incremental_cost(
        current_ingredients, candidate_recipe
    )

    if incremental_result is None:
        return None

    incremental_cost = incremental_result["incremental_cost"]

    # Can't afford recipe
    if incremental_cost > remaining_budget:
        return None

    overlap_score = calculate_recipe_overlap(candidate_recipe, current_ingredients)

    savings_data = calculate_aggregation_savings(candidate_recipe, current_ingredients)

    if savings_data is None:
        return None

    savings_ratio = savings_data["savings_ratio"]

    # -----------------------------------------------------
    # Candidate score
    #
    # Lower incremental cost is better.
    #
    # Savings and overlap are used as secondary signals.
    # -----------------------------------------------------

    score = incremental_cost - (savings_ratio * 2.0) - (overlap_score * 1.0)

    return {
        "recipe": candidate_recipe,
        "score": score,
        "incremental_cost": incremental_cost,
        "overlap_score": overlap_score,
        "aggregation_savings": savings_data["savings"],
        "aggregation_savings_ratio": savings_ratio,
        "pricing": incremental_result,
    }


def find_best_recipe_to_add(
    recipes, selected_recipe_indexes, current_ingredients, remaining_budget
):
    # """
    # Evaluates every recipe that hasn't already been selected
    # and returns the best recipe that fits the remaining budget.
    # """

    candidates = []

    for index, recipe in enumerate(recipes):

        if index in selected_recipe_indexes:
            continue

        result = score_candidate_recipe(recipe, current_ingredients, remaining_budget)

        if result is not None:
            result["recipe_index"] = index
            candidates.append(result)

    if not candidates:
        return None

    # Lowest score is best
    candidates.sort(key=lambda x: x["score"])

    return candidates[0]


# TODO get rid of rendendant overlap checks
# all that mattters is which recepi as incrmenatl cost
# onky needs overlap to decide wht the 1s slected recipe is
def optimize_meal_plan_for_budget(recipes, budget):
    # """
    # Main meal-plan optimization pipeline.

    # Starting with an empty grocery cart, repeatedly finds
    # the best recipe that can fit within the remaining budget.

    # Every time a recipe is added, the grocery cart is
    # re-aggregated and re-priced.
    # """

    selected_recipes = []
    selected_recipe_indexes = set()

    current_ingredients = {}

    total_cost = 0.0

    while True:

        remaining_budget = budget - total_cost

        if remaining_budget <= 0:
            break

        best_candidate = find_best_recipe_to_add(
            recipes, selected_recipe_indexes, current_ingredients, remaining_budget
        )

        if best_candidate is None:
            break

        recipe_index = best_candidate["recipe_index"]
        recipe = recipes[recipe_index]

        # ---------------------------------------------
        # Add recipe
        # ---------------------------------------------

        selected_recipes.append(recipe)
        selected_recipe_indexes.add(recipe_index)

        # ---------------------------------------------
        # Update aggregated ingredients
        # ---------------------------------------------

        current_ingredients = aggregate_recipe_ingredients(selected_recipes)

        # ---------------------------------------------
        # Recalculate actual grocery cost
        # ---------------------------------------------

        pricing_result = calculate_aggregated_cost(current_ingredients)

        total_cost = pricing_result["total_cost"]

        print("\n==========================================")
        print("ADDED RECIPE")
        print("==========================================")

        print(f"Recipe: {recipe.get('name', 'Unknown')}")

        print(f"Incremental cost: " f"${best_candidate['incremental_cost']:.2f}")

        print(f"Aggregation savings: " f"${best_candidate['aggregation_savings']:.2f}")

        print(f"Overlap score: " f"{best_candidate['overlap_score']:.2%}")

        print(f"Meal plan total: " f"${total_cost:.2f}")

        print(f"Remaining budget: " f"${budget - total_cost:.2f}")

    return {
        "recipes": selected_recipes,
        "recipe_indexes": selected_recipe_indexes,
        "ingredients": current_ingredients,
        "pricing": calculate_aggregated_cost(current_ingredients),
        "total_cost": total_cost,
        "remaining_budget": round(budget - total_cost, 2),
    }


# for kroger products and for recipe ingredients
def convert_product_quantity_to_grams(prod_dict):
    # should passin kroger products and ing so yo cna decide wht best conversion to grams is
    # also have conversions for common ingredients and their common unit for better conversions(like flour)
    # figure out where nad how to put conversion fucntion

    quantity = "N/A"
    conversion_done = False
    if (
        prod_dict.get("size") == "N/A"
        or prod_dict.get("size_unit") == "N/A"
        or prod_dict.get("name") == "N/A"
    ):
        return None
    if (
        prod_dict["size_unit"].lower().strip() == "ct"
        or prod_dict["size_unit"].lower().strip() == "each"
    ):
        quantity = prod_dict["size"]
        prod_dict["size_unit"] = "whole"
        return prod_dict
    if prod_dict["size_unit"].lower().strip() != "g":
        for ing in INGREDIENT_CONVERSIONS_GRAMS.keys():
            if ing in prod_dict["name"].lower():

                if prod_dict["size_unit"] in INGREDIENT_CONVERSIONS_GRAMS[ing]:

                    quantity = (
                        prod_dict["size"]
                        * INGREDIENT_CONVERSIONS_GRAMS[ing][prod_dict["size_unit"]]
                    )

                    conversion_done = True
                    break
        if not conversion_done:
            if (
                prod_dict["size_unit"].lower()
                in UNIFORM_INGREDIENT_CONVERSION_GRAMS.keys()
            ):
                quantity = (
                    prod_dict["size"]
                    * UNIFORM_INGREDIENT_CONVERSION_GRAMS[
                        prod_dict["size_unit"].lower()
                    ]
                )

    prod_dict["size"] = quantity
    prod_dict["size_unit"] = "g"
    return None


def convert_ingredient_quantity_to_grams(food_dict):
    quantity = "N/A"
    conversion_done = False
    if (
        food_dict.get("quantity") == "N/A"
        or food_dict.get("unit") == "N/A"
        or food_dict.get("name") == "N/A"
    ):
        return None

    if (
        food_dict["unit"].lower().strip() != "g"
        and food_dict["unit"].lower().strip() != "whole"
    ):
        for ing in INGREDIENT_CONVERSIONS_GRAMS.keys():
            if ing in food_dict["name"].lower().strip():

                if (
                    food_dict["unit"].lower().strip()
                    in INGREDIENT_CONVERSIONS_GRAMS[ing]
                ):

                    quantity = (
                        food_dict["quantity"]
                        * INGREDIENT_CONVERSIONS_GRAMS[ing][food_dict["unit"]]
                    )

                    conversion_done = True
                    break
            elif food_dict["name"].lower().strip() in ing:

                if (
                    food_dict["unit"].lower().strip()
                    in INGREDIENT_CONVERSIONS_GRAMS[ing]
                ):

                    quantity = (
                        food_dict["quantity"]
                        * INGREDIENT_CONVERSIONS_GRAMS[ing][food_dict["unit"]]
                    )

                    conversion_done = True
                    break
        if not conversion_done:
            if food_dict["unit"].lower() in UNIFORM_INGREDIENT_CONVERSION_GRAMS.keys():
                quantity = (
                    food_dict["quantity"]
                    * UNIFORM_INGREDIENT_CONVERSION_GRAMS[food_dict["unit"].lower()]
                )
    food_dict["quantity"] = quantity
    food_dict["unit"] = "g"
    return None


# possible asyncronization convert each ingredient to grmas in parralell
def convert_mealplan_ingredients_to_grams(mealplan):
    for meal in mealplan:
        for ingredient in meal:
            if ingredient["unit"] != "whole":
                convert_ingredient_quantity_to_grams(ingredient)
    return None


def normalize_mealplan_ingredients(mealplan):
    for meal in mealplan:
        for ingredient in meal:
            ing_name = ingredient["name"]
            norm_name, orig_name = normalize_ingredient(ing_name)
            ingredient["normalized_name"] = norm_name
    return None


# will use string similarity to get rid of results from kroger api that arent actually the searched item. api return comletly deifferent items some times
STOPWORDS = {
    "fresh",
    "natural",
    "original",
    "farm",
    "brand",
    "family",
    "pack",
    "value",
    "large",
    "small",
    "medium",
    "classic",
    "premium",
    "kroger",
}

# Productfilter.IMPORTANT_TOKENS


def tokenize(text):
    text = text.lower()

    text = re.sub(r"[^a-z0-9\s]", " ", text)

    tokens = text.split()

    return [t for t in tokens if t not in STOPWORDS]


# what percentage of query is shared with te product name
def token_overlap_score(query_tokens, product_tokens):

    query_set = set(query_tokens)
    product_set = set(product_tokens)

    overlap = query_set & product_set

    if len(query_set) == 0:
        return 0

    return len(overlap) / len(query_set)


def required_token_match(query_tokens, product_tokens):

    important_query_tokens = [t for t in query_tokens if t in IMPORTANT_TOKENS]

    for token in important_query_tokens:
        if token not in product_tokens:
            return False

    return True


BANNED_TOKENS = {
    "dog",
    "cat",
    "toy",
    "soap",
    "detergent",
    "candle",
    "shampoo",
    "conditioner",
}


def contains_banned_tokens(tokens):

    for token in tokens:
        if token in BANNED_TOKENS:
            return True

    return False


# added more results from kroger api so this function
# filters out results that are completly not what The
# The query was searching for. results must have certain
# words that alig with what the query is Ex: chicken has to be
# included in results for chicken breast
def filter_out_wrong_matches_from_krogerapi(ingredient_name, products):

    filtered_products = []

    query_tokens = tokenize(ingredient_name)

    for product in products:

        product_name = product["name"]

        product_tokens = tokenize(product_name)

        # ---------------------------------
        # 1. BANNED TOKEN FILTER
        # ---------------------------------

        if contains_banned_tokens(product_tokens):
            continue

        # ---------------------------------
        # 2. REQUIRED TOKEN FILTER
        # ---------------------------------

        if not required_token_match(query_tokens, product_tokens):
            continue

        # ---------------------------------
        # 3. TOKEN OVERLAP SCORE
        # ---------------------------------

        overlap_score = token_overlap_score(query_tokens, product_tokens)

        # ---------------------------------
        # 4. FUZZY SCORE
        # ---------------------------------

        fuzzy_score = (
            fuzz.token_set_ratio(ingredient_name.lower(), product_name.lower()) / 100
        )

        # ---------------------------------
        # 5. COMBINED SCORE
        # ---------------------------------

        final_score = overlap_score * 0.7 + fuzzy_score * 0.3

        print(f"""
            PRODUCT: {product_name}
            overlap={overlap_score}
            fuzzy={fuzzy_score}
            final={final_score}
            """)

        # ---------------------------------
        # 6. THRESHOLD
        # ---------------------------------

        if final_score >= 0.55:

            product["match_score"] = final_score

            filtered_products.append(product)

    # ---------------------------------
    # SORT BEST TO WORST
    # ---------------------------------

    filtered_products.sort(key=lambda x: x["match_score"], reverse=True)

    return filtered_products


def price_meal_plan():
    return None


def get_kroger_product(ing, quantity):
    normalized_name = ing["normalized_name"]
    actual_name = ing["name"]
    cluster_id = ingredient_to_cluster[normalized_name]
    cluster = clusters[cluster_id]

    if cluster.kroger_cache:
        product = get_best_product_match(cluster.kroger_cache, quantity)
        return product

    token = get_access_token()
    # list of dictionaries of kroger api results for the search term
    products = search_product(token, location_id, actual_name)
    cluster.kroger_cache = products
    product = get_best_product_match(products, quantity)
    return product


def parse_quantity(qty_str):
    # """Convert a quantity string (int, decimal, fraction, or mixed number) to float."""
    qty_str = qty_str.strip()

    # Mixed number: "1 1/2"
    mixed_match = re.match(r"^(\d+)\s+(\d+)/(\d+)$", qty_str)
    if mixed_match:
        whole, num, denom = map(int, mixed_match.groups())
        return whole + num / denom

    # Simple fraction: "1/2"
    frac_match = re.match(r"^(\d+)/(\d+)$", qty_str)
    if frac_match:
        num, denom = map(int, frac_match.groups())
        return num / denom

    # Plain integer or decimal
    return float(qty_str)


# === Step 3: Search for a product and get its price ===
# need to have aaway to deal with units and quantaties tata rent getting parsed formapi results example 1/2 gal of milke was not getting parsed
def search_product(access_token, location_id, search_term):
    url = "https://api.kroger.com/v1/products"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    params = {
        "filter.term": search_term,
        "filter.locationId": location_id,
        "filter.limit": 10,  # limit to a few results
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    products_list = []
    data = response.json().get("data", [])
    if not data:
        print("No products found for that term.")
        return []

    for item in data:
        product_dict = {}
        description = item.get("description", "Unknown product")
        product_dict["name"] = description
        try:
            price = item["items"][0]["price"]["regular"]

            product_dict["price"] = float(price)

        except KeyError:
            price = "N/A"
            product_dict["price"] = price

        try:
            size = item["items"][0]["size"]

            # Quantity group now allows: "1", "1.5", "1/2", or "1 1/2"
            pattern = r"^\s*(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\s*([a-zA-Z ]+?)\s*$"
            match = re.search(pattern, size)

            if match:
                quantity = parse_quantity(match.group(1))
                unit = match.group(2)
                product_dict["size"] = quantity
                product_dict["size_unit"] = unit
            else:
                product_dict["size"] = "N/A"
                product_dict["size_unit"] = "N/A"
        except KeyError:
            size = "N/A"
            product_dict["size"] = "N/A"
            product_dict["size_unit"] = "N/A"

        try:
            soldBy = item["items"][0]["soldBy"]
            if soldBy == "UNIT" or soldBy == "unit":
                product_dict["soldBy"] = 1
            elif soldBy == "EACH" or soldBy == "each":
                product_dict["soldBy"] = 2
            elif (
                "lb" in soldBy
                or "oz" in soldBy
                or "g" in soldBy
                or soldBy == "WEIGHT"
                or soldBy == "weight"
            ):
                product_dict["soldBy"] = 3
        except KeyError:
            soldBy = "N/A"
            product_dict["soldBy"] = soldBy
        print(f"product_dictionary: {product_dict}")
        convert_product_quantity_to_grams(product_dict)
        products_list.append(product_dict)
        print(f"- {description}: ${price} quantity: {size} sold by: {soldBy}")
        print(
            f"{product_dict["name"]} is sold by {product_dict['soldBy']} quantatity is: {product_dict["size"]} of {product_dict["size_unit"]}"
        )
    filtered = filter_out_wrong_matches_from_krogerapi(search_term, products_list)
    if len(filtered) > 5:
        print(
            f"FILTERED PRODUCTS SNIPPED +++++++++++++++++++++++++++++++++++++++++\n{filtered[0:6]}"
        )
        return filtered[0:6]
    print(f"FILTERED PRODUCTS +++++++++++++++++++++++++++++++++++++++++\n{filtered}")
    return filtered[0:4]


# === Step 4: Run the program ===
if __name__ == "__main__":
    zip_code = input("Enter your ZIP code: ").strip()
    search_term = input("Enter a product to search for: ").strip()

    token = get_access_token()
    location_id = get_location_id(token, zip_code)
    # left off here test the functions invilved in the work flow of pricing a meal plan and see how the clustering works
    # recipies = [    {
    #                     "name": "Healthy Chicken Salad",
    #                     "servings": 6,
    #                     "ingredients": {
    #                         "cooked_chicken_breast": 450,      # 3 cups (~150g per cup)
    #                         "celery": 100,                     # 2 stalks (~50g each)
    #                         "red_grapes": 150,                 # 1 cup grapes ~150g
    #                         "thin_sliced_almonds": 60,         # 1/2 cup sliced almonds ~60g
    #                         "green_onions": 45,                # 3 green onions ~15g each
    #                         "parsley": 8,                      # 2 Tbsp parsley ~8g
    #                         "plain_greek_yogurt": 180,         # 3/4 cup Greek yogurt ~180g
    #                         "Dijon_mustard": 15,               # 1 Tbsp Dijon ~15g
    #                         "fresh_lemon_juice": 45,           # 3 Tbsp lemon juice ~45g/ml
    #                         "celery_seed": 1.4,                # 2 tsp celery seed ~1.4g
    #                         "salt": 5,                         # 1 tsp salt ~5g
    #                         "black_pepper": 1                  # 1/2 tsp pepper ~1g
    #                     },
    #                     "instructions": [
    #                         "Chop or shred the cooked chicken.",
    #                         "Dice celery and halve grapes.",
    #                         "Slice green onions and finely chop parsley.",
    #                         "Combine chicken, celery, grapes, almonds, green onions, and parsley in a large bowl.",
    #                         "In a separate bowl, mix Greek yogurt, Dijon mustard, lemon juice, celery seed, salt, and pepper.",
    #                         "Pour dressing over the chicken mixture and stir until evenly coated.",
    #                         "Chill in fridge then serve."
    #                     ]
    #                 },
    #                 {
    #                     "name": "Light Chicken Yogurt Salad",
    #                     "servings": 6,
    #                     "ingredients": {
    #                         "grilled_skinless_chicken_breast": 430,   # ~2.85 cups diced
    #                         "chopped_fresh_celery": 110,              # ~2 medium stalks
    #                         "seedless_red_grapes": 145,               # just under 1 cup
    #                         "toasted_sliced_almonds": 55,             # slightly less than 1/2 cup
    #                         "scallions": 40,                          # ~3 medium scallions
    #                         "fresh_flat_leaf_parsley": 7,             # 2 Tbsp finely chopped
    #                         "nonfat_plain_greek_yogurt": 170,         # ~3/4 cup
    #                         "stone_ground_mustard": 14,               # ~1 Tbsp
    #                         "fresh_squeezed_lemon_juice": 42,         # ~2.75 Tbsp
    #                         "ground_celery_seed": 1.3,                # ~2 tsp
    #                         "kosher_salt": 4.5,                       # ~3/4 tsp
    #                         "freshly_ground_black_pepper": 1.1        # ~1/2 tsp
    #                     },
    #                     "instructions": [
    #                         "Dice the grilled chicken breast into bite-sized pieces.",
    #                         "Finely chop the celery and slice the scallions.",
    #                         "Halve the grapes and roughly chop the parsley.",
    #                         "Combine chicken, celery, grapes, almonds, scallions, and parsley in a mixing bowl.",
    #                         "In a separate bowl, whisk together yogurt, mustard, lemon juice, celery seed, salt, and pepper.",
    #                         "Fold the dressing into the chicken mixture until fully combined.",
    #                         "Refrigerate for 20–30 minutes before serving."
    #                     ]
    #                 }

    #             ]
    # normalized_recipies = []
    # for rec in recipies:
    #     normalized_recipie_dict = {}
    #     name = rec["name"]
    #     normalized_recipie_dict["name"] = name
    #     normalize_ingredient_dict = {}
    #     for ing in rec["ingredients"].keys():
    #         normalized_ing = normalize_ingredient(ing)
    #         normalize_ingredient_dict[normalized_ing] = 20.0
    #     normalized_recipie_dict["ingredients"] = normalize_ingredient_dict
    #     print(normalized_recipie_dict["name"])
    #     for ing in normalized_recipie_dict["ingredients"]:
    #         print(ing)
    #     normalized_recipies.append(normalized_recipie_dict)

    print(f"\n💲 Product results for '{search_term}' near {zip_code}:\n")
    ingr = defaultdict(str)
    list = search_product(token, location_id, search_term, ingr)
    # print(f"{list}")
