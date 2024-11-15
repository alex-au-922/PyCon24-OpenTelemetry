import os

class DynamoDBConfig:
    TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'product_info')

class DelayInjectionConfig:
    ENABLED = os.getenv('DELAY_INJECTION_ENABLED', 'false').lower() == 'true'
    DELAY_MS = int(os.getenv('DELAY_INJECTION_DELAY_MS', '1000'))
    DELAY_PERCENTAGE = int(os.getenv('DELAY_INJECTION_DELAY_PERCENTAGE', '100'))

class FaultInjectionConfig:
    ENABLED = os.getenv('FAULT_INJECTION_ENABLED', 'false').lower() == 'true'
    FAULT_PERCENTAGE = int(os.getenv('FAULT_INJECTION_FAULT_PERCENTAGE', '100'))

class ProjectConfig:
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'product-info-querier')
    