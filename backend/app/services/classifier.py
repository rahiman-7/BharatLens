import re
import logging
from typing import Optional

logger = logging.getLogger("bharatlens.classifier")

# Comprehensive Mapping of Indian States & UTs + Major Cities
INDIAN_STATE_KEYWORDS = {
    "Andhra Pradesh": ["andhra pradesh", "andhra", "amaravati", "visakhapatnam", "vizag", "vijayawada", "tirupati", "guntur"],
    "Arunachal Pradesh": ["arunachal pradesh", "arunachal", "itanagar", "tawang"],
    "Assam": ["assam", "guwahati", "dispur", "silchar", "dibrugarh", "jorhat", "kaziranga"],
    "Bihar": ["bihar", "patna", "gaya", "muzaffarpur", "bhagalpur", "nalanda", "darbhanga"],
    "Chhattisgarh": ["chhattisgarh", "raipur", "bilaspur", "bhilai", "durg", "bastar"],
    "Goa": ["goa", "panaji", "margao", "vasco da gama"],
    "Gujarat": ["gujarat", "gandhinagar", "ahmedabad", "surat", "vadodara", "rajkot", "bhavnagar", "kutch", "gift city"],
    "Haryana": ["haryana", "gurugram", "gurgaon", "faridabad", "panipat", "ambala", "rohtak", "karnal"],
    "Himachal Pradesh": ["himachal pradesh", "himachal", "shimla", "manali", "dharamshala", "kullu", "mandi"],
    "Jharkhand": ["jharkhand", "ranchi", "jamshedpur", "dhanbad", "bokaro"],
    "Karnataka": ["karnataka", "bengaluru", "bangalore", "mysuru", "mysore", "hubballi", "mangalore", "mangaluru", "belagavi"],
    "Kerala": ["kerala", "thiruvananthapuram", "trivandrum", "kochi", "cochin", "kozhikode", "calicut", "thrissur", "wayanad"],
    "Madhya Pradesh": ["madhya pradesh", "bhopal", "indore", "gwalior", "jabalpur", "ujjain"],
    "Maharashtra": ["maharashtra", "mumbai", "pune", "nagpur", "thane", "nashik", "aurangabad", "chhatrapati sambhajinagar", "navi mumbai"],
    "Manipur": ["manipur", "imphal"],
    "Meghalaya": ["meghalaya", "shillong"],
    "Mizoram": ["mizoram", "aizawl"],
    "Nagaland": ["nagaland", "kohima", "dimapur"],
    "Odisha": ["odisha", "orissa", "bhubaneswar", "cuttack", "rourkela", "puri"],
    "Punjab": ["punjab", "amritsar", "ludhiana", "jalandhar", "patiala", "bathinda"],
    "Rajasthan": ["rajasthan", "jaipur", "jodhpur", "udaipur", "kota", "bikaner", "ajmer"],
    "Sikkim": ["sikkim", "gangtok"],
    "Tamil Nadu": ["tamil nadu", "tamilnadu", "chennai", "madurai", "coimbatore", "tiruchirappalli", "trichy", "salem"],
    "Telangana": ["telangana", "hyderabad", "secunderabad", "warangal", "nizamabad", "karimnagar"],
    "Tripura": ["tripura", "agartala"],
    "Uttar Pradesh": ["uttar pradesh", "lucknow", "noida", "greater noida", "varanasi", "kashi", "kanpur", "agra", "prayagraj", "allahabad", "ayodhya", "gorakhpur", "meerut", "ghaziabad"],
    "Uttarakhand": ["uttarakhand", "dehradun", "haridwar", "rishikesh", "nainital", "kedarnath"],
    "West Bengal": ["west bengal", "bengal", "kolkata", "calcutta", "howrah", "darjeeling", "siliguri", "asansol"],
    "Delhi": ["delhi", "new delhi", "ncr"],
    "Jammu and Kashmir": ["jammu and kashmir", "jammu", "kashmir", "srinagar"],
    "Ladakh": ["ladakh", "leh", "kargil"],
    "Chandigarh": ["chandigarh"],
    "Puducherry": ["puducherry", "pondicherry"],
}

# Category Keyword Heuristics
CATEGORY_KEYWORDS = {
    "politics": [
        "parliament", "lok sabha", "rajya sabha", "election", "elections", "minister", "prime minister",
        "modi", "rahul gandhi", "bjp", "congress", "aap", "supreme court", "high court", "cabinet",
        "bill", "legislation", "governor", "chief minister", "cm", "mla", "mp", "opposition", "ruling party"
    ],
    "sports": [
        "cricket", "ipl", "bcci", "virat kohli", "rohit sharma", "football", "fifa", "isl", "tennis",
        "badminton", "p.v. sindhu", "olympics", "hockey", "athletics", "f1", "wrestling", "chess",
        "praggnanandhaa", "gold medal", "trophy", "championship", "tournament", "wicket", "runs"
    ],
    "technology": [
        "ai", "artificial intelligence", "tech", "software", "google", "microsoft", "apple", "nvidia",
        "semiconductor", "chipmaker", "startup", "cybersecurity", "smartphone", "cloud", "robotics",
        "quantum", "5g", "6g", "app", "meta", "openai", "chatgpt", "deep learning"
    ],
    "business": [
        "sensex", "nifty", "stock market", "shares", "rbi", "inflation", "gdp", "economy", "rupee",
        "dollar", "tata", "reliance", "adani", "hdfc", "quarterly profit", "revenue", "fiscal",
        "investment", "merger", "acquisition", "banking", "tax", "gst", "ipo"
    ],
    "movies-entertainment": [
        "bollywood", "hollywood", "tollywood", "kollywood", "box office", "actor", "actress", "cinema",
        "trailer", "movie", "film", "ott", "netflix", "prime video", "director", "song", "album", "oscars"
    ],
    "education": [
        "cbse", "icse", "ugc", "aicte", "neet", "jee", "upsc", "university", "college", "school",
        "admissions", "exam", "syllabus", "students", "iit", "iim", "scholarship", "board results"
    ],
    "science": [
        "isro", "nasa", "space", "satellite", "chandrayaan", "gaganyaan", "astronomy", "physics",
        "quantum", "telescope", "james webb", "mars", "moon", "galaxy", "laboratory", "discovery"
    ],
    "health": [
        "health", "hospital", "doctor", "medical", "disease", "vaccine", "cancer", "diabetes",
        "mental health", "wellness", "diet", "nutrition", "who", "fda", "treatment", "medicine", "pharma"
    ],
    "environment": [
        "climate", "pollution", "aqi", "air quality", "monsoon", "rainfall", "flood", "cyclone",
        "wildlife", "forest", "tiger reserve", "solar energy", "renewable", "carbon emissions", "global warming"
    ],
    "crime": [
        "police", "arrested", "custody", "cbi", "ed", "scam", "fraud", "murder", "robbery", "cybercrime",
        "bribe", "smuggling", "encounter", "court sentence", "jail", "fir", "investigation"
    ],
    "lifestyle": [
        "lifestyle", "fashion", "travel", "tourism", "yoga", "culture", "heritage", "cuisine", "food",
        "recipe", "living", "style", "festival", "architecture"
    ],
}


def classify_region(
    title: str,
    description: Optional[str] = None,
    country_hint: Optional[str] = None,
    source_name: Optional[str] = None,
) -> str:
    """Deterministic region classification: 'INDIA' or 'INTERNATIONAL'."""
    if country_hint:
        if country_hint.upper() in ["IN", "INDIA"]:
            return "INDIA"
        if country_hint.upper() in ["GLOBAL", "WORLD", "INTERNATIONAL"]:
            return "INTERNATIONAL"

    # Inspect Indian news sources
    indian_publishers = ["the hindu", "indian express", "ndtv", "times of india", "mint", "hindustan times", "ani"]
    if source_name and any(p in source_name.lower() for p in indian_publishers):
        return "INDIA"

    text = f"{title} {description or ''}".lower()
    
    # Check for Indian contextual signals
    indian_markers = ["india", "indian", "delhi", "mumbai", "modi", "rupee", "isro", "bengaluru", "bjp"]
    for marker in indian_markers:
        if re.search(r"\b" + re.escape(marker) + r"\b", text):
            return "INDIA"

    return "INTERNATIONAL"


def classify_category_deterministic(
    title: str,
    description: Optional[str] = None,
) -> str:
    """Deterministic fallback category classification based on curated keyword scoring."""
    text = f"{title} {description or ''}".lower()

    scores: dict[str, int] = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                scores[cat] += 2 if kw in title.lower() else 1

    best_cat, max_score = max(scores.items(), key=lambda item: item[1])
    if max_score > 0:
        return best_cat

    return "politics"


def classify_category(
    title: str,
    description: Optional[str] = None,
    raw_category: Optional[str] = None,
    min_ml_confidence: float = 0.18,
) -> str:
    """Map raw category or text to one of the 11 BharatLens categories.
    
    Priority Decision Flow:
    1. Direct Provider Category Mapping:
       If the upstream news provider already supplies a valid category (e.g. 'sports', 'technology'),
       we respect provider metadata and return it directly without override.
    2. ML Category Classification (Conservative Gate):
       If raw category is absent/unmapped, the ML pipeline classifies the combined title + description.
       With 11 categories (uniform baseline = 1/11 = 9.09%), predictions are only accepted if the
       calibrated probability is >= min_ml_confidence (0.18, ~2x random baseline).
    3. Deterministic Keyword Fallback:
       If the ML model is missing, throws an exception, or yields low confidence (< 0.18),
       the system seamlessly falls back to the deterministic keyword scoring heuristic.
    4. Default Safety Fallback:
       Returns 'politics' if no category keywords match.
    """
    if raw_category:
        raw = raw_category.lower().strip()

        direct_map = {
            "politics": "politics",
            "sports": "sports",
            "technology": "technology",
            "business": "business",
            "entertainment": "movies-entertainment",
            "movies": "movies-entertainment",
            "education": "education",
            "science": "science",
            "health": "health",
            "environment": "environment",
            "crime": "crime",
            "lifestyle": "lifestyle",
        }
        if raw in direct_map:
            return direct_map[raw]

    # Try ML prediction with confidence gate
    try:
        from app.ml.category_classifier import get_category_classifier, ALLOWED_CATEGORIES
        classifier = get_category_classifier()
        if classifier and classifier.pipeline is not None:
            pred_cat, conf = classifier.predict(title=title, description=description)
            if pred_cat in ALLOWED_CATEGORIES and conf >= min_ml_confidence:
                return pred_cat
    except Exception as e:
        logger.warning(f"ML classification failed, falling back to deterministic heuristic: {e}")

    # Fallback to deterministic keyword rules
    return classify_category_deterministic(title=title, description=description)



def detect_indian_state(
    title: str,
    description: Optional[str] = None,
    region: str = "INDIA",
) -> Optional[str]:
    """Detect Indian state / UT from title and description. Returns None for International or ambiguous news."""
    if region.upper() != "INDIA":
        return None

    text = f"{title} {description or ''}".lower()

    # Exact word boundary matching for states and major cities
    for state_name, keywords in INDIAN_STATE_KEYWORDS.items():
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text):
                return state_name

    return None
