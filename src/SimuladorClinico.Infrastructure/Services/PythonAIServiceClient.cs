using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using SimuladorClinico.Application.Contracts.Services;

namespace SimuladorClinico.Infrastructure.Services;

/// <summary>
/// Service that interfaces with the Python AI Service (FastAPI)
/// This is the new architecture where .NET calls Python for LLM operations
/// </summary>
public class PythonAIServiceClient : IChatModelService
{
    private readonly HttpClient _httpClient;
    private readonly string _pythonAIHost;
    private readonly IConfiguration _configuration;
    private readonly ILogger<PythonAIServiceClient> _logger;

    public PythonAIServiceClient(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<PythonAIServiceClient> logger)
    {
        _httpClient = httpClient;
        _configuration = configuration;
        _logger = logger;
        _pythonAIHost = configuration["PYTHON_AI_HOST"] ?? "http://localhost:5555";

        if (!_pythonAIHost.StartsWith("http"))
            _pythonAIHost = "http://" + _pythonAIHost;

        _httpClient.BaseAddress = new Uri(_pythonAIHost);
        _httpClient.Timeout = TimeSpan.FromSeconds(120); // Longer timeout for AI processing
    }

    /// <summary>
    /// Generate response by calling Python AI Service
    /// </summary>
    public async Task<string> GerarRespostaAsync(
        Guid sessaoId,
        string textoUsuario,
        CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation($"Calling Python AI Service for session {sessaoId}");

            var request = new
            {
                sessao_id = sessaoId.ToString(),
                user_message = textoUsuario,
                context = (string?)null,
                max_tokens = 512
            };

            var json = JsonSerializer.Serialize(request);
            using var content = new StringContent(json, Encoding.UTF8, "application/json");

            using var response = await _httpClient.PostAsync(
                "/api/ai/generate",
                content,
                cancellationToken);

            var responseText = await response.Content.ReadAsStringAsync(cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError($"Python AI Service error: {response.StatusCode} - {responseText}");
                return $"[AI Service error: {response.StatusCode}]";
            }

            // Parse response
            try
            {
                using var doc = JsonDocument.Parse(responseText);
                var root = doc.RootElement;

                if (root.TryGetProperty("response", out var responseProp))
                {
                    var aiResponse = responseProp.GetString() ?? string.Empty;
                    if (root.TryGetProperty("case_id", out var caseIdProp) && caseIdProp.ValueKind == JsonValueKind.Number)
                    {
                        _logger.LogWarning("Python AI active patient ID: {CaseId} for session {SessionId}", caseIdProp.GetInt32(), sessaoId);
                    }
                    else
                    {
                        _logger.LogWarning("Python AI response returned without case_id for session {SessionId}", sessaoId);
                    }
                    _logger.LogInformation($"AI Service responded successfully");
                    return aiResponse;
                }

                _logger.LogWarning("Unexpected response format from Python AI Service");
                return responseText;
            }
            catch (JsonException ex)
            {
                _logger.LogError($"Failed to parse AI Service response: {ex.Message}");
                return responseText;
            }
        }
        catch (TaskCanceledException)
        {
            _logger.LogError("Python AI Service request timed out");
            return "[AI Service timeout]";
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError($"Failed to connect to Python AI Service: {ex.Message}");
            return "[AI Service unavailable]";
        }
        catch (Exception ex)
        {
            _logger.LogError($"Unexpected error calling Python AI Service: {ex.Message}");
            return $"[AI Service error: {ex.Message}]";
        }
    }
}
