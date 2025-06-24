import requests
import time
import random
import threading
import logging

# Basic logging setup for the controller itself
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(message)s')

# --- Configuration ---
# Define the base URLs for our running services.
# Make sure these ports match what you defined in Step 1.
# AUTH_SERVICE_URL = "http://localhost:8000"
# ORDER_SERVICE_URL = "http://localhost:8001"
# PRODUCT_SERVICE_URL = "http://localhost:8002"
AUTH_SERVICE_URL = "http://auth-service:8000"
ORDER_SERVICE_URL = "http://order-service:8001"
PRODUCT_SERVICE_URL = "http://product-service:8002"
# --- User Scenarios ---
# We define different functions to simulate different user behaviors.

def scenario_happy_shopper():
    """Simulates a user who logs in, checks a product, and places an order."""
    thread_name = threading.current_thread().name
    logging.info("Starting 'Happy Shopper' scenario...")
    
    try:
        # 1. Login
        requests.post(f"{AUTH_SERVICE_URL}/login")
        time.sleep(random.uniform(0.1, 0.5))

        # 2. Check a product
        product_id = random.randint(100, 200)
        requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
        time.sleep(random.uniform(0.1, 0.5))

        # 3. Place an order
        requests.post(f"{ORDER_SERVICE_URL}/place-order")
        logging.info("'Happy Shopper' scenario completed.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed in '{thread_name}': {e}")


def scenario_window_shopper():
    """Simulates a user who just browses products and checks inventory."""
    thread_name = threading.current_thread().name
    logging.info("Starting 'Window Shopper' scenario...")

    try:
        # Browse 2-5 products
        for _ in range(random.randint(2, 5)):
            product_id = random.randint(201, 300)
            requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
            time.sleep(random.uniform(0.2, 0.6))
        
        # Check inventory (this endpoint is designed to fail sometimes)
        requests.get(f"{PRODUCT_SERVICE_URL}/products/inventory-check")
        logging.info("'Window Shopper' scenario completed.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed in '{thread_name}': {e}")


def scenario_order_checker():
    """Simulates a user who repeatedly checks their order status."""
    thread_name = threading.current_thread().name
    logging.info("Starting 'Order Checker' scenario...")

    try:
        # Check order status 3-6 times
        for _ in range(random.randint(3, 6)):
            order_id = f"ORD-{random.randint(1000, 9999)}"
            requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
            time.sleep(random.uniform(0.3, 0.7))
        logging.info("'Order Checker' scenario completed.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed in '{thread_name}': {e}")

# --- Main Traffic Loop ---
def main():
    """The main function to run the traffic simulation."""
    scenarios = [scenario_happy_shopper, scenario_window_shopper, scenario_order_checker]
    
    print("Starting traffic simulation... Press Ctrl+C to stop.")
    
    while True:
        # Choose a random scenario to run
        selected_scenario = random.choice(scenarios)
        
        # We use threading to run multiple scenarios at once, simulating multiple users.
        thread = threading.Thread(target=selected_scenario, name=f"{selected_scenario.__name__}-Thread")
        thread.start()
        
        # Wait for a random interval before starting the next user session
        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    main()