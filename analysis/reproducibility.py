"""Manifiesto portable de la búsqueda sin credenciales."""
import json
import hashlib
import pandas as pd


def manifest(method, df):
    ids = sorted(str(x) for x in df.get('OpenAlex ID', pd.Series(dtype=str)).dropna())
    return {**method, 'identificadores_sha256': hashlib.sha256('\n'.join(ids).encode('utf-8')).hexdigest(),
            'identificadores_contados': len(ids), 'version_esquema': '2.2'}


def manifest_bytes(method, df):
    return json.dumps(manifest(method, df), ensure_ascii=False, indent=2, default=str).encode('utf-8')
