using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Domain.Entities;

public class InteracaoChat
{
    public Guid Id { get; set; }
    public RemetenteInteracao Remetente { get; set; }
    public string TextoDaMensagem { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }

    public Guid SessaoId { get; set; }
    public SessaoDeSimulacao Sessao { get; set; } = null!;
}
