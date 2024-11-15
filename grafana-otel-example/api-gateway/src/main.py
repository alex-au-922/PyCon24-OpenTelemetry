import asyncio
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import httpx
from opentelemetry import trace

from otel_instrumentation import (
    setup_otel,
    setup_fastapi_instrumentation,
    setup_httpx_instrumentation,
    setup_pymysql_instrumentation
)
import logging
from config import ServiceSettings, PymysqlSettings
from pydantic import BaseModel
import pymysql
from pymysql.cursors import DictCursor


logger = logging.getLogger(__name__)


async def lifespan(app: FastAPI):
    setup_otel()
    setup_httpx_instrumentation()
    setup_pymysql_instrumentation()
    yield


app = FastAPI(lifespan=lifespan)
service_settings = ServiceSettings()
pymysql_settings = PymysqlSettings()


class Price(BaseModel):
    currency: str
    value: float

class Product(BaseModel):
    product_id: str
    title: str
    brand: str
    description: str
    stars: float
    reviews_count: int
    price: Price
    url: str

tracer = trace.get_tracer(__name__)

@app.get("/products/ids")
async def list_product_ids():
    with tracer.start_as_current_span("list_product_ids") as span:
        span.set_attribute("product.action", "list_product_ids")

        try:
            logger.info("Listing product ids...")

            with (
                pymysql.connect(
                    host=pymysql_settings.host,
                    port=pymysql_settings.port,
                    database=pymysql_settings.db,
                    user=pymysql_settings.user,
                    password=pymysql_settings.password,
                ) as conn,
                conn.cursor(cursor=DictCursor) as cur,
            ):
                cur.execute("SELECT product_id FROM product_price")
                product_ids = cur.fetchall()

            return JSONResponse(status_code=status.HTTP_200_OK, content=[product_id['product_id'] for product_id in product_ids])
        except httpx.HTTPStatusError as e:
            logger.exception(str(e))
            span.set_status(trace.StatusCode, "ERROR")
            span.record_exception(e)

            return JSONResponse(status_code=e.response.status_code, content=e.response.json())

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    with tracer.start_as_current_span("get_single_product") as span:
        span.set_attribute("product.action", "get_product")
        span.set_attribute("product.count", 1)
        
        try:
            logger.info(f"Getting product {product_id}...")

            async with httpx.AsyncClient() as client:
                info_resp: httpx.Response
                price_resp: httpx.Response


                [info_resp, price_resp] = await asyncio.gather(*[
                    client.get(f"{service_settings.product_info_service_url}/products/infos/{product_id}"),
                    client.get(f"{service_settings.product_price_service_url}/products/prices/{product_id}"),
                ])
                info_resp.raise_for_status()
                price_resp.raise_for_status()

                info_json = info_resp.json()
                price_json = price_resp.json()

                price = Price(**price_json)
                product = Product(**{
                    **info_json,
                    "price": price,
                })

            return JSONResponse(status_code=status.HTTP_200_OK, content=product.model_dump())
        except httpx.HTTPStatusError as e:
            logger.exception(str(e))
            span.set_status(trace.StatusCode, "ERROR")
            span.record_exception(e)
            return JSONResponse(status_code=e.response.status_code, content=e.response.json())



@app.get("/products")
async def list_products():
    with tracer.start_as_current_span("list_products") as span:
        span.set_attribute("product.action", "list_products")

        try:
            async with httpx.AsyncClient() as client:
                logger.info("Listing products...")
                info_resp: httpx.Response
                price_resp: httpx.Response

                [info_resp, price_resp] = await asyncio.gather(*[
                    client.get(f"{service_settings.product_info_service_url}/products/infos"),
                    client.get(f"{service_settings.product_price_service_url}/products/prices"),
                ])
                info_resp.raise_for_status()
                price_resp.raise_for_status()

                info_json = info_resp.json()
                price_json = price_resp.json()

                if len(info_json) != len(price_json):
                    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Mismatch in product info and price data"})
                
                info_json_map = {product_info['product_id']: product_info for product_info in info_json}
                price_json_map = {product_info['product_id']: product_info for product_info in price_json}

                products: list[Product] = []
                for product_id in info_json_map.keys():
                    price = Price(**price_json_map[product_id])
                    product = Product(**{
                        **info_json_map[product_id],
                        "price": price,
                    })
                    products.append(product)

                return JSONResponse(status_code=status.HTTP_200_OK, content=[product.model_dump() for product in products])
        except httpx.HTTPStatusError as e:
            logger.exception(str(e))
            span.set_status(trace.StatusCode, "ERROR")
            span.record_exception(e)

            return JSONResponse(status_code=e.response.status_code, content=e.response.json())
        
#! We need to put it here as we can't add middleware after app is created
setup_fastapi_instrumentation(app)