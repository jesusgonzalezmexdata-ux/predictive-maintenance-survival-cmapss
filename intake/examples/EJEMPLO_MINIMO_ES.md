# Analítica de Calidad Industrial

MDA-Intent: true
Tipo-Intención: PROYECTO
Tipo-Proyecto: CIENCIA DE DATOS
Destino: .
Materialización: SCAFFOLD_ONLY

## Visión
Convertir datos de manufactura en evidencia de calidad trazable y reproducible.

## Objetivo
Construir la arquitectura gobernada necesaria para ingerir datos, validarlos, analizarlos y producir resultados verificables.

## Alcance
- Ingesta y validación de datos.
- Ingeniería de características.
- Evaluación de modelos.

## Restricciones
- No almacenar credenciales ni secretos.
- No promover experimentos automáticamente a producción.

## Entregables
- Arquitectura de repositorio gobernada.
- Contratos locales por carpeta.
- Especificación inicial y paquete de trabajo.

## Criterios de aceptación
- El repositorio conserva estado GREENFIELD después del scaffolding.
- Un agente nuevo puede resolver el contrato raíz y local sin instrucciones manuales adicionales.

## No objetivos
- Despliegue automático a producción.
