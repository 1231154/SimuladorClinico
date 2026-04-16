# Guia de Testes no Postman

Este guia esta alinhado com o estado atual do backend em modo anonimo. Nao existe login de profissional de saude e o fluxo principal e: criar sessao, conversar e concluir para obter feedback do momento.

## 1) Arrancar a API

Na raiz do projeto:

```bat
run-backend.bat
```

Quando aparecer algo como `Now listening on: http://localhost:5070`, a API esta pronta.

## 2) Criar ambiente no Postman

Cria um Environment chamado `Local` com estas variaveis:

- `baseUrl = http://localhost:5070`
- `sessaoId =` (vazio no inicio)

Opcionalmente podes criar tambem:

- `casoId = 22222222-2222-2222-2222-222222222222`

Estes valores sao GUIDs validos e servem para teste. Nao uses textos como `abc` ou `123`, porque o backend espera mesmo `Guid`.

## 3) Ordem certa de testes

Testa nesta sequencia para nao te perderes:

1. Ver se a API responde.
2. Criar uma sessao.
3. Guardar o `id` da sessao.
4. Enviar uma mensagem para essa sessao.
5. Concluir a sessao para gerar feedback.
6. Obter a sessao pelo `id`.

## 4) Requests para testar agora

## 4.1 Health

- Metodo: `GET`
- URL: `{{baseUrl}}/health`
- Esperado: `200 OK` com JSON `{ "status": "ok" }`.

## 4.2 Swagger

- Metodo: `GET`
- URL: `{{baseUrl}}/swagger`
- Esperado: o browser abre o Swagger UI. No Postman vais receber HTML, o que e normal.

## 4.3 Rota invalida

- Metodo: `GET`
- URL: `{{baseUrl}}/api/nao-existe`
- Esperado: `404 Not Found`.

## 4.4 Criar sessao

- Metodo: `POST`
- URL: `{{baseUrl}}/api/simulacoes/sessoes`
- Headers:
  - `Content-Type: application/json`
- Body: `raw` + `JSON`

Importante: nao uses `Text` nem `form-data` no Postman. Se enviares o pedido como `text/plain`, a API devolve `415 Unsupported Media Type`.

O body tem de ser o objeto diretamente. Nao metas um wrapper tipo `{"request": {...}}`, porque isso dispara erro de validacao.

```json
{
  "casoId": "{{casoId}}"
}
```

Exemplo literal valido, para colares diretamente no Postman sem variaveis:

```json
{
  "casoId": "22222222-2222-2222-2222-222222222222"
}
```

### O que deves esperar

- `201 Created`
- Resposta com uma estrutura parecida com esta:

```json
{
  "sessao": {
    "id": "...",
    "dataInicio": "...",
    "dataFim": null,
    "estado": 1,
    "casoId": "22222222-2222-2222-2222-222222222222",
    "interacoes": [],
    "avaliacao": null
  }
}
```

### O que fazer depois

- Copia o `id` devolvido.
- Guarda-o em `sessaoId` no Environment.

## 4.5 Enviar mensagem para a sessao

- Metodo: `POST`
- URL: `{{baseUrl}}/api/simulacoes/sessoes/{{sessaoId}}/mensagens`
- Headers:
  - `Content-Type: application/json`
- Body: `raw` + `JSON`

Este request so funciona depois de criares uma sessao com sucesso. Se `sessaoId` estiver vazio, vais receber erro.

Mesma regra aqui: o pedido tem de ser `raw JSON`. Se o Postman estiver em `Text`, vais cair novamente no `415 Unsupported Media Type`.

O JSON tem de ter apenas o campo `textoDaMensagem`.

```json
{
  "textoDaMensagem": "Paciente com dor toracica ha 2 horas, sem febre."
}
```

Exemplo literal valido:

```json
{
  "textoDaMensagem": "Paciente com dor toracica ha 2 horas, sem febre."
}
```

### O que deves esperar

- `200 OK`
- Resposta com duas mensagens:
  - a mensagem do utilizador
  - a resposta simulada da IA

Exemplo de estrutura:

```json
{
  "sessaoId": "...",
  "mensagemProfissional": {
    "id": "...",
    "remetente": 1,
    "textoDaMensagem": "Paciente com dor toracica ha 2 horas, sem febre.",
    "timestamp": "..."
  },
  "respostaIa": {
    "id": "...",
    "remetente": 2,
    "textoDaMensagem": "Resposta simulada da IA. A integracao real com o modelo sera adicionada numa fase posterior.",
    "timestamp": "..."
  }
}
```

## 4.6 Concluir sessao e gerar feedback

- Metodo: `POST`
- URL: `{{baseUrl}}/api/simulacoes/sessoes/{{sessaoId}}/concluir`

### O que deves esperar

- `200 OK`
- A sessao passa para `estado = 3` (Finalizada)
- `dataFim` preenchida
- `avaliacao` preenchida com pontuacoes desta sessao

Exemplo de estrutura:

```json
{
  "id": "...",
  "dataInicio": "...",
  "dataFim": "...",
  "estado": 3,
  "casoId": "22222222-2222-2222-2222-222222222222",
  "interacoes": [
    {
      "id": "...",
      "remetente": 1,
      "textoDaMensagem": "...",
      "timestamp": "..."
    },
    {
      "id": "...",
      "remetente": 2,
      "textoDaMensagem": "...",
      "timestamp": "..."
    }
  ],
  "avaliacao": {
    "id": "...",
    "rigorCientifico": 80,
    "coerenciaSintomas": 74,
    "grauDeRealismo": 70,
    "maisValiaPedagogica": 78
  }
}
```

## 4.7 Obter sessao por id

- Metodo: `GET`
- URL: `{{baseUrl}}/api/simulacoes/sessoes/{{sessaoId}}`

Tambem depende de `sessaoId` estar preenchido. Sem isso, o request nao representa uma sessao real.

### O que deves esperar

- `200 OK`
- O endpoint devolve a sessao com estado atual, interacoes e avaliacao (se ja tiver sido concluida):

```json
{
  "id": "{{sessaoId}}",
  "dataInicio": "...",
  "dataFim": null,
  "estado": 2,
  "casoId": "22222222-2222-2222-2222-222222222222",
  "interacoes": [
    {
      "id": "...",
      "remetente": 1,
      "textoDaMensagem": "...",
      "timestamp": "..."
    }
  ],
  "avaliacao": null
}
```

## 5) Como validar se esta a funcionar bem

- A API abre sem excecao no terminal.
- O `POST /api/simulacoes/sessoes` devolve `201`.
- O `POST /api/simulacoes/sessoes/{sessaoId}/mensagens` devolve `200`.
- O `POST /api/simulacoes/sessoes/{sessaoId}/concluir` devolve `200` e avaliacao.
- O `GET /api/simulacoes/sessoes/{sessaoId}` devolve `200`.
- O `GET /api/nao-existe` devolve `404` de forma esperada.
- Nenhum pedido devolve `500`.

Se aparece `The request field is required`, significa que o Postman nao esta a enviar o body como JSON no formato esperado.

Se aparece `The JSON value could not be converted to System.Guid`, significa que o valor de `casoId` ou `sessaoId` nao e um GUID valido.

## 6) Erros mais comuns e o que significam

- `Could not get any response`
  - A API nao esta a correr.
  - O `baseUrl` esta errado.
- `404 Not Found`
  - URL errada.
  - Metodo HTTP errado.
  - GUID invalido na rota.
  - No caso do request `GET Rota Inexistente`, o `404` e o resultado esperado.
- `500 Internal Server Error`
  - Ha um problema no codigo do backend.
  - Normalmente aparece também uma excecao no terminal da API.

## 6.1 Se os 3 ultimos requests deram erro

Se `POST Enviar Mensagem`, `GET Obter Sessao` e `GET Rota Inexistente` falharam, verifica isto primeiro:

1. Correste `POST Criar Sessao` antes?
2. O `sessaoId` ficou preenchido no environment?
3. O environment `Local` esta selecionado no canto superior direito do Postman?
4. O request `GET Rota Inexistente` a devolver `404` e normal.

Se o `sessaoId` estiver vazio, os dois requests dependentes vao falhar. O `GET Rota Inexistente` vai falhar sempre, mas de forma esperada.

## 7) Colecao recomendada no Postman

Nome da colecao: `SimuladorClinico API`

Requests:

1. `GET Health`
2. `GET Swagger`
3. `POST Criar Sessao`
4. `POST Enviar Mensagem`
5. `POST Concluir Sessao`
6. `GET Obter Sessao`
7. `GET Rota Inexistente`

Se quiseres importar logo tudo pronto, usa estes ficheiros:

- [Collection](Postman/SimuladorClinicoAPI.postman_collection.json)
- [Environment](Postman/Local.postman_environment.json)

Ordem recomendada de importacao no Postman:

1. Importa primeiro o environment `Local`.
2. Importa depois a collection `SimuladorClinico API`.
3. Seleciona o environment `Local` no canto superior direito do Postman.
4. Executa os requests pela ordem indicada acima.

## 8) Dica importante

Se o `POST Criar Sessao` funcionar, mas o `POST Enviar Mensagem` ou `POST Concluir Sessao` falhar com `Sessao nao encontrada`, significa que nao copiaste o `id` certo para a variavel `sessaoId`.

O fluxo correto e sempre:

1. criar sessao
2. copiar o `id`
3. colar em `sessaoId`
4. enviar mensagem
5. concluir sessao

Se estiveres a usar a collection importada, esta parte fica automatizada porque o request `POST Criar Sessao` grava o `sessaoId` no environment.
