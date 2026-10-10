import streamlit as st
import pandas as pd


def mostrar_indicadores(meta_df):

    st.subheader("Indicadores bibliométricos")

    total_articulos = len(meta_df)

    total_citas = (
        meta_df["Cited by"]
        .fillna(0)
        .sum()
    )

    promedio_citas = (
        meta_df["Cited by"]
        .fillna(0)
        .mean()
    )

    maximo_citas = (
        meta_df["Cited by"]
        .fillna(0)
        .max()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Artículos",
        f"{total_articulos:,}"
    )

    col2.metric(
        "Citas",
        f"{int(total_citas):,}"
    )

    col3.metric(
        "Promedio de citas",
        round(promedio_citas, 2)
    )

    col4.metric(
        "Máximo de citas",
        int(maximo_citas)
    )


def mostrar_indice_h(meta_df):

    st.subheader("Índice H")

    citas = sorted(
        meta_df["Cited by"]
        .fillna(0)
        .astype(int),
        reverse=True
    )

    indice_h = 0

    for i, c in enumerate(citas, start=1):

        if c >= i:
            indice_h = i
        else:
            break

    st.metric(
        "Índice H",
        indice_h
    )


def mostrar_articulos_mas_citados(meta_df):

    st.subheader(
        "Top 20 artículos más citados"
    )

    top_citados = (
        meta_df
        .sort_values(
            "Cited by",
            ascending=False
        )
        .head(20)
    )

    columnas = [
        "Título",
        "Year",
        "Journal",
        "Cited by",
        "DOI"
    ]

    st.dataframe(
        top_citados[columnas]
    )
