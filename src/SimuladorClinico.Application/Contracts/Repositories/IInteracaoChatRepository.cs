using SimuladorClinico.Domain.Entities;

namespace SimuladorClinico.Application.Contracts.Repositories;

public interface IInteracaoChatRepository
{
    Task<IReadOnlyCollection<InteracaoChat>> ObterPorSessaoAsync(Guid sessaoId, CancellationToken cancellationToken = default);
    Task AdicionarAsync(InteracaoChat interacao, CancellationToken cancellationToken = default);
}
