using SimuladorClinico.Application.Contracts.Services;

namespace SimuladorClinico.Infrastructure.Services;

public class MockChatModelService : IChatModelService
{
    public Task<string> GerarRespostaAsync(Guid sessaoId, string textoUsuario, CancellationToken cancellationToken = default)
    {
        var resposta = $"[MOCK] Resposta simulada para a sessão {sessaoId}: '{textoUsuario}'";
        return Task.FromResult(resposta);
    }
}
