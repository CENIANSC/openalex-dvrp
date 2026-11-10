# OpenAlex-DVRP 2.4 — actualización sobre main

## Novedades
- Asistente metodológico: título, pregunta, objetivo y criterios documentales de inclusión y exclusión.
- Selección documental: flujo con resultados identificados, descargados, duplicados y cribado manual; **no equivale por sí solo a PRISMA 2020**.
- Auditoría de cobertura de metadatos, datos faltantes e IDs duplicados.
- Borradores de informe científico en Word y PDF, con campos pendientes explícitos.
- Proyectos portables JSON: guarda/restaura registros, metodología y cifras de selección (máximo 25 MB).
- Corrección de exportación Excel: hoja Metodologia se escribe dentro del contexto ExcelWriter.

## Instalación
Descomprime el ZIP y copia el **contenido** de openalex-dvrp-main a la raíz del repositorio local, conservando la estructura. Revisa los cambios en GitHub Desktop, haz Commit to main y Push origin. Haz antes una copia de seguridad de la versión 2.3.

## Validación
Ejecutar `python -m unittest discover -s tests -q` desde la raíz. Se verificó compilación y 15 pruebas locales. **No se ha comprobado el despliegue real en Streamlit Cloud ni llamadas reales a la API OpenAlex**.

## Precauciones
Los proyectos JSON son archivos locales descargables; Streamlit Cloud no garantiza persistencia entre sesiones. No contienen claves API, pero sí títulos, autores y otros metadatos de las publicaciones. No se realiza automáticamente cribado de elegibilidad, interpretación de resultados ni evaluación de sesgo. El usuario debe revisar los informes antes de publicarlos.
