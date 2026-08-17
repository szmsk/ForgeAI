from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='FORGEAI_', extra='ignore')
    app_name: str = 'ForgeAI'
    environment: str = 'production'
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    database_url: str = 'postgresql+asyncpg://forgeai:forgeai@postgres:5432/forgeai'
    redis_url: str = 'redis://redis:6379/0'
    jwt_secret: str = 'CHANGE_ME_IN_PRODUCTION'
    jwt_algorithm: str = 'HS256'
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    github_token: str = ''
    github_api_url: str = 'https://api.github.com'
    llm_base_url: str = ''
    llm_api_key: str = ''
    llm_model: str = 'demo'
    max_iterations: int = 8
    default_timeout_seconds: int = 120
    sandbox_image: str = 'forgeai-sandbox:latest'
    sandbox_backend: str = 'docker'
    sandbox_runtime_class: str = 'gvisor'
    sandbox_memory: str = '512m'
    sandbox_cpus: float = 1.0
    sandbox_pids: int = 64
    otel_enabled: bool = True
    otel_endpoint: str = 'http://otel-collector:4317'
    model_cost_input_per_1m: float = 0.0
    model_cost_output_per_1m: float = 0.0
    cors_origins: str = 'http://localhost:3000'
    allowed_hosts: str = 'localhost,127.0.0.1'
    rate_limit_per_minute: int = 60
    run_concurrency_per_tenant: int = 2
    artifact_bucket: str = 'forgeai-artifacts'
    s3_endpoint: str = ''
    s3_region: str = 'us-east-1'
    s3_access_key: str = ''
    s3_secret_key: str = ''
    cookie_secure: bool = True

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(',') if x.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [x.strip() for x in self.allowed_hosts.split(',') if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
