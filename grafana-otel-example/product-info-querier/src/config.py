from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    service_name: str = "product-info-querier"
    service_instance_id: str = "product-info-querier-1"
    env: str = "dev"


class OTELSettings(BaseSettings):
    otel_exporter_otlp_endpoint: str

class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    host: str
    port: int
    db: int

class FaultInjectionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FAULT_INJECTION_")
    enabled: bool
    rate: float