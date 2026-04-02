namespace SimuladorClinico.Application.DTOs.Responses;

public sealed class AvaliacaoDto
{
    public Guid Id { get; init; }
    public int RigorCientifico { get; init; }
    public int CoerenciaSintomas { get; init; }
    public int GrauDeRealismo { get; init; }
    public int MaisValiaPedagogica { get; init; }
}
