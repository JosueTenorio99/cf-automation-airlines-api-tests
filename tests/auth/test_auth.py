import pytest
from uuid import uuid4
from tests.auth.data import emails_to_test, passwords_to_test, full_names_to_test, valid_password, valid_full_name, \
    DEFAULT_EMAIL1, DEFAULT_EMAIL2
from tests.conftest import signup_test_case, auth_headers, admin_token

def get_unique_email(prefix="test"):
    return f"{prefix}_{uuid4().hex}@example.com"

# EMAIL TESTS (usa emails definidos en tu data, para cobertura específica)
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

# PASSWORD TESTS (cada test usa un email único para evitar colisiones entre pruebas paralelas)
@pytest.mark.parametrize("case", passwords_to_test)
def test_signup_various_passwords(signup_test_case, case):
    unique_email = get_unique_email(prefix="pwtest")
    signup_test_case(
        {
            "email": unique_email,  # Email único por test
            "password": case["password"],
            "full_name": valid_full_name,
            "expected_status": case["expected_status"]
        },
        variable="password"
    )

# FULL_NAME TESTS (cada test usa un email único)
@pytest.mark.parametrize("case", full_names_to_test)
def test_signup_various_full_names(signup_test_case, case):
    unique_email = get_unique_email(prefix="nametest")
    signup_test_case(
        {
            "email": unique_email,
            "password": valid_password,
            "full_name": case["full_name"],
            "expected_status": case["expected_status"]
        },
        variable="full_name"
    )




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