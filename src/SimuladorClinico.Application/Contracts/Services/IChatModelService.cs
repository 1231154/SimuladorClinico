using System.Threading;
namespace SimuladorClinico.Application.Contracts.Services;

public interface IChatModelService
{
    /// <summary>
    /// Gera uma resposta a partir do modelo LLM (Ollama) para uma dada sessão e texto de utilizador.
    /// Retorna apenas o texto da resposta; metadados podem ser adicionados posteriormente.
    /// </summary>
    Task<string> GerarRespostaAsync(Guid sessaoId, string textoUsuario, CancellationToken cancellationToken = default);
}
