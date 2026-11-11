# Escala Equipes

Planejador de turnos em **Python 3.10+**, com disponibilidade, competências, distribuição de vagas e controle de horas. A API original `Turno` e `detectar_conflitos` permanece intacta.

## Funcionalidades adicionadas

- Cadastro de colaboradores com habilidades e limites diário/semanal de horas.
- Disponibilidade por pessoa com validação de horários e prevenção de sobreposição.
- Demandas por intervalo, quantidade de vagas e habilidade necessária.
- Distribuição determinística para as pessoas com menos horas alocadas na semana.
- Nenhuma alocação parcial: se faltarem candidatos, a demanda inteira é recusada.
- Bloqueio de turnos sobrepostos e respeito aos limites de horas.
- Cancelamento de todas as vagas de uma demanda, resumo diário e detecção de conflitos.
- Arquivo JSON local versionado com gravação atômica e validação na restauração.
- Ferramenta de terminal para cadastro, atribuição, listagem e relatórios.
- Testes do domínio, armazenamento e comandos reais.

**Limites do protótipo:** até 500 pessoas e 10.000 disponibilidades. Os horários do planejador são locais, sem fuso e sem turnos que atravessem meia-noite. Não calcula horas extras, folha de pagamento ou normas trabalhistas.

## Instalar e testar

```bash
python -m pip install -e . pytest
pytest -q
```

## Exemplo no terminal

Os nomes abaixo são fictícios:

```bash
python -m escala_equipes.cli add-member Ana --skills qa,python
python -m escala_equipes.cli add-member Bruno --skills qa
python -m escala_equipes.cli available Ana 2026-11-09T08:00 2026-11-09T16:00
python -m escala_equipes.cli available Bruno 2026-11-09T08:00 2026-11-09T16:00
python -m escala_equipes.cli assign suporte-01 2026-11-09T09:00 2026-11-09T11:00 --slots 2 --skill qa
python -m escala_equipes.cli list
python -m escala_equipes.cli summary 2026-11-09
python -m escala_equipes.cli member Ana --day 2026-11-09
python -m escala_equipes.cli member Ana --week 2026-11-11
python -m escala_equipes.cli member Ana
python -m escala_equipes.cli cancel suporte-01
```

Para escolher outro local de armazenamento, acrescente `--file caminho.json` **antes** do comando. Sem a opção, os dados ficam em `~/.gx-escala/escala.json`, configurável também com a variável `GX_ESCALA_FILE`.

## API Python

```python
from datetime import datetime
from escala_equipes.planning import Membro, Disponibilidade, Demanda, Escalador

escala = Escalador()
escala.adicionar_membro(Membro("Ana", habilidades=("qa",)))
escala.informar_disponibilidade(Disponibilidade(
    "Ana", datetime(2026, 11, 9, 8), datetime(2026, 11, 9, 16)
))
atribuicoes = escala.alocar(Demanda(
    "teste-001", datetime(2026, 11, 9, 9),
    datetime(2026, 11, 9, 11), habilidade="qa"
))
print(atribuicoes)
```

O comando `member NOME [--day AAAA-MM-DD | --week AAAA-MM-DD]` consulta somente as alocações daquele colaborador, ordenadas cronologicamente, com quantidade de turnos e horas. `--week` seleciona a semana ISO (segunda a domingo) que contém a data, inclusive nas viradas de ano; não pode ser combinado com `--day`. Nomes são comparados sem distinção de maiúsculas/minúsculas, e a consulta não altera o JSON local.

## Segurança e privacidade

Este é um protótipo local de demonstração. O JSON não é criptografado, não há autenticação, autorização, banco multiusuário ou mecanismos para sincronização simultânea. Não armazene dados pessoais de colaboradores em repositórios públicos.

## Licença

Ainda não definida.
