# tests/conftest.py

from utils.settings import BASE_URL, AUTH_LOGIN, USERS, AUTH_SIGN_UP
from dotenv import load_dotenv
import os
import pytest
import faker
import time

from utils.api_helpers import api_request

load_dotenv()

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

