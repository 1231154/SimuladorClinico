namespace SimuladorClinico.Application.Contracts.Services;

public interface IKnowledgeService
{
    /// <summary>
    /// Carrega todo o conteúdo disponível nas fontes de conhecimento configuradas e retorna como texto combinado.
    /// Implementações podem devolver texto resumido ou completo.
    /// </summary>
    Task<string> LoadAllAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Lista os identificadores (nomes/paths) dos documentos disponíveis.
    /// </summary>
    Task<IEnumerable<string>> ListDocumentsAsync(CancellationToken cancellationToken = default);
}
