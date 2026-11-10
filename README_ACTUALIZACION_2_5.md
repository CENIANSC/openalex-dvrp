# OpenAlex-DVRP 2.5 · Institutional Edition

Actualización visual construida sobre el ZIP más reciente de la versión 2.4.

## Cambios

- Encabezado institucional con autor, programa y universidad.
- Menú lateral de acceso rápido a las secciones de trabajo.
- Panel de resultados y métricas con estilo visual consistente.
- Tarjetas, formularios y pestañas con espaciado y colores unificados.
- Tema oficial de Streamlit en `.streamlit/config.toml`.
- Módulo aislado de interfaz `core/ui.py` para futuras personalizaciones.

## Importante

No se cambiaron los algoritmos de búsqueda, análisis bibliométrico, redes ni generación de informes. Los enlaces del menú lateral son accesos rápidos a secciones de una sola página; no reemplazan el estado de sesión ni la navegación entre páginas. Los datos mostrados dependen de la consulta real de cada usuario.

## Instalación en `main`

1. Haz respaldo de la versión 2.4.
2. Copia el **contenido** de este ZIP en la carpeta local clonada con GitHub Desktop.
3. Verifica que `.streamlit/config.toml`, `core/ui.py` y `app.py` estén en las rutas correctas.
4. Haz `Commit to main` y `Push origin`.
5. Verifica una búsqueda y la descarga de Excel, Word y PDF en Streamlit Cloud.

No incluyas claves de API en GitHub. Conserva `OPENALEX_API_KEY` en los Secrets de Streamlit Cloud.
