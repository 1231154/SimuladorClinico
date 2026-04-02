using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Application.DTOs.Responses;

public sealed class InteracaoChatDto
{
    public Guid Id { get; init; }
    public RemetenteInteracao Remetente { get; init; }
    public string TextoDaMensagem { get; init; } = string.Empty;
    public DateTime Timestamp { get; init; }
}
