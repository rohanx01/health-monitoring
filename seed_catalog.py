import requests

AUTH_URL = "http://localhost:8001"
CATALOG_URL = "http://localhost:8005"

# Use a new unique admin user for seeding
ADMIN_USER = {"email": "catalog_admin@example.com", "password": "admin123"}
PRODUCTS = [
    {"name": "Blood Pressure Monitor", "description": "Automatic digital BP monitor.", "stock": 50},
    {"name": "Thermometer", "description": "Infrared forehead thermometer.", "stock": 100},
    {"name": "Pulse Oximeter", "description": "Measures blood oxygen saturation.", "stock": 75},
    {"name": "Glucometer", "description": "Blood glucose monitoring device.", "stock": 60},
    {"name": "Weighing Scale", "description": "Digital body weight scale.", "stock": 80},
]

def get_token():
    # Register admin if not exists
    requests.post(f"{AUTH_URL}/register", json=ADMIN_USER)
    # Login
    resp = requests.post(f"{AUTH_URL}/signin", json=ADMIN_USER)
    if resp.status_code == 200:
        return resp.json()["access_token"]
    else:
        raise Exception(f"Failed to get token: {resp.text}")

def add_product(token, product):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{CATALOG_URL}/add_product", json=product, headers=headers)
    if resp.status_code == 200 or resp.status_code == 201:
        print(f"Added: {product['name']}")
    else:
        print(f"Failed to add {product['name']}: {resp.status_code} {resp.text}")

def main():
    token = get_token()
    for product in PRODUCTS:
        add_product(token, product)

if __name__ == "__main__":
    main()
