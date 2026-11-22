from datetime import datetime, timedelta
import pytest
from escala_equipes.core import Turno


def test_shift_rejects_unicode_direction_controls():
    start = datetime(2026, 11, 22, 8)
    for name in ("João\u202eFalso", "João\u2066Falso", "João\u202c"):
        with pytest.raises(ValueError, match="controle"):
            Turno(name, start, start + timedelta(hours=1))


def test_legitimate_name_with_accents_remains_valid():
    start = datetime(2026, 11, 22, 8)
    assert Turno("João Mário", start, start + timedelta(hours=1)).pessoa == "João Mário"
