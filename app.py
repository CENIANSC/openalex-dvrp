import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

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

st.title("Explorador de metadatos en OpenAlex")

# Entrada de búsqueda y rango de años
search_query = st.text_input("Término de búsqueda (en título y abstract)", "dynamic vehicle routing problem")
start_year = st.number_input("Año inicial", min_value=1900, max_value=2100, value=2020)
end_year = st.number_input("Año final", min_value=1900, max_value=2100, value=2025)

if st.button("Buscar artículos"):
    base_url = "https://api.openalex.org/works"
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
        r = requests.get(base_url, params=params)
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

            field = None
            subfield = None
            domain = None
            primary_topic = work.get("primary_topic")
            if primary_topic:
                field = primary_topic.get("field", {}).get("display_name")
                subfield = primary_topic.get("subfield", {}).get("display_name")
                domain = primary_topic.get("domain", {}).get("display_name")

            info = {
                "id": work.get("id"),
                "DOI": work.get("doi"),
                "Título": work.get("title"),
                "Año": work.get("publication_year"),
                "Citado por": work.get("cited_by_count"),
                "Resumen": reconstruir_abstract(work.get("abstract_inverted_index")),
                "Conceptos": "; ".join([c.get("display_name") for c in work.get("concepts", []) if c.get("display_name")]),
                "Temas": "; ".join([t.get("display_name") for t in work.get("topics", []) if t.get("display_name")]),
                "Autores": "; ".join([a.get("author", {}).get("display_name") for a in work.get("authorships", []) if a.get("author")]),
                "Instituciones": "; ".join([
                    inst.get("display_name")
                    for a in work.get("authorships", [])
                    for inst in a.get("institutions", [])
                    if inst.get("display_name")
                ]),
                "Revista": revista,
                "Editorial": editorial,
                "Field": field,
                "Subfield": subfield,
                "Domain": domain,
                "SDGs": "; ".join([sdg.get("display_name") for sdg in work.get("sustainable_development_goals", []) if sdg.get("display_name")]),
                "Funders": "; ".join([f.get("display_name") for f in work.get("funders", []) if f.get("display_name")])
            }
            metadata.append(info)

        next_cursor = data["meta"].get("next_cursor")
        if next_cursor:
            params["cursor"] = next_cursor
        else:
            break

    meta_df = pd.DataFrame(metadata)

    st.write("Total de artículos encontrados:", len(meta_df))
    st.dataframe(meta_df)

    # Gráfico de frecuencia de años
    st.subheader("Frecuencia de año de publicación")
    if not meta_df["Año"].isnull().all():
        plt.figure(figsize=(8,4))
        sns.countplot(x="Año", data=meta_df, order=meta_df["Año"].value_counts().index)
        plt.xticks(rotation=45)
        st.pyplot(plt)

    # Nube de palabras de conceptos
    st.subheader("Nube de palabras de Conceptos")
    all_concepts = " ".join(meta_df["Conceptos"].dropna())
    if all_concepts.strip():
        wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_concepts)
        plt.figure(figsize=(10,5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        st.pyplot(plt)

    # Botón para descargar Excel
    output_file = "openalex_metadata.xlsx"
    meta_df.to_excel(output_file, index=False)
    with open(output_file, "rb") as f:
        st.download_button("Descargar Excel", f, file_name=output_file)
