"""Redes no dirigidas con peso por número de publicaciones compartidas."""
from itertools import combinations
import networkx as nx
import pandas as pd

def build_network(df, kind="authors"):
    if kind not in ("authors", "institutions"):
        raise ValueError("Tipo de red no válido")
    id_col, name_col = (("Author IDs", "Authors") if kind == "authors" else ("Institution IDs", "Institutions"))
    G = nx.Graph()
    if id_col not in df or name_col not in df:
        return G
    for _, row in df.iterrows():
        ids = [x.strip() for x in str(row[id_col] or "").split(";") if x.strip() and x.strip().lower() != "nan"]
        names = [x.strip() for x in str(row[name_col] or "").split(";")]
        pairs = dict(zip(ids, names))
        for node, label in pairs.items():
            G.add_node(node, label=label or node)
        for a,b in combinations(sorted(pairs), 2):
            if G.has_edge(a,b): G[a][b]["weight"] += 1
            else: G.add_edge(a,b,weight=1)
    return G

def node_table(G):
    if not G: return pd.DataFrame(columns=["ID", "Nombre", "Grado", "Centralidad intermediación"])
    # Exact betweenness can be expensive for very large graphs: use a reproducible sample.
    if len(G)>300:
        bet = nx.betweenness_centrality(G,k=100,seed=42)
    else:
        bet = nx.betweenness_centrality(G)
    return pd.DataFrame([{"ID":n,"Nombre":G.nodes[n].get("label",n),"Grado":G.degree(n),"Centralidad intermediación":round(bet[n],6)} for n in G]).sort_values("Grado",ascending=False)
