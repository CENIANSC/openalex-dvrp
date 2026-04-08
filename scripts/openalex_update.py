import requests
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os

# --- Configuración ---
QUERY = "Dynamic Vehicle Routing Problem OR DVRP"
DB_PATH = "db/articulos_dvrp.db"

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = "destinatario@example.com"

# --- Funciones ---
def buscar_articulos(query=QUERY):
    url = f"https://api.openalex.org/works?search={query}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["results"]

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS articulos (
                    id TEXT PRIMARY KEY,
                    titulo TEXT,
                    autores TEXT,
                    año INTEGER,
                    resumen TEXT,
                    json_url TEXT
                )""")
    conn.commit()
    conn.close()

def guardar_articulos(articulos):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    nuevos = []
    for art in articulos:
        autores = ", ".join([a["author"]["display_name"] for a in art.get("authorships", [])])
        datos = (
            art["id"],
            art["title"],
            autores,
            art["publication_year"],
            art.get("abstract", ""),
            art["id"]  # URL JSON de OpenAlex
        )
        try:
            c.execute("INSERT INTO articulos VALUES (?, ?, ?, ?, ?, ?)", datos)
            nuevos.append(art)
        except sqlite3.IntegrityError:
            # Ya existe, lo ignoramos
            pass
    conn.commit()
    conn.close()
    return nuevos

def enviar_notificacion(nuevos):
    if not nuevos:
        return
    cuerpo = "Se encontraron nuevos artículos:\n\n" + "\n".join([art["title"] for art in nuevos])
    msg = MIMEText(cuerpo)
    msg["Subject"] = "Nuevos artículos DVRP en OpenAlex"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# --- Flujo principal ---
def main():
    inicializar_db()
    articulos = buscar_articulos()
    nuevos = guardar_articulos(articulos)

if __name__ == "__main__":
    main()

