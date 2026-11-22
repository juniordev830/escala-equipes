from datetime import datetime, timedelta
import pytest
from escala_equipes.core import Turno, detectar_conflitos


def test_conflict_detection_rejects_oversized_quadratic_workload():
    start = datetime(2026, 11, 22, 8)
    turn = Turno("João", start, start + timedelta(hours=1))
    with pytest.raises(ValueError, match="2000"):
        detectar_conflitos([turn] * 2001)


def test_normal_schedule_conflict_detection_remains_available():
    start = datetime(2026, 11, 22, 8)
    turn = Turno("João", start, start + timedelta(hours=1))
    assert detectar_conflitos([turn, turn]) == [(turn, turn)]
