"""Local, versioned JSON snapshots for scheduling demo data."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .planning import (
    Alocacao, Disponibilidade, Escalador, Membro,
)

MAX_BYTES = 1_000_000
SCHEMA_VERSION = 1


def default_path() -> Path:
    return Path(
        os.environ.get("GX_ESCALA_FILE",
                       str(Path.home() / ".gx-escala" / "escala.json"))
    ).expanduser()


def save_schedule(planner: Escalador, path: Path | None = None) -> int:
    if not isinstance(planner, Escalador):
        raise ValueError("planejador inválido")
    target = path if path is not None else default_path()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "members": [
            {
                "name": item.nome,
                "weekly_hours": item.horas_semana,
                "daily_hours": item.horas_dia,
                "skills": list(item.habilidades),
            } for item in planner.membros
        ],
        "availability": [
            {
                "name": item.pessoa,
                "start": item.inicio.isoformat(),
                "end": item.fim.isoformat(),
            } for item in planner.disponibilidades
        ],
        "allocations": [
            {
                "code": item.codigo,
                "name": item.pessoa,
                "start": item.inicio.isoformat(),
                "end": item.fim.isoformat(),
            } for item in planner.alocacoes
        ],
    }
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    if len(data) > MAX_BYTES:
        raise ValueError("arquivo de escala ultrapassa 1 MB")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="wb", dir=target.parent,
            prefix=".escala-", suffix=".tmp", delete=False,
        ) as output:
            temporary = Path(output.name)
            os.chmod(temporary, 0o600)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return len(planner.alocacoes)


def load_schedule(path: Path | None = None) -> Escalador:
    target = path if path is not None else default_path()
    try:
        if target.stat().st_size > MAX_BYTES:
            raise ValueError("arquivo de escala ultrapassa 1 MB")
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Escalador()
    except json.JSONDecodeError as error:
        raise ValueError("JSON de escala inválido") from error

    if (
        not isinstance(data, dict)
        or data.get("schema_version") != SCHEMA_VERSION
        or not all(isinstance(data.get(field), list) for field in (
            "members", "availability", "allocations"
        ))
    ):
        raise ValueError("versão ou estrutura de escala inválida")

    from datetime import datetime
    planner = Escalador()
    try:
        for item in data["members"]:
            planner.adicionar_membro(Membro(
                item["name"], item["weekly_hours"],
                item["daily_hours"], tuple(item["skills"]),
            ))
        for item in data["availability"]:
            planner.informar_disponibilidade(Disponibilidade(
                item["name"], datetime.fromisoformat(item["start"]),
                datetime.fromisoformat(item["end"]),
            ))
        for item in data["allocations"]:
            planner.restaurar_alocacao(Alocacao(
                item["code"], item["name"],
                datetime.fromisoformat(item["start"]),
                datetime.fromisoformat(item["end"]),
            ))
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ValueError("arquivo de escala contém registros inválidos") from error
    return planner
