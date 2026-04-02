# Estrutura de Pastas Sugerida

```text
src/
  SimuladorClinico.Api/
    Controllers/
    Program.cs

  SimuladorClinico.Application/
    Contracts/
      Repositories/
      Services/
    DTOs/
      Requests/
      Responses/

  SimuladorClinico.Domain/
    Entities/
    Enums/

  SimuladorClinico.Infrastructure/
    Persistence/
    DependencyInjection.cs

tests/
  SimuladorClinico.UnitTests/
  SimuladorClinico.IntegrationTests/
```

## Responsabilidades por Camada

- API: endpoints HTTP, validação de entrada, serialização e códigos de resposta.
- Application: contratos de casos de uso (serviços) e contratos de persistência (repositórios), DTOs de entrada e saída.
- Domain: regras e modelo de domínio (entidades, enums, invariantes).
- Infrastructure: EF Core DbContext, implementações de repositórios e integrações externas.
