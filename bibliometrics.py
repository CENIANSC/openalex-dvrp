import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx

from itertools import combinations


def mostrar_indicadores(meta_df):

    st.subheader("Indicadores bibliométricos")

    total_articles = len(meta_df)

    total_citations = (
        meta_df["Cited by"]
        .fillna(0)
        .sum()
    )

    avg_citations = (
        meta_df["Cited by"]
        .fillna(0)
        .mean()
    )

    max_citations = (
        meta_df["Cited by"]
        .fillna(0)
        .max()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Artículos", f"{total_articles:,}")
    col2.metric("Citaciones", f"{int(total_citations):,}")
    col3.metric("Promedio citas", round(avg_citations, 2))
    col4.metric("Máximo citas", int(max_citations))


def mostrar_h_index(meta_df):

    st.subheader("Índice H")

    citations = sorted(
        meta_df["Cited by"]
        .fillna(0)
        .astype(int),
        reverse=True
    )

    h_index = 0

    for i, c in enumerate(citations, start=1):

        if c >= i:
            h_index = i
        else:
            break

    st.metric("Índice H", h_index)


def mostrar_top_autores(meta_df):

    st.subheader("Autores más productivos")

    authors_series = (
        meta_df["Authors"]
        .dropna()
        .str.split("; ")
        .explode()
    )

    top_authors = authors_series.value_counts().head(20)

    if top_authors.empty:
        return

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=top_authors.values,
        y=top_authors.index,
        palette="viridis"
    )

    plt.xlabel("Artículos")
    plt.ylabel("Autor")

    st.pyplot(plt)


def mostrar_top_instituciones(meta_df):

    st.subheader("Instituciones más productivas")

    institution_series = (
        meta_df["Institutions"]
        .dropna()
        .str.split("; ")
        .explode()
    )

    top_institutions = (
        institution_series
        .value_counts()
        .head(20)
    )

    if top_institutions.empty:
        return

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=top_institutions.values,
        y=top_institutions.index,
        palette="magma"
    )

    plt.xlabel("Artículos")
    plt.ylabel("Institución")

    st.pyplot(plt)


def mostrar_top_paises(meta_df):

    if "Countries" not in meta_df.columns:
        return

    st.subheader("Países más productivos")

    countries_series = (
        meta_df["Countries"]
        .dropna()
        .str.split("; ")
        .explode()
    )

    top_countries = (
        countries_series
        .value_counts()
        .head(20)
    )

    if top_countries.empty:
        return

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=top_countries.values,
        y=top_countries.index,
        palette="cubehelix"
    )

    plt.xlabel("Artículos")
    plt.ylabel("País")

    st.pyplot(plt)


def mostrar_top_citados(meta_df):

    st.subheader("Top 20 artículos más citados")

    top_cited = (
        meta_df
        .sort_values(
            "Cited by",
            ascending=False
        )
        .head(20)
    )

    st.dataframe(
        top_cited[
            [
                "Título",
                "Year",
                "Journal",
                "Cited by",
                "DOI"
            ]
        ]
    )


def mostrar_red_coautoria(meta_df):

    st.subheader("Red de coautoría")

    graph = nx.Graph()

    for authors in meta_df["Authors"].dropna():

        author_list = [
            a.strip()
            for a in authors.split(";")
            if a.strip()
        ]

        for pair in combinations(author_list, 2):
            graph.add_edge(*pair)

    if graph.number_of_nodes() == 0:

        st.info(
            "No hay suficientes autores."
        )

        return

    centrality = nx.degree_centrality(graph)

    plt.figure(figsize=(14, 10))

    pos = nx.spring_layout(
        graph,
        seed=42
    )

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=[
            max(v * 1200, 50)
            for v in centrality.values()
        ],
        alpha=0.7
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        alpha=0.3
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=6
    )

    plt.title(
        "Red de colaboración entre autores"
    )

    st.pyplot(plt)


def mostrar_temas_emergentes(meta_df):

    st.subheader("Temas emergentes")

    topic_records = []

    for _, row in meta_df.iterrows():

        year = row["Year"]

        if pd.isna(year):
            continue

        topics = str(
            row["Themes"]
        ).split(";")

        for topic in topics:

            topic = topic.strip()

            if topic:

                topic_records.append(
                    [year, topic]
                )

    topics_df = pd.DataFrame(
        topic_records,
        columns=[
            "Year",
            "Topic"
        ]
    )

    if topics_df.empty:
        return

    latest_years = sorted(
        topics_df["Year"].unique()
    )[-3:]

    emergent_topics = (
        topics_df[
            topics_df["Year"].isin(
                latest_years
            )
        ]["Topic"]
        .value_counts()
        .head(15)
    )

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=emergent_topics.values,
        y=emergent_topics.index,
        palette="rocket"
    )

    plt.xlabel("Frecuencia reciente")
    plt.ylabel("Tema")

    st.pyplot(plt)
