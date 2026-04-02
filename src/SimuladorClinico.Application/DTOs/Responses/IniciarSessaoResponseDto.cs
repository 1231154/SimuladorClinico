namespace SimuladorClinico.Application.DTOs.Responses;

public sealed class IniciarSessaoResponseDto
{
    public SessaoDeSimulacaoDto Sessao { get; init; } = new();
}
