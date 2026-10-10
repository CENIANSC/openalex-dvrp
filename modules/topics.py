import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def mostrar_temas_emergentes(meta_df):

    st.subheader(
        "Temas emergentes"
    )

    if "Themes" not in meta_df.columns:

        st.info(
            "No existen temas disponibles."
        )

        return

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

        st.info(
            "No existen temas suficientes."
        )

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

    plt.xlabel(
        "Frecuencia reciente"
    )

    plt.ylabel(
        "Tema"
    )

    plt.title(
        "Temas emergentes"
    )

    st.pyplot(plt)


def mostrar_temas_frecuentes(meta_df):

    st.subheader(
        "Temas más frecuentes"
    )

    temas = (
        meta_df["Themes"]
        .dropna()
        .str.split("; ")
        .explode()
    )

    top_temas = (
        temas
        .value_counts()
        .head(20)
    )

    if top_temas.empty:

        st.info(
            "No existen temas disponibles."
        )

        return

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=top_temas.values,
        y=top_temas.index,
        palette="flare"
    )

    plt.xlabel(
        "Frecuencia"
    )

    plt.ylabel(
        "Tema"
    )

    plt.title(
        "Temas más frecuentes"
    )

    st.pyplot(plt)
