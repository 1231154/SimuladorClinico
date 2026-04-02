using SimuladorClinico.Domain.Entities;

namespace SimuladorClinico.Application.Contracts.Repositories;

public interface ICasoRepository
{
    Task<CasoClinico?> ObterPorIdAsync(Guid id, CancellationToken cancellationToken = default);
    Task<IReadOnlyCollection<CasoClinico>> ObterTodosAsync(CancellationToken cancellationToken = default);
    Task AdicionarAsync(CasoClinico casoClinico, CancellationToken cancellationToken = default);
}
