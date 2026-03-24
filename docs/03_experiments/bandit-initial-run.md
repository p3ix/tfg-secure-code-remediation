# Primera ejecución de Bandit sobre el corpus MVP

## 1. Objetivo

El objetivo de este experimento ha sido integrar Bandit en el proyecto y ejecutar una primera pasada de análisis estático sobre el corpus inicial de fixtures vulnerables del MVP.

Con esta ejecución se pretende comprobar:
- si Bandit detecta correctamente las vulnerabilidades priorizadas en el MVP;
- qué cobertura ofrece de forma inmediata sobre el corpus diseñado;
- qué limitaciones aparecen ya en esta primera fase;
- y hasta qué punto resulta necesario complementarlo posteriormente con Semgrep.

## 2. Configuración utilizada

- herramienta: Bandit
- objetivo analizado: `fixtures/mvp/`
- configuración: `pyproject.toml`
- salida estructurada: `reports/bandit/fixtures-mvp-bandit.json`

La ejecución utilizada ha sido la siguiente:

```bash
bandit -c pyproject.toml -r fixtures/mvp -f json -o reports/bandit/fixtures-mvp-bandit.json
```

Además, se ha creado un script de apoyo para reproducir esta ejecución:

```bash
scripts/run_bandit_fixtures.sh
```

## 3. Corpus analizado

El corpus inicial del MVP contiene ejemplos vulnerables de las siguientes categorías:

- command injection mediante shell=True y os.system
- uso inseguro de yaml.load
- uso de verify=False en peticiones HTTPS
- peticiones sin timeout
- debug=True en Flask
- SQL injection como categoría de detección y propuesta, no de autofix

## 4. Resultados observados

La primera ejecución de Bandit ha generado hallazgos relevantes sobre el corpus. En concreto, se han detectado correctamente varias de las categorías principales del MVP.

### 4.1. Hallazgos detectados
**Command injection**

Se han detectado los dos casos incluidos en esta categoría:

- os.system(...) mediante la regla B605
- subprocess.run(..., shell=True) mediante la regla B602

Además, Bandit ha marcado la importación de subprocess con B404, que funciona como señal adicional de revisión, aunque no representa por sí misma una vulnerabilidad concluyente.

**Flask con debug=True**

Se ha detectado correctamente el caso de ejecución de Flask en modo debug mediante la regla B201.

**verify=False en peticiones HTTPS**

Se ha detectado correctamente el caso requests.get(..., verify=False) mediante la regla B501.

**requests sin timeout**

Bandit ha detectado llamadas a requests sin timeout mediante la regla B113.

Este hallazgo aparece:

- en el fixture específico vuln_requests_no_timeout.py;
- y también en el ejemplo de verify=False, ya que la llamada tampoco incluye timeout.

**SQL injection**

El caso de construcción insegura de consulta SQL ha sido señalado mediante la regla B608, que indica un posible vector de inyección SQL a través de construcción de consultas basada en cadenas.

**yaml.load inseguro**

El uso de yaml.load inseguro ha sido detectado mediante la regla B506.

## 5. Cobertura obtenida en esta primera iteración

A partir de esta primera ejecución, la cobertura observada puede resumirse así:

Se han detectado todos los objetivos menos el httpx sin timeout, puede suponer una limitación de cobertura.

## 6. Métricas generales observadas

En esta primera ejecución, Bandit ha generado:

- 9 resultados totales,
- severidades altas, medias y bajas,
- y distintos niveles de confianza según el tipo de hallazgo.

Entre los resultados más relevantes destacan:

- severidad alta en command injection,
- severidad alta en verify=False,
- severidad alta en debug=True de Flask,
- severidad media en yaml.load,
- severidad media en SQL injection,
- severidad media en llamadas requests sin timeout.

## 7. Interpretación de resultados

Los resultados obtenidos son positivos para el objetivo del TFG, ya que muestran que Bandit ofrece una base útil para detectar varias de las vulnerabilidades principales del MVP en proyectos Python.

Al mismo tiempo, esta primera ejecución también muestra límites claros:

- no todos los casos quedan cubiertos por igual;
- la detección de timeout no parece abarcar al menos el ejemplo de httpx;
- algunos hallazgos tienen baja confianza y conviene interpretarlos con prudencia;
- ciertos resultados, como SQL injection, son más útiles como señal de riesgo que como base para una remediación automática fiable.

Esto refuerza la decisión de no depender de una sola herramienta y justifica la integración posterior de Semgrep como complemento del análisis base.

## 8. Conclusiones

La integración inicial de Bandit puede considerarse satisfactoria dentro del alcance del MVP.

En esta fase se ha comprobado que:

- Bandit se integra correctamente en el proyecto;
- puede analizar de forma reproducible el corpus inicial de fixtures;
- detecta varias categorías prioritarias del MVP;
- y proporciona una salida estructurada útil para etapas posteriores de clasificación y normalización.

Como conclusión práctica, Bandit queda validado como primera herramienta base del pipeline de detección del TFG, aunque será necesario complementarlo con Semgrep para mejorar cobertura y comparar resultados.
