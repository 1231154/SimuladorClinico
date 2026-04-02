using SimuladorClinico.Domain.Entities;

namespace SimuladorClinico.Application.Contracts.Repositories;

public interface IProfissionalDeSaudeRepository
{
    Task<ProfissionalDeSaude?> ObterPorIdAsync(Guid id, CancellationToken cancellationToken = default);
    Task<IReadOnlyCollection<ProfissionalDeSaude>> ObterTodosAsync(CancellationToken cancellationToken = default);
    Task AdicionarAsync(ProfissionalDeSaude profissional, CancellationToken cancellationToken = default);
}
