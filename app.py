import streamlit as st
import pandas as pd
import requests

st.title("Revisión de artículos con OpenAlex")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel con IDs de OpenAlex", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Archivo cargado con", len(df), "IDs")

    metadata = []
    for article_id in df["OpenAlex_ID"]:
        r = requests.get(article_id)
        if r.status_code == 200:
            data = r.json()
            metadata.append({
                "id": article_id,
                "title": data.get("title"),
                "year": data.get("publication_year"),
                "type": data.get("type"),
                "is_oa": data.get("open_access", {}).get("is_oa", False)
            })

    meta_df = pd.DataFrame(metadata)

    # Descargar resultado
    st.write("Resultados procesados:")
    st.dataframe(meta_df)

    # Botón para descargar Excel
    output_file = "openalex_metadata.xlsx"
    meta_df.to_excel(output_file, index=False)
    with open(output_file, "rb") as f:
        st.download_button("Descargar Excel", f, file_name=output_file)
