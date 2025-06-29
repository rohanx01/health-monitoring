import asyncio
import aiohttp
import random
import time
import os
import platform
import logging
import json
from datetime import datetime
from typing import Dict, List

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Only log the message (which will be JSON)
    handlers=[logging.FileHandler("logs/metrics.log"), logging.StreamHandler()]
)

def log_json(level, message, **kwargs):
    log_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "service": "controller",
        "message": message,
    }
    log_data.update(kwargs)
    logging.info(json.dumps(log_data))

# Service URLs (adjust based on Docker setup)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:8000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog_service:8000")

# Sample users
USERS = [
    {"email": f"user{i}@example.com", "password": "password123"} for i in range(1, 11)
]

# Cached product list to avoid hardcoding
PRODUCTS: List[Dict] = []

async def wait_for_service(session: aiohttp.ClientSession, service_url: str, service_name: str, max_retries: int = 30):
    for attempt in range(max_retries):
        try:
            async with session.get(f"{service_url}/ping", timeout=5) as resp:
                if resp.status == 200:
                    log_json("INFO", f"{service_name} is ready")
                    return True
        except Exception as e:
            log_json("INFO", f"Waiting for {service_name}... (attempt {attempt + 1}/{max_retries})", error=str(e))
            await asyncio.sleep(2)
    log_json("ERROR", f"{service_name} failed to start after {max_retries} attempts")
    return False

async def wait_for_all_services():
    async with aiohttp.ClientSession() as session:
        services = [
            (AUTH_SERVICE_URL, "Auth Service"),
            (ORDER_SERVICE_URL, "Order Service"), 
            (CATALOG_SERVICE_URL, "Catalog Service")
        ]
        results = await asyncio.gather(*[
            wait_for_service(session, url, name) for url, name in services
        ], return_exceptions=True)
        if not all(results):
            log_json("ERROR", "Some services failed to start. Exiting.")
            return False
        log_json("INFO", "All services are ready! Starting traffic generation...")
        return True

async def fetch_products(session: aiohttp.ClientSession, token: str):
    global PRODUCTS
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(3):
        try:
            async with session.get(f"{CATALOG_SERVICE_URL}/api/v1/all_products", headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    PRODUCTS = await resp.json()
                    log_json("INFO", f"Fetched {len(PRODUCTS)} products from catalog.")
                    return
                else:
                    log_json("ERROR", f"Failed to fetch products: {resp.status} {await resp.text()}")
        except Exception as e:
            if attempt == 2:
                log_json("ERROR", f"Exception during fetch_products after 3 attempts", error=str(e))
                return
            await asyncio.sleep(1)

async def register_user(session: aiohttp.ClientSession, user: Dict) -> str:
    payload = {"email": user["email"], "password": user["password"]}
    for attempt in range(3):
        try:
            async with session.post(f"{AUTH_SERVICE_URL}/register", json=payload, timeout=10) as resp:
                if resp.status in [200, 201]:
                    log_json("INFO", f"Registered user {user['email']}")
                    return await signin_user(session, user)
                return await signin_user(session, user)
        except Exception as e:
            if attempt == 2:
                log_json("ERROR", f"Failed to register user {user['email']} after 3 attempts", error=str(e))
                return None
            await asyncio.sleep(1)

async def signin_user(session: aiohttp.ClientSession, user: Dict) -> str:
    payload = {"email": user["email"], "password": user["password"]}
    for attempt in range(3):
        try:
            async with session.post(f"{AUTH_SERVICE_URL}/signin", json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get("access_token")
                    log_json("INFO", f"Login successful for {user['email']}")
                    return token
                log_json("WARNING", f"Login failed for {user['email']}: {resp.status}")
                return None
        except Exception as e:
            if attempt == 2:
                log_json("ERROR", f"Failed to signin user {user['email']} after 3 attempts", error=str(e))
                return None
            await asyncio.sleep(1)

async def place_order(session: aiohttp.ClientSession, token: str, product: Dict):
    headers = {"Authorization": f"Bearer {token}"}
    product_id = product.get("_id")
    payload = {"item_id": product_id, "quantity": random.randint(1, 3)}
    log_json("INFO", f"Placing order for product: {product}")
    for attempt in range(3):
        try:
            async with session.post(f"{ORDER_SERVICE_URL}/api/v1/order", json=payload, headers=headers, timeout=10) as resp:
                log_json("INFO", f"Order status: {resp.status} | {await resp.text()}")
                return
        except Exception as e:
            if attempt == 2:
                log_json("ERROR", f"Exception during place_order after 3 attempts", error=str(e))
                return
            await asyncio.sleep(1)

async def view_orders(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(3):
        try:
            async with session.get(f"{ORDER_SERVICE_URL}/api/v1/orders", headers=headers, timeout=10) as resp:
                log_json("INFO", f"View orders status: {resp.status}")
                return
        except Exception as e:
            if attempt == 2:
                log_json("ERROR", f"Exception during view_orders after 3 attempts", error=str(e))
                return
            await asyncio.sleep(1)

async def view_product(session: aiohttp.ClientSession, token: str, product_name: str):
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(3):
        try:
            async with session.get(f"{CATALOG_SERVICE_URL}/api/v1/product", params={"name": product_name}, headers=headers, timeout=10) as resp:
                log_json("INFO", f"View product '{product_name}' status: {resp.status}")
                return
        except Exception as e:
            if attempt == 2:
                log_json("ERROR", f"Exception during view_product after 3 attempts", error=str(e))
                return
            await asyncio.sleep(1)

async def simulate_user_interaction(session: aiohttp.ClientSession, user: Dict):
    token = await register_user(session, user) if random.choice([True, False]) else await signin_user(session, user)
    if not token:
        return
    if not PRODUCTS:
        await fetch_products(session, token)
        if not PRODUCTS:
            log_json("ERROR", "No products available for testing.")
            return
    # Add controlled error generation (15% chance of errors for testing)
    if random.random() < 0.15:
        await generate_test_errors(session, token)
        return
    actions = [
        lambda: place_order(session, token, random.choice(PRODUCTS)),
        lambda: view_orders(session, token),
        lambda: view_product(session, token, random.choice(PRODUCTS)["name"])
    ]
    for _ in range(random.randint(1, 3)):
        await random.choice(actions)()

async def generate_test_errors(session: aiohttp.ClientSession, token: str):
    error_types = [
        lambda: test_invalid_auth(session),
        lambda: test_invalid_product(session, token),
        lambda: test_invalid_order(session, token),
        lambda: test_server_error_simulation(session, token),
        lambda: test_forced_500(session, token),
        lambda: test_network_timeout(session, token),
        lambda: test_invalid_payload(session, token),
    ]
    await random.choice(error_types)()

async def test_invalid_auth(session: aiohttp.ClientSession):
    headers = {"Authorization": "Bearer invalid_token"}
    try:
        async with session.get(f"{CATALOG_SERVICE_URL}/api/v1/all_products", headers=headers, timeout=5) as resp:
            log_json("INFO", f"Auth test - Expected 401, got: {resp.status}")
    except Exception as e:
        log_json("ERROR", f"Auth test error", error=str(e))

async def test_invalid_product(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get(f"{CATALOG_SERVICE_URL}/api/v1/product", params={"name": "nonexistent_product"}, headers=headers, timeout=5) as resp:
            log_json("INFO", f"Invalid product test - Expected 404, got: {resp.status}")
    except Exception as e:
        log_json("ERROR", f"Invalid product test error", error=str(e))

async def test_invalid_order(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"item_id": "invalid_id", "quantity": -1}
    try:
        async with session.post(f"{ORDER_SERVICE_URL}/api/v1/order", json=payload, headers=headers, timeout=5) as resp:
            log_json("INFO", f"Invalid order test - Got: {resp.status}")
    except Exception as e:
        log_json("ERROR", f"Invalid order test error", error=str(e))

async def test_server_error_simulation(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get(f"{AUTH_SERVICE_URL}/nonexistent", headers=headers, timeout=5) as resp:
            log_json("INFO", f"Server error simulation - Got: {resp.status}")
    except Exception as e:
        log_json("ERROR", f"Server error simulation", error=str(e))

async def test_forced_500(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # Intentionally call a non-existent endpoint to trigger 500
        async with session.post(f"{ORDER_SERVICE_URL}/api/v1/force_error", headers=headers, timeout=5) as resp:
            log_json("INFO", f"Forced 500 test - Got: {resp.status}")
    except Exception as e:
        log_json("ERROR", f"Forced 500 test error", error=str(e))

async def test_network_timeout(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # Use a very short timeout to simulate network timeout
        async with session.get(f"{CATALOG_SERVICE_URL}/api/v1/all_products", headers=headers, timeout=0.001) as resp:
            log_json("INFO", f"Network timeout test - Got: {resp.status}")
    except Exception as e:
        log_json("ERROR", f"Network timeout test error", error=str(e))

async def test_invalid_payload(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"item_id": None, "quantity": "not_a_number"}
    try:
        async with session.post(f"{ORDER_SERVICE_URL}/api/v1/order", json=payload, headers=headers, timeout=5) as resp:
            log_json("INFO", f"Invalid payload test - Got: {resp.status}")
    except Exception as e:
        log_json("ERROR", f"Invalid payload test error", error=str(e))

async def main():
    if not await wait_for_all_services():
        log_json("ERROR", "Failed to start - services not ready")
        return
    request_rate = 10  # initial RPM
    increase_interval = 300
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [simulate_user_interaction(session, random.choice(USERS)) for _ in range(request_rate)]
            await asyncio.gather(*tasks)
            if time.time() - start_time > increase_interval:
                request_rate = int(request_rate * 1.2)
                start_time = time.time()
            await asyncio.sleep(60 / request_rate)

if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())
