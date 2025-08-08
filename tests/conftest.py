# tests/conftest.py

from utils.settings import BASE_URL, AUTH_LOGIN, USERS, AUTH_SIGN_UP
from dotenv import load_dotenv
import os
import pytest
import faker
import time
import logging
from utils.api_helpers import api_request

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa_tests")

RETRIES = 7
DELAY = 2

fake = faker.Faker()

@pytest.fixture(scope="session")
def admin_token():
    user = os.getenv("ADMIN_USER")
    pwd = os.getenv("ADMIN_PASSWORD")

    response = api_request(
        "post", AUTH_LOGIN, data={"username": user, "password": pwd})

    if response is None:
        raise Exception("❌ Login failed after some retries")

    try:
        return response.json()["access_token"]
    except (KeyError, ValueError):
        raise Exception(f"❌ Login failed. Unexpected Response: {response.text}")

@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

def user_exists(email, auth_headers, retries=RETRIES, delay=DELAY):
    for i in range(retries):
        resp = api_request("get", USERS, headers=auth_headers)
        if resp.status_code == 200:
            users = resp.json()
            return next((user for user in users if user["email"] == email), None)
        elif resp.status_code == 500:
            logger.warning(f"/users returned 500, retrying ({i+1}/{retries}) after {delay}s...")
            time.sleep(delay)
        else:
            logger.error(f"/users returned unexpected status: {resp.status_code}")
            break
    return None

def delete_user_by_email(email, auth_headers, retries=RETRIES, delay=DELAY):
    user = user_exists(email, auth_headers, retries, delay)
    if user:
        user_id = user["id"]
        for i in range(retries):
            resp = api_request("delete", f"{USERS}{user_id}", headers=auth_headers)
            if resp.status_code == 204:
                logger.info(f"🧹 Cleanup: Deleted user '{email}' after test.")
                # Espera unos segundos para que la BD "libere" el email
                time.sleep(3)  # Aumenta a 5 si sigue fallando
                return True
            elif resp.status_code == 500:
                logger.warning(f"Delete user 500, retrying ({i+1}/{retries}) after {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Delete user returned unexpected status: {resp.status_code}")
                break
    return False

@pytest.fixture
def signup_test_case(auth_headers):
    def _signup(case, variable="email", retries=3):
        email = case.get("email")
        password = case.get("password")
        full_name = case.get("full_name")

        existed_before = user_exists(email, auth_headers)
        if existed_before:
            pytest.skip(f"User '{email}' already exists. Skipping test.")

        payload = {
            "email": email,
            "password": password,
            "full_name": full_name
        }

        resp = None
        try:
            for attempt in range(retries):
                resp = api_request("post", AUTH_SIGN_UP, json=payload)
                if (case["expected_status"] == 201 and resp.status_code == 400 and "already registered" in resp.text):
                    logger.warning(f"Retrying after cleanup for {email} (attempt {attempt+1})")
                    user = user_exists(email, auth_headers)
                    if user:
                        api_request("delete", f"{USERS}{user['id']}", headers=auth_headers)
                    continue
                break

            assert resp is not None, "API response is None"
            assert resp.status_code == case["expected_status"], (
                f"\n---\nTest failed for {variable}: {case.get(variable)}\n"
                f"Payload: {payload}\n"
                f"Expected: {case['expected_status']} | Got: {resp.status_code}\n"
                f"Response: {resp.text}\n"
                "---"
            )
        finally:
            # Limpia solo si el usuario fue creado por este test
            user = user_exists(email, auth_headers)
            if user:
                del_resp = api_request("delete", f"{USERS}{user['id']}", headers=auth_headers)
                if del_resp.status_code == 204:
                    logger.info(f"Cleanup: Deleted user '{email}' after test.")
                else:
                    logger.warning(f"Could not cleanup user '{email}', status: {del_resp.status_code}")
    return _signup








# @pytest.fixture
# def user(auth_headers, role: str = "passenger"):
#     user_data = {
#     "email": fake.email(),
#     "password": fake.password(),
#     "full_name": "Pam Bazo",
#     "role": role
#     }
#     r = requests.post(f"{BASE_URL}{USERS}",
#                       json=user_data,
#                       headers=auth_headers,
#                       timeout=5)
#     user_created = r.json()
#     yield user_created
#     requests.delete(f"{BASE_URL}{USERS}/{user_created['id']}")

# @pytest.fixture
# def airport(auth_headers):
#     r = requests.post(BASE_URL + AIRPORT, json=airport_data, headers=auth_headers)
#     r.raise_for_status()
#     airport_response = r.json()
#     yield airport_response
#     requests.delete(BASE_URL + AIRPORT + f'{airport_response["iata_code"]}', headers=auth_headers, timeout=5)
# def test_admin_token_success(auth_headers):
#     print(auth_headers)  # Imprime el diccionario completo
#
#
# def test_create_airport_schema(airport):
#     validate(instance=airport, schema=airport_schema)
#
#
# def test_get_all_airports(airport, auth_headers):
#     r = requests.get(f"{BASE_URL}{AIRPORT}", headers=auth_headers)
#     return r

