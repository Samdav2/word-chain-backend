import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing Health...", end=" ")
    try:
        r = requests.get(f"{BASE_URL}/health")
        if r.status_code == 200:
            print("✅ OK")
            return True
        else:
            print(f"❌ Failed: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_signup():
    print("Testing Signup...", end=" ")
    payload = {
        "email": f"test_{int(time.time())}@example.com",
        "password": "password123",
        "matric_no": f"MAT{int(time.time())}"
    }
    try:
        r = requests.post(f"{BASE_URL}/auth/signup", json=payload)
        if r.status_code == 201:
            print("✅ OK")
            return payload
        else:
            print(f"❌ Failed: {r.status_code} {r.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_login(user_data):
    print("Testing Login...", end=" ")
    if not user_data:
        print("⏭️ Skipped (no user)")
        return None

    payload = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    try:
        r = requests.post(f"{BASE_URL}/auth/login", data=payload)
        if r.status_code == 200:
            print("✅ OK")
            return r.json()["access_token"]
        else:
            print(f"❌ Failed: {r.status_code} {r.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_categories():
    print("Testing Categories...", end=" ")
    try:
        r = requests.get(f"{BASE_URL}/game/categories")
        if r.status_code == 200:
            data = r.json()
            if len(data["categories"]) > 0:
                print(f"✅ OK ({len(data['categories'])} categories)")
                return True
            else:
                print("❌ Failed: No categories returned")
                return False
        else:
            print(f"❌ Failed: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_start_game(token):
    print("Testing Start Game (Science)...", end=" ")
    if not token:
        print("⏭️ Skipped (no token)")
        return

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "mode": "standard",
        "category": "science",
        "difficulty": 3
    }
    try:
        r = requests.post(f"{BASE_URL}/game/start", json=payload, headers=headers)
        if r.status_code == 201:
            data = r.json()
            print(f"✅ OK ({data['start_word']} -> {data['target_word']})")
            return data
        else:
            print(f"❌ Failed: {r.status_code} {r.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # Wait for server to be ready
    for i in range(5):
        if test_health():
            break
        time.sleep(2)

    user = test_signup()
    token = test_login(user)
    test_categories()
    test_start_game(token)
