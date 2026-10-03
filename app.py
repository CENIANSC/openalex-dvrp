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

    # Ajustar índice para que empiece en 1
    meta_df.index = meta_df.index + 1
    meta_df.index.name = "Artículo"

    st.write("Total de artículos encontrados:", len(meta_df))
    st.dataframe(meta_df)

    # Gráfico de frecuencia de años
    st.subheader("Frecuencia de año de publicación")
    if not meta_df["Year"].isnull().all():
        plt.figure(figsize=(8,4))
        sns.countplot(x="Year", data=meta_df, order=meta_df["Year"].value_counts().index)
        plt.xticks(rotation=45)
        st.pyplot(plt)

    # Nube de palabras de conceptos
    st.subheader("Nube de palabras de Conceptos")
    all_concepts = " ".join(meta_df["Concepts"].dropna())
    if all_concepts.strip():
        wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_concepts)
        plt.figure(figsize=(10,5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        st.pyplot(plt)

    # 🔹 1. Distribución por revista
    st.subheader("Revistas más frecuentes")
    if not meta_df["Journal"].isnull().all():
       top_journals = meta_df["Journal"].value_counts().head(10)
       plt.figure(figsize=(8,4))
       sns.barplot(x=top_journals.values, y=top_journals.index, palette="crest")
       plt.xlabel("Número de artículos")
       plt.ylabel("Revista")
       st.pyplot(plt)

    # 🔹 2. Gráfico de dispersión (impacto vs. año)
    st.subheader("Relación entre citas y año de publicación")
    if not meta_df["Year"].isnull().all() and not meta_df["Cited by"].isnull().all():
       plt.figure(figsize=(8,4))
       sns.scatterplot(x="Year", y="Cited by", data=meta_df, hue="Year", palette="viridis", alpha=0.7)
       plt.title("Impacto de publicaciones por año")
       st.pyplot(plt)

    # 🔹 3. Treemap de conceptos (optimizado para evitar empalmes)
    import squarify
    st.subheader("Treemap de conceptos más frecuentes")

    concept_counts = meta_df["Concepts"].str.split("; ").explode().value_counts().head(20)
    if not concept_counts.empty:
        labels = [
            f"{name[:25]}...\n({count})" if len(name) > 25 else f"{name}\n({count})"
            for name, count in zip(concept_counts.index, concept_counts.values)
        ]
        plt.figure(figsize=(12,7))
        squarify.plot(sizes=concept_counts.values, label=labels, alpha=0.8, text_kwargs={'fontsize':8})
        plt.axis("off")
        st.pyplot(plt)
    else:
        st.info("No hay suficientes conceptos para generar el treemap.")


    # 🔹 4. Heatmap de coocurrencia de conceptos
    st.subheader("Coocurrencia de conceptos")
    from itertools import combinations
    concept_pairs = []
    for concepts in meta_df["Concepts"].dropna():
         items = [c.strip() for c in concepts.split(";") if c.strip()]
         for pair in combinations(items, 2):
             concept_pairs.append(tuple(sorted(pair)))

    if concept_pairs:
       pair_df = pd.DataFrame(concept_pairs, columns=["Concept1", "Concept2"])
       pair_counts = pair_df.value_counts().reset_index(name="Count")
       heatmap_df = pair_counts.pivot_table(index="Concept1", columns="Concept2", values="Count", fill_value=0)

       plt.figure(figsize=(10,8))
       sns.heatmap(heatmap_df, cmap="YlGnBu")
       st.pyplot(plt)
    else:
        st.info("No hay suficientes conceptos para generar el heatmap.")

    # 🔹 5. Mapa de colaboración institucional (mejorado con centralidad y etiquetas)
    st.subheader("Mapa de colaboración institucional")
    import networkx as nx

    G = nx.Graph()
    for institutions in meta_df["Institutions"].dropna():
        inst_list = [i.strip() for i in institutions.split(";") if i.strip()]
        for pair in combinations(inst_list, 2):
            G.add_edge(*pair)

    if G.number_of_nodes() > 0:
        # Calcular centralidad de grado (número de conexiones de cada institución)
        degree_centrality = nx.degree_centrality(G)

        plt.figure(figsize=(12,8))
        pos = nx.spring_layout(G, k=0.5)

        # Dibujar nodos con tamaño proporcional a su centralidad
        nx.draw_networkx_nodes(
            G, pos,
            node_size=[v*800 for v in degree_centrality.values()],
            alpha=0.7
        )
        nx.draw_networkx_edges(G, pos, alpha=0.3)

        # Etiquetas de instituciones (pequeñas para evitar empalmes)
        nx.draw_networkx_labels(G, pos, font_size=6)

        plt.title("Mapa de colaboración institucional (tamaño = centralidad)")
        st.pyplot(plt)

        # Resumen textual complementario
        st.write(f"Instituciones representadas: {G.number_of_nodes()}")
        st.write(f"Colaboraciones detectadas: {G.number_of_edges()}")
        # Mostrar la institución más conectada
        top_inst = max(degree_centrality, key=degree_centrality.get)
        st.write(f"La institución más conectada es: **{top_inst}**")
    else:
        st.info("No hay suficientes instituciones para generar el mapa.")


    # Botón para descargar Excel
    output_file = "openalex_metadata.xlsx"
    meta_df.to_excel(output_file, index=False)
    with open(output_file, "rb") as f:
        st.download_button("Descargar Excel", f, file_name=output_file)
