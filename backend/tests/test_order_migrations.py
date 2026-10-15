"""Reale Alembic-Upgrades in leeren und bereits verwendeten Testschemas."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text


def migration_config():
    """Lädt den Migrationsgraph unabhängig vom aktuellen Arbeitsverzeichnis."""
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / 'alembic.ini'))
    config.set_main_option('script_location', str(root / 'alembic'))
    return config


def migrate(engine, revision):
    """Verwendet eine explizite Testverbindung statt Projekt-env-Dateien."""
    config = migration_config()
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, revision)


def test_migration_graph_has_one_head_for_container_startup():
    """Der Container verwendet upgrade head und benötigt deshalb genau ein Ziel."""
    heads = ScriptDirectory.from_config(migration_config()).get_heads()
    assert len(heads) == 1, f'Parallele Migrationsstände verhindern den Containerstart: {heads}'


def test_fresh_migration_creates_order_domain_and_initial_state(isolated_postgres_engine):
    migrate(isolated_postgres_engine, 'head')
    names = set(inspect(isolated_postgres_engine).get_table_names())
    assert {'mes_order', 'order_run', 'product_unit', 'run_review', 'dispatch_state', 'plc_source_state',
            'plc_catalog_product', 'plc_catalog_state', 'storage_outbox_event'} <= names
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


@pytest.mark.parametrize('revisions', [
    ('plc_catalog_01',),
    ('storage_outbox_01',),
    ('plc_catalog_01', 'storage_outbox_01'),
])
def test_merge_upgrades_either_existing_branch_without_losing_data(isolated_postgres_engine, revisions):
    """Erhält bereits befüllte Katalog-/Outboxtabellen aus beiden Featurezweigen."""
    for revision in revisions:
        migrate(isolated_postgres_engine, revision)
    with isolated_postgres_engine.begin() as connection:
        if 'plc_catalog_01' in revisions:
            connection.execute(text(
                "INSERT INTO plc_catalog_product "
                "(product_id,product_text,specification,available,observed_at) "
                "VALUES (1,'Testprodukt','{}',true,now())"
            ))
        if 'storage_outbox_01' in revisions:
            connection.execute(text(
                "INSERT INTO storage_outbox_event (event_id,product_id,quantity_delta,created_at) "
                "VALUES ('test-existing-event',1,1,now())"
            ))

    migrate(isolated_postgres_engine, 'head')

    assert {'plc_catalog_product', 'plc_catalog_state', 'storage_outbox_event'} <= set(
        inspect(isolated_postgres_engine).get_table_names()
    )
    with isolated_postgres_engine.connect() as connection:
        heads = connection.execute(text('SELECT version_num FROM alembic_version')).scalars().all()
        assert heads == ScriptDirectory.from_config(migration_config()).get_heads()
        if 'plc_catalog_01' in revisions:
            assert connection.execute(text(
                'SELECT product_text FROM plc_catalog_product WHERE product_id=1'
            )).scalar_one() == 'Testprodukt'
        if 'storage_outbox_01' in revisions:
            assert connection.execute(text(
                "SELECT quantity_delta FROM storage_outbox_event WHERE event_id='test-existing-event'"
            )).scalar_one() == 1
