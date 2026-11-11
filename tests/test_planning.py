from datetime import datetime, timedelta

import pytest

from escala_equipes.planning import (
    Alocacao, Demanda, Disponibilidade, Escalador, Membro,
)


BASE = datetime(2026, 11, 9, 8)


def when(hours=0, minutes=0):
    return BASE + timedelta(hours=hours, minutes=minutes)


def planner_with_staff():
    planner = Escalador()
    planner.adicionar_membro(Membro("Ana", habilidades=("Python", "QA")))
    planner.adicionar_membro(Membro("Bruno", habilidades=("qa",)))
    planner.adicionar_membro(Membro("Carlos", horas_semana=8, horas_dia=4))
    for name in ("Ana", "Bruno", "Carlos"):
        planner.informar_disponibilidade(
            Disponibilidade(name, when(0), when(8))
        )
    return planner


def test_members_validate_hours_and_skills():
    member = Membro(" Ana ", habilidades=("Python",))
    assert member.nome == "Ana"
    assert member.habilidades == ("python",)
    for kwargs in (
        {"nome": " "},
        {"nome": "bad\nname"},
        {"nome": "A", "horas_semana": 0},
        {"nome": "A", "horas_dia": 0},
        {"nome": "A", "horas_semana": 5, "horas_dia": 8},
        {"nome": "A", "habilidades": ("Python", "python")},
    ):
        with pytest.raises(ValueError):
            Membro(**kwargs)


def test_shift_intervals_must_be_same_day_and_naive():
    with pytest.raises(ValueError):
        Disponibilidade("Ana", when(0), when(0))
    with pytest.raises(ValueError):
        Disponibilidade("Ana", when(0), when(0, 20))
    with pytest.raises(ValueError):
        Disponibilidade("Ana", when(0), when(13))
    with pytest.raises(ValueError):
        Disponibilidade("Ana", when(0), when(24))
    with pytest.raises(ValueError):
        Demanda("D", when(0), when(1), vagas=0)


def test_member_and_availability_are_unique():
    planner = planner_with_staff()
    with pytest.raises(ValueError, match="já cadastrada"):
        planner.adicionar_membro(Membro("ana"))
    with pytest.raises(ValueError, match="sobreposta"):
        planner.informar_disponibilidade(
            Disponibilidade("ANA", when(1), when(2))
        )
    with pytest.raises(KeyError):
        planner.informar_disponibilidade(
            Disponibilidade("Desconhecido", when(0), when(1))
        )
    assert len(planner.membros) == 3


def test_assignments_respect_skill_and_staff_conflicts():
    planner = planner_with_staff()
    assignments = planner.alocar(Demanda(
        "task-1", when(0), when(2), vagas=1, habilidade="Python"
    ))
    assert [item.pessoa for item in assignments] == ["Ana"]
    with pytest.raises(ValueError):
        planner.alocar(Demanda("task-2", when(1), when(3), habilidade="python"))
    assert len(planner.alocacoes) == 1
    assert planner.conflitos() == []
    assert planner.alocar(Demanda("task-3", when(2), when(4), habilidade="python"))[0].pessoa == "Ana"
    with pytest.raises(ValueError, match="já cadastrado"):
        planner.alocar(Demanda("task-1", when(4), when(5)))


def test_no_partial_assignment_if_not_enough_staff():
    planner = planner_with_staff()
    before = planner.alocacoes
    with pytest.raises(ValueError, match="não há pessoas"):
        planner.alocar(Demanda("D", when(0), when(2), vagas=3, habilidade="qa"))
    assert planner.alocacoes == before
    assert len(planner.alocar(Demanda("D", when(0), when(2), vagas=2, habilidade="qa"))) == 2


def test_workload_is_balanced_and_hour_limits_enforced():
    planner = planner_with_staff()
    first = planner.alocar(Demanda("one", when(0), when(2), habilidade="qa"))
    assert first[0].pessoa == "Ana"
    second = planner.alocar(Demanda("two", when(2), when(4), habilidade="qa"))
    assert second[0].pessoa == "Bruno"
    third = planner.alocar(Demanda("three", when(4), when(8), habilidade="qa"))
    assert third[0].pessoa == "Ana"
    assert planner.conflitos() == []
    with pytest.raises(ValueError):
        planner.alocar(Demanda("too-many", when(0), when(8), habilidade="qa"))


def test_cancel_releases_every_allocated_slot():
    planner = planner_with_staff()
    planner.alocar(Demanda("multi", when(0), when(2), vagas=2, habilidade="qa"))
    assert planner.cancelar("MULTI") == 2
    assert planner.alocacoes == ()
    with pytest.raises(KeyError):
        planner.cancelar("missing")
    assert len(planner.alocar(Demanda("multi", when(0), when(2), vagas=2, habilidade="qa"))) == 2


def test_daily_report_and_weekly_assignments():
    planner = planner_with_staff()
    planner.alocar(Demanda("one", when(0), when(2), vagas=2, habilidade="qa"))
    report = planner.resumo(BASE.date())
    assert report == {
        "dia": "2026-11-09", "pessoas": 2, "turnos": 2,
        "horas": 4.0, "conflitos": 0,
    }
    tomorrow = planner.resumo((BASE + timedelta(days=1)).date())
    assert tomorrow["turnos"] == 0


def test_restore_rejects_overlapping_allocations():
    planner = planner_with_staff()
    planner.restaurar_alocacao(
        Alocacao("A", "Ana", when(0), when(2))
    )
    with pytest.raises(ValueError, match="viola"):
        planner.restaurar_alocacao(
            Alocacao("B", "Ana", when(1), when(3))
        )
    with pytest.raises(ValueError, match="duplicada"):
        planner.restaurar_alocacao(
            Alocacao("A", "Ana", when(2), when(4))
        )


def test_available_slots_are_returned_as_immutable_views():
    planner = planner_with_staff()
    assert isinstance(planner.alocacoes, tuple)
    assert isinstance(planner.membros, tuple)
    assert isinstance(planner.disponibilidades, tuple)
    with pytest.raises(AttributeError):
        planner.alocacoes.append("invalid")


def test_member_agenda_is_sorted_filtered_immutable_and_tracks_cancellation():
    planner = planner_with_staff()
    planner.alocar(Demanda("later", when(2), when(4), habilidade="python"))
    planner.alocar(Demanda("early", when(0), when(2), habilidade="python"))
    schedule = planner.agenda_membro("ANA")
    assert [entry.codigo for entry in schedule] == ["early", "later"]
    assert len(planner.agenda_membro("Ana", (BASE + timedelta(days=1)).date())) == 0
    assert isinstance(schedule, tuple)
    assert planner.agenda_membro("Bruno") == ()
    with pytest.raises(AttributeError):
        schedule.append("wrong")
    with pytest.raises(KeyError):
        planner.agenda_membro("inexistente")
    with pytest.raises(ValueError):
        planner.agenda_membro("Ana", "2026-11-09")
    planner.cancelar("early")
    assert [entry.codigo for entry in planner.agenda_membro("ana")] == ["later"]
    assert len(schedule) == 2  # snapshot anterior não muda
