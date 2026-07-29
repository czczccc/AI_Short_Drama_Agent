from sqlalchemy import create_engine, inspect, text

from app.database.session import (
    ensure_project_characters_json_column,
    ensure_project_memory_json_column,
)


def test_existing_sqlite_project_table_gets_characters_json_column(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE projects ("
                "id INTEGER PRIMARY KEY, "
                "name VARCHAR(200) NOT NULL, "
                "status VARCHAR(50) NOT NULL"
                ")"
            )
        )

    ensure_project_characters_json_column(engine)
    ensure_project_characters_json_column(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("projects")}
    assert "characters_json" in columns
    engine.dispose()


def test_existing_sqlite_project_table_gets_memory_json_column(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy_memory.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE projects ("
                "id INTEGER PRIMARY KEY, "
                "name VARCHAR(200) NOT NULL, "
                "status VARCHAR(50) NOT NULL"
                ")"
            )
        )

    ensure_project_memory_json_column(engine)
    ensure_project_memory_json_column(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("projects")}
    assert "memory_json" in columns
    engine.dispose()
