# SPEC-003 — Mantenimiento por condición e impacto medido

Status: ACTIVE (OWNER, chat 2026-10-08 — "ejecuta estos tres pasos")
Derived from: INTENT-446E2407EF97 + revisión de portafolio 2026-10-08
Depends on: SPEC-001 (baseline), SPEC-002 (DoD), TASK-007 (sin fuga)

## Problema que resuelve

SPEC-001/002 entregan un baseline correcto pero sin impacto demostrable:

1. La app no arrancaba (`NameError`) y el CI estaba en rojo.
2. El tiempo de intervención t* sale de una Weibull de flota: el modelo por activo no cambia la decisión.
3. La concordancia contra RUL real en prueba era 0.46 (señal de los primeros 20 ciclos).
4. No existía una cifra de negocio: cuánto cuesta cada política.

## Entregables (MUST)

1. **TASK-009 — saneamiento:** app ejecutable con prueba de humo; CI de producto (ruff + pytest); LICENSE MIT.
2. **TASK-010 — núcleo científico:**
   - Modelo *landmark*: en cada inspección `c`, rasgos con ciclos ≤ c (media y pendiente en ventana de 20 ciclos + edad), objetivo vida residual `T − c`; Weibull AFT ponderado 1/n por motor.
   - Validación cruzada agrupada repetida (5 × 5) sobre los 100 motores run-to-failure; Brier fuera de pliegue frente a tasa base; calibración por deciles.
   - Líneas base en el conjunto de prueba oficial: solo edad (población) y ventana temprana (SPEC-001), con IC 95 % bootstrap.
   - Corrección de Holm de las pruebas de Schoenfeld de SPEC-001 (se reportan ambas lecturas; la regla de SPEC-001 no cambia).
   - Backtest renewal-reward fuera de pliegue de cuatro políticas (dejar fallar, edad t*, condición, oráculo) para C_f/C_p ∈ {2, 3, 5, 10, 20, 50}; umbral de la política por condición ajustado con CV interna sobre motores de entrenamiento.
3. **TASK-011 — comunicación:** app con modo demo sobre artefactos derivados (sin redistribuir datos NASA), comparación de políticas y lista de motores a intervenir; figuras; README con resultados e IC; resumen en inglés; notebook narrado.

## Reglas

- Ninguna cifra se escribe a mano: todo sale de `python -m pm_survival study`.
- El horizonte de decisión (P(falla en ≤ 10 ciclos)) y la ventana (20) se fijan antes de ver resultados.
- El modelo no se presenta como producción; los costos son ilustrativos.
- Dependencias nuevas solo de desarrollo/CI (`requirements-dev.txt`: pytest, ruff, matplotlib).

## Non-goals

FD002–FD004, despliegue en planta, integración MES/SCADA, publicación de la URL (OWNER).
