namespace SimuladorClinico.Application.DTOs.Responses;

public sealed class ProcessarNovaMensagemResponseDto
{
    public Guid SessaoId { get; init; }
    public InteracaoChatDto MensagemProfissional { get; init; } = new();
    public InteracaoChatDto? RespostaIa { get; init; }
}
