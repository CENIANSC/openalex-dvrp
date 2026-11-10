"""Mapeo científico descriptivo de un subconjunto OpenAlex.

Las etiquetas temáticas provienen de OpenAlex, no son palabras clave de autor.
Las redes de referencias están limitadas a las referencias disponibles en los registros descargados.
"""
from collections import Counter, defaultdict
from itertools import combinations
import math
import networkx as nx
import pandas as pd


def tokens(value):
    if not isinstance(value, str):
        return []
    return list(dict.fromkeys(x.strip() for x in value.split(';') if x.strip()))


def topic_network(df, min_occurrences=2, max_topics=60):
    counts = Counter(t for value in df.get('Themes', []) for t in tokens(value))
    allowed = {t for t, n in counts.most_common(max_topics) if n >= min_occurrences}
    graph = nx.Graph()
    for topic in allowed:
        graph.add_node(topic, label=topic, frequency=counts[topic])
    for value in df.get('Themes', []):
        for a, b in combinations(sorted(allowed.intersection(tokens(value))), 2):
            if graph.has_edge(a, b):
                graph[a][b]['weight'] += 1
            else:
                graph.add_edge(a, b, weight=1)
    return graph


def communities(graph):
    if not graph:
        return {}
    groups = nx.community.greedy_modularity_communities(graph, weight='weight') if graph.number_of_edges() else [{n} for n in graph]
    return {node: i + 1 for i, group in enumerate(groups) for node in group}


def topic_table(graph):
    cols = ['Tema', 'Publicaciones', 'Grado', 'Fuerza', 'Comunidad']
    clusters = communities(graph)
    return pd.DataFrame([{'Tema': n, 'Publicaciones': d['frequency'], 'Grado': graph.degree(n),
                          'Fuerza': sum(e.get('weight', 1) for e in graph[n].values()),
                          'Comunidad': clusters[n]} for n, d in graph.nodes(data=True)], columns=cols).sort_values('Publicaciones', ascending=False)


def thematic_evolution(df, periods=3, max_topics=12):
    cols = ['Periodo', 'Tema', 'Publicaciones']
    if df.empty or 'Year' not in df or 'Themes' not in df:
        return pd.DataFrame(columns=cols)
    years = pd.to_numeric(df['Year'], errors='coerce')
    valid = years.dropna()
    if valid.empty:
        return pd.DataFrame(columns=cols)
    lo, hi = int(valid.min()), int(valid.max())
    width = max(1, math.ceil((hi - lo + 1) / max(1, periods)))
    count = Counter(t for val in df['Themes'] for t in tokens(val))
    selected = {x for x, _ in count.most_common(max_topics)}
    results = Counter()
    for (_, row), year in zip(df.iterrows(), years):
        if pd.isna(year):
            continue
        start = lo + ((int(year) - lo) // width) * width
        label = f'{start}–{min(start + width - 1, hi)}'
        for t in selected.intersection(tokens(row.get('Themes'))):
            results[(label, t)] += 1
    return pd.DataFrame([{'Periodo': p, 'Tema': t, 'Publicaciones': n} for (p, t), n in sorted(results.items())], columns=cols)


def emerging_topics(df, recent_years=3, min_total=3):
    cols = ['Tema', 'Anterior', 'Reciente', 'Proporción anterior', 'Proporción reciente', 'Diferencia (pp)']
    if df.empty or 'Year' not in df or 'Themes' not in df:
        return pd.DataFrame(columns=cols)
    years = pd.to_numeric(df['Year'], errors='coerce')
    if years.dropna().empty:
        return pd.DataFrame(columns=cols)
    cutoff = int(years.max()) - recent_years + 1
    recent, earlier = Counter(), Counter()
    nr = ne = 0
    for (_, row), year in zip(df.iterrows(), years):
        if pd.isna(year):
            continue
        if year >= cutoff:
            recent.update(tokens(row.get('Themes'))); nr += 1
        else:
            earlier.update(tokens(row.get('Themes'))); ne += 1
    if not nr or not ne:
        return pd.DataFrame(columns=cols)
    rows = []
    for topic in recent.keys() | earlier.keys():
        if recent[topic] + earlier[topic] < min_total:
            continue
        before, after = earlier[topic] / ne, recent[topic] / nr
        rows.append({'Tema': topic, 'Anterior': earlier[topic], 'Reciente': recent[topic],
                     'Proporción anterior': round(before, 4), 'Proporción reciente': round(after, 4),
                     'Diferencia (pp)': round(100 * (after - before), 2)})
    return pd.DataFrame(rows, columns=cols).sort_values('Diferencia (pp)', ascending=False)


def strategic_map(graph):
    cols = ['Comunidad', 'Temas', 'Centralidad externa', 'Densidad interna', 'Clasificación']
    if not graph:
        return pd.DataFrame(columns=cols)
    groups = communities(graph)
    nodes_by_group = defaultdict(list)
    for node, group in groups.items():
        nodes_by_group[group].append(node)
    rows = []
    for group, nodes in nodes_by_group.items():
        sub = graph.subgraph(nodes)
        internal = sum(d.get('weight', 1) for _, _, d in sub.edges(data=True))
        external = sum(d.get('weight', 1) for node in nodes for neighbor, d in graph[node].items() if groups[neighbor] != group)
        # Densidad ponderada por posibles pares; no equivalente a Callon sin normalización adicional.
        density = 2 * internal / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0
        rows.append({'Comunidad': group, 'Temas': '; '.join(sorted(nodes)[:6]),
                     'Centralidad externa': round(external, 4), 'Densidad interna': round(density, 4)})
    result = pd.DataFrame(rows)
    mc, md = result['Centralidad externa'].median(), result['Densidad interna'].median()
    def quadrant(row):
        high_c = row['Centralidad externa'] >= mc
        high_d = row['Densidad interna'] >= md
        return ('Motor' if high_c and high_d else 'Básico/transversal' if high_c else 'Especializado' if high_d else 'Emergente o declinante (no distinguible)')
    result['Clasificación'] = result.apply(quadrant, axis=1)
    return result[cols]


def reference_network(df, mode='coupling', min_shared=2, max_works=300):
    """Acoplamiento: referencias compartidas; citación: enlaces entre trabajos descargados.
    Cocitación: referencias citadas conjuntamente, aunque no estén en el corpus.
    """
    if mode not in ('coupling', 'citation', 'cocitation'):
        raise ValueError('Modo de red no reconocido')
    graph = nx.DiGraph() if mode == 'citation' else nx.Graph()
    if df.empty or 'OpenAlex ID' not in df:
        return graph
    subset = df.head(max_works)
    works = {}
    for _, row in subset.iterrows():
        work_id = str(row.get('OpenAlex ID') or '').strip()
        if work_id and work_id != 'nan':
            works[work_id] = set(tokens(row.get('Referenced works')))
    if mode == 'citation':
        for work_id in works:
            graph.add_node(work_id)
        for work_id, refs in works.items():
            for ref in refs & works.keys():
                if work_id != ref:
                    graph.add_edge(work_id, ref, weight=1)
        return graph
    if mode == 'coupling':
        for work_id in works:
            graph.add_node(work_id)
        inverted = defaultdict(list)
        for work_id, refs in works.items():
            for ref in refs:
                inverted[ref].append(work_id)
    else:
        inverted = defaultdict(list)
        for work_id, refs in works.items():
            for ref in sorted(refs)[:50]:
                graph.add_node(ref)
            for a, b in combinations(sorted(refs)[:50], 2):
                inverted[(a, b)].append(work_id)
        for pair, citing in inverted.items():
            if len(citing) >= min_shared:
                graph.add_edge(*pair, weight=len(citing))
        return graph
    weights = Counter()
    for ids in inverted.values():
        for a, b in combinations(sorted(ids), 2):
            weights[(a, b)] += 1
    for (a, b), n in weights.items():
        if n >= min_shared:
            graph.add_edge(a, b, weight=n)
    return graph


def edge_table(graph):
    return pd.DataFrame([{'Origen': a, 'Destino': b, 'Peso': d.get('weight', 1)} for a, b, d in graph.edges(data=True)], columns=['Origen', 'Destino', 'Peso'])
