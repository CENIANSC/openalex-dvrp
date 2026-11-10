# OpenAlex-DVRP 2.3 — actualización directa en main

Este paquete parte del ZIP de `main` entregado por el usuario. Mantiene los módulos de 2.2 y añade una sección de inteligencia científica.

## Cambios

1. Mapas de coocurrencia de **temas clasificados por OpenAlex**, comunidades y exportación de nodos/aristas.
2. Evolución de temas por periodos, gráfica de áreas y variación reciente de proporciones.
3. Acoplamiento bibliográfico, citación directa interna y cocitación de referencias, con CSV y figuras.
4. Mapa estratégico exploratorio de comunidades (centralidad externa y densidad interna). **No son índices de Callon**; el cuadrante inferior izquierdo no distingue emergencia de declive.
5. Informe científico ampliado Word/PDF y descarga de figuras PNG/SVG.

## Actualizar

1. Conserva una copia de tu proyecto 2.2 y del ZIP original.
2. Descomprime este paquete y copia **el contenido de la carpeta `openalex-dvrp-main`** en la carpeta local clonada del repositorio (GitHub Desktop > Repository > Show in Explorer).
3. Revisa que `app.py`, `analysis/science_mapping.py`, `reports/science_report.py` y `tests/test_v23.py` estén en las rutas correctas.
4. En GitHub Desktop haz Commit to main y Push origin.
5. Comprueba el despliegue en Streamlit Cloud y realiza una **búsqueda nueva** para obtener las referencias bibliográficas; los resultados anteriores en sesión no contienen la columna `Referenced works`.

## Límites de interpretación

- Todas las métricas se calculan sobre el subconjunto descargado; un límite de registros puede sesgar las redes.
- Los temas son etiquetas OpenAlex, **no palabras clave de autor**.
- Las tendencias son diferencias descriptivas de proporciones, no predicciones.
- Las redes de referencias usan como máximo 300 documentos; la cocitación usa 100 documentos y hasta 50 referencias por documento para evitar bloqueos de memoria.
- La citación directa solo muestra conexiones entre documentos incluidos en el subconjunto.
- Los PDF y Word son borradores de informe para revisión académica, no manuscritos listos para publicación.

## Pruebas locales

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py analysis core modules reports
```

No se ha verificado aquí una consulta en vivo a OpenAlex ni un despliegue en Streamlit Cloud. Tu `OPENALEX_API_KEY` permanece en los Secrets de Streamlit; nunca debe subirse al repositorio.
