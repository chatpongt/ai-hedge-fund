using FruitGardenApi.Services.Garden;
using Microsoft.AspNetCore.Mvc;

namespace FruitGardenApi.Controllers;

[ApiController]
[Route("api/analysis")]
public class AnalysisController(IAnalysisService svc) : ControllerBase
{
    [HttpPost("run")]
    public async Task<IActionResult> RunAnalysis([FromBody] List<Guid>? plantIds = null)
    {
        var run = await svc.StartAnalysisAsync(plantIds);
        return Accepted(new { runId = run.Id, status = run.Status });
    }

    [HttpGet("{runId}")]
    public async Task<IActionResult> GetResult(Guid runId)
    {
        var run = await svc.GetAnalysisRunAsync(runId);
        return run is null ? NotFound() : Ok(run);
    }
}
