import io
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from core.openalex_client import OpenAlexError, buscar_publicaciones
from modules.indicators import mostrar_indicadores, mostrar_indice_h, mostrar_articulos_mas_citados
from modules.authors import mostrar_top_autores, mostrar_red_coautoria
from modules.institutions import mostrar_top_instituciones, mostrar_top_paises
from modules.concepts import mostrar_nube_conceptos, mostrar_treemap_conceptos, mostrar_concurrencia_conceptos
from modules.journals import mostrar_revistas_frecuentes, mostrar_publicaciones_por_anio, mostrar_impacto_por_anio
from modules.topics import mostrar_temas_emergentes, mostrar_temas_frecuentes
from modules.networks import mostrar_metricas_red_institucional

st.set_page_config(page_title="OpenAlex-DVRP 2.0", layout="wide")

def reconstruir_abstract(indice):
    if not indice:
        return ""
    palabras = []
    for palabra, posiciones in indice.items():
        for pos in posiciones:
            if len(palabras) <= pos:
                palabras.extend([""] * (pos - len(palabras) + 1))
            palabras[pos] = palabra
    return " ".join(palabras)

def nombres_unicos(valores):
    return "; ".join(dict.fromkeys(str(v) for v in valores if v))

def normalizar(trabajos):
    filas = []
    for work in trabajos:
        autorias = work.get("authorships") or []
        ubicacion = work.get("primary_location") or {}
        fuente = ubicacion.get("source") or {}
        instituciones = [i for a in autorias for i in (a.get("institutions") or [])]
        filas.append({
            "OpenAlex ID": work.get("id"),
            "Year": work.get("publication_year"),
            "Título": work.get("title"),
            "Journal": fuente.get("display_name"),
            "Authors": nombres_unicos([(a.get("author") or {}).get("display_name") for a in autorias]),
            "Institutions": nombres_unicos([i.get("display_name") for i in instituciones]),
            "Countries": nombres_unicos([c for a in autorias for c in (a.get("countries") or [])]),
            "Editorial": fuente.get("host_organization_name"),
            "Abstract": reconstruir_abstract(work.get("abstract_inverted_index")),
            "Concepts": nombres_unicos([c.get("display_name") for c in (work.get("concepts") or [])]),
            "Themes": nombres_unicos([t.get("display_name") for t in (work.get("topics") or [])]),
            "SDGs": nombres_unicos([s.get("display_name") for s in (work.get("sustainable_development_goals") or [])]),
            "Funders": nombres_unicos([f.get("display_name") for f in (work.get("funders") or [])]),
            "Cited by": work.get("cited_by_count"),
            "DOI": work.get("doi"),
            "Author IDs": nombres_unicos([(a.get("author") or {}).get("id") for a in autorias]),
            "Institution IDs": nombres_unicos([i.get("id") for i in instituciones]),
        })
    return pd.DataFrame(filas)

st.title("Explorador y análisis en OpenAlex")
st.caption("""
**Daniel A. Aguirre Ibarra**  
Doctorado en Logística y Dirección de la Cadena de Suministro  
UPAEP
""")
with st.form("busqueda"):
    consulta = st.text_input("Términos de búsqueda en título y resumen")
    c1, c2, c3 = st.columns(3)
    with c1:
        desde = st.number_input("Año inicial", min_value=1900, max_value=2100, value=2020, step=1)
    with c2:
        hasta = st.number_input("Año final", min_value=1900, max_value=2100, value=datetime.now().year, step=1)
    with c3:
        limite = st.selectbox("Máximo de registros", [200, 500, 1000, 5000], index=1)
    c4, c5, c6 = st.columns(3)
    with c4:
        tipo = st.selectbox("Tipo de documento", ["article", "Todos", "review", "book-chapter", "preprint"])
    with c5:
        solo_oa = st.checkbox("Solo acceso abierto", value=False)
    with c6:
        solo_pdf = st.checkbox("Solo documentos con PDF", value=False)
    tema = st.text_input("ID de tema OpenAlex (opcional; por ejemplo, T10567)")
    enviar = st.form_submit_button("Buscar publicaciones", type="primary")

if enviar:
    try:
        clave = st.secrets.get("OPENALEX_API_KEY", "")
        barra = st.progress(0, text="Consultando OpenAlex...")
        def actualizar(cantidad, total):
            objetivo = min(limite, total or limite)
            barra.progress(min(1.0, cantidad / max(1, objetivo)), text=f"Descargados: {cantidad:,} registros")
        trabajos, total, parametros = buscar_publicaciones(
            clave, consulta, int(desde), int(hasta), solo_oa, solo_pdf,
            tipo, limite, tema.strip() or None, actualizar
        )
        barra.empty()
        st.session_state["resultados_v2"] = normalizar(trabajos)
        st.session_state["metodologia_v2"] = {
            "plataforma": "OpenAlex-DVRP 2.0 Beta",
            "fuente": "OpenAlex API",
            "fecha_consulta_utc": datetime.now(timezone.utc).isoformat(),
            "terminos": consulta,
            "filtros": parametros.get("filter", "Ninguno"),
            "tipo": tipo,
            "limite_solicitado": limite,
            "total_reportado_openalex": total,
            "registros_descargados": len(trabajos),
            "advertencia": "Los indicadores se calculan sobre los registros descargados, no necesariamente sobre todo el universo encontrado."
        }
    except OpenAlexError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"No se pudo completar la búsqueda: {type(exc).__name__}: {exc}")

if "resultados_v2" in st.session_state:
    df = st.session_state["resultados_v2"]
    metodo = st.session_state["metodologia_v2"]
    st.subheader("Resultados de búsqueda")
    a, b = st.columns(2)
    a.metric("Resultados reportados por OpenAlex", f"{metodo['total_reportado_openalex'] or 0:,}")
    b.metric("Registros descargados", f"{len(df):,}")
    if metodo["total_reportado_openalex"] and len(df) < metodo["total_reportado_openalex"]:
        st.warning("El análisis representa únicamente los registros descargados, no todos los resultados encontrados.")
    if df.empty:
        st.info("No se encontraron publicaciones con estos criterios.")
    else:
        st.dataframe(df, use_container_width=True)
        excel = io.BytesIO()
        with pd.ExcelWriter(excel, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Publicaciones", index=False)
            pd.DataFrame([metodo]).to_excel(writer, sheet_name="Metodologia", index=False)
        st.download_button("Descargar Excel y metodología", excel.getvalue(), file_name="openalex_dvrp_v2.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Descargar metodología JSON", json.dumps(metodo, ensure_ascii=False, indent=2).encode("utf-8"), file_name="metodologia_openalex.json", mime="application/json")
        st.subheader("Análisis bibliométrico")
        analisis = [
            ("Publicaciones por año", mostrar_publicaciones_por_anio),
            ("Revistas frecuentes", mostrar_revistas_frecuentes),
            ("Impacto anual", mostrar_impacto_por_anio),
            ("Indicadores", mostrar_indicadores),
            ("Índice h", mostrar_indice_h),
            ("Artículos más citados", mostrar_articulos_mas_citados),
            ("Autores", mostrar_top_autores),
            ("Instituciones", mostrar_top_instituciones),
            ("Países", mostrar_top_paises),
            ("Red de coautoría", mostrar_red_coautoria),
            ("Temas frecuentes", mostrar_temas_frecuentes),
            ("Temas emergentes", mostrar_temas_emergentes),
            ("Nube de conceptos", mostrar_nube_conceptos),
            ("Treemap de conceptos", mostrar_treemap_conceptos),
            ("Concurrencia de conceptos", mostrar_concurrencia_conceptos),
            ("Red institucional", mostrar_metricas_red_institucional),
        ]
        for titulo, funcion in analisis:
            with st.expander(titulo, expanded=False):
                try:
                    funcion(df)
                except Exception as exc:
                    st.error(f"Este análisis requiere revisión: {type(exc).__name__}: {exc}")


# OpenAlex-DVRP 2.1: módulos complementarios sin alterar los análisis heredados.
if "resultados_v2" in st.session_state and not st.session_state["resultados_v2"].empty:
    from analysis.metrics import summarize, yearly
    from analysis.networks import build_network, node_table
    from reports.export import create_docx, create_pdf
    import networkx as nx
    import matplotlib.pyplot as plt

    st.divider()
    st.header("OpenAlex-DVRP 2.1 | Análisis avanzado")
    tab_metrics, tab_network, tab_reports, tab_audit = st.tabs(["Bibliometría avanzada", "Redes interactivas", "Informes académicos", "Auditoría de datos"])
    with tab_metrics:
        summary = summarize(df)
        cols = st.columns(3)
        for i,(name,value) in enumerate(summary.items()): cols[i%3].metric(name,value)
        st.caption("Los índices h y g son del conjunto descargado, no de autores individuales.")
        annual = yearly(df)
        if not annual.empty:
            st.subheader("Evolución anual")
            st.line_chart(annual.set_index("Año")[["Publicaciones", "Citas"]])
            st.dataframe(annual,hide_index=True,use_container_width=True)
    with tab_network:
        kind = st.radio("Red de",["Autores","Instituciones"],horizontal=True)
        G = build_network(df,"authors" if kind=="Autores" else "institutions")
        if G.number_of_nodes():
            x,y,z=st.columns(3)
            x.metric("Nodos",G.number_of_nodes());y.metric("Relaciones",G.number_of_edges());z.metric("Densidad",round(nx.density(G),4))
            nt=node_table(G)
            st.dataframe(nt.head(50),hide_index=True,use_container_width=True)
            st.download_button("Exportar nodos CSV",nt.to_csv(index=False).encode("utf-8-sig"),"nodos_red.csv",mime="text/csv")
            edge_csv=pd.DataFrame([{"Origen":a,"Destino":b,"Peso":d["weight"]} for a,b,d in G.edges(data=True)]).to_csv(index=False).encode("utf-8-sig")
            st.download_button("Exportar relaciones CSV",edge_csv,"relaciones_red.csv",mime="text/csv")
            # Restrict visualization to 40 nodes to keep Streamlit responsive.
            top=nt.head(40)["ID"].tolist();sub=G.subgraph(top)
            if sub.number_of_nodes():
                fig,ax=plt.subplots(figsize=(11,7));pos=nx.spring_layout(sub,seed=42,weight="weight")
                nx.draw_networkx(sub,pos,ax=ax,labels={n:sub.nodes[n].get("label",n)[:25] for n in sub},node_size=180,font_size=7,edge_color="#aaaaaa",alpha=.8)
                ax.set_axis_off();st.pyplot(fig);plt.close(fig)
            st.caption("Los nodos usan identificadores OpenAlex. El gráfico muestra como máximo 40 nodos; las métricas corresponden a la red completa descargada.")
        else: st.info("No hay identificadores suficientes para construir la red.")
    with tab_reports:
        summary=summarize(df);annual=yearly(df)
        st.write("Informe descriptivo con metodología, indicadores, evolución anual y limitaciones.")
        st.download_button("Descargar informe Word",create_docx(summary,metodo,annual),"informe_openalex_2_1.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Descargar informe PDF",create_pdf(summary,metodo,annual),"informe_openalex_2_1.pdf",mime="application/pdf")
    with tab_audit:
        st.write("**Comprobaciones del conjunto descargado**")
        checks={"Filas":len(df),"IDs duplicados":int(df["OpenAlex ID"].duplicated().sum()),"IDs faltantes":int(df["OpenAlex ID"].isna().sum()),"Años faltantes":int(df["Year"].isna().sum()),"Citas faltantes":int(df["Cited by"].isna().sum())}
        st.dataframe(pd.DataFrame(checks.items(),columns=["Comprobación","Valor"]),hide_index=True)
        st.json(metodo)
        st.info("La auditoría automática detecta incidencias básicas; no equivale a una validación científica completa de los registros.")
