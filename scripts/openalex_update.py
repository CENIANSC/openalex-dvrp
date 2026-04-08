import requests
import sqlite3

# Conexión a la base de datos SQLite
conn = sqlite3.connect("db/articulos_dvrp.db")
cur = conn.cursor()

# Crear tabla con más campos de OpenAlex
cur.execute("""
CREATE TABLE IF NOT EXISTS articulos (
    id TEXT PRIMARY KEY,
    doi TEXT,
    title TEXT,
    publication_year INTEGER,
    publication_date TEXT,
    type TEXT,
    cited_by_count INTEGER,
    is_retracted BOOLEAN,
    abstract_inverted_index TEXT,
    authors TEXT,
    institutions TEXT,
    concepts TEXT,
    referenced_works TEXT,
    host_venue TEXT,
    language TEXT,
    open_access TEXT,
    primary_location TEXT,
    updated_date TEXT
)
""")

# URL base de OpenAlex con cursor pagination
url = "https://api.openalex.org/works"
params = {
    "filter": "host_venue.publisher:Facultad de Ingenieria-UNAM",  # ajusta tu filtro
    "per_page": 200,
    "cursor": "*"
}

while True:
    r = requests.get(url, params=params)
    data = r.json()

    for work in data["results"]:
        cur.execute("""
        INSERT OR REPLACE INTO articulos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            work.get("id"),
            work.get("doi"),
            work.get("title"),
            work.get("publication_year"),
            work.get("publication_date"),
            work.get("type"),
            work.get("cited_by_count"),
            work.get("is_retracted"),
            str(work.get("abstract_inverted_index")),
            str(work.get("authorships")),
            str(work.get("institutions")),
            str(work.get("concepts")),
            str(work.get("referenced_works")),
            str(work.get("host_venue")),
            work.get("language"),
            str(work.get("open_access")),
            str(work.get("primary_location")),
            work.get("updated_date")
        ))

    conn.commit()

    # Avanzar al siguiente cursor
    next_cursor = data.get("meta", {}).get("next_cursor")
    if not next_cursor:
        break
    params["cursor"] = next_cursor

conn.close()

