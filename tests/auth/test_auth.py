# tests/auth/test_auth.py

import pytest
import logging
# from tests.conftest import auth_headers, admin_token
from uuid import uuid4
from tests.auth.data import emails_to_test, passwords_to_test, full_names_to_test, valid_password, valid_full_name
from jsonschema import validate
from utils.settings import user_schema


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

# PASSWORD TESTS
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

# FULL NAME TESTS (ahora optimizado)
@pytest.mark.parametrize("case", full_names_to_test)
def test_signup_various_full_names(signup_test_case, case):
    resp, email, user = signup_test_case(case, variable="full_name")

    # Validación extra de normalización solo si aplica
    if case["expected_status"] == 201 and case.get("expected_user_created"):
        assert user, f"User with email '{email}' not found after signup."
        expected_name = case["expected_user_created"]
        real_name = user.get("full_name")
        assert real_name == expected_name, (
            f"Full name was not normalized as expected.\n"
            f"Sent: '{case['full_name']}' | Expected: '{expected_name}' | Got: '{real_name}'"
        )

def test_create_user_schema(signup_test_case, valid_password=valid_password, valid_full_name=valid_full_name):
    case = {
        "email": f"schema_{uuid4().hex}@example.com",
        "password": valid_password,
        "full_name": valid_full_name,
        "expected_status": 201
    }
    resp, email, user = signup_test_case(case, variable="email")

    assert user is not None, f"User with email {email} was not found after signup."