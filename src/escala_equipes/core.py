from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class Turno:
    pessoa: str
    inicio: datetime
    fim: datetime

    def __post_init__(self) -> None:
        if not self.pessoa or not self.pessoa.strip():
            raise ValueError("pessoa obrigatória")
        if self.fim <= self.inicio:
            raise ValueError("fim deve ser posterior ao início")

    def conflita(self, outro: "Turno") -> bool:
        """Uma pessoa não pode estar em dois turnos sobrepostos."""
        return (
            self.pessoa.strip().casefold() == outro.pessoa.strip().casefold()
            and self.inicio < outro.fim
            and outro.inicio < self.fim
        )


def detectar_conflitos(turnos: list[Turno]) -> list[tuple[Turno, Turno]]:
    return [
        (turno, outro)
        for index, turno in enumerate(turnos)
        for outro in turnos[index + 1 :]
        if turno.conflita(outro)
    ]


@dataclass(frozen=True, slots=True)
class ResumoCarga:
    pessoa: str
    turnos: int
    duracao: timedelta


def resumir_carga_horaria(turnos: list[Turno]) -> list[ResumoCarga]:
    """Sum scheduled time for each person; overlapping shifts are rejected."""
    if detectar_conflitos(turnos):
        raise ValueError("turnos sobrepostos para a mesma pessoa")
    totals: dict[str, tuple[str, int, timedelta]] = {}
    for turno in turnos:
        key = turno.pessoa.strip().casefold()
        label, count, duration = totals.get(
            key, (turno.pessoa.strip(), 0, timedelta())
        )
        totals[key] = (label, count + 1, duration + (turno.fim - turno.inicio))
    return [
        ResumoCarga(label, count, duration)
        for key, (label, count, duration) in sorted(totals.items())
    ]
