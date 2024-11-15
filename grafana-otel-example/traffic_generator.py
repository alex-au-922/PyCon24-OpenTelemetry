import requests
import random
from threading import Thread

base_url = "http://localhost:8080"

def main():
    while True:
        all_product_ids = requests.get(
            f"{base_url}/products/ids"
        )

        random_product_ids = all_product_ids.json()
        shuffled_product_ids = random.sample(random_product_ids, len(random_product_ids))
        sampled_product_ids = shuffled_product_ids[:random.randint(1, len(random_product_ids))]

        for product_id in sampled_product_ids:
            resp = requests.get(
                f"{base_url}/products/{product_id}"
            )

            if resp.status_code == 200:
                print(resp.json())
            else:
                print(resp.text)

if __name__ == "__main__":
    threads: list[Thread] = [
        Thread(target=main)
        for _ in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
