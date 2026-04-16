using System.Collections.Concurrent;
using SimuladorClinico.Application.Contracts.Services;
using SimuladorClinico.Application.DTOs.Requests;
using SimuladorClinico.Application.DTOs.Responses;
using SimuladorClinico.Domain.Enums;

namespace SimuladorClinico.Application.Services;

public sealed class SimulacaoService : ISimulacaoService
{
    private static readonly ConcurrentDictionary<Guid, SessaoDeSimulacaoDto> Sessoes = new();

    private static int NormalizarPontuacao(int valor) => Math.Clamp(valor, 0, 100);

    private static AvaliacaoDto GerarAvaliacao(Guid sessaoId, int totalInteracoes)
    {
        var baseScore = 45 + totalInteracoes * 7;

        return new AvaliacaoDto
        {
            Id = Guid.NewGuid(),
            RigorCientifico = NormalizarPontuacao(baseScore + 12),
            CoerenciaSintomas = NormalizarPontuacao(baseScore + 6),
            GrauDeRealismo = NormalizarPontuacao(55 + totalInteracoes * 5),
            MaisValiaPedagogica = NormalizarPontuacao(baseScore + 10)
        };
    }

    public Task<IniciarSessaoResponseDto> IniciarSessaoAsync(
        IniciarSessaoRequestDto request,
        CancellationToken cancellationToken = default)
    {
        var sessao = new SessaoDeSimulacaoDto
        {
            Id = Guid.NewGuid(),
            DataInicio = DateTime.UtcNow,
            Estado = EstadoSessaoDeSimulacao.Criada,
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
        if (!Sessoes.TryGetValue(request.SessaoId, out var sessaoAtual))
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

        var interacoesAtualizadas = sessaoAtual.Interacoes
            .Concat(new[] { mensagemProfissional, respostaIa })
            .ToArray();

        var sessaoAtualizada = new SessaoDeSimulacaoDto
        {
            Id = sessaoAtual.Id,
            DataInicio = sessaoAtual.DataInicio,
            DataFim = sessaoAtual.DataFim,
            Estado = EstadoSessaoDeSimulacao.EmAndamento,
            CasoId = sessaoAtual.CasoId,
            Interacoes = interacoesAtualizadas,
            Avaliacao = sessaoAtual.Avaliacao
        };

        Sessoes[request.SessaoId] = sessaoAtualizada;

        return Task.FromResult(new ProcessarNovaMensagemResponseDto
        {
            SessaoId = request.SessaoId,
            MensagemProfissional = mensagemProfissional,
            RespostaIa = respostaIa
        });
    }

    public Task<SessaoDeSimulacaoDto?> ObterSessaoPorIdAsync(Guid sessaoId, CancellationToken cancellationToken = default)
    {
        Sessoes.TryGetValue(sessaoId, out var sessao);
        return Task.FromResult(sessao);
    }

    public Task<SessaoDeSimulacaoDto?> ConcluirSessaoAsync(Guid sessaoId, CancellationToken cancellationToken = default)
    {
        if (!Sessoes.TryGetValue(sessaoId, out var sessaoAtual))
        {
            return Task.FromResult<SessaoDeSimulacaoDto?>(null);
        }

        var avaliacao = GerarAvaliacao(sessaoId, sessaoAtual.Interacoes.Count);

        var sessaoFinalizada = new SessaoDeSimulacaoDto
        {
            Id = sessaoAtual.Id,
            DataInicio = sessaoAtual.DataInicio,
            DataFim = DateTime.UtcNow,
            Estado = EstadoSessaoDeSimulacao.Finalizada,
            CasoId = sessaoAtual.CasoId,
            Interacoes = sessaoAtual.Interacoes,
            Avaliacao = avaliacao
        };

        Sessoes[sessaoId] = sessaoFinalizada;
        return Task.FromResult<SessaoDeSimulacaoDto?>(sessaoFinalizada);
    }
}
