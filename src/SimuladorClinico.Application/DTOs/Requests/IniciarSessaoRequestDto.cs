namespace SimuladorClinico.Application.DTOs.Requests;

public sealed class IniciarSessaoRequestDto
{
    public Guid CasoId { get; init; }
}
