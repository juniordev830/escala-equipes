"""Deterministic staff scheduling with availability, skills and hour limits.

The original Turno / detectar_conflitos API remains untouched. This module
models staffing requests and guarantees atomic assignments for each request.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

from .core import Turno, detectar_conflitos


def _name(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 80:
        raise ValueError(f"{label} deve conter 1 a 80 caracteres")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{label} contém caracteres de controle")
    return value.strip()


def _interval(start: datetime, end: datetime) -> None:
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        raise ValueError("início e fim devem ser datas e horas")
    if start.tzinfo is not None or end.tzinfo is not None:
        raise ValueError("datas do planejador devem ser locais e sem fuso")
    if start.date() != end.date() or end <= start:
        raise ValueError("turno deve começar e terminar no mesmo dia")
    duration = end - start
    if duration < timedelta(minutes=30) or duration > timedelta(hours=12):
        raise ValueError("duração deve ser entre 30 minutos e 12 horas")


@dataclass(frozen=True, slots=True)
class Membro:
    nome: str
    horas_semana: int = 40
    horas_dia: int = 8
    habilidades: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "nome", _name(self.nome, "nome"))
        if type(self.horas_semana) is not int or not 1 <= self.horas_semana <= 60:
            raise ValueError("horas semanais devem estar entre 1 e 60")
        if type(self.horas_dia) is not int or not 1 <= self.horas_dia <= 12:
            raise ValueError("horas diárias devem estar entre 1 e 12")
        if self.horas_dia > self.horas_semana:
            raise ValueError("limite diário deve ser menor ou igual ao semanal")
        if not isinstance(self.habilidades, tuple) or len(self.habilidades) > 20:
            raise ValueError("habilidades devem ser uma tupla de até 20 itens")
        keys = tuple(_name(x, "habilidade").casefold() for x in self.habilidades)
        if len(set(keys)) != len(keys):
            raise ValueError("habilidades duplicadas")
        object.__setattr__(self, "habilidades", keys)


@dataclass(frozen=True, slots=True)
class Disponibilidade:
    pessoa: str
    inicio: datetime
    fim: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "pessoa", _name(self.pessoa, "pessoa"))
        _interval(self.inicio, self.fim)


@dataclass(frozen=True, slots=True)
class Demanda:
    codigo: str
    inicio: datetime
    fim: datetime
    vagas: int = 1
    habilidade: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "codigo", _name(self.codigo, "código"))
        _interval(self.inicio, self.fim)
        if type(self.vagas) is not int or not 1 <= self.vagas <= 20:
            raise ValueError("vagas devem estar entre 1 e 20")
        if self.habilidade:
            object.__setattr__(self, "habilidade", _name(self.habilidade, "habilidade").casefold())


@dataclass(frozen=True, slots=True)
class Alocacao:
    codigo: str
    pessoa: str
    inicio: datetime
    fim: datetime


class Escalador:
    def __init__(self) -> None:
        self._membros: dict[str, Membro] = {}
        self._disponibilidades: list[Disponibilidade] = []
        self._alocacoes: list[Alocacao] = []

    @property
    def membros(self) -> tuple[Membro, ...]:
        return tuple(sorted(self._membros.values(), key=lambda m: m.nome.casefold()))

    @property
    def disponibilidades(self) -> tuple[Disponibilidade, ...]:
        return tuple(self._disponibilidades)

    @property
    def alocacoes(self) -> tuple[Alocacao, ...]:
        return tuple(sorted(self._alocacoes, key=lambda a: (a.inicio, a.pessoa.casefold())))

    def adicionar_membro(self, membro: Membro) -> None:
        if not isinstance(membro, Membro):
            raise ValueError("membro inválido")
        key = membro.nome.casefold()
        if key in self._membros:
            raise ValueError("pessoa já cadastrada")
        if len(self._membros) >= 500:
            raise ValueError("limite de 500 pessoas")
        self._membros[key] = membro

    def informar_disponibilidade(self, periodo: Disponibilidade) -> None:
        if not isinstance(periodo, Disponibilidade):
            raise ValueError("disponibilidade inválida")
        key = periodo.pessoa.casefold()
        if key not in self._membros:
            raise KeyError("pessoa não cadastrada")
        if len(self._disponibilidades) >= 10000:
            raise ValueError("limite de disponibilidades")
        if any(p.pessoa.casefold() == key and
               p.inicio < periodo.fim and periodo.inicio < p.fim
               for p in self._disponibilidades):
            raise ValueError("disponibilidade sobreposta")
        self._disponibilidades.append(periodo)

    def _horas(self, pessoa: str, dia: date, inicio: datetime) -> tuple[float, float]:
        chave = pessoa.casefold()
        segunda = dia - timedelta(days=dia.weekday())
        fim_semana = segunda + timedelta(days=7)
        diarios = sum(
            (item.fim - item.inicio).total_seconds() / 3600
            for item in self._alocacoes
            if item.pessoa.casefold() == chave and item.inicio.date() == dia
        )
        semanais = sum(
            (item.fim - item.inicio).total_seconds() / 3600
            for item in self._alocacoes
            if item.pessoa.casefold() == chave and
            segunda <= item.inicio.date() < fim_semana
        )
        return diarios, semanais

    def _pode_alocar(self, membro: Membro, demanda: Demanda) -> bool:
        key = membro.nome.casefold()
        if demanda.habilidade and demanda.habilidade not in membro.habilidades:
            return False
        if not any(
            p.pessoa.casefold() == key and
            p.inicio <= demanda.inicio and demanda.fim <= p.fim
            for p in self._disponibilidades
        ):
            return False
        if any(
            a.pessoa.casefold() == key and
            a.inicio < demanda.fim and demanda.inicio < a.fim
            for a in self._alocacoes
        ):
            return False
        diarias, semanais = self._horas(membro.nome, demanda.inicio.date(), demanda.inicio)
        duracao = (demanda.fim - demanda.inicio).total_seconds() / 3600
        return (
            diarias + duracao <= membro.horas_dia and
            semanais + duracao <= membro.horas_semana
        )

    def alocar(self, demanda: Demanda) -> tuple[Alocacao, ...]:
        if not isinstance(demanda, Demanda):
            raise ValueError("demanda inválida")
        if any(a.codigo.casefold() == demanda.codigo.casefold() for a in self._alocacoes):
            raise ValueError("código de demanda já cadastrado")
        disponiveis = [m for m in self._membros.values() if self._pode_alocar(m, demanda)]
        # Least weekly hours first, then stable lexical order.
        disponiveis.sort(key=lambda m: (
            self._horas(m.nome, demanda.inicio.date(), demanda.inicio)[1],
            m.nome.casefold(),
        ))
        if len(disponiveis) < demanda.vagas:
            raise ValueError("não há pessoas disponíveis para todas as vagas")
        selecionadas = tuple(
            Alocacao(demanda.codigo, m.nome, demanda.inicio, demanda.fim)
            for m in disponiveis[:demanda.vagas]
        )
        # Atomic: no partial allocations on failure.
        self._alocacoes.extend(selecionadas)
        return selecionadas

    def restaurar_alocacao(self, alocacao: Alocacao) -> None:
        """Validate one saved allocation and append it without recomputing staffing."""
        if not isinstance(alocacao, Alocacao):
            raise ValueError("alocação inválida")
        _interval(alocacao.inicio, alocacao.fim)
        membro = self._membros.get(alocacao.pessoa.casefold())
        if membro is None:
            raise ValueError("alocação contém pessoa desconhecida")
        if any(a.codigo.casefold() == alocacao.codigo.casefold() and
               a.pessoa.casefold() == alocacao.pessoa.casefold()
               for a in self._alocacoes):
            raise ValueError("alocação duplicada")
        if any(a.codigo.casefold() == alocacao.codigo.casefold() and
               (a.inicio != alocacao.inicio or a.fim != alocacao.fim)
               for a in self._alocacoes):
            raise ValueError("alocações da mesma demanda devem ter horários iguais")
        demanda = Demanda(alocacao.codigo, alocacao.inicio, alocacao.fim)
        if not self._pode_alocar(membro, demanda):
            raise ValueError("alocação salva viola horários ou limites")
        self._alocacoes.append(Alocacao(
            demanda.codigo, membro.nome, demanda.inicio, demanda.fim,
        ))

    def cancelar(self, codigo: str) -> int:
        codigo = _name(codigo, "código").casefold()
        removidas = sum(a.codigo.casefold() == codigo for a in self._alocacoes)
        if removidas == 0:
            raise KeyError("demanda não encontrada")
        self._alocacoes = [
            item for item in self._alocacoes if item.codigo.casefold() != codigo
        ]
        return removidas

    def conflitos(self) -> list[tuple[Turno, Turno]]:
        turnos = [
            Turno(item.pessoa, item.inicio, item.fim)
            for item in self._alocacoes
        ]
        return detectar_conflitos(turnos)

    def resumo(self, dia: date) -> dict[str, object]:
        if not isinstance(dia, date):
            raise ValueError("dia inválido")
        selecionadas = [
            item for item in self._alocacoes if item.inicio.date() == dia
        ]
        return {
            "dia": dia.isoformat(),
            "pessoas": len({a.pessoa.casefold() for a in selecionadas}),
            "turnos": len(selecionadas),
            "horas": round(sum(
                (a.fim - a.inicio).total_seconds() / 3600 for a in selecionadas
            ), 2),
            "conflitos": len(self.conflitos()),
        }
