# OpenAlex-DVRP 2.2 — actualización de main

## Instalación
1. Conservar una copia de seguridad de la versión 2.1.
2. Descomprimir este ZIP y copiar **su contenido** en la raíz del repositorio clonado con GitHub Desktop. Conservar la estructura de carpetas.
3. Revisar cambios en GitHub Desktop, `Commit to main` y `Push origin`.
4. Streamlit Cloud desplegará la rama `main`. No incluir ni publicar la API key; conservar `OPENALEX_API_KEY` en Streamlit Secrets.

## Funciones
- Explorador de temas OpenAlex: nombre, ID, campo, subcampo y volumen de publicaciones.
- Constructor de filtros: búsqueda por texto opcional si se selecciona un tema, varios temas con OR, coincidencia por tema principal o cualquier tema, años, tipo, país, institución, OA y PDF.
- Comparación descriptiva por periodos y entidades y conteo de colaboración internacional.
- Informes Word/PDF Unicode con estrategia, indicadores, evolución, comparación y limitaciones.
- Exportación CSV, Excel y manifiesto JSON con fecha UTC y SHA-256 de IDs.

## Advertencias metodológicas
- OpenAlex puede reportar más resultados de los descargados: las estadísticas solo corresponden al subconjunto descargado.
- Varios temas se combinan con OR; los filtros distintos se combinan con AND.
- El buscador de temas consulta la API en vivo y requiere una clave válida.
- Los indicadores de citas no están normalizados por campo ni edad del documento.
- El PDF utiliza DejaVu Sans (fuente distribuida en `assets/`) para los caracteres acentuados.
- Los informes son descriptivos, no manuscritos listos para publicación.
- La huella SHA-256 permite verificar IDs descargados; no certifica que OpenAlex conserve resultados idénticos en el futuro.

## Pruebas
`python -m unittest discover -s tests -v`

No se realizaron pruebas de conexión real con la API de OpenAlex ni despliegue real en Streamlit Cloud en este entorno.
