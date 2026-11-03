from datetime import datetime, timedelta
import pytest
from escala_equipes import Turno, detectar_conflitos


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
