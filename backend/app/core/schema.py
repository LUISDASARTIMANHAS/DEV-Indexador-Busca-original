from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


_VERSION_FILE_METADATA_COLUMNS = {
    "nome_arquivo_original": "VARCHAR(255)",
    "mime_type": "VARCHAR(255)",
    "tamanho_bytes": "INTEGER",
    "hash_arquivo": "VARCHAR(64)",
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
