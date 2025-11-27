"""
Configuration module for GetMyHouse application.
Centralizes all configuration variables and constants.
"""

import os
from pathlib import Path
from typing import Literal, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Base Paths
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Application Settings
# =============================================================================

class AppConfig:
    """Application-level configuration."""
    
    # Environment
    ENV: Literal["development", "production"] = os.getenv("APP_ENV", "development")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # Application metadata
    NAME = "GetMyHouse"
    VERSION = "2.2.1"  # v2.2.1: Fixed None display (show N/A instead of "none")
    DESCRIPTION = "AI-Powered Property Search System"
    
    # Port configuration (for Railway)
    PORT: int = int(os.getenv("PORT", "8501"))


# =============================================================================
# Google Cloud / ADK Configuration
# =============================================================================

class ADKConfig:
    """Google ADK and Gemini configuration."""
    
    # API Key (required)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    if not GOOGLE_API_KEY and AppConfig.ENV == "production":
        raise ValueError("GOOGLE_API_KEY must be set in production environment")
    
    # Model settings
    MODEL_NAME = "gemini-2.0-flash-exp"  # Using Gemini 2.0 Flash
    TEMPERATURE = 0.7
    MAX_TOKENS = 8192
    TOP_P = 0.95
    TOP_K = 40
    
    # Safety settings
    SAFETY_SETTINGS = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    }


# =============================================================================
# Database Configuration
# =============================================================================

class DatabaseConfig:
    """Database configuration for session management."""
    
    DB_PATH: Path = Path(os.getenv("DB_PATH", str(DATA_DIR / "sessions.db")))
    
    # SQLite settings
    CONNECTION_STRING = f"sqlite:///{DB_PATH}"
    ECHO_SQL = AppConfig.DEBUG_MODE  # Log SQL queries in debug mode
    
    # Session settings
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    MAX_SESSIONS_PER_USER = 10


# =============================================================================
# Logging Configuration
# =============================================================================

class LoggingConfig:
    """Logging and observability configuration."""
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT: Literal["json", "text"] = os.getenv("LOG_FORMAT", "json")
    
    # Enable/disable features
    ENABLE_TRACING: bool = os.getenv("ENABLE_TRACING", "true").lower() == "true"
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    
    # Log file paths
    LOG_FILE = LOGS_DIR / "getmyhouse.log"
    ERROR_LOG_FILE = LOGS_DIR / "errors.log"
    
    # Rotation settings
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5


# =============================================================================
# Feature Flags
# =============================================================================

class FeatureFlags:
    """Feature flags for enabling/disabling functionality."""
    
    # Data sources
    ENABLE_REAL_SCRAPING: bool = os.getenv("ENABLE_REAL_SCRAPING", "false").lower() == "true"
    MOCK_DATA_ONLY: bool = os.getenv("MOCK_DATA_ONLY", "true").lower() == "true"
    
    # Discovery Agent (v2.0)
    USE_DISCOVERY_AGENT: bool = os.getenv("USE_DISCOVERY_AGENT", "true").lower() == "true"
    
    # UI features
    ENABLE_EXCEL_EXPORT = True
    ENABLE_SEARCH_REFINEMENT = True
    ENABLE_HISTORY_VIEW = True
    
    # Agent features
    ENABLE_PARALLEL_SEARCH = True
    ENABLE_PROPERTY_FILTERING = True


# =============================================================================
# Agent Configuration
# =============================================================================

class AgentConfig:
    """Configuration for ADK agents."""
    
    # Coordinator agent
    COORDINATOR_INSTRUCTION = """
    You are the coordinator agent for GetMyHouse, a property search system.
    
    Your responsibilities:
    1. Understand user requirements for property search
    2. Coordinate specialized agents to find properties
    3. Present results in a clear, organized manner
    4. Handle search refinement requests
    
    Always maintain context from previous searches to enable refinement.
    Be helpful, precise, and professional.
    """
    
    # Search agent
    SEARCH_AGENT_INSTRUCTION = """
    You are a property search specialist.
    
    Your responsibilities:
    1. Search for properties matching user criteria
    2. Use available tools (mock data or real scrapers)
    3. Return structured property data
    4. Handle errors gracefully with informative messages
    
    Focus on accuracy and completeness of property information.
    """
    
    # Filter agent
    FILTER_AGENT_INSTRUCTION = """
    You are a property filtering and ranking specialist.
    
    Your responsibilities:
    1. Analyze properties against user requirements
    2. Calculate match scores (0.0 to 1.0)
    3. Rank properties by relevance
    4. Return top 10 properties
    
    Consider all user criteria: location, price, typology, transport, etc.
    Prioritize exact matches over partial matches.
    """
    
    # Report agent
    REPORT_AGENT_INSTRUCTION = """
    You are a report generation specialist.
    
    Your responsibilities:
    1. Format property data into structured tables
    2. Generate Excel exports
    3. Include all relevant information and links
    4. Provide summary statistics
    
    Ensure all output is clear, professional, and easy to understand.
    """


# =============================================================================
# Search Configuration
# =============================================================================

class SearchConfig:
    """Configuration for property search functionality."""
    
    # Rate limiting
    SEARCH_RATE_LIMIT: int = int(os.getenv("SEARCH_RATE_LIMIT", "10"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    
    # Results configuration
    MAX_RESULTS = 20  # Default number of results
    MAX_RESULTS_OPTIONS = [10, 20, 50]  # User can choose
    MIN_MATCH_SCORE = 0.5  # Minimum relevance score
    
    # Default values
    DEFAULT_COUNTRY = "Portugal"
    DEFAULT_DISTANCE = "1 km"
    DEFAULT_WCS = "any"
    DEFAULT_TRANSPORT = "any"
    
    # Load supported countries from JSON (195 countries)
    @staticmethod
    def _load_countries():
        """Load country list from JSON file."""
        import json
        currency_file = DATA_DIR / "country_currency.json"
        try:
            with open(currency_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return sorted(data.keys())
        except Exception:
            # Fallback to basic list
            return ["Portugal", "Spain", "United States", "United Kingdom"]
    
    # Supported countries (195 total, loaded from JSON)
    SUPPORTED_COUNTRIES = None  # Will be loaded on first access
    
    @classmethod
    def get_supported_countries(cls):
        """Get list of supported countries (lazy loading)."""
        if cls.SUPPORTED_COUNTRIES is None:
            cls.SUPPORTED_COUNTRIES = cls._load_countries()
        return cls.SUPPORTED_COUNTRIES
    
    # Supported currencies (country-dependent) - kept for backwards compatibility
    SUPPORTED_CURRENCIES = [
        "EUR",
        "USD",
        "GBP",
        "CAD",
        "AUD",
        "BRL",
        "CHF",
        "JPY",
        "CNY"
    ]
    
    # Currency mapping (now loaded from JSON)
    CURRENCY_BY_COUNTRY = {
        "Portugal": "EUR",
        "Spain": "EUR",
        "Italy": "EUR",
        "France": "EUR",
        "Greece": "EUR",
        "Germany": "EUR",
        "Netherlands": "EUR",
        "Belgium": "EUR",
        "United Kingdom": "GBP",
        "United States": "USD",
        "Canada": "CAD",
        "Australia": "AUD",
        "Brazil": "BRL",
        "Mexico": "MXN",
        "Switzerland": "CHF",
        "Sweden": "SEK",
        "Norway": "NOK",
        "Denmark": "DKK",
        "Poland": "PLN",
        "Turkey": "TRY",
        "Japan": "JPY",
        "South Korea": "KRW",
        "Singapore": "SGD",
        "United Arab Emirates": "AED",
        "India": "INR",
        "China": "CNY"
    }
    
    @staticmethod
    def get_currency_info(country: str) -> Dict[str, str]:
        """Get currency information from JSON file."""
        import json
        currency_file = DATA_DIR / "country_currency.json"
        
        try:
            with open(currency_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(country, {
                    "currency": "EUR",
                    "symbol": "€",
                    "language": "en"
                })
        except Exception:
            # Fallback
            currency = SearchConfig.CURRENCY_BY_COUNTRY.get(country, "EUR")
            symbol = "€" if currency == "EUR" else "$"
            return {"currency": currency, "symbol": symbol, "language": "en"}
    
    # Distance options (in km)
    DISTANCE_OPTIONS = [1, 2, 5, 10, 20, "any"]
    
    # Property types
    PROPERTY_TYPES = ["any", "flat", "house"]
    
    # Typologies
    TYPOLOGIES = ["T0", "T1", "T2", "T3", "T4", "T4+"]
    
    # Usage states
    USAGE_STATES = ["any", "brand new", "new", "used", "recovery"]
    
    # Transport distance options (in minutes)
    TRANSPORT_OPTIONS = [5, 15, 30, "any"]


# =============================================================================
# Mock Data Configuration (MVP Phase)
# =============================================================================

class MockDataConfig:
    """Configuration for mock property data."""
    
    # Number of mock properties to generate per city
    PROPERTIES_PER_CITY = 30  # 30 properties x 10 cities = 300 total
    
    # Portuguese cities for mock data
    MOCK_CITIES = [
        "Lisboa", "Porto", "Coimbra", "Braga", "Setúbal",
        "Almada", "Barreiro", "Seixal", "Amadora", "Cascais"
    ]
    
    # Cities by country for universal mock data support (v2.0.2)
    # Top 5-10 cities for major countries, fallback for others
    MOCK_CITIES_BY_COUNTRY = {
        "Portugal": ["Lisboa", "Porto", "Coimbra", "Braga", "Setúbal", "Almada", "Cascais", "Amadora", "Faro", "Aveiro"],
        "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao", "Málaga", "Zaragoza", "Murcia", "Palma", "Las Palmas"],
        "Italy": ["Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa", "Bologna", "Florence", "Venice", "Verona"],
        "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille"],
        "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne", "Stuttgart", "Düsseldorf", "Dortmund", "Essen", "Leipzig"],
        "United Kingdom": ["London", "Manchester", "Birmingham", "Liverpool", "Leeds", "Sheffield", "Bristol", "Edinburgh", "Glasgow", "Cardiff"],
        "United States": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "Miami"],
        "Canada": ["Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg", "Quebec City", "Hamilton", "Victoria"],
        "Brazil": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza", "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Porto Alegre"],
        "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "León", "Juárez", "Zapopan", "Mérida", "Querétaro"],
        "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven", "Groningen", "Tilburg", "Almere", "Breda", "Nijmegen"],
        "Belgium": ["Brussels", "Antwerp", "Ghent", "Charleroi", "Liège", "Bruges", "Namur", "Leuven", "Mons", "Mechelen"],
        "Switzerland": ["Zurich", "Geneva", "Basel", "Lausanne", "Bern", "Winterthur", "Lucerne", "St. Gallen", "Lugano", "Biel"],
        "Austria": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt", "Villach", "Wels", "St. Pölten", "Dornbirn"],
        "Poland": ["Warsaw", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin", "Bydgoszcz", "Lublin", "Katowice"],
        "Sweden": ["Stockholm", "Gothenburg", "Malmö", "Uppsala", "Västerås", "Örebro", "Linköping", "Helsingborg", "Jönköping", "Norrköping"],
        "Norway": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Drammen", "Fredrikstad", "Kristiansand", "Sandnes", "Tromsø", "Sarpsborg"],
        "Denmark": ["Copenhagen", "Aarhus", "Odense", "Aalborg", "Esbjerg", "Randers", "Kolding", "Horsens", "Vejle", "Roskilde"],
        "Finland": ["Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu", "Turku", "Jyväskylä", "Lahti", "Kuopio", "Pori"],
        "Greece": ["Athens", "Thessaloniki", "Patras", "Heraklion", "Larissa", "Volos", "Rhodes", "Ioannina", "Chania", "Chalcis"],
        "Czech Republic": ["Prague", "Brno", "Ostrava", "Plzeň", "Liberec", "Olomouc", "České Budějovice", "Hradec Králové", "Ústí nad Labem", "Pardubice"],
        "Ireland": ["Dublin", "Cork", "Limerick", "Galway", "Waterford", "Drogheda", "Dundalk", "Swords", "Bray", "Navan"],
        "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Newcastle", "Canberra", "Wollongong", "Hobart"],
        "New Zealand": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga", "Napier", "Dunedin", "Palmerston North", "Nelson", "Rotorua"],
        "Japan": ["Tokyo", "Osaka", "Yokohama", "Nagoya", "Sapporo", "Fukuoka", "Kobe", "Kyoto", "Kawasaki", "Saitama"],
        "South Korea": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Suwon", "Ulsan", "Changwon", "Goyang"],
        "Singapore": ["Singapore City", "Jurong", "Woodlands", "Tampines", "Bedok", "Hougang", "Clementi", "Yishun", "Bukit Batok", "Ang Mo Kio"],
    }
    
    # Real Portuguese property agencies
    MOCK_AGENCIES = [
        "REMAX Portugal",
        "ERA Portugal", 
        "Idealista",
        "Imovirtual",
        "Century 21 Portugal",
        "KW Portugal",
        "Zome",
        "Predimed",
        "Casa Sapo",
        "Supercasa",
        "Comprarcasa",
        "OLX Imóveis",
    ]
    
    # Price ranges by typology (EUR) - adjusted for better search results
    PRICE_RANGES = {
        "T0": (50000, 120000),
        "T1": (70000, 180000),
        "T2": (90000, 280000),   # Most T2 under €300k
        "T3": (120000, 380000),  # Most T3 under €400k
        "T4": (180000, 500000),  # Around €500k
        "T4+": (220000, 650000),
    }


# =============================================================================
# Streamlit UI Configuration
# =============================================================================

class UIConfig:
    """Streamlit UI configuration."""
    
    # Page config
    PAGE_TITLE = "GetMyHouse - AI Property Search"
    PAGE_ICON = "🏠"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"
    
    # Theme
    PRIMARY_COLOR = "#1f77b4"
    BACKGROUND_COLOR = "#ffffff"
    SECONDARY_BACKGROUND_COLOR = "#f0f2f6"
    
    # Session state keys
    SESSION_KEY_USER_ID = "user_id"
    SESSION_KEY_SEARCH_HISTORY = "search_history"
    SESSION_KEY_LAST_SEARCH = "last_search"
    SESSION_KEY_RESULTS = "results"


# =============================================================================
# Export Configuration Objects
# =============================================================================

__all__ = [
    "AppConfig",
    "ADKConfig",
    "DatabaseConfig",
    "LoggingConfig",
    "FeatureFlags",
    "AgentConfig",
    "SearchConfig",
    "MockDataConfig",
    "UIConfig",
    "BASE_DIR",
    "DATA_DIR",
    "LOGS_DIR",
]
