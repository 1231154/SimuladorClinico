using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Domain.Entities;

public class SessaoDeSimulacao
{
    public Guid Id { get; set; }
    public DateTime DataInicio { get; set; }
    public DateTime? DataFim { get; set; }
    public EstadoSessaoDeSimulacao Estado { get; set; }

    public Guid CasoId { get; set; }

    public CasoClinico Caso { get; set; } = null!;

    public ICollection<InteracaoChat> InteracoesChat { get; set; } = new List<InteracaoChat>();
    public Avaliacao? Avaliacao { get; set; }
}
