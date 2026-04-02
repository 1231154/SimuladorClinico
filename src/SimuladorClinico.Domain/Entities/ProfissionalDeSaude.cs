using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Domain.Entities;

public class ProfissionalDeSaude
{
    public Guid Id { get; set; }
    public string Identificacao { get; set; } = string.Empty;
    public NivelExperiencia NivelExperiencia { get; set; }

    public ICollection<SessaoDeSimulacao> SessoesDeSimulacao { get; set; } = new List<SessaoDeSimulacao>();
}
