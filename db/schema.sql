-- Definición de la base de datos para artículos DVRP
-- Ejecuta este script en SQLite para crear la tabla inicial

CREATE TABLE IF NOT EXISTS articulos (
    id TEXT PRIMARY KEY,              -- Identificador único de OpenAlex
    titulo TEXT NOT NULL,             -- Título del artículo
    autores TEXT,                     -- Lista de autores
    año INTEGER,                      -- Año de publicación
    resumen TEXT,                     -- Resumen del artículo
    json_url TEXT,                    -- URL al JSON completo en OpenAlex
    clasificacion TEXT                -- Clasificación taxonómica (llenada manualmente)
);

-- Índices opcionales para mejorar las búsquedas
CREATE INDEX IF NOT EXISTS idx_autores ON articulos(autores);
CREATE INDEX IF NOT EXISTS idx_año ON articulos(año);
CREATE INDEX IF NOT EXISTS idx_titulo ON articulos(titulo);

