"""Reale Alembic-Upgrades in leeren und bereits verwendeten Testschemas."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text


def migrate(engine, revision):
    """Verwendet eine explizite Testverbindung statt Projekt-env-Dateien."""
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'alembic'))
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, revision)


def test_fresh_migration_creates_order_domain_and_initial_state(isolated_postgres_engine):
    migrate(isolated_postgres_engine, 'head')
    names = set(inspect(isolated_postgres_engine).get_table_names())
    assert {'mes_order', 'order_run', 'product_unit', 'run_review', 'dispatch_state', 'plc_source_state'} <= names
    with isolated_postgres_engine.connect() as connection:
        assert connection.execute(text('SELECT accepted_sequence FROM dispatch_state WHERE id=1')).scalar_one() == 0
        assert connection.execute(text('SELECT COUNT(*) FROM plc_source_state')).scalar_one() == 2


def test_upgrade_preserves_existing_machine_and_user_rows(isolated_postgres_engine):
    migrate(isolated_postgres_engine, '13bbe5395414')
    with isolated_postgres_engine.begin() as connection:
        connection.execute(text("INSERT INTO machine (id,name,type,status) VALUES (1,'Testanlage','Test','OFFLINE')"))
        connection.execute(text("INSERT INTO \"user\" (id,email) VALUES (1,'test@example.invalid')"))
    migrate(isolated_postgres_engine, 'head')
    with isolated_postgres_engine.connect() as connection:
        assert connection.execute(text('SELECT name FROM machine WHERE id=1')).scalar_one() == 'Testanlage'
        assert connection.execute(text('SELECT email FROM "user" WHERE id=1')).scalar_one() == 'test@example.invalid'
