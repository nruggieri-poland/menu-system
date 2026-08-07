"""
menu_content.py
Static "newsletter" copy for the printable PDF calendars — the stuff that
doesn't come from Nutrislice (director contact, USDA program blurbs, a la
carte options, pricing). Edit this file directly when prices or option
lists change; nothing here is fetched automatically.

Fields marked [PLACEHOLDER] were not supplied yet and must be replaced
before that PDF variant should be treated as final. Currently placeholdered:
  - McKinley breakfast (pricing/options)
  - PSHS breakfast (pricing/options)

Header banner images: if present, generate_pdf.py will use
  scripts/assets/banner-{school}.jpg   (school photo/watermark banner)
  scripts/assets/logo-nutrition-group.png
and otherwise falls back to a plain color banner with text only.
"""

DIRECTOR = {
    "name": "Wendy Miller",
    "email": "wmiller2@polandschools.org",
    "phone": "330.757.7000 ext. 37214",
}

USDA_NOTICE = "USDA is an equal opportunity provider, employer, and lender."

MILK_CHOICES = "Assorted Lowfat Milk"

LUNCH_WHAT_MAKES_A_MEAL = [
    "You must choose at least 3 to 5 components available for the school lunch price.",
    "Choice of Meat or Meat Alternate",
    "Choice of Vegetable, Choice of Fruit*",
    "Choice of Grain/Bread, and Choice of Milk",
    "*Students must choose at least one fruit or vegetable",
]

BREAKFAST_WHAT_MAKES_A_MEAL_PLACEHOLDER = [
    "[PLACEHOLDER — confirm breakfast component rule wording with the food service director]",
    "Choice of Meat or Meat Alternate",
    "Choice of Fruit",
    "Choice of Grain/Bread, and Choice of Milk",
    "*Students must choose at least one fruit",
]

FRUIT_VEG_CHOICES = [
    "Baby Carrots", "Broccoli", "Red & Green Peppers", "Cucumbers",
    "Grape Tomatoes", "Fresh Orange", "Assorted Applesauce", "Assorted Apples",
    "Mixed Fruit", "Tropical Pineapple Tidbits", "Citrusy Mandarin Oranges",
    "Peach Slices", "Diced Pears", "Blueberries w/Whip Topping", "Assorted Craisins",
]

MCKINLEY_LUNCH_OPTIONS = [
    "Chef Salad (No Meat) w/ Fresh Bread",
    "Popcorn Chicken Salad w/ Fresh Bread",
    "Ham & Cheese Sandwich",
    "Turkey and Cheese Munchable",
    "Ham and Cheese Munchable",
    "Nacho Munchable",
    "Fruit and Yogurt Parfait",
]

PSHS_LUNCH_OPTIONS = [
    "Cheese Pizza", "Pepperoni Pizza", "Breaded Chicken Sandwich",
    "Crispy Spicy Chicken Patty Sandwich", "Cheeseburger on a Bun",
    "Baked French Fries", "Chef Salad, Turkey/Ham/Cheese,Egg",
    "Popcorn Chicken Salad w/ Fresh Bread", "Fruit & Yogurt Parfait with Granola",
    "Charcuterie Bistro Box", "Egg & Cheese Bistro Box", "Grilled Buffalo Chicken Wrap",
]

BREAKFAST_OPTIONS_PLACEHOLDER = ["[PLACEHOLDER — breakfast a la carte options]"]

MENU_CONTENT = {
    ("mckinley-middle", "lunch"): {
        "banner_title": "McKinley Elementary & Poland Middle School",
        "what_makes_a_meal": LUNCH_WHAT_MAKES_A_MEAL,
        "options_heading": "Additional Lunch Menu Options may include:",
        "options": MCKINLEY_LUNCH_OPTIONS,
        "fruit_veg_choices": FRUIT_VEG_CHOICES,
        "milk_choices": MILK_CHOICES,
        "prices": [
            ("Full Lunch", "$2.75"),
            ("Lunch Entrée", "$2.00"),
            ("Fruit/Vegetable Side", "$1.00"),
            ("Milk", "$.65"),
        ],
        "placeholder": False,
    },
    ("mckinley-middle", "breakfast"): {
        "banner_title": "McKinley Elementary & Poland Middle School",
        "what_makes_a_meal": BREAKFAST_WHAT_MAKES_A_MEAL_PLACEHOLDER,
        "options_heading": "Additional Breakfast Menu Options may include:",
        "options": BREAKFAST_OPTIONS_PLACEHOLDER,
        "fruit_veg_choices": FRUIT_VEG_CHOICES,
        "milk_choices": MILK_CHOICES,
        "prices": [
            ("Full Breakfast", "[PLACEHOLDER]"),
            ("Breakfast Entrée", "[PLACEHOLDER]"),
            ("Fruit/Vegetable Side", "[PLACEHOLDER]"),
            ("Milk", "[PLACEHOLDER]"),
        ],
        "placeholder": True,
    },
    ("pshs", "lunch"): {
        "banner_title": "Poland Seminary High School",
        "what_makes_a_meal": LUNCH_WHAT_MAKES_A_MEAL,
        "options_heading": "Additional Lunch Menu Options may include:",
        "options": PSHS_LUNCH_OPTIONS,
        "fruit_veg_choices": FRUIT_VEG_CHOICES,
        "milk_choices": MILK_CHOICES,
        "prices": [
            ("Full Lunch", "$3.00"),
            ("Lunch Entrée", "$2.50"),
            ("Fruit/Vegetable Side", "$1.00"),
            ("Milk", "$.65"),
        ],
        "placeholder": False,
    },
    ("pshs", "breakfast"): {
        "banner_title": "Poland Seminary High School",
        "what_makes_a_meal": BREAKFAST_WHAT_MAKES_A_MEAL_PLACEHOLDER,
        "options_heading": "Additional Breakfast Menu Options may include:",
        "options": BREAKFAST_OPTIONS_PLACEHOLDER,
        "fruit_veg_choices": FRUIT_VEG_CHOICES,
        "milk_choices": MILK_CHOICES,
        "prices": [
            ("Full Breakfast", "[PLACEHOLDER]"),
            ("Breakfast Entrée", "[PLACEHOLDER]"),
            ("Fruit/Vegetable Side", "[PLACEHOLDER]"),
            ("Milk", "[PLACEHOLDER]"),
        ],
        "placeholder": True,
    },
}


def get_content(school: str, menutype: str) -> dict:
    return MENU_CONTENT.get((school, menutype), {
        "banner_title": school,
        "what_makes_a_meal": ["[PLACEHOLDER — no content configured for this feed]"],
        "options_heading": "Additional Menu Options may include:",
        "options": ["[PLACEHOLDER]"],
        "fruit_veg_choices": FRUIT_VEG_CHOICES,
        "milk_choices": MILK_CHOICES,
        "prices": [("Price", "[PLACEHOLDER]")],
        "placeholder": True,
    })
