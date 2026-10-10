import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def mostrar_top_instituciones(meta_df):

    st.subheader(
        "Instituciones más productivas"
    )

    instituciones = (
        meta_df["Institutions"]
        .dropna()
        .str.split("; ")
        .explode()
    )

    top_instituciones = (
        instituciones
        .value_counts()
        .head(20)
    )

    if top_instituciones.empty:

        st.info(
            "No se encontraron instituciones."
        )

        return

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=top_instituciones.values,
        y=top_instituciones.index,
        palette="magma"
    )

    plt.title(
        "Instituciones más productivas"
    )

    plt.xlabel(
        "Número de publicaciones"
    )

    plt.ylabel(
        "Institución"
    )

    st.pyplot(plt)

    tabla = (
        top_instituciones
        .reset_index()
    )

    tabla.columns = [
        "Institución",
        "Publicaciones"
    ]

    st.dataframe(
        tabla,
        use_container_width=True
    )


def mostrar_top_paises(meta_df):

    if "Countries" not in meta_df.columns:

        st.info(
            "No hay información de países."
        )

        return

    st.subheader(
        "Países más productivos"
    )

    paises = (
        meta_df["Countries"]
        .dropna()
        .str.split("; ")
        .explode()
    )

    top_paises = (
        paises
        .value_counts()
        .head(20)
    )

    if top_paises.empty:

        st.info(
            "No se encontraron países."
        )

        return

    plt.figure(figsize=(10, 6))

    sns.barplot(
        x=top_paises.values,
        y=top_paises.index,
        palette="cubehelix"
    )

    plt.title(
        "Países más productivos"
    )

    plt.xlabel(
        "Número de publicaciones"
    )

    plt.ylabel(
        "País"
    )

    st.pyplot(plt)

    tabla = (
        top_paises
        .reset_index()
    )

    tabla.columns = [
        "País",
        "Publicaciones"
    ]

    st.dataframe(
        tabla,
        use_container_width=True
    )
