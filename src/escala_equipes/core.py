from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True, slots=True)
class Turno:
    pessoa: str
    inicio: datetime
    fim: datetime
    def __post_init__(self) -> None:
        if not self.pessoa.strip(): raise ValueError("pessoa obrigatória")
        if self.fim <= self.inicio: raise ValueError("fim deve ser posterior ao início")
    def conflita(self, outro: "Turno") -> bool:
        return self.inicio < outro.fim and outro.inicio < self.fim

def detectar_conflitos(turnos: list[Turno]) -> list[tuple[Turno, Turno]]:
    return [(turno, outro) for index, turno in enumerate(turnos) for outro in turnos[index + 1:] if turno.conflita(outro)]
