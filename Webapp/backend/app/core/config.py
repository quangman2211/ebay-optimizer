from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "eBay Listing Optimizer"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./ebay_optimizer.db"
    
    # CORS - Updated to support Chrome Extensions
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8000",
        "chrome-extension://*",  # Allow all Chrome extensions
        "https://*.ngrok.io",  # For ngrok testing
        "https://*.ngrok-free.app",  # New ngrok domain
        "https://*.onrender.com"  # For Render deployment
    ]
    
    # Extension API Keys (comma-separated in production)
    EXTENSION_API_KEYS: str = "dev-api-key-12345"
    
    # Testing
    TEST_MODE: bool = False
    TESTING: bool = False
    
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_PATH: str = "credentials/google-service-account.json"
    SPREADSHEET_ID: Optional[str] = None
    SHEET_NAME: str = "Listings"  # Default sheet for listings
    ORDERS_SHEET_NAME: str = "Orders"  # Sheet for orders data
    SOURCES_SHEET_NAME: str = "Sources"  # Sheet for sources data
    
    # Optimization settings
    MAX_TITLE_LENGTH: int = 80
    MAX_DESCRIPTION_LENGTH: int = 4000
    
    # Fallback mode settings
    USE_FALLBACK_DATA: bool = False
    FALLBACK_DATA_PATH: str = "data/sample_listings.json"
    
    # eBay Categories (can be extended)
    EBAY_CATEGORIES: dict = {
        "electronics": ["brand", "model", "condition", "capacity", "color"],
        "clothing": ["brand", "size", "color", "material", "condition"],
        "collectibles": ["year", "edition", "condition", "authenticity", "rarity"],
        "home": ["brand", "dimensions", "material", "color", "condition"]
    }
    
    # Keywords priority
    HIGH_PRIORITY_KEYWORDS: list = ["new", "sealed", "authentic", "original", "genuine", "oem"]
    MEDIUM_PRIORITY_KEYWORDS: list = ["fast shipping", "free shipping", "warranty", "guaranteed"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()