"""Environment-backed settings. Secrets stay in the environment, never in code."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py → parents[1]=backend, parents[2]=repo root
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = Path(__file__).resolve().parents[2]
# Prefer backend/.env when present; also load repo-root .env (common local layout).
_ENV_FILES = (
    _BACKEND_DIR / ".env",
    _REPO_ROOT / ".env",
    Path(".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    app_base_url: str = ""
    internal_api_token: str = ""
    pii_salt: str = ""

    llm_provider: str = ""
    groq_api_key: str = ""
    groq_text_model: str = ""
    groq_vision_model: str = ""
    groq_transcribe_model: str = ""
    meta_api_key: str = ""
    meta_api_base_url: str = ""
    meta_text_model: str = ""
    meta_vision_model: str = ""

    typesafe_api_key: str = ""
    typesafe_api_base_url: str = "https://api.typesafe.ai"

    intron_api_key: str = ""
    intron_stt_url: str = ""

    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    instagram_account_id: str = ""
    instagram_access_token: str = ""
    # Instagram product App ID (Instagram → API setup with Instagram login).
    # Not META_APP_ID — using the Facebook app id causes "Invalid platform app".
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    # Instagram Login OAuth (seller Connect). redirect_uri must match Meta app settings.
    instagram_oauth_redirect_uri: str = ""
    instagram_oauth_scopes: str = "instagram_business_basic,instagram_business_manage_messages"
    web_base_url: str = ""
    fb_page_id: str = ""
    fb_page_access_token: str = ""
    graph_api_version: str = ""

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    supabase_storage_bucket: str = ""

    paystack_secret_key: str = ""
    flutterwave_secret_key: str = ""
    flutterwave_webhook_hash: str = ""
    mono_secret_key: str = ""
    alert_inbound_secret: str = ""

    crypto_network: str = "base-sepolia"
    crypto_rpc_url: str = ""
    crypto_chain_id: int = 84532
    crypto_token_contract: str = ""
    crypto_min_confirmations: int = 3
    crypto_explorer_url: str = "https://sepolia.basescan.org"
    demo_real_tx_hash: str = ""


def get_settings() -> Settings:
    return Settings()
