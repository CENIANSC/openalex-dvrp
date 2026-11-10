"""Indicadores calculados sobre el conjunto descargado, no sobre todo OpenAlex."""
import pandas as pd

def citation_values(df):
    if "Cited by" not in df.columns:
        return []
    return sorted([max(0, int(x)) for x in pd.to_numeric(df["Cited by"], errors="coerce").fillna(0)], reverse=True)

def h_index(values):
    return sum(c >= i for i, c in enumerate(sorted(values, reverse=True), 1))

def g_index(values):
    values = sorted(values, reverse=True)
    cumulative = 0
    g = 0
    for i, v in enumerate(values, 1):
        cumulative += v
        if cumulative >= i*i:
            g = i
    return g

def summarize(df):
    cites = citation_values(df)
    s = pd.Series(cites, dtype="float64")
    return {"Publicaciones": len(df), "Citas totales": sum(cites), "Promedio citas": round(float(s.mean()), 2) if cites else 0.0,
            "Mediana citas": float(s.median()) if cites else 0.0, "Publicaciones citadas (%)": round(100*sum(v>0 for v in cites)/len(cites), 2) if cites else 0.0,
            "Índice h del conjunto": h_index(cites), "Índice g del conjunto": g_index(cites)}

def yearly(df):
    if "Year" not in df or "Cited by" not in df:
        return pd.DataFrame(columns=["Año", "Publicaciones", "Citas"])
    d = df.copy()
    d["Year"] = pd.to_numeric(d["Year"], errors="coerce")
    d["Cited by"] = pd.to_numeric(d["Cited by"], errors="coerce").fillna(0)
    d = d.dropna(subset=["Year"])
    if d.empty:
        return pd.DataFrame(columns=["Año", "Publicaciones", "Citas"])
    return d.groupby("Year").agg(Publicaciones=("Year", "size"), Citas=("Cited by", "sum")).reset_index().rename(columns={"Year":"Año"})
