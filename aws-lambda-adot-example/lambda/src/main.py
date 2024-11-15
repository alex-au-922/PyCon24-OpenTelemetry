from aws_lambda_powertools import Logger
import boto3
from config import ProjectConfig, DynamoDBConfig, FaultInjectionConfig, DelayInjectionConfig
import random
import time
from contextlib import contextmanager

logger = Logger(
    service = ProjectConfig.SERVICE_NAME,
)

@contextmanager
def fault_injection(error_message: str):
    yield
    fault_injected = random.randint(1, 100) <= FaultInjectionConfig.FAULT_PERCENTAGE
    if fault_injected and FaultInjectionConfig.ENABLED:
        logger.error(f"Fault injected: {error_message}")
        raise Exception(error_message)

@contextmanager
def delay_injection():
    yield
    delay_injected = random.randint(1, 100) <= DelayInjectionConfig.DELAY_PERCENTAGE
    if delay_injected and DelayInjectionConfig.ENABLED:
        logger.info(f"Delay injected: {DelayInjectionConfig.DELAY_MS}ms")
        time.sleep(DelayInjectionConfig.DELAY_MS / 1000)


def get_product_infos(product_ids: list[str]):
    dynamodb = boto3.client("dynamodb")
    with (
        fault_injection("Failed to get product info from DynamoDB"),
        delay_injection()
    ):
        keys = [{"product_id": {"S": product_id}} for product_id in product_ids]
        response = dynamodb.batch_get_item(
            RequestItems={
                DynamoDBConfig.TABLE_NAME: {
                    "Keys": keys
                }
            }
        )
        return response["Responses"][DynamoDBConfig.TABLE_NAME]

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    product_ids = event["product_ids"]
    product_infos = get_product_infos(product_ids)
    return product_infos