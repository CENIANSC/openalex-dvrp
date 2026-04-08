import sqlite3
import streamlit as st

# Conexión a la base de datos
DB_PATH = "db/articulos_dvrp.db"

def obtener_articulos(filtro_año, filtro_autor, filtro_titulo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = "SELECT titulo, autores, año, resumen, json_url FROM articulos WHERE año BETWEEN ? AND ?"
    params = [filtro_año[0], filtro_año[1]]

    if filtro_autor:
        query += " AND autores LIKE ?"
        params.append(f"%{filtro_autor}%")

    if filtro_titulo:
        query += " AND titulo LIKE ?"
        params.append(f"%{filtro_titulo}%")

    rows = c.execute(query, params).fetchall()
    conn.close()
    return rows

# --- Interfaz Streamlit ---
st.title("📚 Base de artículos DVRP (OpenAlex)")

# Filtros
st.sidebar.header("Filtros de búsqueda")
filtro_año = st.sidebar.slider("Año de publicación", 1990, 2026, (2000, 2026))
filtro_autor = st.sidebar.text_input("Autor contiene:")
filtro_titulo = st.sidebar.text_input("Título contiene:")

# Consultar artículos
articulos = obtener_articulos(filtro_año, filtro_autor, filtro_titulo)

st.write(f"Se encontraron {len(articulos)} artículos.")

# Mostrar resultados
for titulo, autores, año, resumen, url in articulos:
    st.subheader(titulo)
    st.write(f"**Autores:** {autores}")
    st.write(f"**Año:** {año}")
    if resumen:
        st.write(f"**Resumen:** {resumen[:500]}...")  # mostrar primeros 500 caracteres
    st.markdown(f"[Ver JSON completo en OpenAlex]({url})")
    st.markdown("---")

