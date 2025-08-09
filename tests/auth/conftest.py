# tests/auth/conftest.py

import pytest
import logging
from utils.api_helpers import api_request
from utils.user_helpers import get_user_by_email, delete_user_by_email
from utils.settings import AUTH_SIGN_UP, USERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa_tests")

@pytest.fixture
def signup_test_case(auth_headers):
    def _signup(case, variable="email", retries=3):
        email = case.get("email")
        password = case.get("password")
        full_name = case.get("full_name")

        existed_before = get_user_by_email(email, auth_headers)
        if existed_before:
            pytest.skip(f"User '{email}' already exists. Skipping test.")

        payload = {
            "email": email,
            "password": password,
            "full_name": full_name
        }

        resp = None
        user = None
        try:
            for attempt in range(retries):
                resp = api_request("post", AUTH_SIGN_UP, json=payload)
                if (case["expected_status"] == 201 and resp.status_code == 400 and "already registered" in resp.text):
                    logger.warning(f"Retrying after cleanup for {email} (attempt {attempt+1})")
                    user = get_user_by_email(email, auth_headers)
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
            # Devuelve user sólo si fue creado
            if resp.status_code == 201:
                user = get_user_by_email(email, auth_headers)
            return resp, email, user
        finally:
            deleted = delete_user_by_email(email, auth_headers)
            if deleted:
                logger.info(f"Cleanup: Deleted user '{email}' after test.")
            else:
                logger.warning(f"Could not cleanup user '{email}' after test.")
    return _signup

