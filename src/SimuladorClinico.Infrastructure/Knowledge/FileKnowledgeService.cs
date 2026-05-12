using System.IO;
using Microsoft.Extensions.Configuration;
using SimuladorClinico.Application.Contracts.Services;

namespace SimuladorClinico.Infrastructure.Knowledge;

public class FileKnowledgeService : IKnowledgeService
{
    private readonly string _knowledgePath;

    public FileKnowledgeService(IConfiguration configuration)
    {
        _knowledgePath = configuration["KNOWLEDGE_PATH"] ?? Path.Combine(Directory.GetCurrentDirectory(), "docs", "knowledge");
    }

    public Task<IEnumerable<string>> ListDocumentsAsync(CancellationToken cancellationToken = default)
    {
        if (!Directory.Exists(_knowledgePath)) return Task.FromResult(Enumerable.Empty<string>());
        var files = Directory.EnumerateFiles(_knowledgePath, "*.md", SearchOption.TopDirectoryOnly)
            .Concat(Directory.EnumerateFiles(_knowledgePath, "*.txt", SearchOption.TopDirectoryOnly));
        return Task.FromResult(files);
    }

    public async Task<string> LoadAllAsync(CancellationToken cancellationToken = default)
    {
        if (!Directory.Exists(_knowledgePath)) return string.Empty;
        var sb = new System.Text.StringBuilder();
        var files = await ListDocumentsAsync(cancellationToken);
        foreach (var f in files)
        {
            try
            {
                var txt = await File.ReadAllTextAsync(f, cancellationToken);
                sb.AppendLine($"--- FILE: {Path.GetFileName(f)} ---");
                sb.AppendLine(txt);
                sb.AppendLine();
            }
            catch
            {
                // ignore read errors per-file
            }
        }

        return sb.ToString();
    }
}

