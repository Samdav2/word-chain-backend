import requests
import time
import sys
import uuid

BASE_URL = "http://localhost:8000"

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

def test_start_game(token):
    print("Testing Start Game...", end=" ")
    if not token:
        print("⏭️ Skipped (no token)")
        return None

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
            print(f"✅ OK (Session: {data['session_id']})")
            return data['session_id']
        else:
            print(f"❌ Failed: {r.status_code} {r.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_complete_game(token, session_id, forfeit=True):
    print(f"Testing Complete Game (Forfeit={forfeit})...", end=" ")
    if not token or not session_id:
        print("⏭️ Skipped (no token/session)")
        return

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "session_id": session_id,
        "forfeit": forfeit
    }
    try:
        r = requests.post(f"{BASE_URL}/game/complete", json=payload, headers=headers)
        if r.status_code == 200:
            print("✅ OK")
            print(r.json())
        else:
            print(f"❌ Failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_complete_game_invalid_uuid(token):
    print("Testing Complete Game (Invalid UUID)...", end=" ")
    if not token:
        print("⏭️ Skipped (no token)")
        return

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "session_id": "invalid-uuid",
        "forfeit": True
    }
    try:
        r = requests.post(f"{BASE_URL}/game/complete", json=payload, headers=headers)
        if r.status_code == 422:
            print("✅ OK (Expected 422)")
        else:
            print(f"❌ Failed: Expected 422, got {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_complete_game_random_uuid(token):
    print("Testing Complete Game (Random UUID)...", end=" ")
    if not token:
        print("⏭️ Skipped (no token)")
        return

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "session_id": str(uuid.uuid4()),
        "forfeit": True
    }
    try:
        r = requests.post(f"{BASE_URL}/game/complete", json=payload, headers=headers)
        if r.status_code == 400:
            print(f"✅ OK (Expected 400: {r.text})")
        else:
            print(f"❌ Failed: Expected 400, got {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    user = test_signup()
    token = test_login(user)
    session_id = test_start_game(token)

    # 1. Test valid completion (forfeit)
    test_complete_game(token, session_id, forfeit=True)

    # 2. Test completing already completed game
    print("Retrying completion on completed game...")
    test_complete_game(token, session_id, forfeit=True)

    # 3. Test invalid UUID
    test_complete_game_invalid_uuid(token)

    # 4. Test random UUID
    test_complete_game_random_uuid(token)
