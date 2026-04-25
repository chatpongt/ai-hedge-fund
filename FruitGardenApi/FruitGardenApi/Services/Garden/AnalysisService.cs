using System.Text.Json;
using FruitGardenApi.Agents;
using FruitGardenApi.Models.Garden;
using FruitGardenApi.Repositories;

namespace FruitGardenApi.Services.Garden;

public class AnalysisService(GardenAnalysisOrchestrator orchestrator, IGardenRepository repo) : IAnalysisService
{
    public async Task<AnalysisRun> StartAnalysisAsync(List<Guid>? plantIds = null)
    {
        var run = await repo.CreateAnalysisRunAsync(new AnalysisRun { Status = "running" });
        _ = Task.Run(async () =>
        {
            try
            {
                var plan = await orchestrator.RunAnalysisAsync(plantIds);
                run.ResultJson = JsonSerializer.Serialize(plan);
                run.Status = "completed";
            }
            catch (Exception ex)
            {
                run.ResultJson = JsonSerializer.Serialize(new { error = ex.Message });
                run.Status = "failed";
            }
            await repo.UpdateAnalysisRunAsync(run);
        });
        return run;
    }

    public Task<AnalysisRun?> GetAnalysisRunAsync(Guid runId) => repo.GetAnalysisRunAsync(runId);
}
