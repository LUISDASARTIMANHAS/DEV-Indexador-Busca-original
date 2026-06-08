from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


_VERSION_FILE_METADATA_COLUMNS = {
    "nome_arquivo_original": "VARCHAR(255)",
    "mime_type": "VARCHAR(255)",
    "tamanho_bytes": "INTEGER",
    "hash_arquivo": "VARCHAR(64)",
}

_OCR_COLUMNS = {
    "ocr_executado": "BOOLEAN DEFAULT FALSE NOT NULL",
    "ocr_status": "VARCHAR(50)",
    "ocr_idioma": "VARCHAR(20)",
    "ocr_paginas_processadas": "INTEGER",
    "ocr_tempo_ms": "INTEGER",
    "ocr_erro": "TEXT",
    "ocr_executado_em": "TIMESTAMP",
}


def ensure_version_file_metadata_columns(engine: Engine) -> None:
    existing_columns = {
        column["name"]
        for column in inspect(engine).get_columns("historico_documento")
    }
    missing_columns = [
        (column_name, column_type)
        for column_name, column_type in _VERSION_FILE_METADATA_COLUMNS.items()
        if column_name not in existing_columns
    ]
    if not missing_columns:
        return

    with engine.begin() as connection:
        for column_name, column_type in missing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE historico_documento "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )


def ensure_ocr_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("historico_documento"):
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("historico_documento")
    }
    missing_columns = [
        (column_name, column_type)
        for column_name, column_type in _OCR_COLUMNS.items()
        if column_name not in existing_columns
    ]
    if not missing_columns:
        return

    with engine.begin() as connection:
        for column_name, column_type in missing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE historico_documento "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )


def ensure_full_text_search_schema(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return

    statements = [
        """
        CREATE OR REPLACE FUNCTION ifesdoc_search_config()
        RETURNS regconfig AS $$
            SELECT COALESCE(
                (SELECT oid::regconfig FROM pg_ts_config WHERE cfgname = 'portuguese' LIMIT 1),
                'pg_catalog.simple'::regconfig
            );
        $$ LANGUAGE sql IMMUTABLE
        """,
        "ALTER TABLE historico_documento ADD COLUMN IF NOT EXISTS search_vector tsvector",
        """
        CREATE OR REPLACE FUNCTION historico_documento_search_vector_update()
        RETURNS trigger AS $$
        DECLARE
            document_title TEXT;
        BEGIN
            SELECT titulo
            INTO document_title
            FROM documento
            WHERE cod_documento = NEW.cod_documento;

            NEW.search_vector :=
                setweight(to_tsvector(ifesdoc_search_config(), coalesce(document_title, '')), 'A') ||
                setweight(to_tsvector(ifesdoc_search_config(), coalesce(NEW.texto_extraido, '')), 'B') ||
                setweight(to_tsvector(ifesdoc_search_config(), coalesce(NEW.nome_arquivo_original, '')), 'C');

            RETURN NEW;
        END
        $$ LANGUAGE plpgsql
        """,
        "DROP TRIGGER IF EXISTS trg_historico_documento_search_vector_update ON historico_documento",
        """
        CREATE TRIGGER trg_historico_documento_search_vector_update
        BEFORE INSERT OR UPDATE OF texto_extraido, texto_processado, nome_arquivo_original, cod_documento
        ON historico_documento
        FOR EACH ROW
        EXECUTE FUNCTION historico_documento_search_vector_update()
        """,
        """
        CREATE OR REPLACE FUNCTION documento_refresh_history_search_vector()
        RETURNS trigger AS $$
        BEGIN
            UPDATE historico_documento
            SET texto_extraido = texto_extraido
            WHERE cod_documento = NEW.cod_documento;

            RETURN NEW;
        END
        $$ LANGUAGE plpgsql
        """,
        "DROP TRIGGER IF EXISTS trg_documento_refresh_history_search_vector ON documento",
        """
        CREATE TRIGGER trg_documento_refresh_history_search_vector
        AFTER UPDATE OF titulo
        ON documento
        FOR EACH ROW
        EXECUTE FUNCTION documento_refresh_history_search_vector()
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_historico_documento_search_vector
        ON historico_documento
        USING GIN(search_vector)
        """,
        """
        UPDATE historico_documento
        SET texto_extraido = texto_extraido
        WHERE search_vector IS NULL
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
