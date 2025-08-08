# tests/auth/test_auth.py

import pytest
import logging
from uuid import uuid4
from tests.auth.data import emails_to_test, passwords_to_test, full_names_to_test, valid_password, valid_full_name
from tests.conftest import signup_test_case, user_exists, auth_headers, admin_token
from utils.api_helpers import api_request
from utils.settings import AUTH_SIGN_UP, USERS

# Configura logging para consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa_tests")

def get_unique_email(prefix="test"):
    return f"{prefix}_{uuid4().hex}@example.com"

# EMAIL TESTS
@pytest.mark.parametrize("case", emails_to_test)
def test_signup_various_emails(signup_test_case, case):
    signup_test_case(
        {
            "email": case["email"],
            "password": valid_password,
            "full_name": valid_full_name,
            "expected_status": case["expected_status"]
        },
        variable="email"
    )

# PASSWORD TESTS (email único por test)
@pytest.mark.parametrize("case", passwords_to_test)
def test_signup_various_passwords(signup_test_case, case):
    unique_email = get_unique_email(prefix="pwtest")
    signup_test_case(
        {
            "email": unique_email,
            "password": case["password"],
            "full_name": valid_full_name,
            "expected_status": case["expected_status"]
        },
        variable="password"
    )

@pytest.mark.parametrize("case", full_names_to_test)
def test_signup_various_full_names(auth_headers, case):
    # Siempre genera un email único para evitar colisiones
    unique_email = get_unique_email(prefix="fn")
    payload = {
        "email": unique_email,
        "password": valid_password,
        "full_name": case["full_name"]
    }

    # Asegúrate de que no existe antes
    existed_before = user_exists(unique_email, auth_headers)
    if existed_before:
        pytest.skip(f"User '{unique_email}' already exists. Skipping test.")

    resp = None
    try:
        for attempt in range(3):
            resp = api_request("post", AUTH_SIGN_UP, json=payload)
            # Si hay error por "already registered" (muy raro aquí), lo intenta limpiar
            if (case["expected_status"] == 201 and resp.status_code == 400 and "already registered" in resp.text):
                user = user_exists(unique_email, auth_headers)
                if user:
                    api_request("delete", f"{USERS}{user['id']}", headers=auth_headers)
                continue
            break

        assert resp is not None, "API response is None"
        assert resp.status_code == case["expected_status"], (
            f"\n---\nTest failed for full_name: {case.get('full_name')}\n"
            f"Payload: {payload}\n"
            f"Expected: {case['expected_status']} | Got: {resp.status_code}\n"
            f"Response: {resp.text}\n"
            "---"
        )

        # Si el usuario se crea, verifica que el nombre esté normalizado (o no)
        if case["expected_status"] == 201 and case["expected_user_created"]:
            # Busca al usuario y revisa el campo full_name
            user = user_exists(unique_email, auth_headers)
            assert user, f"User with email '{unique_email}' not found after signup."
            expected_name = case["expected_user_created"]
            real_name = user.get("full_name")
            assert real_name == expected_name, (
                f"Full name was not normalized as expected.\n"
                f"Sent: '{case['full_name']}' | Expected: '{expected_name}' | Got: '{real_name}'"
            )
    finally:
        # Limpieza
        user = user_exists(unique_email, auth_headers)
        if user:
            del_resp = api_request("delete", f"{USERS}{user['id']}", headers=auth_headers)
            if del_resp.status_code == 204:
                logger.info(f"Cleanup: Deleted user '{unique_email}' after test.")
            else:
                logger.warning(f"Could not cleanup user '{unique_email}', status: {del_resp.status_code}")






# def test_login_as_admin():
#     admin_user_name = os.getenv("ADMIN_USER")
#     admin_password = os.getenv("ADMIN_PASSWORD")
#
#     r = api_request("post", AUTH_LOGIN,
#                     data={"username": admin_user_name , "password": admin_password})
#     response_data = r.json()
#     assert r.status_code == 200
#     assert "access_token" in r.json()
#     assert response_data.get("token_type") == "bearer"