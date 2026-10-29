"""Environment-backed settings. Secrets stay in the environment, never in code."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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
    instagram_app_secret: str = ""
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

    refpay_api_key: str = ""
    chain: str = ""
    chain_rpc_url: str = ""
    usdc_contract_address: str = ""
    seller_wallet_address: str = ""
    min_confirmations: str = ""


def get_settings() -> Settings:
    return Settings()
