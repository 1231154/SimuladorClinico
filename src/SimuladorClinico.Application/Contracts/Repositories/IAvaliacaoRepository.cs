using SimuladorClinico.Domain.Entities;

namespace SimuladorClinico.Application.Contracts.Repositories;

public interface IAvaliacaoRepository
{
    Task<Avaliacao?> ObterPorSessaoAsync(Guid sessaoId, CancellationToken cancellationToken = default);
    Task AdicionarAsync(Avaliacao avaliacao, CancellationToken cancellationToken = default);
    Task AtualizarAsync(Avaliacao avaliacao, CancellationToken cancellationToken = default);
}
