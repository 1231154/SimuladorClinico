namespace SimuladorClinico.Domain.Entities;

public class CasoClinico
{
    public Guid Id { get; set; }
    public string ConhecimentoDescritivo { get; set; } = string.Empty;
    public string Sintomas { get; set; } = string.Empty;
    public string Restricoes { get; set; } = string.Empty;
    public string ValidacaoClinica { get; set; } = string.Empty;

    public ICollection<SessaoDeSimulacao> SessoesDeSimulacao { get; set; } = new List<SessaoDeSimulacao>();
}
