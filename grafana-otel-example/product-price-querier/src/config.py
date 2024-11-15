from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    service_name: str = "product-info-querier"
    service_instance_id: str = "product-info-querier-1"
    env: str = "dev"


class OTELSettings(BaseSettings):
    otel_exporter_otlp_endpoint: str

class PymysqlSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYSQL_")
    host: str
    port: int
    db: str
    user: str
    password: str

class DelayInjectionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DELAY_INJECTION_")
    enabled: bool
    rate: float
    ms: int