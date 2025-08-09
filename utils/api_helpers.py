# utils/api_helpers.py

import requests
import time
import logging
from utils.settings import BASE_URL, USERS

RETRIES = 15
DELAY = 1
DEFAULT_TIMEOUT = 20

logger = logging.getLogger("qa_tests")

# Api general function
def api_request(method, path, **kwargs):
    url = f"{BASE_URL}{path}"

    for i in range(RETRIES):
        try:
            r = requests.request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)
            if r.status_code < 500 or i == RETRIES - 1:
                return r
            logger.warning(f"Received {r.status_code} from {url} on attempt {i+1}. Retrying after {DELAY}s...")
        except requests.exceptions.ReadTimeout as e:
            logger.warning(f"ReadTimeout on {url} (attempt {i+1}/{RETRIES}), retrying after {DELAY}s...")
            last_exc = e
        except Exception as e:
            logger.error(f"Exception on {url}: {e}")
            last_exc = e
        time.sleep(DELAY)
    if last_exc:
        raise last_exc
    raise Exception(f"Request to {url} failed after {RETRIES} retries")



