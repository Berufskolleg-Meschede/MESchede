"""Verify container startup without touching a database or the PLC."""

from pathlib import Path
import subprocess

import pytest
import yaml


BACKEND_ROOT = Path(__file__).resolve().parents[1]
START_SCRIPT = BACKEND_ROOT / "start.sh"


def test_compose_waits_for_database_readiness_before_running_migrations():
    compose = yaml.safe_load((BACKEND_ROOT.parent / "docker-compose.yaml").read_text())
    services = compose["services"]
    assert "pg_isready" in services["db"]["healthcheck"]["test"][1]
    assert services["backend"]["depends_on"]["db"]["condition"] == "service_healthy"


def test_container_entrypoint_exists_is_executable_and_has_valid_shell_syntax():
    assert START_SCRIPT.is_file()
    assert START_SCRIPT.stat().st_mode & 0o111
    result = subprocess.run(
        ["/bin/sh", "-n", str(START_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("migration_exit_code", [0, 1])
def test_startup_runs_server_only_after_successful_migrations(tmp_path, migration_exit_code):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    call_log = tmp_path / "commands.log"
    for command in ("alembic", "fastapi"):
        executable = fake_bin / command
        executable.write_text(
            "#!/bin/sh\n"
            f'printf \'{command}:%s\\n\' "$*" >> "$STARTUP_TEST_LOG"\n'
            + ('exit "$STARTUP_TEST_ALEMBIC_EXIT"\n' if command == "alembic" else "exit 0\n")
        )
        executable.chmod(0o755)

    result = subprocess.run(
        [str(START_SCRIPT)],
        cwd=tmp_path,
        env={
            "PATH": str(fake_bin),
            "STARTUP_TEST_LOG": str(call_log),
            "STARTUP_TEST_ALEMBIC_EXIT": str(migration_exit_code),
        },
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == migration_exit_code, result.stderr
    expected_commands = ["alembic:upgrade head"]
    if migration_exit_code == 0:
        expected_commands.append("fastapi:run app/main.py --host 0.0.0.0 --port 8000")
    assert call_log.read_text().splitlines() == expected_commands
