import pytest

from escala_equipes.planning import Demanda
from test_cli import cli
from test_planning import planner_with_staff, when


def test_simulation_matches_assignment_without_reserving_code_or_people():
    planner=planner_with_staff()
    demand=Demanda("test",when(0),when(2),vagas=2,habilidade="qa")
    before=(planner.alocacoes,planner.membros,planner.disponibilidades)
    result=planner.simular(demand)
    assert [a.pessoa for a in result]==["Ana","Bruno"]
    assert isinstance(result,tuple)
    assert (planner.alocacoes,planner.membros,planner.disponibilidades)==before
    assert planner.simular(demand)==result
    assert planner.alocar(demand)==result
    with pytest.raises(ValueError,match="já cadastrado"):planner.simular(demand)


def test_preview_is_recomputed_after_other_assignments():
    planner=planner_with_staff()
    demand=Demanda("preview",when(0),when(2),habilidade="qa")
    result=planner.simular(demand)
    assert result[0].pessoa=="Ana"
    planner.alocar(Demanda("intervening",when(0),when(2),habilidade="python"))
    assert planner.alocar(demand)[0].pessoa=="Bruno"
    assert result[0].pessoa=="Ana"


def test_simulation_failure_never_leaves_partial_allocations():
    planner=planner_with_staff()
    with pytest.raises(ValueError,match="não há pessoas"):
        planner.simular(Demanda("too-many",when(0),when(2),vagas=3,habilidade="qa"))
    assert planner.alocacoes==()
    with pytest.raises(ValueError,match="demanda inválida"):planner.simular(None)


def test_cli_dry_run_is_read_only_and_allows_later_confirmation(tmp_path):
    path=tmp_path/"schedule.json"
    assert cli(path,"add-member","Ana","--skills","qa").returncode==0
    assert cli(path,"available","Ana","2026-11-09T08:00","2026-11-09T16:00").returncode==0
    before=path.read_bytes()
    args=("assign","preview","2026-11-09T09:00","2026-11-09T11:00","--skill","qa")
    result=cli(path,*args,"--dry-run")
    assert result.returncode==0,result.stderr
    assert "Simulação" in result.stdout and "Ana" in result.stdout
    assert path.read_bytes()==before
    assert cli(path,*args).returncode==0
    assert path.read_bytes()!=before
    assert cli(path,*args,"--dry-run").returncode==2
