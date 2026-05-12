# Estrutura de Pastas Sugerida

```text
src/
  SimuladorClinico.Api/
    Controllers/
    Program.cs

  SimuladorClinico.Application/
    Contracts/
      Services/
    DTOs/
      Requests/
      Responses/
    Services/

  SimuladorClinico.Domain/
    Entities/
    Enums/

  SimuladorClinico.Infrastructure/
    Knowledge/
    Persistence/
    Services/
    DependencyInjection.cs

  SimuladorClinico.Web/
    src/
    index.html

python/

docs/
  knowledge/

testes/
  SimuladorClinico.UnitTests/
  SimuladorClinico.IntegrationTests/

docs/fase2/arquitetura/
  README.md
  logicalview.puml
  processview.puml
  deploymentview.puml
```

## Responsabilidades por Camada

- API: endpoints HTTP, validação de entrada, serialização e códigos de resposta.
- Application: contratos de casos de uso (serviços) e DTOs de entrada e saída.
- Domain: regras e modelo de domínio (entidades, enums, invariantes).
- Infrastructure: serviços de IA, conhecimento, integrações externas e armazenamento temporário da fase atual.
- Web: SPA React/Vite que consome a API REST.
- python: serviço AI opcional/documentado para a arquitetura híbrida.

> Nota: o workspace usa `testes/` como pasta de testes e não `tests/`.
