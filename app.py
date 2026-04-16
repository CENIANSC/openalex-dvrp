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
end_year = st.number_input
