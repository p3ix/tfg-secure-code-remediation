"""Variante segura de Flask: `debug=False`.

No debe disparar la categoría `flask_debug_true` (B201).
"""

from flask import Flask

app = Flask(__name__)


def main() -> None:
    app.run(debug=False)
