"""Variante segura de HTTPS: `verify=True` y `timeout` presente.

No debe disparar la categoría `verify_false` (B501).
"""

import requests


def fetch():
    return requests.get("https://example.com", verify=True, timeout=5)
