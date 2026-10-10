import streamlit as st
import pandas as pd
import networkx as nx

from itertools import combinations


def mostrar_metricas_red_institucional(meta_df):

    st.subheader(
        "Métricas de colaboración institucional"
    )

    G = nx.Graph()

    for institutions in meta_df["Institutions"].dropna():

        inst_list = list(
            set(
                i.strip()
                for i in institutions.split(";")
                if i.strip()
            )
        )

        for pair in combinations(
            inst_list,
            2
        ):

            if G.has_edge(*pair):

                G[pair[0]][pair[1]][
                    "weight"
                ] += 1

     *      else:

                G.add*edge(
                    pair[0],*                    pair[1],
     *              weight=1
           *    )

    if G.number_of_nodes() *= 0:

        st.info(
           *"No existen instituciones suficien*es."
        )

        return

  * col1, col2, col3 = st.columns(3)
*    col1.metric(
        "Instituc*ones",
        G.number_of_nodes()*    )

    col2.metric(
        "C*laboraciones",
        G.number_of*edges()
    )

    col3.metric(
  *     "Densidad",
        round(
  *         nx.density(G),
          * 4
        )
    )
