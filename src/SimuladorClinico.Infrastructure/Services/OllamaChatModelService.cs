using System.Net.Http;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using SimuladorClinico.Application.Contracts.Services;
using SimuladorClinico.Infrastructure.Knowledge;

namespace SimuladorClinico.Infrastructure.Services;

public class OllamaChatModelService : IChatModelService
{
    private readonly HttpClient _httpClient;
    private readonly string _host;
    private readonly string _model;
    private readonly IConfiguration _configuration;
    private readonly IKnowledgeService _knowledgeService;

    public OllamaChatModelService(HttpClient httpClient, IConfiguration configuration, IKnowledgeService knowledgeService)
    {
        _httpClient = httpClient;
        _configuration = configuration;
        _knowledgeService = knowledgeService;
        _host = configuration["OLLAMA_HOST"] ?? "http://localhost:11434";
        _model = configuration["OLLAMA_MODEL"] ?? "mistral:latest";
        // Ensure base address
        if (!_host.StartsWith("http")) _host = "http://" + _host;
        _httpClient.BaseAddress = new Uri(_host);
    }

    private static string Truncate(string s, int maxChars)
    {
        if (string.IsNullOrEmpty(s)) return string.Empty;
        if (s.Length <= maxChars) return s;
        return s.Substring(0, maxChars);
    }

    public async Task<string> GerarRespostaAsync(Guid sessaoId, string textoUsuario, CancellationToken cancellationToken = default)
    {
        // Optionally load knowledge and build prompt
        var useKnowledge = string.Equals(_configuration["USE_KNOWLEDGE"], "true", StringComparison.OrdinalIgnoreCase);
        string knowledgeText = string.Empty;
        if (useKnowledge)
        {
            try
            {
                knowledgeText = await _knowledgeService.LoadAllAsync(cancellationToken);
            }
            catch
            {
                knowledgeText = string.Empty;
            }
        }

        var maxChars = 4000;
        if (int.TryParse(_configuration["KNOWLEDGE_MAX_CHARS"], out var mc)) maxChars = mc;
        knowledgeText = Truncate(knowledgeText, maxChars);

        var systemPrompt = _configuration["LLM:SystemPrompt"] ?? "Você é um assistente clínico. Responda de forma concisa e pedagógica.";

        var fullPromptBuilder = new StringBuilder();
        fullPromptBuilder.AppendLine("SYSTEM:");
        fullPromptBuilder.AppendLine(systemPrompt);
        if (!string.IsNullOrWhiteSpace(knowledgeText))
        {
            fullPromptBuilder.AppendLine();
            fullPromptBuilder.AppendLine("CONTEXT:");
            fullPromptBuilder.AppendLine(knowledgeText);
        }
        fullPromptBuilder.AppendLine();
        fullPromptBuilder.AppendLine("USER:");
        fullPromptBuilder.AppendLine(textoUsuario);

        var promptText = fullPromptBuilder.ToString();

        // Simple request body for Ollama local HTTP API. Adjust if Ollama API differs.
        var requestPayload = new
        {
            model = _model,
            prompt = promptText,
            max_tokens = 512
        };

        // Ollama /api/generate streams responses as NDJSON (newline-delimited JSON)
        // To avoid streaming, optionally add "stream": false to the payload

        var json = JsonSerializer.Serialize(requestPayload);
        using var content = new StringContent(json, Encoding.UTF8, "application/json");

        try
        {
            using var resp = await _httpClient.PostAsync("/api/generate", content, cancellationToken);
            var responseText = await resp.Content.ReadAsStringAsync(cancellationToken);
            if (!resp.IsSuccessStatusCode)
            {
                return $"[Ollama error: {resp.StatusCode}] {responseText}";
            }

            // Parse Ollama's streaming response (NDJSON = newline-delimited JSON)
            try
            {
                var responseBuilder = new StringBuilder();
                var lines = responseText.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.RemoveEmptyEntries);

                foreach (var line in lines)
                {
                    if (string.IsNullOrEmpty(line)) continue;
                    using var lineDoc = JsonDocument.Parse(line);
                    var lineRoot = lineDoc.RootElement;
                    if (lineRoot.TryGetProperty("response", out var respChunk))
                    {
                        responseBuilder.Append(respChunk.GetString() ?? string.Empty);
                    }
                }

                var combinedResponse = responseBuilder.ToString();
                if (!string.IsNullOrEmpty(combinedResponse))
                {
                    return combinedResponse;
                }

                // Fallback: try single JSON parse for non-streaming responses
                using (var doc = JsonDocument.Parse(responseText))
                {
                    var root = doc.RootElement;
                    if (root.TryGetProperty("text", out var textProp))
                        return textProp.GetString() ?? string.Empty;
                    if (root.TryGetProperty("response", out var respProp))
                        return respProp.GetString() ?? string.Empty;
                    if (root.TryGetProperty("choices", out var choices) && choices.GetArrayLength() > 0)
                    {
                        var first = choices[0];
                        if (first.TryGetProperty("text", out var ctext)) return ctext.GetString() ?? string.Empty;
                        if (first.TryGetProperty("message", out var msg) && msg.TryGetProperty("content", out var contentProp)) return contentProp.GetString() ?? string.Empty;
                    }
                }
            }
            catch
            {
                // If parsing fails, return raw response
            }

            return responseText;
        }
        catch (TaskCanceledException)
        {
            return "[Ollama timeout]";
        }
        catch (Exception ex)
        {
            return $"[Ollama exception] {ex.Message}";
        }
    }
}



