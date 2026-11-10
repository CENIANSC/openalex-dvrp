"""Comparaciones descriptivas basadas en el conjunto descargado."""
import pandas as pd


def compare_periods(df, start_a, end_a, start_b, end_b):
    d = df.copy()
    d['Year'] = pd.to_numeric(d['Year'], errors='coerce')
    d['Cited by'] = pd.to_numeric(d['Cited by'], errors='coerce').fillna(0)
    rows = []
    for label, start, end in [('Periodo A', start_a, end_a), ('Periodo B', start_b, end_b)]:
        part = d[d['Year'].between(start, end)]
        rows.append({'Periodo': label, 'Años': f'{start}–{end}', 'Publicaciones': len(part),
                     'Citas acumuladas': int(part['Cited by'].sum()),
                     'Promedio de citas': round(float(part['Cited by'].mean()), 2) if len(part) else 0})
    return pd.DataFrame(rows)


def compare_entities(df, column, limit=20):
    counts = {}
    for _, row in df.iterrows():
        entities = set(x.strip() for x in str(row.get(column) or '').split(';') if x.strip() and x.strip() != 'nan')
        for entity in entities:
            counts[entity] = counts.get(entity, 0) + 1
    return pd.DataFrame(sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:limit], columns=[column, 'Publicaciones'])


def international_collaboration(df):
    countries = df.get('Countries', pd.Series(dtype=str)).fillna('')
    return int(sum(len(set(x.strip() for x in value.split(';') if x.strip())) >= 2 for value in countries))
