using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Application.DTOs.Responses;

public sealed class SessaoDeSimulacaoDto
{
    public Guid Id { get; init; }
    public DateTime DataInicio { get; init; }
    public DateTime? DataFim { get; init; }
    public EstadoSessaoDeSimulacao Estado { get; init; }
    public Guid CasoId { get; init; }
    public IReadOnlyCollection<InteracaoChatDto> Interacoes { get; init; } = [];
    public AvaliacaoDto? Avaliacao { get; init; }
}
