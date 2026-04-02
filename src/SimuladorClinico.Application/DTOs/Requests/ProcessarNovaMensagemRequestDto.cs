namespace SimuladorClinico.Application.DTOs.Requests;

public sealed class ProcessarNovaMensagemRequestDto
{
    public Guid SessaoId { get; init; }
    public string TextoDaMensagem { get; init; } = string.Empty;
}
