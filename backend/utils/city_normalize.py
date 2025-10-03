"""
City normalization utility for Turkish cities
Handles common misspellings and variations
"""
import re
from typing import Dict

# Turkish city normalization mapping
CITY_MAPPING: Dict[str, str] = {
    # Adana
    "adana": "adana",
    "adana": "adana",
    
    # Adıyaman
    "adıyaman": "adıyaman",
    "adiyaman": "adıyaman",
    
    # Afyon
    "afyon": "afyon",
    "afyonkarahisar": "afyon",
    "afyon karahisar": "afyon",
    
    # Ağrı
    "ağrı": "ağrı",
    "agri": "ağrı",
    
    # Aksaray - Most common misspelling
    "aksary": "aksaray",
    "aksaray": "aksaray",
    "akasray": "aksaray",
    "akasary": "aksaray",
    
    # Amasya
    "amasya": "amasya",
    
    # Ankara
    "ankara": "ankara",
    "anakara": "ankara",
    
    # Antalya
    "antalya": "antalya",
    "antalaya": "antalya",
    
    # Artvin
    "artvin": "artvin",
    
    # Aydın
    "aydın": "aydın",
    "aydin": "aydın",
    
    # Balıkesir
    "balıkesir": "balıkesir",
    "balikesir": "balıkesir",
    "balıkessir": "balıkesir",
    
    # Bilecik
    "bilecik": "bilecik",
    
    # Bingöl
    "bingöl": "bingöl",
    "bingol": "bingöl",
    
    # Bitlis
    "bitlis": "bitlis",
    
    # Bolu
    "bolu": "bolu",
    
    # Burdur
    "burdur": "burdur",
    
    # Bursa
    "bursa": "bursa",
    
    # Çanakkale
    "çanakkale": "çanakkale",
    "canakkale": "çanakkale",
    "chanakkale": "çanakkale",
    
    # Çankırı
    "çankırı": "çankırı",
    "cankiri": "çankırı",
    "çankiri": "çankırı",
    
    # Çorum
    "çorum": "çorum",
    "corum": "çorum",
    
    # Denizli
    "denizli": "denizli",
    
    # Diyarbakır
    "diyarbakır": "diyarbakır",
    "diyarbakir": "diyarbakır",
    "diyarbekir": "diyarbakır",
    
    # Edirne
    "edirne": "edirne",
    
    # Elazığ
    "elazığ": "elazığ",
    "elazig": "elazığ",
    "elazıg": "elazığ",
    
    # Erzincan
    "erzincan": "erzincan",
    
    # Erzurum
    "erzurum": "erzurum",
    
    # Eskişehir
    "eskişehir": "eskişehir",
    "eskisehir": "eskişehir",
    
    # Gaziantep
    "gaziantep": "gaziantep",
    "gaziantap": "gaziantep",
    "antep": "gaziantep",
    
    # Giresun
    "giresun": "giresun",
    
    # Gümüşhane
    "gümüşhane": "gümüşhane",
    "gumushane": "gümüşhane",
    
    # Hakkari
    "hakkari": "hakkari",
    "hakkâri": "hakkari",
    
    # Hatay
    "hatay": "hatay",
    "antakya": "hatay",
    
    # Isparta
    "ısparta": "ısparta",
    "isparta": "ısparta",
    
    # İstanbul - Most common variations
    "ıstanbul": "ıstanbul",
    "istanbul": "ıstanbul",
    "istambul": "ıstanbul",
    "stanbul": "ıstanbul",
    
    # İzmir
    "ızmir": "ızmir",
    "izmir": "ızmir",
    
    # Kars
    "kars": "kars",
    
    # Kastamonu
    "kastamonu": "kastamonu",
    
    # Kayseri
    "kayseri": "kayseri",
    "kaiseri": "kayseri",
    
    # Kırklareli
    "kırklareli": "kırklareli",
    "kirklareli": "kırklareli",
    
    # Kırşehir
    "kırşehir": "kırşehir",
    "kirsehir": "kırşehir",
    
    # Kocaeli
    "kocaeli": "kocaeli",
    "izmit": "kocaeli",
    
    # Konya
    "konya": "konya",
    
    # Kütahya
    "kütahya": "kütahya",
    "kutahya": "kütahya",
    
    # Malatya
    "malatya": "malatya",
    
    # Manisa
    "manisa": "manisa",
    
    # Mardin
    "mardin": "mardin",
    
    # Mersin
    "mersin": "mersin",
    "içel": "mersin",
    
    # Muğla
    "muğla": "muğla",
    "mugla": "muğla",
    
    # Muş
    "muş": "muş",
    "mus": "muş",
    
    # Nevşehir
    "nevşehir": "nevşehir",
    "nevsehir": "nevşehir",
    
    # Niğde
    "niğde": "niğde",
    "nigde": "niğde",
    
    # Ordu
    "ordu": "ordu",
    
    # Rize
    "rize": "rize",
    
    # Sakarya
    "sakarya": "sakarya",
    
    # Samsun
    "samsun": "samsun",
    
    # Siirt
    "siirt": "siirt",
    
    # Sinop
    "sinop": "sinop",
    
    # Sivas
    "sivas": "sivas",
    
    # Tekirdağ
    "tekirdağ": "tekirdağ",
    "tekirdag": "tekirdağ",
    
    # Tokat
    "tokat": "tokat",
    
    # Trabzon
    "trabzon": "trabzon",
    
    # Tunceli
    "tunceli": "tunceli",
    
    # Şanlıurfa
    "şanlıurfa": "şanlıurfa",
    "sanliurfa": "şanlıurfa",
    "urfa": "şanlıurfa",
    
    # Uşak
    "uşak": "uşak",
    "usak": "uşak",
    
    # Van
    "van": "van",
    
    # Yozgat
    "yozgat": "yozgat",
    
    # Zonguldak
    "zonguldak": "zonguldak",
    
    # Aksaray specific variations (most problematic)
    "aksary": "aksaray",
    "akasry": "aksaray",
    "akasray": "aksaray",
    "aksarai": "aksaray",
    
    # Other common misspellings
    "burssa": "bursa",
    "izmt": "ızmir",
    "ankar": "ankara",
}

def normalize_city_name(city: str) -> str:
    """
    Normalize Turkish city name to standard form
    
    Args:
        city: Input city name (possibly misspelled)
        
    Returns:
        Normalized city name
    """
    if not city:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = city.lower().strip()
    
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove non-alphabetic characters except spaces
    normalized = re.sub(r'[^a-zçğıöşü\s]', '', normalized)
    
    # Check direct mapping
    if normalized in CITY_MAPPING:
        return CITY_MAPPING[normalized]
    
    # Try fuzzy matching for common patterns
    for key, value in CITY_MAPPING.items():
        # Check if input starts with key (partial match)
        if normalized.startswith(key[:3]) and len(key) > 3:
            return value
            
        # Check Levenshtein-like distance for very similar strings
        if len(normalized) == len(key) and _similar_strings(normalized, key):
            return value
    
    # If no match found, return cleaned version
    return normalized

def _similar_strings(s1: str, s2: str, max_diff: int = 2) -> bool:
    """Check if two strings are similar (simple implementation)"""
    if len(s1) != len(s2):
        return False
    
    diff_count = sum(c1 != c2 for c1, c2 in zip(s1, s2))
    return diff_count <= max_diff

def get_all_normalized_cities() -> list:
    """Get list of all normalized city names"""
    return sorted(set(CITY_MAPPING.values()))

# Example usage and test cases
if __name__ == "__main__":
    test_cases = [
        "Aksary",
        "aksaray", 
        "İstanbul",
        "istanbul",
        "ıstanbul",
        "Gaziantap",
        "Burssa",
        "Ankar",
    ]
    
    print("City Normalization Test:")
    print("-" * 40)
    for city in test_cases:
        normalized = normalize_city_name(city)
        print(f"{city:12} → {normalized}")