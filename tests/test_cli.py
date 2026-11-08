import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def cli(file, *args):
    return subprocess.run(
        [sys.executable, "-m", "escala_equipes.cli", "--file", str(file), *args],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_end_to_end_staff_and_schedule(tmp_path):
    storage = tmp_path / "staff.json"
    first = cli(storage, "add-member", "Ana", "--skills", "qa,python")
    assert first.returncode == 0, first.stderr
    assert "Ana" in first.stdout

    second = cli(storage, "add-member", "Bruno", "--skills", "qa")
    assert second.returncode == 0, second.stderr

    for name in ("Ana", "Bruno"):
        available = cli(
            storage, "available", name,
            "2026-11-09T08:00", "2026-11-09T16:00",
        )
        assert available.returncode == 0, available.stderr

    assignment = cli(
        storage, "assign", "test-01",
        "2026-11-09T09:00", "2026-11-09T11:00",
        "--slots", "2", "--skill", "qa",
    )
    assert assignment.returncode == 0, assignment.stderr
    assert "2 pessoa(s)" in assignment.stdout

    listing = cli(storage, "list")
    assert listing.returncode == 0
    assert "test-01" in listing.stdout
    assert "Ana" in listing.stdout
    assert "Bruno" in listing.stdout

    summary = cli(storage, "summary", "2026-11-09")
    assert summary.returncode == 0
    assert "turnos: 2" in summary.stdout
    assert "conflitos: 0" in summary.stdout

    cancelled = cli(storage, "cancel", "test-01")
    assert cancelled.returncode == 0, cancelled.stderr
    assert "2 alocação(ões)" in cancelled.stdout
    assert "Nenhuma alocação" in cli(storage, "list").stdout


def test_invalid_inputs_do_not_overwrite_schedule(tmp_path):
    storage = tmp_path / "staff.json"
    assert cli(storage, "add-member", "Ana").returncode == 0
    initial = storage.read_bytes()
    duplicate = cli(storage, "add-member", "ana")
    assert duplicate.returncode != 0
    assert storage.read_bytes() == initial

    missing = cli(
        storage, "available", "Desconhecido",
        "2026-11-09T08:00", "2026-11-09T12:00",
    )
    assert missing.returncode != 0
    assert storage.read_bytes() == initial

    failed = cli(
        storage, "assign", "no-availability",
        "2026-11-09T09:00", "2026-11-09T11:00",
    )
    assert failed.returncode != 0
    assert storage.read_bytes() == initial


def test_help_without_command(tmp_path):
    result = cli(tmp_path / "missing.json")
    assert result.returncode == 0
    assert "usage:" in result.stdout
