import random
from flask import Flask, render_template, request, jsonify
from thefuzz import process  # Ensure you ran: pip install thefuzz

app = Flask(__name__)

# --- THE SCIENCE BRAIN (Periodic Table Metals) ---
PERIODIC_METALS = [
    "lithium",
    "beryllium",
    "sodium",
    "magnesium",
    "aluminum",
    "aluminium",
    "potassium",
    "calcium",
    "scandium",
    "titanium",
    "vanadium",
    "chromium",
    "manganese",
    "iron",
    "cobalt",
    "nickel",
    "copper",
    "zinc",
    "gallium",
    "rubidium",
    "strontium",
    "yttrium",
    "zirconium",
    "niobium",
    "molybdenum",
    "technetium",
    "ruthenium",
    "rhodium",
    "palladium",
    "silver",
    "cadmium",
    "indium",
    "tin",
    "antimony",
    "cesium",
    "barium",
    "lanthanum",
    "cerium",
    "praseodymium",
    "neodymium",
    "promethium",
    "samarium",
    "europium",
    "gadolinium",
    "terbium",
    "dysprosium",
    "holmium",
    "erbium",
    "thulium",
    "ytterbium",
    "lutetium",
    "hafnium",
    "tantalum",
    "tungsten",
    "rhenium",
    "osmium",
    "iridium",
    "platinum",
    "gold",
    "mercury",
    "thallium",
    "lead",
    "bismuth",
    "polonium",
    "francium",
    "radium",
    "actinium",
    "thorium",
    "protactinium",
    "uranium",
    "neptunium",
    "plutonium",
    "americium",
    "curium",
    "berkelium",
    "californium",
    "einsteinium",
    "fermium",
    "mendelevium",
    "nobelium",
    "lawrencium",
    "rutherfordium",
    "dubnium",
    "seaborgium",
    "bohrium",
    "hassium",
    "meitnerium",
    "darmstadtium",
    "roentgenium",
    "copernicium",
    "nihonium",
    "flerovium",
    "moscovium",
    "livermorium",
    "tennessine",
    "oganesson",
]

# 1. SPECIFIC DATABASE
GOMI_DATA = {
    "gemini": "A helpful AI partner. Not trash. Please don't recycle me.",
    "my mom": "The System Admin. Scanning restricted. Error 404.",
    "pizza box": "If it's greasy, it's trash. If it's clean, it's paper recycling.",
    "plastic bottle": "Recyclable. Remove the cap or it stays here forever.",
}

# 2. THE SYNONYM BRAIN
SYNONYMS = {
    "metal": [
        "metal",
        "steel",
        "can",
        "foil",
        "tin",
        "wire",
        "pot",
        "pan",
        "brass",
        "bronze",
        "sinker",
    ]
    + PERIODIC_METALS,
    "paper": [
        "paper",
        "cardboard",
        "magazine",
        "newspaper",
        "envelope",
        "book",
        "flyer",
        "carton",
        "letter",
    ],
    "plastic": [
        "plastic",
        "styrofoam",
        "vinyl",
        "pvc",
        "wrapper",
        "bag",
        "container",
        "jug",
        "toy",
    ],
    "glass": ["glass", "jar", "bottle", "mirror", "window", "cup", "vase"],
    "electronic": [
        "phone",
        "cable",
        "charger",
        "battery",
        "laptop",
        "wire",
        "remote",
        "appliance",
        "pc",
    ],
    "food": [
        "food",
        "scrap",
        "peel",
        "leftover",
        "meat",
        "veg",
        "fruit",
        "egg",
        "bread",
        "banana",
    ],
    "cloth": [
        "shirt",
        "sock",
        "towel",
        "fabric",
        "cloth",
        "rag",
        "shoe",
        "curtain",
        "jean",
    ],
}

# 3. THE CATEGORY RULES
CATEGORY_RULES = {
    "metal": "CAN RECYCLING: Rinse it out and put it in the metal resource bin.",
    "paper": "RESOURCE RECYCLING: Bundle it with string or put in the paper bin.",
    "plastic": "RECYCLING BIN: Check for the plastic mark; rinse and recycle.",
    "glass": "GLASS RECYCLING: Remove the lid and sort by color.",
    "food": "BURNABLE TRASH: Please drain all water before disposing.",
    "electronic": "HAZARDOUS/E-WASTE: Take to a specialized collection box.",
    "cloth": "TEXTILE RECYCLING: If clean, donate or recycle; otherwise, burnable.",
}

SEARCH_HISTORY = []
TOTAL_SCANNED = 0


@app.route("/", methods=["GET", "POST"])
def index():
    global TOTAL_SCANNED
    result = None
    query = ""
    if request.method == "POST":
        query = request.form.get("search", "").lower().strip()
        if query:
            # --- STEP 1: EXACT MATCH ---
            if query in GOMI_DATA:
                result = GOMI_DATA[query]

            # --- STEP 2: KEYWORD SEARCH ---
            if not result:
                for category, synonyms_list in SYNONYMS.items():
                    if any(word in query for word in synonyms_list):
                        result = (
                            f"DETECTED {category.upper()} -> {CATEGORY_RULES[category]}"
                        )
                        break

            # --- STEP 3: SMART FUZZY FALLBACK (Search Everything) ---
            if not result:
                # Create a master list of all known words
                master_list = list(GOMI_DATA.keys())
                for category_words in SYNONYMS.values():
                    master_list.extend(category_words)

                closest_match = process.extractOne(query, master_list, score_cutoff=60)

                if closest_match:
                    match_name = closest_match[0]
                    # Check if the match belongs to GOMI_DATA
                    if match_name in GOMI_DATA:
                        result = f"Did you mean {match_name.upper()}? -> {GOMI_DATA[match_name]}"
                    else:
                        # Otherwise, find which category it belongs to
                        for category, words in SYNONYMS.items():
                            if match_name in words:
                                result = f"Did you mean {match_name.upper()}? -> {CATEGORY_RULES[category]}"
                                break
                else:
                    result = "UNKNOWN OBJECT. STATUS: SEND TO INCINERATOR."

            SEARCH_HISTORY.insert(0, query)
            TOTAL_SCANNED += 1
            if len(SEARCH_HISTORY) > 5:
                SEARCH_HISTORY.pop()

    return render_template(
        "index.html",
        result=result,
        query=query,
        history=SEARCH_HISTORY,
        total_count=TOTAL_SCANNED,
    )


@app.route("/suggest")
def suggest():
    q = request.args.get("q", "").lower()
    if not q:
        return jsonify([])
    all_words = list(GOMI_DATA.keys())
    for word_list in SYNONYMS.values():
        all_words.extend(word_list)
    unique_words = list(set(all_words))
    suggestions = [w for w in unique_words if q in w]
    return jsonify(suggestions[:5])


@app.route("/fortune")
def trash_fortune():
    fortunes = [
        "You will find a shiny nickel in a pile of wet cardboard.",
        "Your future is like a plastic bag: drifting through the wind.",
        "Beware of the bin on 5th street; it knows what you did.",
        "A discarded soda can holds the answer to your deepest question.",
        "You will soon be reunited with that one sock you lost in 2019.",
    ]
    prediction = random.choice(fortunes)
    return render_template(
        "index.html",
        result=prediction,
        query="THE SPIRITS",
        history=SEARCH_HISTORY,
        total_count=TOTAL_SCANNED,
    )


if __name__ == "__main__":
    app.run(debug=True)
