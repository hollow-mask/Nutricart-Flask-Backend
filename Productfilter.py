IMPORTANT_TOKENS = {
    # =========================
    # MEATS
    # =========================
    "beef",
    "steak",
    "sirloin",
    "ribeye",
    "brisket",
    "roast",
    "ground",
    "burger",
    "hamburger",
    "meatballs",
    "chicken",
    "breast",
    "thigh",
    "drumstick",
    "wing",
    "tenderloin",
    "turkey",
    "bacon",
    "ham",
    "sausage",
    "pepperoni",
    "salami",
    "pork",
    "loin",
    "chop",
    "ribs",
    "lamb",
    "veal",
    # =========================
    # SEAFOOD
    # =========================
    "fish",
    "salmon",
    "tuna",
    "cod",
    "tilapia",
    "trout",
    "catfish",
    "sardines",
    "anchovies",
    "shrimp",
    "crab",
    "lobster",
    "scallops",
    "mussels",
    "clams",
    "oysters",
    # =========================
    # DAIRY
    # =========================
    "milk",
    "cheese",
    "yogurt",
    "cream",
    "butter",
    "halfandhalf",
    "kefir",
    "mozzarella",
    "cheddar",
    "parmesan",
    "swiss",
    "provolone",
    "feta",
    "gouda",
    "ricotta",
    "cottage",
    # =========================
    # EGGS
    # =========================
    "egg",
    "eggs",
    "eggwhite",
    "yolk",
    # =========================
    # BREAD / GRAINS
    # =========================
    "bread",
    "bun",
    "bagel",
    "biscuit",
    "roll",
    "tortilla",
    "pita",
    "naan",
    "rice",
    "quinoa",
    "oats",
    "oatmeal",
    "barley",
    "couscous",
    "pasta",
    "spaghetti",
    "macaroni",
    "penne",
    "fettuccine",
    "noodles",
    "cereal",
    # =========================
    # FLOURS / BAKING
    # =========================
    "flour",
    "cornmeal",
    "cornstarch",
    "baking",
    "yeast",
    "sugar",
    "brownsugar",
    "powderedsugar",
    # =========================
    # BEANS / LEGUMES
    # =========================
    "beans",
    "blackbeans",
    "kidneybeans",
    "pintobeans",
    "garbanzo",
    "chickpeas",
    "lentils",
    "peas",
    "edamame",
    # =========================
    # VEGETABLES
    # =========================
    "broccoli",
    "cauliflower",
    "carrot",
    "celery",
    "lettuce",
    "spinach",
    "kale",
    "cabbage",
    "onion",
    "green onion",
    "shallot",
    "garlic",
    "ginger",
    "pepper",
    "jalapeno",
    "habanero",
    "potato",
    "sweetpotato",
    "yam",
    "tomato",
    "cucumber",
    "zucchini",
    "squash",
    "eggplant",
    "corn",
    "peas",
    "okra",
    "asparagus",
    "artichoke",
    "mushroom",
    "avocado",
    # =========================
    # FRUITS
    # =========================
    "apple",
    "banana",
    "orange",
    "grape",
    "grapes",
    "strawberry",
    "blueberry",
    "raspberry",
    "blackberry",
    "pineapple",
    "mango",
    "watermelon",
    "cantaloupe",
    "peach",
    "pear",
    "plum",
    "kiwi",
    "lemon",
    "lime",
    "cherries",
    # =========================
    # NUTS / SEEDS
    # =========================
    "almonds",
    "walnuts",
    "pecans",
    "cashews",
    "peanuts",
    "pistachios",
    "chia",
    "flax",
    "sunflower",
    "pumpkinseed",
    # =========================
    # OILS / CONDIMENTS
    # =========================
    "oil",
    "oliveoil",
    "canolaoil",
    "vinegar",
    "mustard",
    "mayo",
    "mayonnaise",
    "ketchup",
    "hotsauce",
    "soy",
    "soy sauce",
    # =========================
    # FROZEN / COMMON STAPLES
    # =========================
    "pizza",
    "waffles",
    "fries",
    "hashbrowns",
    # =========================
    # DRINKS
    # =========================
    "juice",
    "coffee",
    "tea",
    "soda",
    # =========================
    # PROTEIN / FITNESS
    # =========================
    "protein",
    "whey",
    "casein",
    # =========================
    # COMMON RECIPE ITEMS
    # =========================
    "broth",
    "stock",
    "bouillon",
    "tofu",
    "tempeh",
    "hummus",
    "salsa",
    "guacamole",
    "pickles",
    "olives",
    "jam",
    "jelly",
    "peanutbutter",
    "almondbutter",
    # =========================
    # HERBS
    # =========================
    "parsley",
    "cilantro",
    "basil",
    "oregano",
    "thyme",
    "rosemary",
    "dill",
    # =========================
    # SPICES
    # =========================
    "salt",
    "pepper",
    "paprika",
    "cumin",
    "turmeric",
    "cinnamon",
    "nutmeg",
    "curry",
}

INGREDIENT_CONVERSIONS_GRAMS = {
    "all-purpose flour": {
        "tsp": 2.6,
        "tbsp": 7.8,
        "cup": 120,
        "oz": 28.35,
    },
    "all purpose flour": {
        "tsp": 2.6,
        "tbsp": 7.8,
        "cup": 120,
        "oz": 28.35,
    },
    "bread flour": {
        "tsp": 2.7,
        "tbsp": 8.1,
        "cup": 127,
        "oz": 28.35,
    },
    "whole wheat flour": {
        "tsp": 2.8,
        "tbsp": 8.4,
        "cup": 130,
        "oz": 28.35,
    },
    "granulated sugar": {
        "tsp": 4.2,
        "tbsp": 12.5,
        "cup": 200,
        "oz": 28.35,
    },
    "brown sugar": {
        "tsp": 4.6,
        "tbsp": 13.8,
        "cup": 220,
        "oz": 28.35,
    },
    "powdered sugar": {
        "tsp": 2.5,
        "tbsp": 7.5,
        "cup": 120,
        "oz": 28.35,
    },
    "salt": {
        "tsp": 6,
        "tbsp": 18,
        "cup": 288,
        "oz": 28.35,
    },
    "kosher salt": {
        "tsp": 3,
        "tbsp": 9,
        "cup": 144,
        "oz": 28.35,
    },
    "baking powder": {
        "tsp": 4,
        "tbsp": 12,
        "cup": 192,
        "oz": 28.35,
    },
    "baking soda": {
        "tsp": 4.8,
        "tbsp": 14.4,
        "cup": 230,
        "oz": 28.35,
    },
    "cornstarch": {
        "tsp": 2.7,
        "tbsp": 8,
        "cup": 128,
        "oz": 28.35,
    },
    "rolled oats": {
        "tsp": 1.0,
        "tbsp": 3.0,
        "cup": 80,
        "oz": 28.35,
    },
    "white rice": {
        "tsp": 2.8,
        "tbsp": 8.5,
        "cup": 185,
        "oz": 28.35,
    },
    "brown rice": {
        "tsp": 3.0,
        "tbsp": 9.0,
        "cup": 195,
        "oz": 28.35,
    },
    "uncooked pasta": {
        "cup": 100,
        "oz": 28.35,
    },
    "butter": {
        "tsp": 4.7,
        "tbsp": 14.2,
        "cup": 227,
        "oz": 28.35,
    },
    "olive oil": {
        "tsp": 4.5,
        "tbsp": 13.5,
        "cup": 216,
        "fl oz": 27,
    },
    "vegetable oil": {
        "tsp": 4.6,
        "tbsp": 13.8,
        "cup": 218,
        "fl oz": 27.3,
    },
    "milk": {
        "tsp": 5.1,
        "tbsp": 15.3,
        "cup": 245,
        "fl oz": 30.6,
    },
    "heavy cream": {
        "tsp": 5,
        "tbsp": 15,
        "cup": 238,
        "fl oz": 29.8,
    },
    "water": {
        "tsp": 5,
        "tbsp": 15,
        "cup": 236.6,
        "fl oz": 29.57,
    },
    "honey": {
        "tsp": 7,
        "tbsp": 21,
        "cup": 340,
        "fl oz": 42.5,
    },
    "maple syrup": {
        "tsp": 6.6,
        "tbsp": 19.8,
        "cup": 315,
        "fl oz": 39.4,
    },
    "peanut butter": {
        "tsp": 5.3,
        "tbsp": 16,
        "cup": 258,
        "oz": 28.35,
    },
    "greek yogurt": {
        "tsp": 5.3,
        "tbsp": 16,
        "cup": 245,
        "oz": 28.35,
    },
    "sour cream": {
        "tsp": 4.9,
        "tbsp": 14.7,
        "cup": 230,
        "oz": 28.35,
    },
    "mayonnaise": {
        "tsp": 4.8,
        "tbsp": 14.4,
        "cup": 230,
        "oz": 28.35,
    },
    "tomato paste": {
        "tsp": 5.3,
        "tbsp": 16,
        "cup": 256,
        "oz": 28.35,
    },
    "ketchup": {
        "tsp": 5.7,
        "tbsp": 17,
        "cup": 272,
        "fl oz": 34,
    },
    "soy sauce": {
        "tsp": 5.7,
        "tbsp": 17,
        "cup": 272,
        "fl oz": 34,
    },
    "cocoa powder": {
        "tsp": 1.7,
        "tbsp": 5,
        "cup": 85,
        "oz": 28.35,
    },
    "chocolate chips": {
        "tsp": 2.9,
        "tbsp": 14,
        "cup": 170,
        "oz": 28.35,
    },
    "shredded cheese": {
        "tsp": 1.7,
        "tbsp": 5,
        "cup": 113,
        "oz": 28.35,
    },
    "parmesan cheese": {
        "tsp": 1.7,
        "tbsp": 5,
        "cup": 100,
        "oz": 28.35,
    },
    "breadcrumbs": {
        "tsp": 1.3,
        "tbsp": 4,
        "cup": 120,
        "oz": 28.35,
    },
    "almonds": {
        "cup": 143,
        "oz": 28.35,
    },
    "walnuts": {
        "cup": 120,
        "oz": 28.35,
    },
    "spinach": {
        "cup": 30,
        "oz": 28.35,
    },
    "chopped onion": {
        "tsp": 2.3,
        "tbsp": 7,
        "cup": 160,
        "oz": 28.35,
    },
    "diced tomatoes": {
        "cup": 245,
        "oz": 28.35,
    },
    "carrots": {
        "cup": 128,
        "oz": 28.35,
    },
    "broccoli florets": {
        "cup": 91,
        "oz": 28.35,
    },
    "ground beef": {
        "cup": 225,
        "oz": 28.35,
        "lb": 453.6,
    },
    "chicken breast": {
        "cup": 140,
        "oz": 28.35,
        "lb": 453.6,
    },
    "cooked chicken": {
        "cup": 140,
        "oz": 28.35,
        "lb": 453.6,
    },
    "ground turkey": {
        "cup": 220,
        "oz": 28.35,
        "lb": 453.6,
    },
    "black beans": {
        "cup": 172,
        "oz": 28.35,
    },
    "kidney beans": {
        "cup": 177,
        "oz": 28.35,
    },
    "lentils": {
        "cup": 192,
        "oz": 28.35,
    },
    "quinoa": {
        "cup": 170,
        "oz": 28.35,
    },
    "chia seeds": {
        "tsp": 4,
        "tbsp": 12,
        "cup": 192,
        "oz": 28.35,
    },
    "flax seeds": {
        "tsp": 3.4,
        "tbsp": 10.2,
        "cup": 168,
        "oz": 28.35,
    },
}

UNIFORM_INGREDIENT_CONVERSION_GRAMS = {
    # =========================
    # WEIGHT UNITS (Exact)
    # =========================
    "mg": 0.001,
    "milligrams": 0.001,
    "milligram": 0.001,
    "g": 1,
    "gram": 1,
    "grams": 1,
    "kg": 1000,
    "oz": 28.35,
    "ounce": 28.35,
    "ounces": 28.35,
    "lb": 453.6,
    "lbs": 453.6,
    "pound": 453.6,
    "pounds": 453.6,
    # =========================
    # COMMON SOLID VOLUME ESTIMATES
    # (generic ingredient baseline)
    # =========================
    "tsp": 5,
    "teaspoon": 5,
    "teaspoons": 5,
    "tbsp": 15,
    "tablespoon": 15,
    "tablespoons": 15,
    "cup": 240,
    "cups": 240,
    "pt": 473,
    "pint": 473,
    "pints": 473,
    "qt": 946,
    "quart": 946,
    "quarts": 946,
    "gal": 3785,
    "gallon": 3785,
    "gallons": 3785,
    # =========================
    # LIQUID VOLUME UNITS
    # assuming water-like density
    # =========================
    "ml": 1,
    "mL": 1,
    "milliliter": 1,
    "milliliters": 1,
    "l": 1000,
    "liter": 1000,
    "liters": 1000,
    "fl oz": 29.57,
    "floz": 29.57,
    "fluid ounce": 29.57,
    "fluid ounces": 29.57,
    # produce estimates
    "stick": 113,  # butter stick baseline
    "clove": 5,  # garlic clove baseline
    "slice": 28,  # generic slice estimate
    # =========================
    # INTERNATIONAL
    # =========================
    "dl": 100,  # deciliter
    "cl": 10,  # centiliter
}
