import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI无人值守工厂智能告警与自动处置平台"
    APP_VERSION: str = "V1.0"
    APP_ENV: str = "production"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    DATABASE_URL: str = "sqlite:///./data/factory.db"

    # 呼叫提供商：aliyun (真实外呼) / mock (模拟外呼)
    CALL_PROVIDER: str = "mock"

    # 阿里云语音服务 (Dyvmsapi)
    ALIBABA_CLOUD_ACCESS_KEY_ID: str = ""
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: str = ""
    CALL_CALLED_SHOW_NUMBER: str = ""
    TTS_CODE: str = "TTS_2026100301"
    CALL_TIMEOUT_SECONDS: int = 25

    # 演示预设联系人
    DEMO_PRIMARY_CONTACT_NAME: str = "张工"
    DEMO_PRIMARY_CONTACT_PHONE: str = "13800000001"
    DEMO_SECONDARY_CONTACT_NAME: str = "李主管"
    DEMO_SECONDARY_CONTACT_PHONE: str = "13900000002"

    # AI 引擎设置
    AI_PROVIDER: str = "rule_expert"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL_NAME: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
