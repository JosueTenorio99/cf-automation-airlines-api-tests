from utils.settings import BASE_URL, AUTH_LOGIN
from dotenv import load_dotenv
import os
import pytest
import requests
import faker
from utils.api_helpers import api_request
from jsonschema import validate
load_dotenv()
import time

CLEANUP_RETRIES = 7   # O más si la API sigue dando 500
CLEANUP_DELAY = 2     # Segundos entre intentos, puedes subirlo si ves muchas fallas


fake = faker.Faker()

@pytest.fixture(scope="session")
def admin_token():
    user = os.getenv("ADMIN_USER")
    pwd = os.getenv("ADMIN_PASSWORD")

    response = api_request(
        "post", AUTH_LOGIN, data={"username": user, "password": pwd})

    if response is None:
        raise Exception("❌ Falló el login después de varios intentos")

    try:
        return response.json()["access_token"]
    except (KeyError, ValueError):
        raise Exception(f"❌ Login fallido. Respuesta inesperada: {response.text}")


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

def test_admin_token(auth_headers):
    print(auth_headers)


import pytest
from utils.api_helpers import api_request
from utils.settings import USERS

def user_exists(email, auth_headers, retries=CLEANUP_RETRIES, delay=CLEANUP_DELAY):
    for i in range(retries):
        resp = api_request("get", USERS, headers=auth_headers)
        if resp.status_code == 200:
            users = resp.json()
            return next((user for user in users if user["email"] == email), None)
        elif resp.status_code == 500:
            print(f"[QA WARNING] /users returned 500, retrying ({i+1}/{retries}) after {delay}s...")
            time.sleep(delay)
        else:
            print(f"[QA ERROR] /users returned unexpected status: {resp.status_code}")
            break
    return None


def delete_user_by_email(email, auth_headers, retries=CLEANUP_RETRIES, delay=CLEANUP_DELAY):
    user = user_exists(email, auth_headers, retries, delay)
    if user:
        user_id = user["id"]
        for i in range(retries):
            resp = api_request("delete", f"{USERS}{user_id}", headers=auth_headers)
            if resp.status_code == 204:
                print(f"🧹 Cleanup: Deleted user '{email}' after test.")
                return True
            elif resp.status_code == 500:
                print(f"[QA WARNING] Delete user 500, retrying ({i+1}/{retries}) after {delay}s...")
                time.sleep(delay)
            else:
                print(f"[QA ERROR] Delete user returned unexpected status: {resp.status_code}")
                break
    return False



@pytest.fixture
def setup_test_user(auth_headers):
    """
    Setup/Cleanup fixture:
    - Limpia el usuario antes del test
    - Luego del test, si se creó un usuario (201), lo elimina
    """
    users_to_cleanup = []
    def _setup_user(email):
        # Limpia antes
        user = user_exists(email, auth_headers)
        if user:
            deleted = delete_user_by_email(email, auth_headers)
            if not deleted:
                pytest.skip(f"Could not clean user '{email}' before test.")
        # La función retorna un 'callback' para cleanup después
        def post_cleanup(resp):
            # Si la respuesta fue 201, elimina ese user
            if resp is not None and resp.status_code == 201:
                try:
                    user_id = resp.json().get("id")
                    if user_id:
                        del_resp = api_request("delete", f"{USERS}{user_id}", headers=auth_headers)
                        if del_resp.status_code == 204:
                            print(f"🧹 Cleanup: Deleted user '{email}' after test.")
                        else:
                            print(f"⚠️ Cleanup failed for user '{email}' (id: {user_id}) after test.")
                except Exception as e:
                    print(f"⚠️ Exception during cleanup for '{email}': {e}")
        return post_cleanup
    return _setup_user

import pytest
import time
from utils.api_helpers import api_request
from utils.settings import USERS, AUTH_SIGN_UP
from tests.auth.data import valid_email, valid_password, valid_full_name

def user_exists(email, auth_headers, retries=7, delay=2):
    for i in range(retries):
        resp = api_request("get", USERS, headers=auth_headers)
        if resp.status_code == 200:
            users = resp.json()
            return next((user for user in users if user["email"] == email), None)
        elif resp.status_code == 500:
            print(f"[QA WARNING] /users returned 500, retrying ({i+1}/{retries}) after {delay}s...")
            time.sleep(delay)
    return None

@pytest.fixture
def signup_test_case(auth_headers):
    def _signup(case, variable="email", retries=3):
        base_email = case.get("email", valid_email)
        email = case.get("email", valid_email)
        password = case.get("password", valid_password)
        full_name = case.get("full_name", valid_full_name)

        # 1. Antes de test, verifica si ya existe
        existed_before = user_exists(email, auth_headers)

        if existed_before:
            pytest.skip(f"User '{email}' already exists. Skipping test.")

        payload = {
            "email": email,
            "password": password,
            "full_name": full_name
        }

        resp = None
        created_user_id = None

        try:
            # 2. Intenta crear el usuario, reintenta si es necesario (ej. por 400/500)
            attempt = 0
            while attempt < retries:
                resp = api_request("post", AUTH_SIGN_UP, json=payload)
                if (case["expected_status"] == 201 and resp.status_code == 400 and "already registered" in resp.text):
                    print(f"[QA RETRY] Got 400 on signup for {email}, cleaning up and retrying... (attempt {attempt+1})")
                    # Borra el usuario si existe y reintenta
                    user = user_exists(email, auth_headers)
                    if user:
                        api_request("delete", f"{USERS}{user['id']}", headers=auth_headers)
                    attempt += 1
                    time.sleep(1)
                    continue
                break

            # 3. Si la API lo creó, obtén el id para borrarlo después
            if resp is not None and resp.status_code == 201:
                created_user_id = resp.json().get("id")

            # 4. Assert de status esperado
            assert resp.status_code == case["expected_status"], (
                f"{variable.capitalize()}: {case.get(variable)} | Expected: {case['expected_status']} | "
                f"Got: {resp.status_code} | Response: {resp.text}"
            )
        finally:
            # 5. Cleanup SIEMPRE si el usuario no existía antes (pase lo que pase)
            user = user_exists(email, auth_headers)
            if not existed_before and user:
                del_resp = api_request("delete", f"{USERS}{user['id']}", headers=auth_headers)
                if del_resp.status_code == 204:
                    print(f"🧹 Cleanup: Deleted user '{email}' after test.")
                else:
                    print(f"[QA WARNING] Could not cleanup user '{email}', status: {del_resp.status_code}")

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

