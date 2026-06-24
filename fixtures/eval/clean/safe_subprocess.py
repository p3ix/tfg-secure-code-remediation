"""Variante segura de command injection: lista de argumentos, sin shell.

No debe disparar la categoría `command_injection` (B602/B605).
"""


def run(user_input: str) -> None:
    import subprocess

    subprocess.run(["ls", user_input], check=False)
