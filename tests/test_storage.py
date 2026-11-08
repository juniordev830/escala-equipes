import json
from datetime import datetime

import pytest

from escala_equipes.planning import Demanda, Disponibilidade, Escalador, Membro
from escala_equipes.storage import load_schedule, save_schedule


def make_schedule():
    agenda = Escalador()
    agenda.adicionar_membro(Membro("Ana", habilidades=("qa",)))
    agenda.adicionar_membro(Membro("Bruno", horas_semana=16, horas_dia=4))
    agenda.informar_disponibilidade(Disponibilidade(
        "Ana", datetime(2026, 11, 9, 8), datetime(2026, 11, 9, 16)
    ))
    agenda.informar_disponibilidade(Disponibilidade(
        "Bruno", datetime(2026, 11, 9, 8), datetime(2026, 11, 9, 12)
    ))
    agenda.alocar(Demanda(
        "chamado-1", datetime(2026, 11, 9, 9),
        datetime(2026, 11, 9, 10), habilidade="qa"
    ))
    return agenda


def test_new_file_loads_empty_schedule(tmp_path):
    assert load_schedule(tmp_path / "missing.json").membros == ()


def test_round_trip_preserves_members_availability_and_allocations(tmp_path):
    filename = tmp_path / "private" / "schedule.json"
    agenda = make_schedule()
    assert save_schedule(agenda, filename) == 1
    restored = load_schedule(filename)
    assert restored.membros == agenda.membros
    assert restored.disponibilidades == agenda.disponibilidades
    assert restored.alocacoes == agenda.alocacoes
    assert restored.conflitos() == []
    data = json.loads(filename.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1


def test_save_rejects_invalid_object_without_changing_original(tmp_path):
    filename = tmp_path / "schedule.json"
    save_schedule(make_schedule(), filename)
    previous = filename.read_bytes()
    with pytest.raises(ValueError):
        save_schedule(object(), filename)
    assert filename.read_bytes() == previous


def test_rejects_bad_json_and_unsupported_schema(tmp_path):
    filename = tmp_path / "schedule.json"
    for raw in (
        "{invalid",
        '{"schema_version":2,"members":[],"availability":[],"allocations":[]}',
        '{"schema_version":1,"members":[],"availability":null,"allocations":[]}',
    ):
        filename.write_text(raw, encoding="utf-8")
        with pytest.raises(ValueError):
            load_schedule(filename)


def test_rejects_unknown_staff_and_overlapping_data(tmp_path):
    filename = tmp_path / "schedule.json"
    save_schedule(make_schedule(), filename)
    data = json.loads(filename.read_text(encoding="utf-8"))
    data["allocations"][0]["name"] = "Ficticio"
    filename.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="inválidos"):
        load_schedule(filename)

    save_schedule(make_schedule(), filename)
    data = json.loads(filename.read_text(encoding="utf-8"))
    data["allocations"].append({
        "code": "chamado-2",
        "name": "Ana",
        "start": "2026-11-09T09:30:00",
        "end": "2026-11-09T10:30:00",
    })
    filename.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="inválidos"):
        load_schedule(filename)


def test_rejects_file_over_one_megabyte(tmp_path):
    filename = tmp_path / "huge.json"
    filename.write_bytes(b"x" * 1_000_001)
    with pytest.raises(ValueError, match="1 MB"):
        load_schedule(filename)
