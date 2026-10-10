import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import squarify

from wordcloud import WordCloud
from itertools import combinations


def mostrar_nube_conceptos(meta_df):

    st.subheader(
        "Nube de palabras de conceptos"
    )

    all_concepts = " ".join(
        meta_df["Concepts"]
        .dropna()
    )

    if not all_concepts.strip():

        st.info(
            "No existen conceptos disponibles."
        )

        return

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white"
    ).generate(all_concepts)

    plt.figure(figsize=(10, 5))

    plt.imshow(
        wordcloud,
        interpolation="bilinear"
    )

    plt.axis("off")

    st.pyplot(plt)


def mostrar_treemap_conceptos(meta_df):

    st.subheader(
        "Conceptos más frecuentes"
    )

    concept_counts = (
        meta_df["Concepts"]
        .str.split("; ")
        .explode()
        .value_counts()
        .head(20)
    )

    if concept_counts.empty:

        st.info(
            "No existen conceptos suficientes."
        )

        return

    labels = [
        (
            f"{concepto[:25]}...\n({cantidad})"
            if len(concepto) > 25
            else f"{concepto}\n({cantidad})"
        )
        for concepto, cantidad
        in zip(
            concept_counts.index,
            concept_counts.values
        )
    ]

    plt.figure(figsize=(12, 7))

    squarify.plot(
        sizes=concept_counts.values,
        label=labels,
        alpha=0.8,
        text_kwargs={
            "fontsize": 8
        }
    )

    plt.axis("off")

    st.pyplot(plt)


def mostrar_coocurrencia_conceptos(meta_df):

    st.subheader(
        "Coocurrencia de conceptos"
    )

    concept_pairs = []

    for concepts in meta_df["Concepts"].dropna():

        items = [
            c.strip()
            for c in concepts.split(";")
            if c.strip()
        ]

        for pair in combinations(
            items,
            2
        ):

            concept_pairs.append(
                tuple(
                    sorted(pair)
                )
            )

    if not concept_pairs:

        st.info(
            "No existen suficientes conceptos para generar la matriz."
        )

        return

    pair_df = pd.DataFrame(
        concept_pairs,
        columns=[
            "Concepto 1",
            "Concepto 2"
        ]
    )

    pair_counts = (
        pair_df
        .value_counts()
        .reset_index(name="Frecuencia")
    )

    heatmap_df = (
        pair_counts
        .pivot_table(
            index="Concepto 1",
            columns="Concepto 2",
            values="Frecuencia",
            fill_value=0
        )
    )

    plt.figure(figsize=(10, 8))

    sns.heatmap(
        heatmap_df,
        cmap="YlGnBu"
    )

    st.pyplot(plt)
