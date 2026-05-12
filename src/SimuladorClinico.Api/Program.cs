using SimuladorClinico.Application.Contracts.Services;
using SimuladorClinico.Infrastructure.Services;
using SimuladorClinico.Infrastructure.Knowledge;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddCors(options =>
{
    options.AddPolicy("FrontendDev", policy =>
    {
        policy.WithOrigins(
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "https://localhost:5173",
                "https://127.0.0.1:5173")
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});
// Registrar serviço de LLM (Python AI por omissão, ou mock)
var useMock = string.Equals(Environment.GetEnvironmentVariable("USE_MOCK_OLLAMA"), "true", StringComparison.OrdinalIgnoreCase);
var usePythonAi = string.Equals(Environment.GetEnvironmentVariable("USE_PYTHON_AI_SERVICE") ?? "true", "true", StringComparison.OrdinalIgnoreCase);
if (useMock)
{
    builder.Services.AddSingleton<IChatModelService, MockChatModelService>();
}
else if (usePythonAi)
{
    builder.Services.AddHttpClient<IChatModelService, PythonAIServiceClient>(client =>
    {
        var timeoutSec = int.TryParse(Environment.GetEnvironmentVariable("PYTHON_AI_TIMEOUT"), out var t) ? t : 120;
        client.Timeout = TimeSpan.FromSeconds(timeoutSec);
    });
}
else
{
    // Registar HttpClient-based implementation. Timeout configurable via OLLAMA_TIMEOUT (segundos)
    builder.Services.AddHttpClient<IChatModelService, OllamaChatModelService>(client =>
    {
        var timeoutSec = int.TryParse(Environment.GetEnvironmentVariable("OLLAMA_TIMEOUT"), out var t) ? t : 60;
        client.Timeout = TimeSpan.FromSeconds(timeoutSec);
    });
}

// Registrar serviço de conhecimento (leitura de ficheiros) para futuras integrações RAG
builder.Services.AddSingleton<IKnowledgeService, FileKnowledgeService>();

builder.Services.AddScoped<SimuladorClinico.Application.Contracts.Services.ISimulacaoService, SimuladorClinico.Application.Services.SimulacaoService>();

var app = builder.Build();

var runningInContainer = string.Equals(
    Environment.GetEnvironmentVariable("DOTNET_RUNNING_IN_CONTAINER"),
    "true",
    StringComparison.OrdinalIgnoreCase);

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("FrontendDev");

if (!app.Environment.IsDevelopment() && !runningInContainer)
{
    app.UseHttpsRedirection();
}

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.MapControllers();

app.Run();
