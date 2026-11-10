
import streamlit as st
import pandas as pd
import networkx as nx

from itertools import combinations


def mostrar_metricas_red_institucional(meta_df):

    st.subheader("Métricas de colaboración institucional")

    if meta_df is None or "Institutions" not in meta_df.columns:
        st.warning("No se encontraron datos de instituciones.")
        return

    G = nx.Graph()

    for institutions in meta_df["Institutions"].dropna():

        if not isinstance(institutions, str):
            continue

        inst_list = list(
            dict.fromkeys(
                i.strip()
                for i in institutions.split(";")
                if i.strip()
            )
        )

        G.add_nodes_from(inst_list)

        for inst1, inst2 in combinations(inst_list, 2):

            if G.has_edge(inst1, inst2):
                G[inst1][inst2]["weight"] += 1
            else:
                G.add_edge(inst1, inst2, weight=1)

    if G.number_of_nodes() == 0:
        st.info("No existen instituciones suficientes para el análisis.")
        return

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Instituciones",
        G.number_of_nodes()
    )

    col2.metric(
        "Colaboraciones",
        G.number_of_edges()
    )

    col3.metric(
        "Densidad",
        round(nx.density(G), 4)
    )
