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

# Subir archivo Excel (sin encabezado, solo IDs en la columna A)
uploaded_file = st.file_uploader("Sube tu archivo Excel con IDs de OpenAlex (sin encabezado)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=None)
    df.rename(columns={0: "OpenAlex_ID"}, inplace=True)

    st.write("Archivo cargado con", len(df), "IDs")

    metadata = []
    for article_id in df["OpenAlex_ID"]:
        r = requests.get(article_id)
        if r.status_code == 200:
            data = r.json()
            info = {
                "id": data.get("id"),
                "DOI": data.get("doi"),
                "Título": data.get("title"),
                "Año": data.get("publication_year"),
                "Citado por": data.get("cited_by_count"),
                "Resumen": reconstruir_abstract(data.get("abstract_inverted_index")),
                "Conceptos": "; ".join([c["display_name"] for c in data.get("concepts", [])]),
                "Temas": "; ".join([t["display_name"] for t in data.get("topics", [])]),
                "Autores": "; ".join([a["author"]["display_name"] for a in data.get("authorships", [])]),
                "Instituciones": "; ".join([a["institutions"][0]["display_name"]
                                            for a in data.get("authorships", []) if a.get("institutions")]),
                "Revista": data.get("primary_location", {}).get("source", {}).get("display_name"),
                "Editorial": data.get("primary_location", {}).get("source", {}).get("host_organization_name"),
                "Field": data.get("primary_topic", {}).get("field", {}).get("display_name"),
                "Subfield": data.get("primary_topic", {}).get("subfield", {}).get("display_name"),
                "Domain": data.get("primary_topic", {}).get("domain", {}).get("display_name"),
                "SDGs": "; ".join([sdg["display_name"] for sdg in data.get("sustainable_development_goals", [])]),
                "Funders": "; ".join([f["display_name"] for f in data.get("funders", [])])
            }
            metadata.append(info)

    meta_df = pd.DataFrame(metadata)

    # Mostrar resultados
    st.write("Resultados procesados:")
    st.dataframe(meta_df)

    # Gráfico de frecuencia de años de publicación
    st.subheader("Frecuencia de año de publicación")
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
