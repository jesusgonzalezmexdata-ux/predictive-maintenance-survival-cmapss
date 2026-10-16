# MVP «Lista semanal de intervención»: protocolo de piloto

**Para quién:** jefe de mantenimiento o ingeniero de confiabilidad con una familia de al menos 30 equipos iguales: montacargas, compresores, bombas, motores eléctricos, husillos CNC.
**Qué decide:** cada cuánto intervenir cada familia y qué equipos entran al taller esta semana.
**Qué recibe:** el intervalo óptimo por familia con su ahorro anual, la lista de la semana limitada por la capacidad del taller y un reporte de una página.

## 1. Datos que se piden

| Hoja | Obligatorio | Opcional |
|---|---|---|
| `ordenes` (una fila por orden de trabajo) | equipo, fecha, tipo (correctiva / preventiva; acepta variantes como CORR, PM, Falla) | familia del equipo; lectura del horómetro en la orden |
| `equipos` | — | equipo, familia, fecha de alta, horómetro actual |

Mínimo 5 fallas por familia; ideal 20 o más. Con horómetro el análisis usa horas de operación; sin él, días de calendario.

**Lo que más cuesta conseguir:** que cada orden distinga falla de preventivo (ISO 14224). Inspecciones, lubricaciones o ajustes menores que no reemplazan ni reparan no se capturan como orden; el archivo los marca como tipo no reconocido.

## 2. Cómo funciona

1. **Vidas.** Cada intervención inicia una vida nueva. Si la siguiente orden es correctiva, la vida terminó en falla; si es preventiva, se sabe que el equipo duró *al menos* eso (dato censurado). Ignorar las preventivas, o tratarlas como fallas, sesga el resultado; por eso se usa análisis de supervivencia.
2. **Régimen de falla por familia (Weibull).**
   - β > 1 con todo su intervalo de 95 % por encima de 1: desgaste demostrado; el preventivo por edad reduce costo.
   - β ≈ 1: fallas aleatorias; intervenir por calendario no evita fallas. La recomendación es inspección por condición y bajar la frecuencia del preventivo.
3. **Intervalo óptimo.** Con el costo de un preventivo y el de una falla (reparación + paro + urgencia), el modelo clásico de reemplazo por edad da el intervalo que minimiza el costo por hora de operación. Se compara con el intervalo preventivo actual (mediana de las vidas cerradas por preventivo).
4. **Lista de la semana.** Probabilidad de que cada equipo falle en los próximos 7 días dada su edad actual. Los equipos que ya pasaron el intervalo óptimo entran en orden de riesgo hasta llenar la capacidad del taller; el resto queda como «vencido sin capacidad».

## 3. Privacidad

En la demo publicada el archivo se procesa dentro del navegador del usuario y no se envía a ningún servidor. Para el piloto basta con códigos de equipo; no hacen falta nombres de técnicos ni costos reales de proveedores.

## 4. Fases

| Fase | Duración | Actividad | Entregable |
|---|---|---|---|
| 0 · Acuerdo | 1 semana | Exportación de órdenes de 12–36 meses de una familia; responsable de mantenimiento | Archivo con la plantilla llena |
| 1 · Retrospectiva | 1 semana | Reporte sobre el histórico y revisión de los errores de datos con el responsable | Reporte de una página |
| 2 · Sombra | 8 semanas | Cada lunes se entrega la lista; nadie actúa sobre ella; se registran las fallas reales | Captura real de la lista |
| 3 · Acción controlada | 12 semanas | La mitad de los equipos (al azar) sigue el intervalo óptimo; la otra mitad, el actual | Costo por 1,000 h de ambos grupos |
| 4 · Cierre | 1 semana | Actualizar plan de mantenimiento y caso de estudio | Caso publicable con autorización |

## 5. Criterios definidos antes de empezar

**Pasa de fase 1 a 2 si:**
- la familia tiene desgaste demostrado (β > 1 con intervalo), y
- en la retrospectiva la lista anticipa más fallas que elegir los mismos equipos al azar.

**Éxito en fase 2:** al menos la mitad de las fallas de la sombra estaban en la lista de esa semana o en la de «vencidos».
**Éxito en fase 3:** menor costo por 1,000 h en el grupo con intervalo óptimo, sin más fallas en servicio.

**Abandono:**
- menos de 10 fallas en la familia;
- las órdenes no distinguen correctivo de preventivo;
- la retrospectiva no supera al azar.

Si la familia resulta con β ≈ 1, el resultado no es un fracaso: muestra que el preventivo por calendario no le sirve y libera horas de taller.

## 6. Supuestos y límites

- **Cada orden deja el equipo como nuevo.** Si las reparaciones son parciales, la edad real es mayor y el intervalo óptimo, más corto.
- **Sin sensores**, el modelo ordena por edad dentro de cada familia. La versión con lecturas de condición (vibración, temperatura, corriente) usa el modelo *landmark* del repositorio y ordena mejor dentro de la familia.
- **Fecha de alta:** solo se usa si el equipo entró en servicio dentro del periodo registrado; si es anterior, pudo tener intervenciones que no están en el archivo.

## 7. Referencias

| Requisito | Cómo se atiende |
|---|---|
| ISO 9001 · 7.1.3 Infraestructura | Mantenimiento planificado con base en el desempeño del equipo |
| IATF 16949 · 8.5.1.5 Mantenimiento productivo total | Frecuencia del preventivo basada en datos y en costo |
| ISO 14224 | Cada orden distingue falla de preventivo; esto es lo que hace usable el histórico |
| ISO 55001 · 6.2 | Decisión por costo de ciclo de vida del activo |
