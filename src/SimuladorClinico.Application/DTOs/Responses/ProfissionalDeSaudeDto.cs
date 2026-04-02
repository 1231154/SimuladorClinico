using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Application.DTOs.Responses;

public sealed class ProfissionalDeSaudeDto
{
    public Guid Id { get; init; }
    public string Identificacao { get; init; } = string.Empty;
    public NivelExperiencia NivelExperiencia { get; init; }
}
