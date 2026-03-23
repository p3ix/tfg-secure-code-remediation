# Primera ejecución de Semgrep sobre el corpus MVP

## 1. Objetivo

El objetivo de este experimento ha sido integrar Semgrep en el proyecto y ejecutar una primera pasada de análisis sobre el corpus inicial de fixtures vulnerables del MVP.

Esta ejecución busca comprobar:
- qué categorías del corpus detecta Semgrep;
- cómo se compara su cobertura con la obtenida previamente con Bandit;
- y qué valor aporta como herramienta complementaria dentro del pipeline de detección del TFG.

## 2. Configuración utilizada

- herramienta: Semgrep Community Edition
- comando principal: `semgrep scan`
- ruleset inicial: `p/default`
- objetivo analizado: `fixtures/mvp/`
- salida estructurada: `reports/semgrep/fixtures-mvp-semgrep.json`

La ejecución utilizada ha sido:

```bash
semgrep scan --config p/default --metrics off --json-output reports/semgrep/fixtures-mvp-semgrep.json fixtures/mvp
```

Además, se ha realizado una ejecución adicional por terminal para revisar visualmente los hallazgos.

## 3. Corpus analizado

El corpus inicial del MVP contiene ejemplos vulnerables de las siguientes categorías:

- command injection mediante shell=True y os.system
- uso inseguro de yaml.load
- uso de verify=False en peticiones HTTPS
- peticiones sin timeout
- debug=True en Flask
- SQL injection como categoría de detección y propuesta, no de autofix

## 4. Resultados observados

La primera ejecución de Semgrep ha generado 6 hallazgos sobre el corpus analizado.

### 4.1. Hallazgos detectados
**shell=True**

Semgrep ha detectado correctamente el uso de subprocess.run(..., shell=True).

**debug=True en Flask**

Semgrep ha detectado correctamente el caso de ejecución de Flask en modo debug.

**verify=False**

Semgrep ha detectado correctamente el uso de verify=False en una petición HTTPS.

**yaml.load inseguro**

Semgrep ha detectado correctamente el uso inseguro de yaml.load y además ha mostrado una orientación clara hacia el uso de yaml.safe_load o loaders seguros.

**SQL injection**

Semgrep ha detectado el caso de consulta SQL construida mediante interpolación insegura.

En esta categoría ha generado dos hallazgos:

- una regla relacionada con consulta SQL formateada;
- una regla adicional orientada a ejecución insegura de consultas.

## 5. Casos no detectados en esta iteración

En esta primera pasada, Semgrep no ha detectado los siguientes ejemplos del corpus:

- os.system(...)
- requests sin timeout
- httpx sin timeout

Esta limitación es relevante porque muestra que la cobertura inicial de Semgrep sobre el corpus del MVP no sustituye completamente la cobertura observada con Bandit.

## 6. Comparación inicial con Bandit

La comparación inicial entre Bandit y Semgrep puede resumirse así:

shell=True -> Ambos lo detectan
os.system -> Mejor cobertura inicial de Bandit
yaml.load inseguro -> Ambos lo detectan
verify=False -> Ambos lo detectan
requests sin timeout -> Mejor cobertura inicial de Bandit
httpx sin timeout -> Caso pendiente de cubrir
debug=True en Flask -> Ambos lo detectan
SQL injection -> Ambos lo detectan, aunque Semgrep genera dos hallazgos

## 7. Interpretación de resultados

Los resultados muestran que Semgrep aporta valor como herramienta complementaria, pero no sustituye a Bandit en esta primera configuración.

Entre los aspectos positivos observados destacan:

- mensajes descriptivos claros;
- detección correcta de varias categorías prioritarias del MVP;
- orientación útil hacia remediaciones en algunos casos.

Al mismo tiempo, también se observan límites:

- no detecta todos los casos detectados previamente por Bandit;
- no cubre todavía los casos de timeout del corpus inicial;
- en SQL injection aparece un hallazgo cuya denominación parece más asociada a SQLAlchemy, aunque el ejemplo usa sqlite3, lo que sugiere que algunos - resultados deben interpretarse con prudencia.

## 8. Conclusiones

La integración inicial de Semgrep puede considerarse útil y satisfactoria para esta fase del TFG.

Esta primera ejecución permite concluir que:

- Semgrep se integra correctamente en el proyecto;
- detecta varias categorías importantes del MVP;
- aporta información complementaria a Bandit;
- y confirma que el uso combinado de ambas herramientas está justificado.

Por tanto, Semgrep queda validado como segunda herramienta base del pipeline de detección, aunque será necesario seguir ajustando reglas y revisar cobertura real en iteraciones posteriores.
