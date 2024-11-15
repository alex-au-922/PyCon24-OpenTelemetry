from contextlib import contextmanager
import random
import time
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from opentelemetry import trace

from otel_instrumentation import (
    setup_otel,
    setup_fastapi_instrumentation,
    setup_pymysql_instrumentation
)
import logging
from config import DelayInjectionSettings, PymysqlSettings
import pymysql
from pymysql.cursors import DictCursor
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


async def lifespan(app: FastAPI):
    setup_otel()
    setup_pymysql_instrumentation()
    yield


app = FastAPI(lifespan=lifespan)
pymysql_settings = PymysqlSettings()
delay_injection_settings = DelayInjectionSettings()

class ProductPrice(BaseModel):
    product_id: str
    currency: str
    value: float

    @field_validator("value")
    def convert_non_compatible_to_zero(cls, value):
        return value if isinstance(value, (int, float)) else 0.0

tracer = trace.get_tracer(__name__)

@contextmanager
def delay_injection():
    yield
    delay_injected = random.randint(1, 100) <= delay_injection_settings.rate
    if delay_injected and delay_injection_settings.enabled:
        logger.info(f"Delay injected, sleeping for {delay_injection_settings.ms}ms")
        time.sleep(delay_injection_settings.ms / 1000)


@app.get("/products/prices/{product_id}")
def get_product_price(product_id: str):
    with tracer.start_as_current_span("get_product_price") as span:
        span.set_attribute("product.action", "get_product_price")
        span.set_attribute("product.count", 1)
        
        try:
            logger.info(f"Getting product price of {product_id}...")

            with (
                delay_injection(),
                pymysql.connect(
                    host=pymysql_settings.host,
                    port=pymysql_settings.port,
                    database=pymysql_settings.db,
                    user=pymysql_settings.user,
                    password=pymysql_settings.password,
                ) as conn,
                conn.cursor(cursor=DictCursor) as cur,
            ):
                cur.execute("SELECT * FROM product_price WHERE product_id = %s", (product_id,))
                price = cur.fetchone()
            if price:
                logger.info(f"Found product price of {product_id}")
                return JSONResponse(content=ProductPrice(**price).model_dump(), status_code=status.HTTP_200_OK)
            logger.info(f"Product price of {product_id} not found")
            return JSONResponse(content={"message": "Product not found"}, status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            span.set_status(trace.StatusCode, "ERROR")
            span.record_exception(e)
            return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/products/prices")
def list_product_infos():
    with tracer.start_as_current_span("list_product_prices") as span:
        span.set_attribute("product.action", "list_product_prices")

        logger.info("Listing products infos...")
        try:
            with (
                delay_injection(),
                pymysql.connect(
                    host=pymysql_settings.host,
                    port=pymysql_settings.port,
                    database=pymysql_settings.db,
                    user=pymysql_settings.user,
                    password=pymysql_settings.password,
                ) as conn,
                conn.cursor(cursor=DictCursor) as cur,
            ):
                cur.execute("SELECT * FROM product_price")
                prices = cur.fetchall()
            if prices:
                logger.info(f"Found {len(prices)} product prices")
                return JSONResponse(content=[ProductPrice(**price).model_dump() for price in prices], status_code=status.HTTP_200_OK)
            logger.info("No products found")
            return JSONResponse(content={"message": "No products found"}, status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(str(e))
            span.set_status(trace.StatusCode, "ERROR")
            span.record_exception(e)
            return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#! We need to put it here as we can't add middleware after app is created
setup_fastapi_instrumentation(app)