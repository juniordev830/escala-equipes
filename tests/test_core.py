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

def test_shift_rejects_bad_people_and_datetime_types():
    start = datetime(2026, 11, 21, 8)
    for value in (None, 123, " ", "A" * 81, "Pessoa\nInvalida"):
        with pytest.raises(ValueError):
            Turno(value, start, start + timedelta(hours=1))
    for initial, ending in (("08:00", start), (start, "09:00")):
        with pytest.raises(ValueError):
            Turno("Ana", initial, ending)


def test_shift_rejects_mixed_timezone_awareness():
    from datetime import timezone
    start = datetime(2026, 11, 21, 8)
    with pytest.raises(ValueError, match="fuso"):
        Turno("Ana", start, (start + timedelta(hours=1)).replace(tzinfo=timezone.utc))


def test_detect_conflicts_rejects_non_shift_members():
    with pytest.raises(ValueError, match="Turno"):
        detectar_conflitos([None])
    with pytest.raises(ValueError, match="Turno"):
        detectar_conflitos(None)


def test_conflict_check_rejects_mixed_timezone_awareness_between_shifts():
    from datetime import timezone
    start = datetime(2026, 11, 21, 8)
    naive = Turno("Ana", start, start + timedelta(hours=1))
    aware = Turno("Ana", start.replace(tzinfo=timezone.utc),
                  (start + timedelta(hours=1)).replace(tzinfo=timezone.utc))
    with pytest.raises(ValueError, match="fuso"):
        naive.conflita(aware)
    with pytest.raises(ValueError, match="fuso"):
        detectar_conflitos([naive, aware])


def test_legacy_conflict_requires_another_shift_record():
    start = datetime(2026, 11, 21, 8)
    shift = Turno("Ana", start, start + timedelta(hours=1))
    with pytest.raises(ValueError, match="inválido"):
        shift.conflita(None)
