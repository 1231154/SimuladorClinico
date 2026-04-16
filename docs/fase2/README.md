# Fase 2 - Desenho da Solucao (09 Marco a 27 Marco)

Este pacote contem os artefactos de desenho da solucao para o Simulador Clinico.

## Conteudo

- arquitetura/
  - logicalview.puml
  - processview.puml
  - deploymentview.puml
- interfaces/
  - desenho-interfaces.md
- prompts/
  - prompts-base-llm.md

## Objetivos da Fase 2

- Definir a arquitetura do sistema com vistas complementares.
- Desenhar as interfaces principais da SPA para o fluxo de simulacao.
- Definir prompts base para o LLM, incluindo guardrails e formato de resposta.

## Notas de alinhamento com o codigo atual

- API principal: SimulacoesController com rotas em /api/simulacoes.
- Sessao: criada, em andamento e finalizada.
- Fluxo principal: criar sessao, trocar mensagens, consultar sessao e concluir.
