"""Cliente de OpenAlex con paginación acotada y reintentos."""
import time
import requests

BASE_URL = "https://api.openalex.org/works"

class OpenAlexError(Exception):
    pass

def buscar_publicaciones(api_key, consulta, anio_inicial=None, anio_final=None,
                         solo_oa=False, solo_pdf=False, tipo="article", limite=500,
                         tema_id=None, progreso=None, pais=None, institucion_id=None, topic_mode="primary", temas_ids=None):
    if not api_key:
        raise OpenAlexError("Falta OPENALEX_API_KEY en los Secrets de Streamlit.")
    if not (consulta and consulta.strip()) and not (tema_id or temas_ids):
        raise OpenAlexError("Escribe términos o selecciona al menos un tema.")
    if anio_inicial and anio_final and anio_inicial > anio_final:
        raise OpenAlexError("El año inicial no puede superar el final.")
    filtros = []
    if anio_inicial and anio_final:
        filtros.append(f"publication_year:{anio_inicial}-{anio_final}")
    elif anio_inicial:
        filtros.append(f"from_publication_date:{anio_inicial}-01-01")
    elif anio_final:
        filtros.append(f"to_publication_date:{anio_final}-12-31")
    if solo_oa:
        filtros.append("open_access.is_oa:true")
    if solo_pdf:
        filtros.append("has_content.pdf:true")
    if tipo != "Todos":
        filtros.append(f"type:{tipo}")
    topic_list = temas_ids or ([tema_id] if tema_id else [])
    topic_list = [str(t).strip().rsplit("/", 1)[-1] for t in topic_list if str(t).strip()]
    if topic_list:
        campo = "topics.id" if topic_mode == "any" else "primary_topic.id"
        filtros.append(f"{campo}:{'|'.join(topic_list)}")
    if pais:
        filtros.append(f"authorships.countries:{pais.upper()}")
    if institucion_id:
        filtros.append(f"institutions.id:{institucion_id.strip().rsplit('/', 1)[-1]}")
    params = {
        "api_key": api_key,
        "per_page": min(200, limite),
        "cursor": "*",
    }
    if consulta and consulta.strip():
        params["search.title_and_abstract"] = consulta.strip()
    if filtros:
        params["filter"] = ",".join(filtros)
    resultados = []
    ids = set()
    total = None
    with requests.Session() as sesion:
        while len(resultados) < limite:
            respuesta = None
            for intento in range(4):
                try:
                    respuesta = sesion.get(BASE_URL, params=params, timeout=35)
                except requests.RequestException as exc:
                    if intento == 3:
                        raise OpenAlexError(f"Error de conexión con OpenAlex: {exc}") from exc
                    time.sleep(2 ** intento)
                    continue
                if respuesta.status_code in (429, 500, 502, 503, 504) and intento < 3:
                    espera = respuesta.headers.get("Retry-After", "")
                    try:
                        segundos = min(float(espera), 30)
                    except ValueError:
                        segundos = 2 ** intento
                    time.sleep(segundos)
                    continue
                break
            if respuesta is None or not respuesta.ok:
                estado = respuesta.status_code if respuesta is not None else "desconocido"
                raise OpenAlexError(f"OpenAlex devolvió HTTP {estado}. Revisa tu API key, filtros y cuota.")
            try:
                datos = respuesta.json()
            except ValueError as exc:
                raise OpenAlexError("OpenAlex no devolvió un JSON válido.") from exc
            total = datos.get("meta", {}).get("count", total)
            pagina = datos.get("results", [])
            if not pagina:
                break
            for trabajo in pagina:
                identificador = trabajo.get("id")
                if identificador and identificador not in ids:
                    ids.add(identificador)
                    resultados.append(trabajo)
                    if len(resultados) >= limite:
                        break
            if progreso:
                progreso(len(resultados), total)
            cursor = datos.get("meta", {}).get("next_cursor")
            if not cursor or len(resultados) >= limite:
                break
            params["cursor"] = cursor
    return resultados, total, {k: v for k, v in params.items() if k != "api_key"}
