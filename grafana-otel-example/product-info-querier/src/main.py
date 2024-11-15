from contextlib import contextmanager
import random
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from opentelemetry import trace
import redis

from otel_instrumentation import (
    setup_otel,
    setup_fastapi_instrumentation,
    setup_redis_instrumentation,
)
import logging
from config import RedisSettings, FaultInjectionSettings
from pydantic import BaseModel

logger = logging.getLogger(__name__)


async def lifespan(app: FastAPI):
    setup_otel()
    setup_redis_instrumentation()
    yield


app = FastAPI(lifespan=lifespan)
redis_settings = RedisSettings()
fault_injection_settings = FaultInjectionSettings()

class ProductInfo(BaseModel):
    product_id: str
    title: str
    brand: str
    description: str
    stars: float
    reviews_count: int
    bread_crumbs: str
    url: str

tracer = trace.get_tracer(__name__)

@contextmanager
def fault_injection(error_message: str):
    yield
    fault_injected = random.randint(1, 100) <= fault_injection_settings.rate
    if fault_injected and fault_injection_settings.enabled:
        logger.error(f"Fault injected: {error_message}")
        raise Exception(error_message)


def connect_redis():
    with trace.get_tracer(__name__).start_as_current_span("connect_redis"):
        return redis.Redis(
            host=redis_settings.host,
            port=redis_settings.port,
            db=redis_settings.db,
            decode_responses=True,
        )

def get_redis_product_key(product_id: str):
    return f"product:{product_id}"

@app.get("/products/infos")
def list_product_infos():
    with tracer.start_as_current_span("list_product_infos") as span:
        span.set_attribute("product.action", "list_product_infos")

        logger.info("Listing products infos...")
        try:
            with fault_injection("Database connection failed"):
                redis_client = connect_redis()
                all_product_infos: list[ProductInfo] = []
                for key in redis_client.scan_iter("product:*"):
                    all_product_infos.append(ProductInfo(**redis_client.hgetall(get_redis_product_key(key))))
            if all_product_infos:
                logger.info(f"Found {len(all_product_infos)} product infos")
                return JSONResponse(content=[product_info.model_dump() for product_info in all_product_infos], status_code=status.HTTP_200_OK)
            logger.info("No products found")
            return JSONResponse(content={"message": "No products found"}, status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            span.set_status(trace.StatusCode, "ERROR")
            span.record_exception(e)
            return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@app.get("/products/infos/{product_id}")
def get_product_info(product_id: str):
    with tracer.start_as_current_span("get_product_info") as span:
        span.set_attribute("product.action", "get_product_info")
        span.set_attribute("product.count", 1)
        
        try:
            logger.info(f"Getting product info of {product_id}...")

            with fault_injection("Database connection failed"):
                redis_client = connect_redis()
                product_info = ProductInfo(**redis_client.hgetall(get_redis_product_key(product_id)))
            if product_info:
                logger.info(f"Found product info: {product_info}")
                return JSONResponse(content=product_info.model_dump(), status_code=status.HTTP_200_OK)
            logger.info(f"Product {product_id} not found")
            return JSONResponse(content={"message": "Product not found"}, status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            span.set_status(trace.StatusCode, "ERROR")
            span.record_exception(e)
            return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

#! We need to put it here as we can't add middleware after app is created
setup_fastapi_instrumentation(app)