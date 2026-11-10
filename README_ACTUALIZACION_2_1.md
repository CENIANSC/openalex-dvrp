# OpenAlex-DVRP 2.1

## Instalación en main
1. Conserva una copia ZIP de la versión 2.0.
2. En GitHub rama main, sube los archivos de este paquete reemplazando los existentes. Mantén la estructura de carpetas.
3. Conserva OPENALEX_API_KEY exclusivamente en Secrets de Streamlit Cloud.
4. Espera el redeploy y ejecuta una búsqueda de 200 registros.
5. Revisa las cuatro pestañas nuevas al final de la página.

## Validación local
`pip install -r requirements.txt`
`python -m unittest discover -s tests -v`
`streamlit run app.py`

## Alcance
La auditoría es preliminar, la red usa IDs de OpenAlex y las gráficas se acotan a 40 nodos. Los informes son descriptivos y no sustituyen evaluación metodológica ni revisión crítica. No se incluyen citas bibliográficas formateadas ni gráficos incrustados en los informes.
