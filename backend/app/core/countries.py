"""Canonical country normalization and registry for travel destinations."""

import re

# Standard popular travel countries (displayed in UI before initial import)
POPULAR_COUNTRIES = [
    "Hiszpania",
    "Grecja",
    "Egipt",
    "Turcja",
    "Włochy",
    "Bułgaria",
    "Cypr",
    "Chorwacja",
    "Tunezja",
    "Dominikana",
    "Malediwy",
    "Meksyk",
    "Zjednoczone Emiraty Arabskie",
    "Tanzania",
    "Albania",
    "Czarnogóra",
    "Portugalia",
]

# Default region catalogs per country before DB import
DEFAULT_COUNTRY_REGIONS: dict[str, list[str]] = {
    "Hiszpania": ["Costa Brava", "Costa del Sol", "Costa de la Luz", "Costa Blanca", "Costa Dorada", "Fuerteventura", "Gran Canaria", "Lanzarote", "Majorka", "Teneryfa", "Ibiza", "Menorca"],
    "Grecja": ["Kreta", "Rodos", "Zakynthos", "Korfu", "Kos", "Santorini", "Mykonos", "Chania", "Heraklion", "Kefalonia", "Lefkada", "Evia", "Thassos", "Lesbos", "Samos"],
    "Egipt": ["Hurghada", "Marsa Alam", "Sharm el Sheikh", "Sharm El Sheikh", "El Gouna", "Sahl Hasheesh", "Marsa Matrouh", "El Alamein"],
    "Turcja": ["Riwiera Turecka", "Alanya", "Side", "Bodrum", "Antalya", "Marmaris", "Kemer", "Belek", "Dalaman", "Fethiye"],
    "Włochy": ["Sardynia", "Sycylia", "Kalabria", "Rimini"],
    "Cypr": ["Paphos", "Larnaca", "Ayia Napa", "Limassol"],
    "Bułgaria": ["Słoneczny Brzeg", "Złote Piaski"],
    "Chorwacja": ["Istria", "Dalmacja", "Makarska"],
    "Tunezja": ["Djerba", "Hammamet", "Monastir", "Sousse"],
    "Dominikana": ["Punta Cana", "Puerto Plata"],
    "Malediwy": ["Atol Male", "Atol Ari"],
    "Meksyk": ["Cancun", "Playa del Carmen", "Riviera Maya"],
    "Zjednoczone Emiraty Arabskie": ["Dubaj", "Abu Dhabi", "Ras al Khaimah"],
    "Tanzania": ["Zanzibar"],
    "Albania": ["Durres", "Saranda", "Vlora"],
    "Czarnogóra": ["Budva", "Kotor", "Ulcinj"],
    "Portugalia": ["Algarve", "Madera"],
}

# Mapping from raw/alias strings to canonical polish country names
# Includes country names, ISO codes, cities, airports, and regions
COUNTRY_CANONICAL_MAP = {
    # === Hiszpania ===
    "hiszpania": "Hiszpania",
    "spain": "Hiszpania",
    "es": "Hiszpania",
    # Popularne lotniska/miasta w Hiszpanii
    "malaga": "Hiszpania",
    "málaga": "Hiszpania",
    "barcelona": "Hiszpania",
    "madryt": "Hiszpania",
    "madrid": "Hiszpania",
    "majorka": "Hiszpania",
    "mallorca": "Hiszpania",
    "palma de mallorca": "Hiszpania",
    "ibiza": "Hiszpania",
    "teneryfa": "Hiszpania",
    "tenerife": "Hiszpania",
    "gran canaria": "Hiszpania",
    "fuerteventura": "Hiszpania",
    "lanzarote": "Hiszpania",
    "alicante": "Hiszpania",
    "walencja": "Hiszpania",
    "valencia": "Hiszpania",
    "sevilla": "Hiszpania",
    "kordoba": "Hiszpania",
    "andaluzja": "Hiszpania",
    "costa del sol": "Hiszpania",
    "costa brava": "Hiszpania",
    "costa blanca": "Hiszpania",
    "costa daurada": "Hiszpania",
    "reus": "Hiszpania",
    "girona": "Hiszpania",
    "menorca": "Hiszpania",
    # === Grecja ===
    "grecja": "Grecja",
    "greece": "Grecja",
    "gr": "Grecja",
    # Popularne wyspy/regiony Grecji
    "kreta": "Grecja",
    "crete": "Grecja",
    "heraklion": "Grecja",
    "chania": "Grecja",
    "rodos": "Grecja",
    "rhodes": "Grecja",
    "zakynthos": "Grecja",
    "zante": "Grecja",
    "korfu": "Grecja",
    "corfu": "Grecja",
    "kerkyra": "Grecja",
    "kos": "Grecja",
    "mykonos": "Grecja",
    "santoryn": "Grecja",
    "santorini": "Grecja",
    "lefkada": "Grecja",
    "kefalonia": "Grecja",
    "skiathos": "Grecja",
    "thessaloniki": "Grecja",
    "ateny": "Grecja",
    "athens": "Grecja",
    "samos": "Grecja",
    "lesbos": "Grecja",
    "rethymno": "Grecja",
    # === Egipt ===
    "egipt": "Egipt",
    "egypt": "Egipt",
    "eg": "Egipt",
    "hurghada": "Egipt",
    "marsa alam": "Egipt",
    "sharm el sheikh": "Egipt",
    "sharm el-sheikh": "Egipt",
    "cairo": "Egipt",
    "kair": "Egipt",
    "luksor": "Egipt",
    "luxor": "Egipt",
    "el gouna": "Egipt",
    "port ghalib": "Egipt",
    "safaga": "Egipt",
    "sahl hasheesh": "Egipt",
    # === Turcja ===
    "turcja": "Turcja",
    "turkey": "Turcja",
    "tr": "Turcja",
    "antalya": "Turcja",
    "alanya": "Turcja",
    "side": "Turcja",
    "bodrum": "Turcja",
    "marmaris": "Turcja",
    "istanbul": "Turcja",
    "stambuł": "Turcja",
    "izmir": "Turcja",
    "kemer": "Turcja",
    "belek": "Turcja",
    "dalaman": "Turcja",
    "kusadasi": "Turcja",
    "fethiye": "Turcja",
    "riwiera turecka": "Turcja",
    "turkish riviera": "Turcja",
    # === Włochy ===
    "włochy": "Włochy",
    "wlochy": "Włochy",
    "italy": "Włochy",
    "it": "Włochy",
    "rzym": "Włochy",
    "rome": "Włochy",
    "mediolan": "Włochy",
    "milan": "Włochy",
    "wenecja": "Włochy",
    "venice": "Włochy",
    "sardynia": "Włochy",
    "sardinia": "Włochy",
    "sycylia": "Włochy",
    "sicily": "Włochy",
    "rimini": "Włochy",
    "kalabria": "Włochy",
    "calabria": "Włochy",
    "neapol": "Włochy",
    "naples": "Włochy",
    # === Bułgaria ===
    "bułgaria": "Bułgaria",
    "bulgaria": "Bułgaria",
    "bg": "Bułgaria",
    "słoneczny brzeg": "Bułgaria",
    "sunny beach": "Bułgaria",
    "złote piaski": "Bułgaria",
    "golden sands": "Bułgaria",
    "warna": "Bułgaria",
    "varna": "Bułgaria",
    "burgas": "Bułgaria",
    "sozopol": "Bułgaria",
    # === Cypr ===
    "cypr": "Cypr",
    "cyprus": "Cypr",
    "cy": "Cypr",
    "paphos": "Cypr",
    "larnaka": "Cypr",
    "larnaca": "Cypr",
    "limassol": "Cypr",
    "ayia napa": "Cypr",
    "protaras": "Cypr",
    "nikosia": "Cypr",
    "nicosia": "Cypr",
    # === Chorwacja ===
    "chorwacja": "Chorwacja",
    "croatia": "Chorwacja",
    "hr": "Chorwacja",
    "split": "Chorwacja",
    "dubrownik": "Chorwacja",
    "dubrovnik": "Chorwacja",
    "zadar": "Chorwacja",
    "rijeka": "Chorwacja",
    "istria": "Chorwacja",
    "dalmacja": "Chorwacja",
    "dalmatia": "Chorwacja",
    "makarska": "Chorwacja",
    "pula": "Chorwacja",
    "rovinj": "Chorwacja",
    # === Tunezja ===
    "tunezja": "Tunezja",
    "tunisia": "Tunezja",
    "tn": "Tunezja",
    "djerba": "Tunezja",
    "hammamet": "Tunezja",
    "monastir": "Tunezja",
    "sousse": "Tunezja",
    "enfidha": "Tunezja",
    "tunis": "Tunezja",
    "nabeul": "Tunezja",
    # === Dominikana ===
    "dominikana": "Dominikana",
    "dominican republic": "Dominikana",
    "do": "Dominikana",
    "punta cana": "Dominikana",
    "puerto plata": "Dominikana",
    "la romana": "Dominikana",
    "santo domingo": "Dominikana",
    # === Malediwy ===
    "malediwy": "Malediwy",
    "maldives": "Malediwy",
    "mv": "Malediwy",
    "malé": "Malediwy",
    "male": "Malediwy",
    "atol ari": "Malediwy",
    "atol male": "Malediwy",
    "ari atoll": "Malediwy",
    # === Meksyk ===
    "meksyk": "Meksyk",
    "mexico": "Meksyk",
    "mx": "Meksyk",
    "cancun": "Meksyk",
    "cancún": "Meksyk",
    "playa del carmen": "Meksyk",
    "riviera maya": "Meksyk",
    "tulum": "Meksyk",
    "los cabos": "Meksyk",
    # === Zjednoczone Emiraty Arabskie ===
    "emiraty arabskie": "Zjednoczone Emiraty Arabskie",
    "zjednoczone emiraty arabskie": "Zjednoczone Emiraty Arabskie",
    "uae": "Zjednoczone Emiraty Arabskie",
    "ae": "Zjednoczone Emiraty Arabskie",
    "dubai": "Zjednoczone Emiraty Arabskie",
    "dubaj": "Zjednoczone Emiraty Arabskie",
    "abu dhabi": "Zjednoczone Emiraty Arabskie",
    "abu zabi": "Zjednoczone Emiraty Arabskie",
    "ras al khaimah": "Zjednoczone Emiraty Arabskie",
    "ras al-khaimah": "Zjednoczone Emiraty Arabskie",
    "sharjah": "Zjednoczone Emiraty Arabskie",
    # === Tanzania / Zanzibar ===
    "tanzania": "Tanzania",
    "zanzibar": "Tanzania",
    "tz": "Tanzania",
    "dar es salaam": "Tanzania",
    # === Albania ===
    "albania": "Albania",
    "al": "Albania",
    "durres": "Albania",
    "durrës": "Albania",
    "saranda": "Albania",
    "sarandë": "Albania",
    "vlora": "Albania",
    "vlorë": "Albania",
    "tirana": "Albania",
    "tiranë": "Albania",
    # === Czarnogóra ===
    "czarnogóra": "Czarnogóra",
    "czarnogora": "Czarnogóra",
    "montenegro": "Czarnogóra",
    "me": "Czarnogóra",
    "budva": "Czarnogóra",
    "kotor": "Czarnogóra",
    "ulcinj": "Czarnogóra",
    "bar": "Czarnogóra",
    "tivat": "Czarnogóra",
    "podgorica": "Czarnogóra",
    # === Portugalia ===
    "portugalia": "Portugalia",
    "portugal": "Portugalia",
    "pt": "Portugalia",
    "lizbona": "Portugalia",
    "lisbon": "Portugalia",
    "faro": "Portugalia",
    "algarve": "Portugalia",
    "madera": "Portugalia",
    "madeira": "Portugalia",
    "porto": "Portugalia",
}

# Slug map for search URLs across providers (e.g. Itaka, Wakacje.pl, TUI, Rainbow)
COUNTRY_SLUG_MAP = {
    "Hiszpania": "hiszpania",
    "Grecja": "grecja",
    "Egipt": "egipt",
    "Turcja": "turcja",
    "Włochy": "wlochy",
    "Bułgaria": "bulgaria",
    "Cypr": "cypr",
    "Chorwacja": "chorwacja",
    "Tunezja": "tunezja",
    "Dominikana": "republika-dominikanska",
    "Malediwy": "malediwy",
    "Meksyk": "meksyk",
    "Zjednoczone Emiraty Arabskie": "zjednoczone-emiraty-arabskie",
    "Tanzania": "tanzania",
    "Albania": "albania",
    "Czarnogóra": "czarnogora",
    "Portugalia": "portugalia",
}


def normalize_country_name(raw_name: str | None) -> str:
    """Clean and normalize a raw country string to canonical Polish format."""
    if not raw_name:
        return "Inne"
    
    text = raw_name.strip()
    
    # Handle composite strings like "Tunezja / Djerba" or "Hiszpania - Mallorca"
    if "/" in text:
        text = text.split("/")[0].strip()
    if " - " in text:
        text = text.split(" - ")[0].strip()

    cleaned_key = text.lower()
    if cleaned_key in COUNTRY_CANONICAL_MAP:
        return COUNTRY_CANONICAL_MAP[cleaned_key]
    
    # Titlecase fallback for unlisted countries
    return text.title()


# Pre-computed region lookup map for Python-side region normalization
_REGION_CANONICAL_MAP: dict[str, str] = {}
for _cname, _rlist in DEFAULT_COUNTRY_REGIONS.items():
    for _r in _rlist:
        _REGION_CANONICAL_MAP[_r.lower().strip()] = _r


def normalize_region_name(raw_name: str | None) -> str | None:
    """Clean and normalize a raw region string to canonical DB representation.
    
    Allows standard SQL equality (Offer.region == normalized_region) to use indexes.
    """
    if not raw_name:
        return None
    cleaned = str(raw_name).strip()
    if not cleaned:
        return None
    key = cleaned.lower()
    if key in _REGION_CANONICAL_MAP:
        return _REGION_CANONICAL_MAP[key]
    
    # Capitalize words while keeping lowercase particles (de, la, del, el, al) intact unless starting a word
    words = cleaned.split()
    particles = {"de", "la", "del", "el", "al"}
    norm_words = []
    for i, w in enumerate(words):
        w_lower = w.lower()
        if i > 0 and w_lower in particles:
            norm_words.append(w_lower)
        else:
            norm_words.append(w.capitalize())
    return " ".join(norm_words)


def normalize_provider_name(raw_name: str | None) -> str | None:
    """Clean and normalize a provider string or alias to canonical Provider enum value.
    
    Maps aliases ('wakacje.pl', 'wakacje-pl', 'Wakacje.pl') to canonical DB value ('wakacje_pl').
    Allows standard SQL equality (Offer.provider == normalized_provider) to use indexes.
    """
    if not raw_name:
        return None
    cleaned = str(raw_name).strip().lower()
    if not cleaned:
        return None
    alias_map = {
        "wakacje.pl": "wakacje_pl",
        "wakacje-pl": "wakacje_pl",
        "wakacje pl": "wakacje_pl",
        "wakacje": "wakacje_pl",
        "itaka": "itaka",
        "tui": "tui",
        "rainbow": "rainbow",
    }
    return alias_map.get(cleaned, cleaned.replace(".", "_").replace("-", "_").replace(" ", "_"))


def get_country_slug(country_name: str) -> str:
    """Get standard web URL slug for a given country name."""
    canonical = normalize_country_name(country_name)
    if canonical in COUNTRY_SLUG_MAP:
        return COUNTRY_SLUG_MAP[canonical]
    
    # Generic slugify
    slug = canonical.lower()
    slug = re.sub(r'[ąąćęęłłńńóóśśźźżż]', lambda m: {
        'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z'
    }.get(m.group(0), m.group(0)), slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug).strip('-')
    return slug or "hiszpania"

