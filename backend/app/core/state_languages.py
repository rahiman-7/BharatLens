from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class LanguageInfo(BaseModel):
    code: str
    name: str
    native_name: str


class StateLanguageMetadata(BaseModel):
    slug: str
    name: str
    default_language: LanguageInfo
    available_languages: List[LanguageInfo]
    cities: List[str]


# Standard Language Definitions for Indian States and Union Territories
LANGUAGES: Dict[str, LanguageInfo] = {
    "en": LanguageInfo(code="en", name="English", native_name="English"),
    "te": LanguageInfo(code="te", name="Telugu", native_name="తెలుగు"),
    "ta": LanguageInfo(code="ta", name="Tamil", native_name="தமிழ்"),
    "kn": LanguageInfo(code="kn", name="Kannada", native_name="ಕನ್ನಡ"),
    "ml": LanguageInfo(code="ml", name="Malayalam", native_name="മലയാളം"),
    "mr": LanguageInfo(code="mr", name="Marathi", native_name="मराठी"),
    "bn": LanguageInfo(code="bn", name="Bengali", native_name="বাংলা"),
    "gu": LanguageInfo(code="gu", name="Gujarati", native_name="ગુજરાતી"),
    "pa": LanguageInfo(code="pa", name="Punjabi", native_name="ਪੰਜਾਬੀ"),
    "or": LanguageInfo(code="or", name="Odia", native_name="ଓଡ଼ିଆ"),
    "hi": LanguageInfo(code="hi", name="Hindi", native_name="हिन्दी"),
    "as": LanguageInfo(code="as", name="Assamese", native_name="অসমীয়া"),
    "ur": LanguageInfo(code="ur", name="Urdu", native_name="اردو"),
    "kok": LanguageInfo(code="kok", name="Konkani", native_name="कोंकणी"),
    "ne": LanguageInfo(code="ne", name="Nepali", native_name="नेपाली"),
    "mni": LanguageInfo(code="mni", name="Meitei", native_name="মৈতৈলোন্"),
    "lus": LanguageInfo(code="lus", name="Mizo", native_name="Mizo ṭawng"),
}


# Centralized Registry: All 28 Indian States + 8 Union Territories
INDIAN_STATES_REGISTRY: List[Dict[str, Any]] = [
    # Southern States
    {
        "slug": "telangana",
        "name": "Telangana",
        "default_lang": "te",
        "supported_langs": ["te", "en", "ur", "hi"],
        "cities": ["Hyderabad", "Secunderabad", "Warangal", "Nizamabad", "Karimnagar"],
    },
    {
        "slug": "andhra-pradesh",
        "name": "Andhra Pradesh",
        "default_lang": "te",
        "supported_langs": ["te", "en", "hi"],
        "cities": ["Amaravati", "Visakhapatnam", "Vijayawada", "Tirupati", "Guntur"],
    },
    {
        "slug": "tamil-nadu",
        "name": "Tamil Nadu",
        "default_lang": "ta",
        "supported_langs": ["ta", "en"],
        "cities": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    },
    {
        "slug": "karnataka",
        "name": "Karnataka",
        "default_lang": "kn",
        "supported_langs": ["kn", "en", "hi"],
        "cities": ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru", "Belagavi"],
    },
    {
        "slug": "kerala",
        "name": "Kerala",
        "default_lang": "ml",
        "supported_langs": ["ml", "en"],
        "cities": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam"],
    },
    # Western States
    {
        "slug": "maharashtra",
        "name": "Maharashtra",
        "default_lang": "mr",
        "supported_langs": ["mr", "en", "hi"],
        "cities": ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Chhatrapati Sambhajinagar"],
    },
    {
        "slug": "gujarat",
        "name": "Gujarat",
        "default_lang": "gu",
        "supported_langs": ["gu", "en", "hi"],
        "cities": ["Gandhinagar", "Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    },
    {
        "slug": "goa",
        "name": "Goa",
        "default_lang": "kok",
        "supported_langs": ["kok", "en", "mr", "hi"],
        "cities": ["Panaji", "Margao", "Vasco da Gama", "Mapusa"],
    },
    # Eastern States
    {
        "slug": "west-bengal",
        "name": "West Bengal",
        "default_lang": "bn",
        "supported_langs": ["bn", "en", "hi"],
        "cities": ["Kolkata", "Howrah", "Siliguri", "Asansol", "Durgapur", "Darjeeling"],
    },
    {
        "slug": "odisha",
        "name": "Odisha",
        "default_lang": "or",
        "supported_langs": ["or", "en", "hi"],
        "cities": ["Bhubaneswar", "Cuttack", "Rourkela", "Puri", "Sambalpur"],
    },
    {
        "slug": "bihar",
        "name": "Bihar",
        "default_lang": "hi",
        "supported_langs": ["hi", "en", "ur"],
        "cities": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
    },
    {
        "slug": "jharkhand",
        "name": "Jharkhand",
        "default_lang": "hi",
        "supported_langs": ["hi", "en"],
        "cities": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar"],
    },
    # Northern & Central States
    {
        "slug": "uttar-pradesh",
        "name": "Uttar Pradesh",
        "default_lang": "hi",
        "supported_langs": ["hi", "en", "ur"],
        "cities": ["Lucknow", "Noida", "Varanasi", "Kanpur", "Agra", "Prayagraj", "Ayodhya"],
    },
    {
        "slug": "madhya-pradesh",
        "name": "Madhya Pradesh",
        "default_lang": "hi",
        "supported_langs": ["hi", "en"],
        "cities": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain"],
    },
    {
        "slug": "rajasthan",
        "name": "Rajasthan",
        "default_lang": "hi",
        "supported_langs": ["hi", "en"],
        "cities": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer"],
    },
    {
        "slug": "punjab",
        "name": "Punjab",
        "default_lang": "pa",
        "supported_langs": ["pa", "en", "hi"],
        "cities": ["Amritsar", "Ludhiana", "Jalandhar", "Patiala", "Bathinda"],
    },
    {
        "slug": "haryana",
        "name": "Haryana",
        "default_lang": "hi",
        "supported_langs": ["hi", "en", "pa"],
        "cities": ["Gurugram", "Faridabad", "Panipat", "Ambala", "Rohtak"],
    },
    {
        "slug": "chhattisgarh",
        "name": "Chhattisgarh",
        "default_lang": "hi",
        "supported_langs": ["hi", "en"],
        "cities": ["Raipur", "Bilaspur", "Bhilai", "Durg", "Korba"],
    },
    {
        "slug": "uttarakhand",
        "name": "Uttarakhand",
        "default_lang": "hi",
        "supported_langs": ["hi", "en"],
        "cities": ["Dehradun", "Haridwar", "Rishikesh", "Nainital", "Haldwani"],
    },
    {
        "slug": "himachal-pradesh",
        "name": "Himachal Pradesh",
        "default_lang": "hi",
        "supported_langs": ["hi", "en"],
        "cities": ["Shimla", "Manali", "Dharamshala", "Kullu", "Mandi"],
    },
    # Northeastern States
    {
        "slug": "assam",
        "name": "Assam",
        "default_lang": "as",
        "supported_langs": ["as", "en", "bn", "hi"],
        "cities": ["Guwahati", "Dispur", "Silchar", "Dibrugarh", "Jorhat"],
    },
    {
        "slug": "sikkim",
        "name": "Sikkim",
        "default_lang": "ne",
        "supported_langs": ["ne", "en", "hi"],
        "cities": ["Gangtok", "Namchi", "Gyalshing"],
    },
    {
        "slug": "tripura",
        "name": "Tripura",
        "default_lang": "bn",
        "supported_langs": ["bn", "en", "hi"],
        "cities": ["Agartala", "Udaipur", "Dharmanagar"],
    },
    {
        "slug": "manipur",
        "name": "Manipur",
        "default_lang": "mni",
        "supported_langs": ["mni", "en"],
        "cities": ["Imphal", "Churachandpur", "Thoubal"],
    },
    {
        "slug": "meghalaya",
        "name": "Meghalaya",
        "default_lang": "en",
        "supported_langs": ["en", "hi"],
        "cities": ["Shillong", "Tura", "Jowai"],
    },
    {
        "slug": "mizoram",
        "name": "Mizoram",
        "default_lang": "lus",
        "supported_langs": ["lus", "en"],
        "cities": ["Aizawl", "Lunglei", "Champhai"],
    },
    {
        "slug": "nagaland",
        "name": "Nagaland",
        "default_lang": "en",
        "supported_langs": ["en", "hi"],
        "cities": ["Kohima", "Dimapur", "Mokokchung"],
    },
    {
        "slug": "arunachal-pradesh",
        "name": "Arunachal Pradesh",
        "default_lang": "en",
        "supported_langs": ["en", "hi"],
        "cities": ["Itanagar", "Naharlagun", "Pasighat", "Tawang"],
    },
    # Union Territories
    {
        "slug": "delhi",
        "name": "Delhi",
        "default_lang": "hi",
        "supported_langs": ["hi", "en", "pa", "ur"],
        "cities": ["New Delhi", "Central Delhi", "South Delhi", "North Delhi"],
    },
    {
        "slug": "jammu-and-kashmir",
        "name": "Jammu and Kashmir",
        "default_lang": "ur",
        "supported_langs": ["ur", "en", "hi"],
        "cities": ["Srinagar", "Jammu", "Anantnag", "Baramulla"],
    },
    {
        "slug": "ladakh",
        "name": "Ladakh",
        "default_lang": "hi",
        "supported_langs": ["hi", "en", "ur"],
        "cities": ["Leh", "Kargil"],
    },
    {
        "slug": "chandigarh",
        "name": "Chandigarh",
        "default_lang": "pa",
        "supported_langs": ["pa", "en", "hi"],
        "cities": ["Chandigarh"],
    },
    {
        "slug": "puducherry",
        "name": "Puducherry",
        "default_lang": "ta",
        "supported_langs": ["ta", "en", "fr"],
        "cities": ["Puducherry", "Karaikal", "Mahe", "Yanam"],
    },
    {
        "slug": "andaman-and-nicobar",
        "name": "Andaman and Nicobar Islands",
        "default_lang": "hi",
        "supported_langs": ["hi", "en", "bn", "ta", "te"],
        "cities": ["Port Blair"],
    },
    {
        "slug": "dadra-and-nagar-haveli-and-daman-and-diu",
        "name": "Dadra and Nagar Haveli and Daman and Diu",
        "default_lang": "gu",
        "supported_langs": ["gu", "en", "hi", "mr"],
        "cities": ["Daman", "Diu", "Silvassa"],
    },
    {
        "slug": "lakshadweep",
        "name": "Lakshadweep",
        "default_lang": "ml",
        "supported_langs": ["ml", "en"],
        "cities": ["Kavaratti"],
    },
]


def get_all_states_metadata() -> List[StateLanguageMetadata]:
    """Retrieve structured metadata for all states and UTs."""
    res = []
    for item in INDIAN_STATES_REGISTRY:
        default_l = LANGUAGES.get(item["default_lang"], LANGUAGES["en"])
        avail = [LANGUAGES[code] for code in item["supported_langs"] if code in LANGUAGES]
        # Always ensure English is included
        if LANGUAGES["en"] not in avail:
            avail.append(LANGUAGES["en"])
        
        res.append(
            StateLanguageMetadata(
                slug=item["slug"],
                name=item["name"],
                default_language=default_l,
                available_languages=avail,
                cities=item["cities"],
            )
        )
    return res


def get_state_by_slug(slug: str) -> Optional[StateLanguageMetadata]:
    """Find state metadata by URL slug."""
    clean_slug = slug.strip().lower()
    for item in get_all_states_metadata():
        if item.slug == clean_slug or item.name.lower() == clean_slug.replace("-", " "):
            return item
    return None


def get_state_by_name(name: str) -> Optional[StateLanguageMetadata]:
    """Find state metadata by name."""
    clean_name = name.strip().lower()
    for item in get_all_states_metadata():
        if item.name.lower() == clean_name:
            return item
    return None
