"""Presentación institucional. No modifica los cálculos bibliométricos."""
import html
import streamlit as st

VERSION = "2.5"

STYLE = """
<style>
:root { --dvrp-navy:#153858; --dvrp-blue:#23649a; --dvrp-muted:#62758a; --dvrp-border:#e0e8f0; }
[data-testid="stAppViewContainer"] { background: #f6f9fc; }
[data-testid="stHeader"] { background: rgba(246,249,252,.92); }
[data-testid="stSidebar"] { background: #102d48; }
[data-testid="stSidebar"] * { color: #f0f6ff; }
[data-testid="stSidebar"] a { text-decoration: none; }
[data-testid="stSidebar"] a:hover { color: #92d2ff !important; }
.block-container { max-width: 1480px; padding-top: 1.7rem; padding-bottom: 3.5rem; }
h1, h2, h3 { color: #173858; letter-spacing: -.025em; }
[data-testid="stMetric"] { border: 1px solid var(--dvrp-border); background: #fff; padding: 1rem 1.15rem; border-radius: 14px; box-shadow: 0 3px 16px rgba(24,56,89,.035); }
[data-testid="stMetricLabel"] { color: #60778b; }
[data-testid="stMetricValue"] { color: #153858; }
[data-testid="stExpander"], [data-testid="stForm"] { background: #fff; border: 1px solid var(--dvrp-border); border-radius: 13px; }
[data-testid="stTabs"] button[role="tab"] { font-weight: 550; }
[data-testid="stDataFrame"] { border: 1px solid var(--dvrp-border); border-radius: 10px; }
.dvrp-hero { background: linear-gradient(120deg,#123657 0%,#205a83 72%,#247c9e 100%); color: white; border-radius: 20px; padding: 2rem 2.2rem; margin: .25rem 0 1.4rem; box-shadow: 0 12px 28px rgba(18,54,87,.12); }
.dvrp-kicker { color: #a7d7ed; font-size: .78rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
.dvrp-hero h1 { color: white !important; font-size: clamp(1.8rem,3vw,2.75rem); margin: .35rem 0 .4rem; line-height: 1.15; }
.dvrp-hero p { color: #e1eff8; margin: .25rem 0; font-size: .98rem; }
.dvrp-hero .dvrp-credit { margin-top: 1.25rem; font-size: .82rem; color: #c7e0f0; }
.dvrp-section { color: #173858; font-size: 1.2rem; font-weight: 720; margin: 1.6rem 0 .7rem; padding-bottom: .5rem; border-bottom: 1px solid #dce6ef; }
.dvrp-nav-title { font-size: .73rem; font-weight: 750; letter-spacing: .13em; text-transform: uppercase; color: #a7c8e0 !important; margin-top: 1.4rem; }
.dvrp-nav a { display:block; padding: .56rem .7rem; border-radius: 9px; color:#e8f4fc !important; margin:.12rem 0; font-size:.92rem; }
.dvrp-nav a:hover { background:#204d71; }
.dvrp-brand { font-size: 1.35rem; font-weight: 800; letter-spacing: -.03em; color: white !important; margin: .5rem 0 .2rem; }
.dvrp-sidecaption { font-size:.78rem; color:#b2d1e5 !important; }
.dvrp-note { color: #65798b; font-size: .86rem; margin: -.2rem 0 1rem; }
@media(max-width: 760px) { .dvrp-hero {padding: 1.35rem;} .block-container {padding-top: 1rem;} }
</style>
"""


def install_style():
    st.markdown(STYLE, unsafe_allow_html=True)


def sidebar():
    with st.sidebar:
        st.markdown('<div class="dvrp-brand">◈ OpenAlex Analítica</div><div class="dvrp-sidecaption">Inteligencia científica · v2.5</div>', unsafe_allow_html=True)
        st.markdown('''<div class="dvrp-nav-title">Espacios de trabajo</div><nav class="dvrp-nav">
<a href="#inicio">⌂ &nbsp; Inicio</a>
<a href="#protocolo">▤ &nbsp; Protocolo</a>
<a href="#explorador">⌕ &nbsp; Explorador</a>
<a href="#resultados">▥ &nbsp; Resultados</a>
<a href="#bibliometria">▥ &nbsp; Bibliometría</a>
<a href="#avanzado">◇ &nbsp; Análisis avanzado</a>
<a href="#inteligencia">◎ &nbsp; Inteligencia científica</a>
<a href="#proyectos">▣ &nbsp; Proyectos e informes</a>
</nav>''', unsafe_allow_html=True)
        st.divider()
        st.caption('Fuente: OpenAlex API. Los indicadores describen el corpus descargado.')
        st.caption('Daniel A. Aguirre Ibarra · UPAEP')


def hero():
    st.markdown('''<div id="inicio" class="dvrp-hero">
<div class="dvrp-kicker">Inteligencia científica  · Versión 2.5</div>
<h1>OpenAlex Analítica</h1>
<p>Exploración, análisis bibliométrico e inteligencia científica de publicaciones indexadas en OpenAlex.</p>
<div class="dvrp-credit"><strong>Daniel A. Aguirre Ibarra</strong><br>Doctorado en Logística y Dirección de la Cadena de Suministro<br>UPAEP</div>
</div>''', unsafe_allow_html=True)


def section(anchor, label, description=None):
    safe_anchor = html.escape(anchor, quote=True)
    safe_label = html.escape(label)
    st.markdown(f'<div id="{safe_anchor}" class="dvrp-section">{safe_label}</div>', unsafe_allow_html=True)
    if description:
        st.markdown(f'<div class="dvrp-note">{html.escape(description)}</div>', unsafe_allow_html=True)
