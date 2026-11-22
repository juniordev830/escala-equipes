from datetime import datetime
import pytest
from escala_equipes.planning import Membro, Disponibilidade


def test_planning_name_rejects_delete_character():
    with pytest.raises(ValueError, match="controle"):
        Membro("Ana\x7fLima")
    with pytest.raises(ValueError, match="controle"):
        Disponibilidade("Ana\x7fLima", datetime(2026, 11, 22, 9), datetime(2026, 11, 22, 10))


def test_normal_name_still_valid():
    assert Membro("Ana Lima").nome == "Ana Lima"
