import asyncio
import aiohttp
import random
import time
import os
import platform
from typing import Dict, List

# Service URLs (adjust based on Docker setup)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8001")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8002")

# Sample data
USERS = [
    {"email": f"user{i}@example.com", "password": "password123"} for i in range(1, 11)
]
PRODUCT_IDS = [str(i) for i in range(1, 6)]  # Assume 5 products exist in catalog

async def register_user(session: aiohttp.ClientSession, user: Dict) -> str:
    """Register a user and return access token."""
    payload = {"email": user["email"], "password": user["password"]}
    async with session.post(f"{AUTH_SERVICE_URL}/register", json=payload) as resp:
        if resp.status == 200:
            return await signin_user(session, user)  # Sign in after registering
        return None

async def signin_user(session: aiohttp.ClientSession, user: Dict) -> str:
    """Sign in a user and return access token."""
    payload = {"email": user["email"], "password": user["password"]}
    async with session.post(f"{AUTH_SERVICE_URL}/signin", json=payload) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data["access_token"]
        return None

async def place_order(session: aiohttp.ClientSession, token: str, product_id: str, quantity: int):
    """Place an order for a random product."""
    payload = {"item_id": product_id, "quantity": quantity}
    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(f"{ORDER_SERVICE_URL}/order", json=payload, headers=headers):
        pass

async def view_orders(session: aiohttp.ClientSession, token: str):
    """View orders for a user."""
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{ORDER_SERVICE_URL}/orders", headers=headers):
        pass

async def view_product(session: aiohttp.ClientSession, token: str, product_name: str):
    """View a product by name."""
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{CATALOG_SERVICE_URL}/product", params={"name": product_name}, headers=headers):
        pass

async def simulate_user_interaction(session: aiohttp.ClientSession, user: Dict):
    """Simulate a single user's interaction with the services."""
    # Register or sign in user
    token = await register_user(session, user) if random.choice([True, False]) else await signin_user(session, user)
    if not token:
        return

    # Randomly select actions
    actions = [
        lambda: place_order(session, token, random.choice(PRODUCT_IDS), random.randint(1, 3)),
        lambda: view_orders(session, token),
        lambda: view_product(session, token, f"product{random.randint(1, 5)}")
    ]
    # Execute 1-3 random actions per user
    for _ in range(random.randint(1, 3)):
        await random.choice(actions)()

async def main():
    """Main function to simulate user interactions with increasing load."""
    request_rate = 10  # Initial requests per minute
    increase_interval = 300  # 5 minutes in seconds
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []
            for _ in range(request_rate):
                user = random.choice(USERS)
                tasks.append(simulate_user_interaction(session, user))

            await asyncio.gather(*tasks)

            # Increase request rate by 20% every 5 minutes
            if time.time() - start_time > increase_interval:
                request_rate = int(request_rate * 1.2)
                start_time = time.time()

            # Wait before next batch
            await asyncio.sleep(60 / request_rate)

if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())