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
    public ActionResult<SessaoDeSimulacaoDto> ObterSessaoPorIdAsync([FromRoute] Guid sessaoId)
    {
        return Ok(new SessaoDeSimulacaoDto { Id = sessaoId });
    }
}
