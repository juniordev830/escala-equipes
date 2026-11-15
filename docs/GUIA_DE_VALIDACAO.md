# Desenvolvimento e validação — Escala de Equipes

## Estado implementado

CLI Python de alocação de pessoas por disponibilidade e habilidade, com armazenamento JSON local.

## Estrutura relevante

`src/escala_equipes/planning.py`, `storage.py`, `cli.py`, `core.py` e testes.

## Como reproduzir verificações

`python -m pip install -e . pytest`; `pytest -q`.

Os exemplos devem usar entradas fictícias. Registrar explicitamente o que foi de fato executado no ambiente e comparar com o CI.

## Regressão prioritária

Testar turnos sobrepostos, indisponibilidade parcial, demanda por habilidade, excesso de membros, cancelamento e restauração de JSON inválido.

## Próximos limites a resolver

Não calcula folha nem legislação de jornada; os horários não contemplam turnos cruzando meia-noite. Antes de dados reais, implementar segurança e autorização.

## Revisão de contribuição

- [ ] Mudança melhora uma regra, teste ou integração real.
- [ ] Cenários de entrada, saída e erro estão documentados.
- [ ] Nada de dados pessoais, credenciais ou arquivos gerados versionados.
- [ ] PR separado antes de alterar a principal.
