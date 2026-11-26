"""One place for calling web APIs: timeouts, retries and readable errors."""
import time

import requests

RETRY_STATUS = {429, 500, 502, 503, 504}  # rate limit and temporary server errors


def get_json(url: str, params: dict, timeout: int = 120, retries: int = 4) -> dict:
    """GET a URL and return its JSON body, retrying temporary failures.

    Waits 2, 4, 8... seconds between attempts. Any other error (for example
    401 for a wrong key) is raised at once, with the key hidden from the message.
    """
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries:
                raise
        else:
            if response.status_code not in RETRY_STATUS:
                if response.status_code != 200:
                    detail = response.text[:200]
                    key = params.get("api_key")
                    if key:
                        detail = detail.replace(key, "***")
                    raise RuntimeError(
                        f"{url} returned HTTP {response.status_code}: {detail}"
                    )
                return response.json()
            if attempt == retries:
                raise RuntimeError(f"{url} still returned HTTP {response.status_code}")
        time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")
