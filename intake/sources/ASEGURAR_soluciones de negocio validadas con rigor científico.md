**ANALIZA SIEMPRE LA CALIDAD DONDE RECOMIENDO:**

* **Selecciona 3-5 preguntas críticas** según el proyecto que estás desarrollando (no las respondas todas en cada proyecto).  
* **Crea una sección "Decisiones de Diseño"** en tu README.md donde respondas estas preguntas con el nivel de detalle mostrado a continuación.  
* **Documenta con evidencia visual:** gráficos, tablas, capturas de código, diagramas de arquitectura.

**El objetivo de un respositorio es tener una diferenciacion de alto nivel:**   
**Problema Central:** ¿Qué preguntas debe responder un científico de datos en su portafolio para demostrar nivel senior en manufactura/calidad industrial?

* **Rama 1: Preguntas de Rigor Estadístico y Metodológico (La Ciencia)**  
  * 1.1. Validación y prevención de data leakage  
  * 1.2. Manejo de desbalance y costo asimétrico de errores  
  * 1.3. Robustez frente a datos ruidosos y deriva (drift)  
* **Rama 2: Preguntas de Ingeniería y Despliegue (La Producción)**  
  * 2.1. Reproducibilidad y versionado  
  * 2.2. Latencia, escalabilidad y monitoreo en producción  
  * 2.3. Integración con sistemas legacy (MES, SCADA, ERP)  
* **Rama 3: Preguntas de Comunicación y Valor de Negocio (El Impacto)**  
  * 3.1. Traducción de métricas técnicas a impacto financiero  
  * 3.2. Accionabilidad y cambio de comportamiento operativo  
  * 3.3. Gestión del cambio y adopción por usuarios finales

### 2\. Priorización (Regla 80/20)

El 20% de las preguntas que generarán el 80% de la diferenciación son aquellas que **casi ningún candidato junior responde**, porque requieren pensar más allá del modelo:

1. **¿Cómo validas que tu modelo no está filtrando información del futuro en un proceso secuencial?** (Rama 1.1)  
2. **¿Qué costo tiene para el negocio un Falso Negativo vs. un Falso Positivo, y cómo lo incorporas en la función de pérdida?** (Rama 1.2)  
3. **¿Cómo detectas que tu modelo está degradándose en producción sin etiquetas ground truth?** (Rama 2.2)  
4. **¿Cuánto dinero ahorra o genera tu modelo por cada punto porcentual de mejora en Recall?** (Rama 3.1)  
5. **¿Qué acción concreta debe tomar un operador de planta cuando tu modelo alerta un riesgo, y cómo reduces su carga cognitiva?** (Rama 3.2)

### 3\. Formulación de la Hipótesis

**Hipótesis:** Un portafolio que documenta explícitamente las respuestas a estas 5 preguntas críticas (y sus sub-preguntas asociadas) demostrará un nivel de madurez superior al 90% de los candidatos, porque evidencia que el profesional no solo construye modelos, sino que **diseña sistemas de decisión robustos, accionables y monetizables** que sobreviven al caos de la manufactura real.

### 4\. Búsqueda Activa de Evidencia Refutatoria (Escrutinio Crítico)

Intentemos destruir esta hipótesis para asegurar su solidez:

* **Refutación 1 (Contra la exhaustividad):** Crítica: Responder todas estas preguntas en cada proyecto es inviable. Te tomará más tiempo documentar que programar, y los reclutadores no leerán todo.  
  * Defensa: No debes responder todas en cada proyecto. Debes seleccionar las 3-5 más críticas según el tipo de proyecto (calidad, mantenimiento, NLP) y responderlas con profundidad en el README.md y en una sección de "Decisiones de Diseño" en tu documentación. La calidad de la respuesta, no la cantidad, es lo que diferencia.  
* **Refutación 2 (Contra la complejidad):** Crítica: Estas preguntas son demasiado avanzadas para un portafolio. Los reclutadores de RRHH no las entenderán y los técnicos las darán por sentadas.  
  * Defensa: Falso. Los reclutadores de RRHH buscan palabras clave y estructura clara (que estas preguntas te obligan a organizar). Los técnicos (Hiring Managers) **exactamente** buscan a alguien que haya pensado en estos problemas, porque son los dolores reales que enfrentan en producción. Si no las respondes, asumen que no las has enfrentado.  
* **Refutación 3 (Contra la aplicabilidad):** Crítica: ¿Y si el candidato no tiene experiencia real en planta? ¿Cómo puede responder preguntas sobre integración con SCADA o cambio de comportamiento operativo?  
  * Defensa: No necesitas haberlo vivido para investigarlo y proponer una solución basada en mejores prácticas. Documentar que "en un escenario real, integraría el modelo con el MES vía API REST y capacitaría a los operadores mediante sesiones de 30 minutos con dashboards simplificados" demuestra que piensas en la implementación, no solo en el algoritmo. Eso es nivel senior.

### 5\. Síntesis y Conclusión Sólida (Principio de la Pirámide)

**Conclusión Principal:** Para destacar como científico de datos de alto nivel en manufactura, tu portafolio debe ir más allá de mostrar código y métricas. Debe **documentar explícitamente las decisiones críticas de diseño** que demuestran que entiendes la física del proceso, las limitaciones de producción y el impacto financiero. A continuación, presento el arsenal de preguntas organizadas por dimensión, con ejemplos de cómo responderlas en tu documentación.

### ARSENAL DE PREGUNTAS CRÍTICAS PARA TU PORTAFOLIO

#### A. Dimensión Estadística y Metodológica (La Ciencia)

**1\. ¿Cómo garantizas que tu validación no filtra información del futuro en un proceso secuencial?**

* Respuesta de nivel alto: "En el dataset SECOM, implementé una división temporal basada en el ID de secuencia (no aleatoria), entrenando con los primeros 1200 lotes y validando con los últimos 367\. Esto refleja la realidad de producción, donde las condiciones de la máquina (desgaste de herramientas, acumulación de residuos) evolucionan. Además, utilicé GroupKFold agrupando por lote de producción para evitar que muestras del mismo lote estuvieran en train y test simultáneamente."  
* Evidencia a mostrar: Gráfico de distribución temporal de las clases, código de validación temporal.

**2\. ¿Cómo manejas el desbalance extremo y el costo asimétrico de los errores?**

* Respuesta de nivel alto: "En SECOM, la clase positiva (defecto) es solo el 6%. En lugar de usar SMOTE (que altera la distribución física de los sensores), ajusté el parámetro scale\_pos\_weight en XGBoost para penalizar 16 veces más los falsos negativos. Además, definí un umbral de clasificación móvil basado en la matriz de costos: un Falso Negativo cuesta \$10,000 USD (scrap no detectado), mientras que un Falso Positivo cuesta \$500 USD (inspección innecesaria). Optimicé el umbral para minimizar el costo esperado, no para maximizar el F1-Score."  
* Evidencia a mostrar: Curva Precision-Recall, matriz de confusión monetizada, gráfico de umbral óptimo vs. costo.

**3\. ¿Cómo evalúas la robustez de tu modelo frente a deriva de sensores o cambios en el proceso?**

* Respuesta de nivel alto: "Implementé un monitoreo de deriva utilizando la distancia de Population Stability Index (PSI) entre las distribuciones de las características de entrenamiento y las de producción (simuladas con ruido gaussiano del 5%). Si el PSI \> 0.2 para más de 3 sensores críticos, el sistema alerta para reentrenamiento. Además, validé el modelo con datos de 'estrés' (condiciones extremas de temperatura y presión) para asegurar que no se degrada en escenarios no vistos."  
* Evidencia a mostrar: Código de cálculo de PSI, gráfico de deriva temporal, resultados de pruebas de estrés.

#### B. Dimensión de Ingeniería y Despliegue (La Producción)

**4\. ¿Cómo aseguras la reproducibilidad y el versionado de tu modelo y datos?**

* Respuesta de nivel alto: "Utilicé DVC (Data Version Control) para versionar los datasets crudos y procesados, y MLflow para registrar experimentos (hiperparámetros, métricas, artefactos del modelo). Cada ejecución genera un hash único que permite replicar exactamente las condiciones de entrenamiento. El modelo se empaqueta en un contenedor Docker con un requirements.txt congelado, y el despliegue se automatiza con GitHub Actions."  
* Evidencia a mostrar: Estructura del repositorio, capturas de MLflow UI, Dockerfile y docker-compose.yml.

**5\. ¿Cómo detectas que tu modelo está degradándose en producción sin etiquetas ground truth?**

* Respuesta de nivel alto: "Implementé monitoreo de deriva de características (PSI) y monitoreo de predicciones (distribución de probabilidades de salida). Si la distribución de predicciones cambia significativamente (Kolmogorov-Smirnov test, p \< 0.05) o si el PSI de las características críticas supera 0.2, el sistema genera una alerta. Además, registré todas las predicciones en una base de datos SQLite para auditoría futura y reentrenamiento cuando se disponga de etiquetas reales."  
* Evidencia a mostrar: Diagrama de arquitectura de monitoreo, código de detección de deriva, dashboard de alertas.

**6\. ¿Cómo integrarías tu modelo con sistemas legacy de manufactura (MES, SCADA)?**

* Respuesta de nivel alto: "Expondría el modelo como una API REST en FastAPI, consumible por el MES vía HTTP. Para sistemas SCADA con protocolos OPC-UA, implementaría un gateway intermedio que traduzca las lecturas de sensores en JSON. La latencia objetivo es \< 200 ms por predicción para no interrumpir el ciclo de producción. En caso de caída de la API, el sistema vuelve a reglas heurísticas predefinidas (fallback) para no detener la línea."  
* Evidencia a mostrar: Diagrama de arquitectura de integración, documentación de la API (Swagger), prueba de carga con Locust.

#### C. Dimensión de Comunicación y Valor de Negocio (El Impacto)

**7\. ¿Cuánto dinero ahorra o genera tu modelo por cada punto porcentual de mejora en Recall?**

* Respuesta de nivel alto: "En el dataset SECOM, cada punto porcentual de mejora en Recall (detección de defectos) evita \$10,000 USD en scrap no detectado, pero incrementa \$500 USD en inspecciones innecesarias por cada punto de Falsos Positivos. El modelo actual opera en un Recall del 85% con un costo total de \$12,500 USD por lote de 1000 unidades. Optimizar el umbral para alcanzar 90% de Recall reduciría el costo total a \$9,000 USD, un ahorro del 28%."  
* Evidencia a mostrar: Tabla de costos por escenario, gráfico de costo total vs. umbral de clasificación.

**8\. ¿Qué acción concreta debe tomar un operador de planta cuando tu modelo alerta un riesgo, y cómo reduces su carga cognitiva?**

* Respuesta de nivel alto: "El modelo no solo alerta 'Riesgo de defecto: 87%', sino que proporciona un diagnóstico accionable: 'Sensor de temperatura en zona 2 excede 2 desviaciones estándar. Acción recomendada: verificar calibración del termopar y reducir velocidad de línea en 10%'. Esto se logra mediante SHAP values mapeados a variables físicas. El dashboard muestra solo 3 KPIs: riesgo actual, tendencia (últimas 2 horas) y acción recomendada, evitando sobrecargar al operador con información técnica."  
* Evidencia a mostrar: Captura del dashboard Streamlit, ejemplo de alerta con SHAP mapeado, mockup de interfaz de operador.

**9\. ¿Cómo gestionas el cambio y la adopción del modelo por usuarios finales escépticos?**

* Respuesta de nivel alto: "Implementaría un periodo de 'sombra' de 30 días donde el modelo opera en paralelo a las reglas actuales, sin tomar decisiones automáticas. Los operadores comparan las alertas del modelo con sus decisiones y documentan discrepancias. Esto genera confianza y permite ajustar el modelo basado en feedback operativo. Además, capacitaría a los operadores con sesiones de 30 minutos enfocadas en 'cómo interpretar la alerta' y 'qué acción tomar', no en 'cómo funciona el algoritmo'."  
* Evidencia a mostrar: Plan de despliegue en fases, documento de capacitación, métricas de adopción (% de alertas atendidas).

