from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://snaplist:password@localhost:5432/snaplist"

    groq_api_key: str = ""  # Groq — free tier at console.groq.com, no credit card
    anthropic_api_key: str = ""  # Claude Vision fallback for product identification
    serpapi_key: str = ""  # Google Lens reverse image search (serpapi.com — 100 free/mo)

    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_oauth_token: str = ""
    ebay_sandbox: bool = True

    etsy_api_key: str = ""
    etsy_api_secret: str = ""
    etsy_access_token: str = ""

    sendgrid_api_key: str = ""
    notification_email: str = ""
    from_email: str = "noreply@snaplist.app"

    pushover_app_token: str = ""
    pushover_user_key: str = ""

    secret_key: str = "change-me"
    environment: str = "development"
    upload_dir: str = "uploads"

    # Region settings — drives marketplace IDs, currency, platform URLs
    country: str = "CA"          # CA, US, UK, AU ...
    currency: str = "CAD"        # CAD, USD, GBP, AUD ...
    ebay_marketplace_id: str = "EBAY_CA"  # EBAY_CA, EBAY_US, EBAY_GB ...
    city: str = "Surrey"
    region: str = "BC"


settings = Settings()
