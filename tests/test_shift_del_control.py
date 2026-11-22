from datetime import datetime, timedelta
import pytest
from escala_equipes.core import Turno


def test_person_name_rejects_delete_control():
    start = datetime(2026, 11, 22, 9)
    with pytest.raises(ValueError, match="controle"):
        Turno("Equipe\x7fTeste", start, start + timedelta(hours=1))


def test_valid_portuguese_name_is_accepted():
    start = datetime(2026, 11, 22, 9)
    shift = Turno("João da Silva", start, start + timedelta(hours=2))
    assert shift.pessoa == "João da Silva"
