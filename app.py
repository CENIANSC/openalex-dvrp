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

st.title("Explorador de metadatos")

# Subir archivo Excel (sin encabezado, solo IDs en la columna A)
uploaded_file = st.file_uploader("Sube tu archivo Excel con IDs de OpenAlex (sin encabezado)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=None)
    df.rename(columns={0: "OpenAlex_ID"}, inplace=True)

    st.write("Archivo cargado con", len(df), "IDs")

    metadata = []
    for article_id in df["OpenAlex_ID"]:
        # Asegurar que el ID sea de la API
        if article_id.startswith("https://openalex.org/"):
            identifier = article_id.split("/")[-1]
            api_url = f"https://api.openalex.org/works/{identifier}"
        else:
            api_url = article_id

        r = requests.get(api_url)
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception as e:
                st.error(f"No se pudo decodificar JSON para {api_url}: {e}")
                continue

            # Manejo seguro de campos que pueden ser None
            revista = None
            editorial = None
            primary_location = data.get("primary_location")
            if primary_location:
                source = primary_location.get("source")
                if source:
                    revista = source.get("display_name")
                    editorial = source.get("host_organization_name")

            field = None
            subfield = None
            domain = None
            primary_topic = data.get("primary_topic")
            if primary_topic:
                field = primary_topic.get("field", {}).get("display_name")
                subfield = primary_topic.get("subfield", {}).get("display_name")
                domain = primary_topic.get("domain", {}).get("display_name")

            info = {
                "id": data.get("id"),
                "DOI": data.get("doi"),
                "Título": data.get("title"),
                "Año": data.get("publication_year"),
                "Citado por": data.get("cited_by_count"),
                "Resumen": reconstruir_abstract(data.get("abstract_inverted_index")),
                "Conceptos": "; ".join([c.get("display_name") for c in data.get("concepts", []) if c.get("display_name")]),
                "Temas": "; ".join([t.get("display_name") for t in data.get("topics", []) if t.get("display_name")]),
                "Autores": "; ".join([a.get("author", {}).get("display_name") for a in data.get("authorships", []) if a.get("author")]),
                "Instituciones": "; ".join([inst.get("display_name") for a in data.get("authorships", []) for inst in a.get("institutions", []) if inst.get("display_name")]),
                "Revista": revista,
                "Editorial": editorial,
                "Field": field,
                "Subfield": subfield,
                "Domain": domain,
                "SDGs": "; ".join([sdg.get("display_name") for sdg in data.get("sustainable_development_goals", []) if sdg.get("display_name")]),
                "Funders": "; ".join([f.get("display_name") for f in data.get("funders", []) if f.get("display_name")])
            }
            metadata.append(info)

    meta_df = pd.DataFrame(metadata)

    # Mostrar resultados
    st.write("Resultados procesados:")
    st.dataframe(meta_df)

    # Gráfico de frecuencia de años de publicación
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

