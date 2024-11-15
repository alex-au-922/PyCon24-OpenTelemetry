from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    service_name: str = "api-gateway"
    service_instance_id: str = "api-gateway-1"
    env: str = "dev"


class OTELSettings(BaseSettings):
    otel_exporter_otlp_endpoint: str

class ServiceSettings(BaseSettings):
    product_info_service_url: str
    product_price_service_url: str

class PymysqlSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYSQL_")
    host: str
    port: int
    db: str
    user: str
    password: str