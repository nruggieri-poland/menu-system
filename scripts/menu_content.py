"""
menu_content.py
Static "newsletter" copy for the printable PDF calendars — the stuff that
doesn't come from Nutrislice (director contact, USDA program blurbs, a la
carte options, pricing). Edit this file directly when prices or option
lists change; nothing here is fetched automatically.

Each feed's sidebar is a `sections` list, rendered top to bottom exactly in
order — breakfast and lunch intentionally use a different box order/color
scheme (matches the district's actual reference designs), so this is kept
generic rather than assuming a fixed 5-box layout.

Section kinds:
  {"kind": "box", "color": "blue"|"pink"|"tan"|"green"|"purple",
   "heading": str, "heading_italic": bool, "body": [str, ...],
   "body_italic": bool, "columns": 1 | 2}
  {"kind": "band", "label": str, "value": str}   -- plain gray band, e.g. milk

Header banner images: generate_pdf.py uses
  assets/images/{school}-menu-header.jpg   (school photo/watermark banner)
  assets/images/the-nutrition-group.png
falling back to a plain text-only header if either is missing.
and otherwise falls back to a plain color banner with text only.
"""

DIRECTOR = {
    "name": "Wendy Miller",
    "email": "wmiller2@polandschools.org",
    "phone": "330.757.7000 ext. 37214",
}

USDA_NOTICE = "USDA is an equal opportunity provider, employer, and lender."

WHAT_MAKES_A_MEAL = [
    "You must choose at least 3 to 5 components available for the school lunch price.",
    "Choice of Meat or Meat Alternate",
    "Choice of Vegetable, Choice of Fruit*",
    "Choice of Grain/Bread, and Choice of Milk",
    "*Students must choose at least one fruit or vegetable",
]

FRUIT_VEG_CHOICES = [
    "Baby Carrots", "Broccoli", "Red & Green Peppers", "Cucumbers",
    "Grape Tomatoes", "Fresh Orange", "Assorted Applesauce", "Assorted Apples",
    "Mixed Fruit", "Tropical Pineapple Tidbits", "Citrusy Mandarin Oranges",
    "Peach Slices", "Diced Pears", "Blueberries w/Whip Topping", "Assorted Craisins",
]

BREAKFAST_ENTREES = [
    "Assorted Poptarts", "Fruit and Yogurt Parfait", "Smoothies",
    "Assorted Cereal with Toast", "Chocolate Chip Oatmeal Bar",
    "String Cheese and Crackers", "Assorted Benefit Bars", "Goody Ring",
    "Banana Muffin", "Chocolate Chip Muffin",
]

BREAKFAST_FRUIT_JUICE = [
    "Apple, Orange, Blue Raspberry and Fruit Punch Juices",
    "Assorted Applesauce flavors",
    "Assorted Craisins",
    "Assorted Fresh Fruit",
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


def _what_makes_a_meal_section():
    return {
        "kind": "box", "color": "blue", "heading": "What makes a meal?",
        "heading_italic": False, "body": WHAT_MAKES_A_MEAL, "body_italic": False,
        "columns": 1,
    }


def _milk_band():
    return {"kind": "band", "label": "Daily Milk Choices", "value": "Assorted Lowfat Milk"}


def _breakfast_sections():
    return [
        _what_makes_a_meal_section(),
        {
            "kind": "box", "color": "tan", "heading": "Additional Breakfast Entrées may include:",
            "heading_italic": True, "body": BREAKFAST_ENTREES, "body_italic": True, "columns": 1,
        },
        {
            "kind": "box", "color": "pink", "heading": "Breakfast Fruit and Juice Choices",
            "heading_italic": True, "body": BREAKFAST_FRUIT_JUICE, "body_italic": True, "columns": 1,
        },
        _milk_band(),
        {
            "kind": "box", "color": "green", "heading": "Breakfast Prices", "heading_italic": False,
            "body": ["Full Breakfast: $1.50", "Breakfast Entrée: $1.25", "Fruit Side: $1.00", "Milk: $.65"],
            "body_italic": False, "columns": 1,
        },
    ]


def _lunch_sections(options: list[str], options_columns: int, prices: list[str]):
    return [
        _what_makes_a_meal_section(),
        {
            "kind": "box", "color": "pink", "heading": "Additional Lunch Menu Options may include:",
            "heading_italic": True, "body": options, "body_italic": True, "columns": options_columns,
        },
        {
            "kind": "box", "color": "tan", "heading": "Lunch fruit and vegetable choices may include:",
            "heading_italic": True, "body": FRUIT_VEG_CHOICES, "body_italic": True, "columns": 2,
        },
        _milk_band(),
        {
            "kind": "box", "color": "purple", "heading": "Lunch Prices", "heading_italic": False,
            "body": prices, "body_italic": False, "columns": 1,
        },
    ]


MENU_CONTENT = {
    ("mckinley-middle", "lunch"): {
        "banner_title": "McKinley Elementary & Poland Middle School",
        "sections": _lunch_sections(
            MCKINLEY_LUNCH_OPTIONS, 1,
            ["Full Lunch: $2.75", "Lunch Entrée: $2.00", "Fruit/Vegetable Side: $1.00", "Milk: $.65"],
        ),
        "placeholder": False,
    },
    ("mckinley-middle", "breakfast"): {
        "banner_title": "McKinley Elementary & Poland Middle School",
        "sections": _breakfast_sections(),
        "placeholder": False,
    },
    ("pshs", "lunch"): {
        "banner_title": "Poland Seminary High School",
        "sections": _lunch_sections(
            PSHS_LUNCH_OPTIONS, 2,
            ["Full Lunch: $3.00", "Lunch Entrée: $2.50", "Fruit/Vegetable Side: $1.00", "Milk: $.65"],
        ),
        "placeholder": False,
    },
    ("pshs", "breakfast"): {
        "banner_title": "Poland Seminary High School",
        "sections": _breakfast_sections(),
        "placeholder": False,
    },
}


def get_content(school: str, menutype: str) -> dict:
    return MENU_CONTENT.get((school, menutype), {
        "banner_title": school,
        "sections": [{
            "kind": "box", "color": "blue", "heading": "No content configured",
            "heading_italic": False, "body": ["[PLACEHOLDER]"], "body_italic": False, "columns": 1,
        }],
        "placeholder": True,
    })
