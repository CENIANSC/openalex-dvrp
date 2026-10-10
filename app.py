import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

from modules.indicators import (
    mostrar_indicadores,
    mostrar_indice_h,
    mostrar_articulos_mas_citados
)

from modules.authors import (
    mostrar_top_autores,
    mostrar_red_coautoria
)

from modules.institutions import (
    mostrar_top_instituciones,
    mostrar_top_paises
)

from modules.concepts import (
    mostrar_nube_conceptos,
    mostrar_treemap_conceptos,
    mostrar_concurrencia_conceptos
)

from modules.journals import (
    mostrar_revistas_frecuentes,
    mostrar_publicaciones_por_anio,
    mostrar_impacto_por_anio
)

from modules.topics import (
    mostrar_temas_emergentes,
    mostrar_temas_frecuentes
)

from modules.networks import (
    mostrar_metricas_red_institucional
)


# Función auxiliar para reconstruir el abstract
def reconstruir_abstract(abstract_inverted_index):
    if not abstract_inverted_index:
        return ""
    words = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            if len(words) <= pos:
                words.extend([""] * (pos - len(words) + 1))
            words[pos] = word
    return " ".join(words)

st.markdown(
    """
    <h1 style='text-align: center; margin-bottom: 0;'>Explorador de metadatos en OpenAlex</h1>
    <p style='text-align: center; font-size:14px; margin-top: 0;'>
    Desarrollado por: Daniel A. Aguirre Ibarra<br>
    Doctorado en Logística y Dirección de la Cadena de Suministro<br>
    UPAEP
    </p>
    """,
    unsafe_allow_html=True
)


# Entrada de búsqueda y rango de años
search_query = st.text_input("Término de búsqueda (en título y abstract)", "")
start_year = st.number_input("Año inicial", min_value=1900, max_value=2100, value=None, step=1, format="%d")
end_year = st.number_input("Año final", min_value=1900, max_value=2100, value=None, step=1, format="%d")


if st.button("Buscar artículos"):
    base_url = "https://api.openalex.org/works"
    headers = {"Authorization": "Bearer 2yBYOdo5vQTH51W9k0dCEI"}
    params = {
        "sort": "relevance_score:desc",
        "filter": f"open_access.is_oa:true,primary_topic.id:t10567,type:article,has_content.pdf:true,publication_year:{start_year}-{end_year}",
        "search.title_and_abstract": search_query,
        "per_page": 200,
        "cursor": "*"
    }

    ids = []
    metadata = []

    while True:
        r = requests.get(base_url, params=params, headers=headers)
        if r.status_code != 200:
            st.error(f"Error {r.status_code}: {r.text}")
            break

        try:
            data = r.json()
        except Exception as e:
            st.error(f"No se pudo decodificar JSON: {e}")
            st.text(r.text)
            break

        for work in data.get("results", []):
            ids.append(work["id"])

            # Manejo seguro de campos
            revista = None
            editorial = None
            primary_location = work.get("primary_location")
            if primary_location:
                source = primary_location.get("source")
                if source:
                    revista = source.get("display_name")
                    editorial = source.get("host_organization_name")

            info = {
                "Year": work.get("publication_year"),
                "Título": work.get("title"),
                "Journal": revista,
                "Authors": "; ".join([a.get("author", {}).get("display_name") for a in work.get("authorships", []) if a.get("author")]),
                "Institutions": "; ".join([
                    inst.get("display_name")
                    for a in work.get("authorships", [])
                    for inst in a.get("institutions", [])
                    if inst.get("display_name")
                ]),
                "Countries": "; ".join(
                    set(
                       c
                       for a in work.get("authorships", [])
                       for c in a.get("countries", [])
                       )
                ),
                "Editorial": editorial,                
                "Abstract": reconstruir_abstract(work.get("abstract_inverted_index")),
                "Concepts": "; ".join([c.get("display_name") for c in work.get("concepts", []) if c.get("display_name")]),
                "Themes": "; ".join([t.get("display_name") for t in work.get("topics", []) if t.get("display_name")]),
                "SDGs": "; ".join([sdg.get("display_name") for sdg in work.get("sustainable_development_goals", []) if sdg.get("display_name")]),
                "Funders": "; ".join([f.get("display_name") for f in work.get("funders", []) if f.get("display_name")]),
                "Cited by": work.get("cited_by_count"),
                "DOI": work.get("doi"),
            }
            metadata.append(info)

        next_cursor = data["meta"].get("next_cursor")
        if next_cursor:
            params["cursor"] = next_cursor
        else:
            break

    meta_df = pd.DataFrame(metadata)

    if meta_df.empty:
        st.warning("No se encontraron artículos para los criterios de búsqueda.")
    else:
        # Ajustar índice para que empiece en 1
        meta_df.index = meta_df.index + 1
        meta_df.index.name = "Artículo"

        st.write("Total de artículos encontrados:", len(meta_df))
        st.dataframe(meta_df)







    
        mostrar_publicaciones_por_anio(meta_df)
        mostrar_revistas_frecuentes(meta_df)
        mostrar_impacto_por_anio(meta_df)
        mostrar_indicadores(meta_df)
        mostrar_indice_h(meta_df)
        mostrar_articulos_mas_citados(meta_df)
        mostrar_top_autores(meta_df)
        mostrar_top_instituciones(meta_df)
        mostrar_top_paises(meta_df)
        mostrar_red_coautoria(meta_df)
        mostrar_temas_frecuentes(meta_df)
        mostrar_temas_emergentes(meta_df)
        mostrar_nube_conceptos(meta_df)
        mostrar_treemap_conceptos(meta_df)
        mostrar_concurrencia_conceptos(meta_df)
        mostrar_metricas_red_institucional(meta_df)
        
        
        # Botón para descargar Excel
        output_file = "openalex_metadata.xlsx"
        meta_df.to_excel(output_file, index=False)
        with open(output_file, "rb") as f:
            st.download_button("Descargar Excel", f, file_name=output_file)
