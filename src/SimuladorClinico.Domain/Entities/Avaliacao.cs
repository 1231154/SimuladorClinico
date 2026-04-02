namespace SimuladorClinico.Domain.Entities;

public class Avaliacao
{
    public Guid Id { get; set; }
    public int RigorCientifico { get; set; }
    public int CoerenciaSintomas { get; set; }
    public int GrauDeRealismo { get; set; }
    public int MaisValiaPedagogica { get; set; }

    public Guid SessaoId { get; set; }
    public SessaoDeSimulacao Sessao { get; set; } = null!;
}
