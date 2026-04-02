using System.Collections.Concurrent;
using SimuladorClinico.Application.Contracts.Services;
using SimuladorClinico.Application.DTOs.Requests;
using SimuladorClinico.Application.DTOs.Responses;
using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Application.Services;

public sealed class SimulacaoService : ISimulacaoService
{
    private static readonly ConcurrentDictionary<Guid, SessaoDeSimulacaoDto> Sessoes = new();

    public Task<IniciarSessaoResponseDto> IniciarSessaoAsync(
        IniciarSessaoRequestDto request,
        CancellationToken cancellationToken = default)
    {
        var sessao = new SessaoDeSimulacaoDto
        {
            Id = Guid.NewGuid(),
            DataInicio = DateTime.UtcNow,
            Estado = EstadoSessaoDeSimulacao.Criada,
            ProfissionalId = request.ProfissionalId,
            CasoId = request.CasoId,
            Interacoes = Array.Empty<InteracaoChatDto>(),
            Avaliacao = null
        };

        Sessoes[sessao.Id] = sessao;

        return Task.FromResult(new IniciarSessaoResponseDto
        {
            Sessao = sessao
        });
    }

    public Task<ProcessarNovaMensagemResponseDto> ProcessarNovaMensagemAsync(
        ProcessarNovaMensagemRequestDto request,
        CancellationToken cancellationToken = default)
    {
        if (!Sessoes.ContainsKey(request.SessaoId))
        {
            throw new KeyNotFoundException($"Sessao {request.SessaoId} nao encontrada.");
        }

        var mensagemProfissional = new InteracaoChatDto
        {
            Id = Guid.NewGuid(),
            Remetente = RemetenteInteracao.Profissional,
            TextoDaMensagem = request.TextoDaMensagem,
            Timestamp = DateTime.UtcNow
        };

        var respostaIa = new InteracaoChatDto
        {
            Id = Guid.NewGuid(),
            Remetente = RemetenteInteracao.IA,
            TextoDaMensagem = "Resposta simulada da IA. A integracao real com o modelo sera adicionada numa fase posterior.",
            Timestamp = DateTime.UtcNow
        };

        return Task.FromResult(new ProcessarNovaMensagemResponseDto
        {
            SessaoId = request.SessaoId,
            MensagemProfissional = mensagemProfissional,
            RespostaIa = respostaIa
        });
    }
}
