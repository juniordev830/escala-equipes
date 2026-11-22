from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Turno:
    pessoa: str
    inicio: datetime
    fim: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.pessoa, str) or not 1 <= len(self.pessoa.strip()) <= 80:
            raise ValueError("pessoa deve conter de 1 a 80 caracteres")
        if any(ord(char) < 32 or ord(char) == 127 for char in self.pessoa):
            raise ValueError("pessoa contém caracteres de controle")
        if not isinstance(self.inicio, datetime) or not isinstance(self.fim, datetime):
            raise ValueError("início e fim devem ser datas e horas")
        if (self.inicio.tzinfo is None) != (self.fim.tzinfo is None):
            raise ValueError("início e fim devem ter o mesmo padrão de fuso")
        if self.fim <= self.inicio:
            raise ValueError("fim deve ser posterior ao início")

    def conflita(self, outro: "Turno") -> bool:
        """Uma pessoa não pode estar em dois turnos sobrepostos."""
        if not isinstance(outro, Turno):
            raise ValueError("turno comparado inválido")
        if (self.inicio.tzinfo is None) != (outro.inicio.tzinfo is None):
            raise ValueError("não compare turnos com padrões de fuso diferentes")
        return (
            self.pessoa.strip().casefold() == outro.pessoa.strip().casefold()
            and self.inicio < outro.fim
            and outro.inicio < self.fim
        )


def detectar_conflitos(turnos: list[Turno]) -> list[tuple[Turno, Turno]]:
    if not isinstance(turnos, list) or any(not isinstance(turno, Turno) for turno in turnos):
        raise ValueError("turnos deve ser uma lista de Turno")
    return [
        (turno, outro)
        for index, turno in enumerate(turnos)
        for outro in turnos[index + 1 :]
        if turno.conflita(outro)
    ]
