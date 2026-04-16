using SimuladorClinico.Application.DTOs.Requests;
using SimuladorClinico.Application.DTOs.Responses;

namespace SimuladorClinico.Application.Contracts.Services;

public interface ISimulacaoService
{
    Task<IniciarSessaoResponseDto> IniciarSessaoAsync(IniciarSessaoRequestDto request, CancellationToken cancellationToken = default);
    Task<ProcessarNovaMensagemResponseDto> ProcessarNovaMensagemAsync(ProcessarNovaMensagemRequestDto request, CancellationToken cancellationToken = default);
    Task<SessaoDeSimulacaoDto?> ObterSessaoPorIdAsync(Guid sessaoId, CancellationToken cancellationToken = default);
    Task<SessaoDeSimulacaoDto?> ConcluirSessaoAsync(Guid sessaoId, CancellationToken cancellationToken = default);
}
