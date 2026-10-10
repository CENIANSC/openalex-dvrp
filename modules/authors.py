# modules/authors.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx

from itertools import combinations


def mostrar_top_autores(meta_df):

    st.subheader("Autores más productivos")

    autores = (
        meta_df["Authors"]
        .dropna()
        .str.split("; ")
        .explode()
    )

    top_autores = (
        autores
        .value_counts()
        .head(20)
    )

    if top_autores.empty:

        st.info(
            "No se encontraron autores."
        )

        return

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=top_autores.values,
        y=top_autores.index,
        palette="viridis"
    )

    plt.title(
        "Autores más productivos"
    )

    plt.xlabel(
        "Número de publicaciones"
    )

    plt.ylabel(
        "Autor"
    )

    st.pyplot(plt)


def mostrar_red_coautoria(meta_df):

    st.subheader(
        "Red de coautoría"
    )

    G = nx.Graph()

    for authors in meta_df["Authors"].dropna():

        author_list = [
            a.strip()
            for a in authors.split(";")
            if a.strip()
        ]

        author_list = list(
            set(author_list)
        )

        for pair in combinations(
            author_list,
            2
        ):

            if G.has_edge(
                pair[0],
                pair[1]
            ):

                G[pair[0]][pair[1]][
                    "weight"
                ] += 1

            else:

                G.add_edge(
                    pair[0],
                    pair[1],
                    weight=1
                )

    if G.number_of_nodes() == 0:

        st.info(
            "No hay suficientes datos para construir la red."
        )

        return

    centrality = nx.betweenness_centrality(
        G
    )

    top_nodes = sorted(
        centrality,
        key=centrality.get,
        reverse=True
    )[:30]

    subG = G.subgraph(
        top_nodes
    )

    st.write(
        f"Autores representados: {subG.number_of_nodes()}"
    )

    st.write(
        f"Relaciones de coautoría: {subG.number_of_edges()}"
    )

    tabla_centralidad = pd.DataFrame({
        "Autor": list(
            centrality.keys()
        ),
        "Centralidad": list(
            centrality.values()
        )
    })

    tabla_centralidad = (
        tabla_centralidad
        .sort_values(
            "Centralidad",
            ascending=False
        )
        .head(20)
    )

    st.subheader(
        "Autores con mayor centralidad"
    )

    st.dataframe(
        tabla_centralidad
    )

    plt.figure(
        figsize=(12, 8)
    )

    pos = nx.spring_layout(
        subG,
        seed=42
    )

    nx.draw_networkx_nodes(
        subG,
        pos,
        node_size=[
            max(
                centrality[node] * 5000,
                100
            )
            for node in subG.nodes()
        ],
        alpha=0.7
    )

    nx.draw_networkx_edges(
        subG,
        pos,
        alpha=0.3
    )

    nx.draw_networkx_labels(
        subG,
        pos,
        font_size=7
    )

    plt.title(
        "Red de colaboración entre autores"
    )

    st.pyplot(plt)
