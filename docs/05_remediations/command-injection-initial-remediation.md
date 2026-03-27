# Quinta remediación asistida: command injection

## Objetivo

Implementar una remediación asistida y conservadora para patrones simples de inyección de comandos del MVP, y verificar que el hallazgo desaparece al reanalizar el contenido corregido.

## Estrategia de remediación

Se cubren dos patrones del corpus:

Para `subprocess.run` con `shell=True`:
```python
subprocess.run(f"ls {user_input}", shell=True, check=False)
```
se propone:
```python
subprocess.run(shlex.split(f"ls {user_input}"), shell=False, check=False)
```

Para `os.system`:
```python
os.system("ls " + user_input)
```
se propone:
```python
subprocess.run(shlex.split("ls " + user_input), check=False)
```

En ambos casos se elimina el paso por un intérprete de shell, que es lo que permite que metacaracteres como `;`, `|` o `&&` se interpreten.

## Criterio de verificación

La verificación se considera satisfactoria si, tras aplicar la propuesta, no aparecen hallazgos clasificados como `command_injection` (Bandit B602/B605 y reglas equivalentes de Semgrep).

## Limitaciones

Esta primera versión no cubre:

- patrones multilínea o comandos construidos con lógica compleja;
- usos de `os.popen`, `os.exec*` u otras APIs de ejecución;
- la entrada del usuario sigue formando parte del comando, aunque sin paso por shell.

El objetivo del MVP es demostrar el flujo detect–repair–verify sobre casos acotados, no cubrir todos los vectores posibles de command injection.
