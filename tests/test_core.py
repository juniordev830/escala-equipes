from datetime import datetime, timedelta
import pytest
from escala_equipes import Turno, detectar_conflitos, ResumoCarga, resumir_carga_horaria


def test_detects_same_person_overlapping_shifts():
    start = datetime(2026, 11, 3, 8)
    shifts = [
        Turno("Ana", start, start + timedelta(hours=4)),
        Turno(" ana ", start + timedelta(hours=3), start + timedelta(hours=5)),
        Turno("Bruno", start + timedelta(hours=3), start + timedelta(hours=5)),
    ]
    conflicts = detectar_conflitos(shifts)
    assert len(conflicts) == 1
    assert conflicts[0][0].pessoa == "Ana"


def test_different_people_can_work_at_same_time_and_adjacent_shifts_are_valid():
    start = datetime(2026, 11, 3, 8)
    shifts = [
        Turno("Ana", start, start + timedelta(hours=4)),
        Turno("Bruno", start, start + timedelta(hours=4)),
        Turno("Ana", start + timedelta(hours=4), start + timedelta(hours=8)),
    ]
    assert detectar_conflitos(shifts) == []


def test_rejects_invalid_shift():
    start = datetime(2026, 11, 3, 8)
    with pytest.raises(ValueError):
        Turno("", start, start + timedelta(hours=1))
    with pytest.raises(ValueError):
        Turno("Ana", start, start)


def test_sums_hours_by_person_across_adjacent_and_overnight_shifts():
    start = datetime(2026, 11, 3, 20)
    shifts = [
        Turno("Ana", start, start + timedelta(hours=4)),
        Turno(" ana ", start + timedelta(hours=4), start + timedelta(hours=8)),
        Turno("Bruno", start, start + timedelta(hours=6, minutes=30)),
    ]
    assert resumir_carga_horaria(shifts) == [
        ResumoCarga("Ana", 2, timedelta(hours=8)),
        ResumoCarga("Bruno", 1, timedelta(hours=6, minutes=30)),
    ]
    assert len(shifts) == 3


def test_empty_shift_roster_has_no_scheduled_hours():
    assert resumir_carga_horaria([]) == []


def test_overlapping_shifts_are_rejected_before_hours_are_counted():
    start = datetime(2026, 11, 3, 8)
    shifts = [
        Turno("ANA", start, start + timedelta(hours=4)),
        Turno("ana", start + timedelta(hours=3), start + timedelta(hours=5)),
    ]
    with pytest.raises(ValueError, match="sobrepostos"):
        resumir_carga_horaria(shifts)
