# utils/api_helpers.py

import requests
import time
import logging
from utils.settings import BASE_URL

RETRIES = 15
DELAY = 1
DEFAULT_TIMEOUT = 20

logger = logging.getLogger("qa_tests")

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







# import time
# import requests
# from typing import Optional
# from utils.settings import BASE_URL, MAX_WAIT_SECONDS
#
# SIMULATED_ERRORS = {
#     "Error 400",
#     "Simulated 4xx bug",
#     "Simulated 5xx bug",
#     "Simulated timeout",
# }
#
#
# def is_simulated_error(response: requests.Response) -> bool:
#     try:
#         data = response.json()
#         # Si es lista completa, no es un error simulado
#         if isinstance(data, list):
#             return False
#
#         # Verificamos si "detail" es string y está en los errores simulados
#         detail = data.get("detail", "")
#         if isinstance(detail, str):
#             return detail in SIMULATED_ERRORS
#         else:
#             return False
#     except Exception:
#         return False
#
#
#
# def api_request(
#     method: str,
#     path: str,
#     max_attempts: int = 10,
#     initial_timeout: float = 5.0,
#     max_timeout: float = 30.0,
#     retry_400: bool = True,
#     retry_5xx: bool = True,
#     **kwargs
# ) -> Optional[requests.Response]:
#     url = f"{BASE_URL}{path}"
#     start_time = time.time()
#     last_response = None
#     last_exception = None
#
#     for attempt in range(max_attempts):
#         current_timeout = min(initial_timeout * (attempt + 1), max_timeout)
#         kwargs['timeout'] = current_timeout
#
#         try:
#             response = requests.request(method, url, **kwargs)
#             last_response = response
#
#             # ✅ Éxito
#             if 200 <= response.status_code < 300 and not is_simulated_error(response):
#                 return response
#
#             # Manejo especial para 400 Bad Request
#             if response.status_code == 400:
#                 try:
#                     detail = response.json().get("detail", "")
#                 except Exception:
#                     detail = ""
#
#                 if "Email already registered" in detail:
#                     # No reintentar si email ya registrado
#                     return response
#
#                 if retry_400 and attempt < max_attempts - 1:
#                     wait_time = min((2 ** attempt) * 0.5, 10)
#                     print(f"⚠️ 400 Bad Request (attempt {attempt + 1}). Retrying in {wait_time}s...")
#                     time.sleep(wait_time)
#                     continue
#
#             # ✅ Reintento para errores simulados
#             if is_simulated_error(response):
#                 wait_time = min((2 ** attempt) * 0.5, 10)
#                 print(f"⚠️ Simulated error: {response.json().get('detail')} (attempt {attempt + 1}). Retrying in {wait_time}s...")
#                 time.sleep(wait_time)
#                 continue
#
#             # ✅ Reintento para errores 5xx reales
#             if 500 <= response.status_code < 600 and retry_5xx and attempt < max_attempts - 1:
#                 wait_time = min((2 ** attempt) * 0.5, 10)
#                 print(f"⚠️ {response.status_code} Server Error (attempt {attempt + 1}). Retrying in {wait_time}s...")
#                 time.sleep(wait_time)
#                 continue
#
#             # ❌ Otros errores: no reintentar
#             return response
#
#         except requests.RequestException as e:
#             last_exception = e
#
#         # ⏳ Espera entre reintentos por excepción
#         wait_time = min((2 ** attempt) * 0.5, 10)
#         remaining_time = MAX_WAIT_SECONDS - (time.time() - start_time)
#         if remaining_time < wait_time:
#             break
#         if attempt < max_attempts - 1:
#             time.sleep(wait_time)
#
#     return last_response
#
#
