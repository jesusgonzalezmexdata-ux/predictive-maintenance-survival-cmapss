# Taxonomía de desgaste L2 ↔ NASA C-MAPSS

Status: DOCUMENTO DE EVIDENCIA (SPEC-002)  
Dataset ancla: **NASA C-MAPSS Turbofan Engine Degradation** (público, PHM / Saxena et al.)  
Regla: C-MAPSS **no** etiqueta “L2”. L2 es el marco de negocio del portafolio (desgaste del componente crítico / etapa limitante de vida). Aquí se declara el **mapeo explícito** de modos L2 a proxies medibles en el dataset.

## 1. Qué es L2 en este proyecto

| Concepto | Definición operativa |
|----------|----------------------|
| **Activo** | Una unidad turbofan (`unit_id`) en C-MAPSS FD001 |
| **Evento de falla L2** | Fin de la trayectoria run-to-failure en train (`event = 1` en el último ciclo). En test, la unidad está **censurada** (`event = 0`): sigue “operando” al corte de observación |
| **Desgaste L2** | Degradación progresiva que acelera el riesgo de llegar al evento (régimen Weibull wear-out, β > 1) |

## 2. Modos de falla L2 (taxonomía)

| Código | Modo | Descripción de negocio | Evidencia física en turbofan |
|--------|------|------------------------|------------------------------|
| L2-T | Desgaste térmico / fatiga térmica | Calentamiento excesivo acelera el fin de vida | Temperaturas de gas / metal en etapas HPC–LPT |
| L2-P | Pérdida de eficiencia de presión | Compresión degradada → más esfuerzo para misma potencia | Relación de presiones / flujo |
| L2-N | Desgaste mecánico de rotación | Desbalance o fricción en ejes / ventilador | Velocidades de eje (Nf, Nc) |
| L2-F | Deriva de flujo / consumo | Cambio de margen de operación | Fuel flow, bypass, ratios de flujo |
| L2-O | Régimen operativo agresivo | Condiciones de vuelo que aceleran el desgaste | `op_setting_1..3` (altitud, Mach, throttle) |

## 3. Mapeo a columnas C-MAPSS (FD001)

Convención de columnas del loader: `sensor_1` … `sensor_21`, `op_setting_1` … `op_setting_3`  
(nombres físicos estándar de la literatura C-MAPSS / Damage Propagation Modeling)

| Columna | Señal física (referencia) | Modo(s) L2 |
|---------|---------------------------|------------|
| `op_setting_1` | Altitud | L2-O |
| `op_setting_2` | Número de Mach | L2-O |
| `op_setting_3` | Throttle resolver angle | L2-O |
| `sensor_1` | T2 — temp. entrada fan | L2-T |
| `sensor_2` | T24 — temp. salida LPC | L2-T |
| `sensor_3` | T30 — temp. salida HPC | L2-T |
| `sensor_4` | T50 — temp. salida LPT | L2-T |
| `sensor_5` | P2 — presión entrada fan | L2-P |
| `sensor_6` | P15 — presión bypass | L2-P |
| `sensor_7` | P30 — presión salida HPC | L2-P |
| `sensor_8` | Nf — velocidad fan | L2-N |
| `sensor_9` | Nc — velocidad core | L2-N |
| `sensor_10` | epr — engine pressure ratio | L2-P |
| `sensor_11` | Ps30 — presión estática HPC | L2-P |
| `sensor_12` | phi — ratio fuel flow | L2-F |
| `sensor_13` | NRf — velocidad fan corregida | L2-N |
| `sensor_14` | NRc — velocidad core corregida | L2-N |
| `sensor_15` | BPR — bypass ratio | L2-F |
| `sensor_16` | farB — bleed enabler | L2-F |
| `sensor_17` | htBleed — bleed enthalpy | L2-T / L2-F |
| `sensor_18` | Nf_dmd — demanda fan | L2-O / L2-N |
| `sensor_19` | PCNfR_dmd — demanda corrección | L2-O / L2-N |
| `sensor_20` | W31 — coolant bleed | L2-F |
| `sensor_21` | W32 — HPT coolant bleed | L2-F |

## 4. Features del modelo y taxonomía

El baseline usa medias y pendientes **solo en la ventana temprana** (`early_window`, TASK-007):

| Feature | Lectura de negocio |
|---------|-------------------|
| `sensor_*_early` | Nivel medio del sensor en los primeros ciclos (estado inicial del activo) |
| `sensor_*_slope` | Ritmo de cambio **temprano** del sensor (aceleración del desgaste L2 sin mirar el futuro) |
| `op_setting_*_*` | Régimen operativo (L2-O) |

## 5. Lo que este mapeo no afirma

- No afirma que C-MAPSS mida una pieza llamada “L2”.
- No sustituye una FMEA de planta real.
- No convierte el baseline en certificación aeronáutica.

Es el puente explícito entre el lenguaje de portafolio (desgaste L2) y el dataset público reconocido (NASA C-MAPSS).
