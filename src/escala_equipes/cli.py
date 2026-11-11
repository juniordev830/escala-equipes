"""Local command-line interface for team scheduling.

Commands write only to the explicitly supplied local JSON file. No network
services are contacted. Demonstration data should never contain real staff PII.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
import sys

from .planning import (
    Demanda, Disponibilidade, Membro, Escalador,
)
from .storage import load_schedule, save_schedule


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="escala-equipes",
        description="Planejador local de turnos, habilidades e disponibilidade.",
    )
    root.add_argument(
        "--file", type=Path, default=None,
        help="caminho do JSON local (opcional)",
    )
    actions = root.add_subparsers(dest="command")

    member = actions.add_parser("add-member", help="cadastrar colaborador fictício")
    member.add_argument("name")
    member.add_argument("--week", type=int, default=40)
    member.add_argument("--day", type=int, default=8)
    member.add_argument("--skills", default="",
                        help="habilidades separadas por vírgula")

    availability = actions.add_parser("available", help="informar disponibilidade")
    availability.add_argument("name")
    availability.add_argument("start", help="AAAA-MM-DDTHH:MM")
    availability.add_argument("end", help="AAAA-MM-DDTHH:MM")

    assignment = actions.add_parser("assign", help="alocar vagas para uma demanda")
    assignment.add_argument("code")
    assignment.add_argument("start", help="AAAA-MM-DDTHH:MM")
    assignment.add_argument("end", help="AAAA-MM-DDTHH:MM")
    assignment.add_argument("--slots", type=int, default=1)
    assignment.add_argument("--skill", default="")

    cancel = actions.add_parser("cancel", help="cancelar toda uma demanda")
    cancel.add_argument("code")

    actions.add_parser("list", help="mostrar escala e responsáveis")

    member_schedule = actions.add_parser("member", help="consultar escala de um colaborador")
    member_schedule.add_argument("name")
    member_schedule.add_argument("--day", default=None, help="filtrar por dia AAAA-MM-DD")

    summary = actions.add_parser("summary", help="resumo de turnos do dia")
    summary.add_argument("day", help="AAAA-MM-DD")
    return root


def run(argv: list[str] | None = None) -> int:
    root = parser()
    args = root.parse_args(argv)
    if args.command is None:
        root.print_help()
        return 0

    try:
        planner = load_schedule(args.file)
        if args.command == "add-member":
            skills = tuple(
                skill.strip() for skill in args.skills.split(",") if skill.strip()
            )
            planner.adicionar_membro(Membro(
                args.name, args.week, args.day, skills,
            ))
            save_schedule(planner, args.file)
            print(f"Membro cadastrado: {args.name}")
        elif args.command == "available":
            planner.informar_disponibilidade(Disponibilidade(
                args.name, datetime.fromisoformat(args.start),
                datetime.fromisoformat(args.end),
            ))
            save_schedule(planner, args.file)
            print(f"Disponibilidade registrada: {args.name}")
        elif args.command == "assign":
            chosen = planner.alocar(Demanda(
                args.code, datetime.fromisoformat(args.start),
                datetime.fromisoformat(args.end),
                args.slots, args.skill,
            ))
            save_schedule(planner, args.file)
            print(f"Demanda {args.code}: {len(chosen)} pessoa(s) alocada(s)")
            for item in chosen:
                print(f"  {item.pessoa} | {item.inicio.isoformat()} | {item.fim.isoformat()}")
        elif args.command == "cancel":
            amount = planner.cancelar(args.code)
            save_schedule(planner, args.file)
            print(f"Demanda {args.code}: {amount} alocação(ões) cancelada(s)")
        elif args.command == "list":
            if not planner.alocacoes:
                print("Nenhuma alocação encontrada.")
            for item in planner.alocacoes:
                print(
                    f"{item.codigo} | {item.pessoa} | "
                    f"{item.inicio.isoformat()} até {item.fim.isoformat()}"
                )
        elif args.command == "member":
            selected_day = date.fromisoformat(args.day) if args.day else None
            allocations = planner.agenda_membro(args.name, selected_day)
            hours = sum((a.fim - a.inicio).total_seconds() / 3600 for a in allocations)
            print(f"Alocações: {len(allocations)} | horas: {hours:.2f}")
            for item in allocations:
                print(f"{item.codigo} | {item.inicio.isoformat()} até {item.fim.isoformat()}")
        elif args.command == "summary":
            report = planner.resumo(date.fromisoformat(args.day))
            for key in ("dia", "pessoas", "turnos", "horas", "conflitos"):
                print(f"{key}: {report[key]}")
        return 0
    except (ValueError, KeyError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
