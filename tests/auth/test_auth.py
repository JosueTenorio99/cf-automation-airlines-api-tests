import os
from utils.api_helpers import api_request
from utils.settings import AUTH_LOGIN, AUTH_SIGN_UP
from dotenv import load_dotenv

load_dotenv()

def test_login_as_admin():
    admin_user_name = os.getenv("ADMIN_USER")
    admin_password = os.getenv("ADMIN_PASSWORD")

    r = api_request("post", AUTH_LOGIN,
                    data={"username": admin_user_name , "password": admin_password})
    response_data = r.json()
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert response_data.get("token_type") == "bearer"

def test_sign_up(user):
    return user

