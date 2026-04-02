namespace SimuladorClinico.Application.DTOs.Requests;

public sealed class IniciarSessaoRequestDto
{
    public Guid ProfissionalId { get; init; }
    public Guid CasoId { get; init; }
}
