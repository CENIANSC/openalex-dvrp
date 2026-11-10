import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns


def mostrar_revistas_frecuentes(meta_df):

    st.subheader(
        "Revistas más frecuentes"
    )

    if meta_df["Journal"].isnull().all():

        st.info(
            "No hay información de revistas."
        )

        return

    top_journals = (
        meta_df["Journal"]
        .value_counts()
        .head(10)
    )

    plt.figure(figsize=(10, 5))

    sns.barplot(
        x=top_journals.values,
        y=top_journals.index,
        palette="crest"
    )

    plt.xlabel(
        "Número de publicaciones"
    )

    plt.ylabel(
        "Revista"
    )

    plt.title(
        "Revistas con mayor frecuencia"
    )

    st.pyplot(plt)


def mostrar_publicaciones_por_anio(meta_df):

    st.subheader(
        "Producción científica por año"
    )

    if meta_df["Year"].isnull().all():

        st.info(
            "No existen años de publicación."
        )

        return

    plt.figure(figsize=(10, 5))

    sns.countplot(
        x="Year",
        data=meta_df,
        order=sorted(
            meta_df["Year"]
            .dropna()
            .unique()
        )
    )

    plt.xlabel("Año")
    plt.ylabel("Número de publicaciones")

    plt.xticks(rotation=45)

    st.pyplot(plt)


def mostrar_impacto_por_anio(meta_df):

    st.subheader(
        "Promedio de citas por año"
    )

    impact_by_year = (
        meta_df
        .groupby("Year")["Cited by"]
        .mean()
        .reset_index()
    )

    if impact_by_year.empty:

        st.info(
            "No existen citas disponibles."
        )

        return

    plt.figure(figsize=(10, 5))

    sns.barplot(
        data=impact_by_year,
        x="Year",
        y="Cited by",
        palette="viridis"
    )

    plt.xlabel("Año")
    plt.ylabel("Promedio de citas")

    plt.xticks(rotation=45)

    st.pyplot(plt)
