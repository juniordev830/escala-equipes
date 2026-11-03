# Escala de Equipes

Biblioteca Python 3.10+ que verifica conflitos de turnos e apresenta carga horária programada por pessoa.

## Funcionalidades

- `detectar_conflitos(turnos)`: encontra pares sobrepostos da **mesma pessoa**, comparando nomes sem diferenciar maiúsculas/minúsculas e ignorando espaços externos.
- `resumir_carga_horaria(turnos)`: soma durações em `datetime.timedelta`, conta os turnos por pessoa e retorna resultados ordenados por nome.
- Rejeita escalas com turnos sobrepostos da mesma pessoa para **não duplicar horas**. Aceita turnos adjacentes e turnos que cruzam a meia-noite.

## Exemplo

```python
from datetime import datetime, timedelta
from escala_equipes import Turno, resumir_carga_horaria

inicio = datetime(2026, 11, 3, 20)
turnos = [
    Turno("Ana", inicio, inicio + timedelta(hours=4)),
    Turno(" ana ", inicio + timedelta(hours=4), inicio + timedelta(hours=8)),
]
print(resumir_carga_horaria(turnos))
# [ResumoCarga(pessoa='Ana', turnos=2, duracao=datetime.timedelta(seconds=28800))]
```

## Testes

```bash
python -m pip install -e . pytest
pytest -q
```

O GitHub Actions valida turnos simultâneos, adjacência, turnos noturnos, normalização de nomes, resumos e erros de conflito.

## Limitações

MVP de domínio em memória, sem banco, folha de pagamento, validação de jornada legal, fusos mistos, descanso obrigatório, banco de horas ou interface. A duração representa horas **programadas**, não horas trabalhadas ou remuneradas; para escalas com mudança de horário de verão é necessário definir tratamento explícito de fuso horário. Exemplos fictícios.

Licença: ainda não definida.
