using SimuladorClinico.Domain.Entities;

namespace SimuladorClinico.Application.Contracts.Repositories;

public interface ISessaoRepository
{
    Task<SessaoDeSimulacao?> ObterPorIdAsync(Guid id, CancellationToken cancellationToken = default);
    Task AdicionarAsync(SessaoDeSimulacao sessao, CancellationToken cancellationToken = default);
    Task AtualizarAsync(SessaoDeSimulacao sessao, CancellationToken cancellationToken = default);
}
