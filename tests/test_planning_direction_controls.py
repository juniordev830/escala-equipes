from datetime import datetime
import pytest
from escala_equipes.planning import Demanda, Disponibilidade, Membro


def test_staff_and_skill_names_reject_bidi_controls():
    for name in ("Ana\u202eFalsa", "Ana\u2066Falsa"):
        with pytest.raises(ValueError, match="controle"):
            Membro(name)
        with pytest.raises(ValueError, match="controle"):
            Membro("Ana", habilidades=(name,))

    start = datetime(2026, 11, 22, 9)
    end = datetime(2026, 11, 22, 10)
    with pytest.raises(ValueError, match="controle"):
        Disponibilidade("Ana\u202e", start, end)
    with pytest.raises(ValueError, match="controle"):
        Demanda("evento\u2066", start, end)


def test_legitimate_names_remain_supported():
    assert Membro("João Silva", habilidades=("Violão",)).habilidades == ("violão",)
