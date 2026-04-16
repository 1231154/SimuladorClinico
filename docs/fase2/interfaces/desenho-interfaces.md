# Desenho de Interfaces - Fase 2

## Objetivo

Definir as interfaces base da SPA para suportar o fluxo de treino clinico end-to-end.

## Mapa de Ecras

1. Ecrã de Entrada de Simulacao
2. Ecrã de Conversa Clinica (Chat)
3. Ecrã de Encerramento e Feedback

## 1) Ecrã de Entrada de Simulacao

### Componentes

- Cabecalho da plataforma (nome do produto e estado da API).
- Seletor de caso clinico (ID ou lista de casos disponiveis).
- Botao primario "Iniciar simulacao".
- Area de contexto inicial (resumo do caso).

### Wireframe textual

```text
+---------------------------------------------------------------+
| Simulador Clinico                                API: Online  |
+---------------------------------------------------------------+
| Caso clinico: [ dropdown/lista ]                              |
|                                                               |
| Resumo inicial do caso                                        |
| - Sintomas principais                                          |
| - Contexto do paciente                                         |
| - Objetivo pedagogico                                          |
|                                                               |
|                              [ Iniciar simulacao ]            |
+---------------------------------------------------------------+
```

### Acao principal

- Clique em Iniciar simulacao executa POST /api/simulacoes/sessoes.

## 2) Ecrã de Conversa Clinica (Chat)

### Componentes

- Timeline de mensagens (profissional vs paciente virtual).
- Campo de texto para pergunta clinica.
- Botao enviar.
- Painel lateral com estado da sessao (tempo, estado, numero de interacoes).
- Botao secundario para atualizar estado via GET da sessao.
- Botao de alto destaque para concluir sessao.

### Wireframe textual

```text
+----------------------------+----------------------------------+
| Sessao em andamento        | Chat clinico                     |
| Estado: EmAndamento        |----------------------------------|
| Interacoes: 8              | [Profissional] Onde tem dor?     |
| Inicio: 14:10              | [Paciente IA] Dor no peito.      |
|                            | [Profissional] Irradia para...   |
| [ Atualizar estado ]       | [Paciente IA] Sim, para o braco. |
|                            |                                  |
|                            | Pergunta: [___________________]  |
|                            |                 [ Enviar ]       |
|                            |                                  |
|                            | [ Concluir simulacao ]           |
+----------------------------+----------------------------------+
```

### Acoes principais

- Enviar pergunta executa POST /api/simulacoes/sessoes/{sessaoId}/mensagens.
- Atualizar estado executa GET /api/simulacoes/sessoes/{sessaoId}.
- Concluir simulacao executa POST /api/simulacoes/sessoes/{sessaoId}/concluir.

## 3) Ecrã de Encerramento e Feedback

### Componentes

- Cartao de resumo da sessao (inicio, fim, duracao, total de interacoes).
- Cartoes de metricas de avaliacao:
  - rigor cientifico
  - coerencia de sintomas
  - grau de realismo
  - mais valia pedagogica
- Bloco de recomendacoes de melhoria.
- Botao para iniciar nova simulacao.

### Wireframe textual

```text
+---------------------------------------------------------------+
| Sessao concluida                                               |
+---------------------------------------------------------------+
| Duracao: 18 min | Interacoes: 14 | Caso: Dor toracica         |
+---------------------------------------------------------------+
| Rigor cientifico: 82   Coerencia sintomas: 76                 |
| Grau de realismo: 80   Mais valia pedagogica: 88              |
+---------------------------------------------------------------+
| Recomendacoes                                                  |
| - Investigar diagnosticos diferenciais mais cedo              |
| - Melhorar perguntas sobre fatores de risco                   |
+---------------------------------------------------------------+
| [ Nova simulacao ]                                             |
+---------------------------------------------------------------+
```

## Principios de UX adotados

- Fluxo linear: preparar, conversar, concluir.
- Feedback imediato apos cada acao critica.
- Linguagem clinica simples e objetiva.
- Priorizacao de foco no chat durante a simulacao.
