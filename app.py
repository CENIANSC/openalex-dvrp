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
                "Año": data.get("publication_year
