import requests

AUTH_URL = "http://localhost:8001"
ORDER_URL = "http://localhost:8000"

users = [
    {"email": "sachin@example.com", "password": "test123"},
    {"email": "demo@example.com", "password": "demo456"},
    {"email": "newuser@example.com", "password": "newpassword"},
    {"email": "anotheruser@example.com", "password": "anotherpassword"},
    {"email": "yetanotheruser@example.com", "password": "yetanotherpassword"},
]

for user in users:
    print(f"\n🔐 Trying to log in as {user['email']}")

    login_resp = requests.post(f"{AUTH_URL}/signin", json=user)

    if login_resp.status_code == 200:
        print("✅ Login successful")

    elif login_resp.status_code == 401:
        print("❌ Login failed, trying to register...")
        reg_resp = requests.post(f"{AUTH_URL}/register", json=user)
        if reg_resp.status_code == 200:
            print("📝 Registration successful")
        else:
            print("❌ Registration failed:", reg_resp.json())

    # Either way, now place an order
    order_payload = {
        "user_email": user["email"],
        "item_id": "item_test_001",
        "quantity": 1
    }

    order_resp = requests.post(f"{ORDER_URL}/order", json=order_payload)
    if order_resp.status_code == 200:
        print("📦 Order placed:", order_resp.json())
    else:
        print("❌ Order failed:", order_resp.json())
