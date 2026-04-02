namespace SimuladorClinico.Application.DTOs.Responses;

public sealed class CasoClinicoDto
{
    public Guid Id { get; init; }
    public string ConhecimentoDescritivo { get; init; } = string.Empty;
    public string Sintomas { get; init; } = string.Empty;
    public string Restricoes { get; init; } = string.Empty;
    public string ValidacaoClinica { get; init; } = string.Empty;
}
