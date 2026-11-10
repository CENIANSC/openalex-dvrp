import io
import json
import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from core.openalex_client import OpenAlexError, buscar_publicaciones
from core.topics_client import search_topics
from core.ui import install_style, sidebar, hero, section
from analysis.comparative import compare_periods, compare_entities, international_collaboration
from analysis.reproducibility import manifest_bytes
from reports.research import research_docx, research_pdf
from modules.indicators import mostrar_indicadores, mostrar_indice_h, mostrar_articulos_mas_citados
from modules.authors import mostrar_top_autores, mostrar_red_coautoria
from modules.institutions import mostrar_top_instituciones, mostrar_top_paises
from modules.concepts import mostrar_nube_conceptos, mostrar_treemap_conceptos, mostrar_concurrencia_conceptos
from modules.journals import mostrar_revistas_frecuentes, mostrar_publicaciones_por_anio, mostrar_impacto_por_anio
from modules.topics import mostrar_temas_emergentes, mostrar_temas_frecuentes
from modules.networks import mostrar_metricas_red_institucional

st.set_page_config(page_title="OpenAlex-DVRP | Inteligencia científica", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")
install_style()
sidebar()

def limpiar_para_excel(valor):
    if isinstance(valor, str):
        return re.sub(
            r"[\x00-\x08\x0B\x0C\x0E-\x1F]",
            "",
            valor
        )
    return valor


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
            "Referenced works": nombres_unicos(work.get("referenced_works") or []),
        })
    return pd.DataFrame(filas)

hero()
section("protocolo", "Protocolo de investigación", "Documenta el propósito y los criterios de tu estudio antes de recuperar publicaciones.")
with st.expander("Definir protocolo de investigación", expanded=False):
    st.text_input("Título del estudio", key="study_title", placeholder="Ej. Evolución de la investigación en logística sostenible")
    st.text_area("Pregunta de investigación", key="study_question")
    st.text_area("Objetivo del estudio", key="study_objective")
    st.text_area("Criterios de inclusión", key="study_inclusion", placeholder="Años, idiomas, tipos documentales y pertinencia temática")
    st.text_area("Criterios de exclusión", key="study_exclusion", placeholder="Duplicados, documentos fuera del alcance, etc.")
    st.caption("Los criterios son documentales: la aplicación no excluye automáticamente publicaciones por estos textos. Registra manualmente las decisiones de cribado.")

section("explorador", "Explorador de publicaciones", "Define la estrategia de búsqueda y los filtros de recuperación en OpenAlex.")
selected_topics = []
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
    st.caption("Puedes buscar solo por temas, solo por texto o combinar ambos. Los temas múltiples se unen mediante OR.")
    modo_tema = st.radio("Coincidencia temática", ["Tema principal", "Cualquier tema asignado"], horizontal=True)
    pais = st.text_input("País de afiliación (ISO 3166-1 alfa-2; opcional, ej. MX)", max_chars=2)
    institucion = st.text_input("ID de institución OpenAlex (opcional, ej. I123456789)")
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
            tipo, limite, tema.strip() or None, actualizar, pais.strip() or None,
            institucion.strip() or None, "any" if modo_tema == "Cualquier tema asignado" else "primary", (selected_topics + ([tema.strip()] if tema.strip() else []))
        )
        barra.empty()
        st.session_state["resultados_v2"] = normalizar(trabajos)
        st.session_state["metodologia_v2"] = {
            "plataforma": "OpenAlex-DVRP 2.5",
            "fuente": "OpenAlex API",
            "fecha_consulta_utc": datetime.now(timezone.utc).isoformat(),
            "terminos": consulta,
            "temas_seleccionados": selected_topics + ([tema.strip()] if tema.strip() else []),
            "modo_tema": modo_tema,
            "pais": pais,
            "institucion": institucion,
            "periodo": f"{desde}-{hasta}",
            "solo_oa": solo_oa,
            "solo_pdf": solo_pdf,
            "filtros": parametros.get("filter", "Ninguno"),
            "tipo": tipo,
            "limite_solicitado": limite,
            "total_reportado_openalex": total,
            "registros_descargados": len(trabajos),
            "advertencia": "Los indicadores se calculan sobre los registros descargados, no necesariamente sobre todo el universo encontrado.",
            "titulo_estudio": st.session_state.get("study_title", ""),
            "pregunta_investigacion": st.session_state.get("study_question", ""),
            "objetivo_estudio": st.session_state.get("study_objective", ""),
            "criterios_inclusion": st.session_state.get("study_inclusion", ""),
            "criterios_exclusion": st.session_state.get("study_exclusion", "")
        }
    except OpenAlexError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"No se pudo completar la búsqueda: {type(exc).__name__}: {exc}")

if "resultados_v2" in st.session_state:
    df = st.session_state["resultados_v2"]
    metodo = st.session_state["metodologia_v2"]
    section("resultados", "Panel de resultados", "Resumen del corpus recuperado en la consulta actual.")
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
            df_excel = df.map(limpiar_para_excel)
            df_excel.to_excel(writer, sheet_name="Publicaciones", index=False)   
            pd.DataFrame([metodo]).astype(str).map(limpiar_para_excel).to_excel(writer, sheet_name="Metodologia", index=False)
        st.download_button("Descargar Excel y metodología", excel.getvalue(), file_name="openalex_dvrp_v2.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Descargar registros CSV (UTF-8)", df.to_csv(index=False).encode("utf-8-sig"), file_name="openalex_dvrp_2_2.csv", mime="text/csv")
        st.download_button("Descargar manifiesto reproducible JSON", manifest_bytes(metodo, df), file_name="manifiesto_openalex_2_2.json", mime="application/json")
        st.download_button("Descargar metodología JSON", json.dumps(metodo, ensure_ascii=False, indent=2).encode("utf-8"), file_name="metodologia_openalex.json", mime="application/json")
        section("bibliometria", "Análisis bibliométrico", "Indicadores, autores, instituciones, fuentes y relaciones del conjunto descargado.")
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
    section("avanzado", "Análisis avanzado", "Métricas, redes de colaboración, comparaciones, informes y auditoría.")
    tab_metrics, tab_network, tab_compare, tab_reports, tab_audit = st.tabs(["Bibliometría avanzada", "Redes interactivas", "Comparaciones", "Informes académicos", "Auditoría de datos"])
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
    with tab_compare:
        st.caption("Comparaciones descriptivas del subconjunto descargado; no implican causalidad ni impacto normalizado.")
        years = pd.to_numeric(df["Year"], errors="coerce").dropna()
        if not years.empty:
            y0, y1 = int(years.min()), int(years.max())
            mid = (y0 + y1) // 2
            a1, a2, b1, b2 = st.columns(4)
            start_a = a1.number_input("Inicio A", 1900, 2100, y0)
            end_a = a2.number_input("Fin A", 1900, 2100, mid)
            start_b = b1.number_input("Inicio B", 1900, 2100, min(mid + 1, 2100))
            end_b = b2.number_input("Fin B", 1900, 2100, y1)
            if start_a <= end_a and start_b <= end_b:
                comparison = compare_periods(df, start_a, end_a, start_b, end_b)
                st.dataframe(comparison, hide_index=True, use_container_width=True)
                st.download_button("Exportar comparación CSV", comparison.to_csv(index=False).encode("utf-8-sig"), "comparacion_periodos.csv", mime="text/csv")
                st.session_state["comparison_22"] = comparison
            else:
                st.warning("Revisa los rangos de años.")
        entity = st.selectbox("Comparar producción por", ["Institutions", "Countries", "Authors", "Journal"])
        entities = compare_entities(df, entity)
        st.dataframe(entities, hide_index=True, use_container_width=True)
        st.download_button("Exportar entidades CSV", entities.to_csv(index=False).encode("utf-8-sig"), "comparacion_entidades.csv", mime="text/csv")
        st.metric("Publicaciones con colaboración internacional (2+ países)", international_collaboration(df))
    with tab_reports:
        summary=summarize(df);annual=yearly(df)
        st.write("Informe descriptivo con metodología, indicadores, evolución anual y limitaciones.")
        comp = st.session_state.get("comparison_22")
        st.download_button("Descargar informe Word 2.2",research_docx(summary,metodo,annual,comp),"informe_openalex_2_2.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Descargar informe PDF 2.2",research_pdf(summary,metodo,annual,comp),"informe_openalex_2_2.pdf",mime="application/pdf")
    with tab_audit:
        st.write("**Comprobaciones del conjunto descargado**")
        checks={"Filas":len(df),"IDs duplicados":int(df["OpenAlex ID"].duplicated().sum()),"IDs faltantes":int(df["OpenAlex ID"].isna().sum()),"Años faltantes":int(df["Year"].isna().sum()),"Citas faltantes":int(df["Cited by"].isna().sum())}
        st.dataframe(pd.DataFrame(checks.items(),columns=["Comprobación","Valor"]),hide_index=True)
        st.json(metodo)
        st.info("La auditoría automática detecta incidencias básicas; no equivale a una validación científica completa de los registros.")

# OpenAlex-DVRP 2.3: análisis de estructura y evolución del conocimiento.
if 'resultados_v2' in st.session_state and not st.session_state['resultados_v2'].empty:
    from analysis.science_mapping import (topic_network, topic_table, thematic_evolution,
        emerging_topics, strategic_map, reference_network, edge_table)
    import matplotlib.pyplot as plt
    import networkx as nx

    st.divider()
    section("inteligencia", "Inteligencia científica", "Mapas de conocimiento, evolución temática y redes de referencias.")
    st.caption('Análisis exploratorios del subconjunto descargado. Los temas son etiquetas clasificadas por OpenAlex, no palabras clave declaradas por autores.')
    t_map, t_evo, t_cite, t_strategy, t_figures = st.tabs([
        'Mapa de conocimiento', 'Evolución temática', 'Redes de referencias',
        'Mapa estratégico', 'Figuras e informe 2.3'])

    def draw_science_graph(graph, limit=45):
        fig, ax = plt.subplots(figsize=(11, 7))
        if graph.number_of_nodes():
            ranking = sorted(graph, key=lambda n: graph.degree(n), reverse=True)[:limit]
            sub = graph.subgraph(ranking)
            pos = nx.spring_layout(sub, seed=42, weight='weight')
            nx.draw_networkx(sub, pos, ax=ax, node_size=210, font_size=6,
                             labels={n: str(n).rsplit('/', 1)[-1][:23] for n in sub},
                             width=.65, alpha=.85, arrows=sub.is_directed())
        ax.axis('off')
        fig.tight_layout()
        return fig

    def figure_download(fig, basename):
        image = io.BytesIO()
        fig.savefig(image, format='png', dpi=240, bbox_inches='tight')
        st.download_button('Descargar figura PNG (240 dpi)', image.getvalue(),
                           file_name=f'{basename}.png', mime='image/png', key=f'png_{basename}')
        vector = io.BytesIO()
        fig.savefig(vector, format='svg', bbox_inches='tight')
        st.download_button('Descargar figura SVG (vectorial)', vector.getvalue(),
                           file_name=f'{basename}.svg', mime='image/svg+xml', key=f'svg_{basename}')

    with t_map:
        min_count = st.slider('Publicaciones mínimas por tema', 1, 20, 2)
        graph_topics = topic_network(df, min_count)
        topic_stats = topic_table(graph_topics)
        st.metric('Temas representados', graph_topics.number_of_nodes())
        st.dataframe(topic_stats, hide_index=True, use_container_width=True)
        st.download_button('Exportar temas y comunidades CSV', topic_stats.to_csv(index=False).encode('utf-8-sig'),
                           'mapa_temas_23.csv', mime='text/csv')
        st.download_button('Exportar relaciones temáticas CSV', edge_table(graph_topics).to_csv(index=False).encode('utf-8-sig'),
                           'relaciones_temas_23.csv', mime='text/csv')
        if graph_topics.number_of_nodes():
            fig = draw_science_graph(graph_topics)
            st.pyplot(fig)
            figure_download(fig, 'red_tematica_23')
            plt.close(fig)

    with t_evo:
        periods = st.slider('Número aproximado de periodos', 2, 6, 3)
        evolution = thematic_evolution(df, periods)
        st.dataframe(evolution, hide_index=True, use_container_width=True)
        if not evolution.empty:
            pivot = evolution.pivot_table(index='Periodo', columns='Tema', values='Publicaciones', fill_value=0)
            st.area_chart(pivot)
        st.download_button('Exportar evolución CSV', evolution.to_csv(index=False).encode('utf-8-sig'),
                           'evolucion_tematica_23.csv', mime='text/csv')
        emerging = emerging_topics(df)
        st.subheader('Variación reciente de la presencia temática')
        st.caption('Diferencia en puntos porcentuales entre la proporción de publicaciones con cada tema en el periodo reciente y anterior. No es una predicción ni una prueba estadística.')
        st.dataframe(emerging, hide_index=True, use_container_width=True)
        st.download_button('Exportar tendencias CSV', emerging.to_csv(index=False).encode('utf-8-sig'),
                           'tendencias_temas_23.csv', mime='text/csv')

    with t_cite:
        mode_label = st.selectbox('Tipo de relación', ['Acoplamiento bibliográfico', 'Citación directa (dentro del corpus)', 'Cocitación de referencias'])
        mode = {'Acoplamiento bibliográfico': 'coupling', 'Citación directa (dentro del corpus)': 'citation',
                'Cocitación de referencias': 'cocitation'}[mode_label]
        shared = st.slider('Mínimo de referencias compartidas / cocitaciones', 1, 10, 2,
                           disabled=mode == 'citation')
        graph_refs = reference_network(df, mode=mode, min_shared=shared, max_works=100 if mode == 'cocitation' else 300)
        st.caption('Se utilizan como máximo los primeros 300 documentos descargados (100 para cocitación, con hasta 50 referencias por documento). La red de citación directa solo conecta documentos presentes en ese subconjunto; los nodos de cocitación representan referencias, no necesariamente documentos recuperados.')
        x, y = st.columns(2)
        x.metric('Nodos', graph_refs.number_of_nodes())
        y.metric('Relaciones', graph_refs.number_of_edges())
        ref_edges = edge_table(graph_refs)
        st.dataframe(ref_edges.head(300), hide_index=True, use_container_width=True)
        st.download_button('Exportar red de referencias CSV', ref_edges.to_csv(index=False).encode('utf-8-sig'),
                           'referencias_red_23.csv', mime='text/csv')
        if graph_refs.number_of_nodes() and graph_refs.number_of_edges():
            fig = draw_science_graph(graph_refs)
            st.pyplot(fig)
            figure_download(fig, 'red_referencias_23')
            plt.close(fig)
        elif 'Referenced works' not in df or not df['Referenced works'].fillna('').str.strip().any():
            st.warning('Este conjunto no contiene referencias bibliográficas recuperadas. Ejecuta una nueva búsqueda con la versión 2.3.')

    with t_strategy:
        strategic = strategic_map(graph_topics)
        st.dataframe(strategic, hide_index=True, use_container_width=True)
        st.download_button('Exportar mapa estratégico CSV', strategic.to_csv(index=False).encode('utf-8-sig'),
                           'mapa_estrategico_23.csv', mime='text/csv')
        if not strategic.empty:
            fig, ax = plt.subplots(figsize=(9, 6))
            ax.scatter(strategic['Centralidad externa'], strategic['Densidad interna'], s=90)
            for _, row in strategic.iterrows():
                ax.annotate(str(row['Comunidad']), (row['Centralidad externa'], row['Densidad interna']), xytext=(4, 4), textcoords='offset points')
            ax.axvline(strategic['Centralidad externa'].median(), linestyle='--', color='grey')
            ax.axhline(strategic['Densidad interna'].median(), linestyle='--', color='grey')
            ax.set_xlabel('Centralidad externa (peso de enlaces entre comunidades)')
            ax.set_ylabel('Densidad interna ponderada')
            ax.set_title('Mapa estratégico exploratorio de comunidades')
            st.pyplot(fig)
            figure_download(fig, 'mapa_estrategico_23')
            plt.close(fig)
        st.info('La etiqueta «emergente o declinante» describe un cuadrante de baja centralidad y densidad; para distinguir crecimiento de declive es necesario contrastar los periodos. Estas medidas no son índices de Callon.')

    with t_figures:
        from reports.science_report import science_docx, science_pdf
        summary23 = summarize(df)
        annual23 = yearly(df)
        st.write('Informe complementario con indicadores, mapa temático, tendencias, comunidades y limitaciones metodológicas.')
        st.download_button('Descargar informe científico Word 2.3',
                           science_docx(summary23, metodo, annual23, topic_stats, emerging, strategic),
                           'informe_cientifico_openalex_23.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        st.download_button('Descargar informe científico PDF 2.3',
                           science_pdf(summary23, metodo, annual23, topic_stats, emerging, strategic),
                           'informe_cientifico_openalex_23.pdf', mime='application/pdf')
        st.caption('Las figuras pueden descargarse en PNG y SVG desde las pestañas anteriores. El informe es descriptivo y requiere interpretación y revisión del investigador.')


# OpenAlex-DVRP 2.4: protocolo, selección, calidad, informe y proyectos portables.
from analysis.study_workflow import quality_table, selection_flow, project_bytes, read_project, study_report_docx, study_report_pdf
st.divider()
section("proyectos", "Proyectos e informes", "Recupera estudios, revisa calidad documental y exporta informes académicos.")
with st.expander("Recuperar un proyecto guardado (JSON)"):
    uploaded_project = st.file_uploader("Archivo de proyecto 2.4", type=["json"], key="project_upload")
    if uploaded_project is not None and st.button("Cargar proyecto", key="load_project"):
        try:
            restored_df, restored_method, restored_flow = read_project(uploaded_project.getvalue())
            st.session_state["resultados_v2"] = restored_df
            st.session_state["metodologia_v2"] = restored_method
            st.session_state["selection_24"] = restored_flow
            st.success("Proyecto recuperado. Se restauraron registros, metodología y selección; las visualizaciones se recalcularán.")
            st.rerun()
        except (ValueError, KeyError, TypeError) as exc:
            st.error(f"No fue posible cargar el proyecto: {exc}")
if "resultados_v2" in st.session_state:
    current_df = st.session_state["resultados_v2"]
    current_method = st.session_state["metodologia_v2"]
    t_protocol, t_selection, t_quality, t_article, t_save = st.tabs([
        "Protocolo", "Selección documental", "Calidad de metadatos", "Informe científico 2.4", "Guardar proyecto"])
    with t_protocol:
        st.json({k: current_method.get(k, "") for k in ["titulo_estudio", "pregunta_investigacion", "objetivo_estudio", "criterios_inclusion", "criterios_exclusion", "filtros", "fecha_consulta_utc", "registros_descargados", "total_reportado_openalex"]})
        st.caption("Documentar una estrategia no implica que se hayan aplicado criterios de elegibilidad manuales.")
    with t_selection:
        st.caption("Flujo descriptivo de selección. No debe presentarse como PRISMA 2020 completo sin documentar todas las fuentes, fases y motivos de exclusión.")
        identified = int(current_method.get("total_reportado_openalex") or len(current_df))
        downloaded = len(current_df)
        duplicates = int(current_df["OpenAlex ID"].duplicated().sum()) if "OpenAlex ID" in current_df else 0
        max_screen = max(0, downloaded - duplicates)
        defaults = st.session_state.get("selection_24", {})
        screened = st.number_input("Registros examinados manualmente", min_value=0, max_value=max_screen, value=min(max_screen, int(defaults.get("screened", 0))), key="screened_24")
        excluded = st.number_input("Registros excluidos durante el cribado", min_value=0, max_value=int(screened), value=min(int(screened), int(defaults.get("excluded", 0))), key="excluded_24")
        included = int(screened) - int(excluded)
        st.session_state["selection_24"] = {"screened": int(screened), "excluded": int(excluded)}
        flow_df = selection_flow(identified, downloaded, duplicates, int(screened), int(excluded))
        st.dataframe(flow_df, hide_index=True, use_container_width=True)
        st.metric("Registros incluidos tras cribado", included)
        st.download_button("Descargar flujo CSV", flow_df.to_csv(index=False).encode("utf-8-sig"), "seleccion_documental_2_4.csv", mime="text/csv")
    with t_quality:
        quality = quality_table(current_df)
        st.dataframe(quality, hide_index=True, use_container_width=True)
        st.download_button("Descargar auditoría CSV", quality.to_csv(index=False).encode("utf-8-sig"), "calidad_metadatos_2_4.csv", mime="text/csv")
        st.caption("La disponibilidad de referencias y resúmenes varía por fuente; los datos faltantes no implican necesariamente registros inválidos.")
    with t_article:
        st.caption("Documento estructurado de apoyo, no un artículo validado ni una discusión científica generada automáticamente.")
        flow_data = st.session_state.get("selection_24", {"screened": 0, "excluded": 0})
        st.download_button("Descargar borrador académico Word 2.4", study_report_docx(current_df, current_method, flow_data), "borrador_openalex_2_4.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.download_button("Descargar borrador académico PDF 2.4", study_report_pdf(current_df, current_method, flow_data), "borrador_openalex_2_4.pdf", mime="application/pdf")
    with t_save:
        st.write("Guarda un archivo JSON portable con los registros, protocolo y cifras de selección. No incluye credenciales.")
        st.download_button("Guardar proyecto completo JSON", project_bytes(current_df, current_method, st.session_state.get("selection_24", {})), "proyecto_openalex_dvrp_2_4.json", mime="application/json")
        st.warning("Los proyectos se descargan a tu equipo; Streamlit Cloud no conserva automáticamente tus estudios entre sesiones. Evita compartir proyectos que contengan información sensible.")
