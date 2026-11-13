from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from app.common import database


def test_existing_database_and_keys_survive_idempotent_upgrade(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path}/existing.db")
    monkeypatch.setattr(database, "engine", engine)
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    try:
        command.upgrade(cfg, "3a7b9c1d2e3f")
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO roles (id,name) VALUES ('admin','Admin')")
            )
            connection.execute(
                text(
                    "INSERT INTO users (id,username,password_hash,api_key,role_id,"
                    "enable_smart_filter,smart_filter_limit) "
                    "VALUES ('user','existing','existing-hash','existing-api-key','admin',0,1)"
                )
            )
        command.upgrade(cfg, "head")
        with engine.connect() as connection:
            schema = connection.execute(
                text(
                    "SELECT name,sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY name"
                )
            ).all()
        command.upgrade(cfg, "head")
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT username,password_hash,api_key FROM users WHERE id='user'")
            ).one() == ("existing", "existing-hash", "existing-api-key")
            assert (
                connection.execute(
                    text(
                        "SELECT name,sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY name"
                    )
                ).all()
                == schema
            )
            assert (
                connection.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
            )
            assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
    finally:
        engine.dispose()
