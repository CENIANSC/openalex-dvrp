"""Búsqueda de temas OpenAlex. No almacena ni expone la clave."""
import requests
from core.openalex_client import OpenAlexError


def search_topics(api_key, query, limit=20):
    if not api_key:
        raise OpenAlexError('Falta OPENALEX_API_KEY en Secrets.')
    if not query.strip():
        return []
    try:
        response = requests.get('https://api.openalex.org/topics', params={'search': query.strip(), 'per_page': min(limit, 50), 'api_key': api_key}, timeout=25)
        response.raise_for_status()
        return [{'id': x.get('id', '').rsplit('/', 1)[-1], 'name': x.get('display_name', ''),
                 'works_count': x.get('works_count', 0), 'field': (x.get('field') or {}).get('display_name', ''),
                 'subfield': (x.get('subfield') or {}).get('display_name', '')} for x in response.json().get('results', [])]
    except (requests.RequestException, ValueError) as exc:
        raise OpenAlexError(f'No fue posible consultar los temas: {exc}') from exc
