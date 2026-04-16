using Microsoft.AspNetCore.Mvc;
using SimuladorClinico.Application.Contracts.Services;
using SimuladorClinico.Application.DTOs.Requests;
using SimuladorClinico.Application.DTOs.Responses;

namespace SimuladorClinico.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class SimulacoesController : ControllerBase
{
    private readonly ISimulacaoService _simulacaoService;

    public SimulacoesController(ISimulacaoService simulacaoService)
    {
        _simulacaoService = simulacaoService;
    }

    [HttpPost("sessoes")]
    [ProducesResponseType(typeof(IniciarSessaoResponseDto), StatusCodes.Status201Created)]
    public async Task<ActionResult<IniciarSessaoResponseDto>> IniciarSessaoAsync(
        [FromBody] IniciarSessaoRequestDto request,
        CancellationToken cancellationToken)
    {
        var response = await _simulacaoService.IniciarSessaoAsync(request, cancellationToken);
        return CreatedAtRoute("ObterSessaoPorId", new { sessaoId = response.Sessao.Id }, response);
    }

    [HttpPost("sessoes/{sessaoId:guid}/mensagens")]
    [ProducesResponseType(typeof(ProcessarNovaMensagemResponseDto), StatusCodes.Status200OK)]
    public async Task<ActionResult<ProcessarNovaMensagemResponseDto>> ProcessarNovaMensagemAsync(
        [FromRoute] Guid sessaoId,
        [FromBody] ProcessarNovaMensagemRequestDto request,
        CancellationToken cancellationToken)
    {
        var requestComSessao = new ProcessarNovaMensagemRequestDto
        {
            SessaoId = sessaoId,
            TextoDaMensagem = request.TextoDaMensagem
        };

        var response = await _simulacaoService.ProcessarNovaMensagemAsync(requestComSessao, cancellationToken);
        return Ok(response);
    }

    [HttpGet("sessoes/{sessaoId:guid}", Name = "ObterSessaoPorId")]
    [ProducesResponseType(typeof(SessaoDeSimulacaoDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<SessaoDeSimulacaoDto>> ObterSessaoPorIdAsync([FromRoute] Guid sessaoId, CancellationToken cancellationToken)
    {
        var sessao = await _simulacaoService.ObterSessaoPorIdAsync(sessaoId, cancellationToken);

        if (sessao is null)
        {
            return NotFound();
        }

        return Ok(sessao);
    }

    [HttpPost("sessoes/{sessaoId:guid}/concluir")]
    [ProducesResponseType(typeof(SessaoDeSimulacaoDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<SessaoDeSimulacaoDto>> ConcluirSessaoAsync([FromRoute] Guid sessaoId, CancellationToken cancellationToken)
    {
        var sessao = await _simulacaoService.ConcluirSessaoAsync(sessaoId, cancellationToken);

        if (sessao is null)
        {
            return NotFound();
        }

        return Ok(sessao);
    }
}
