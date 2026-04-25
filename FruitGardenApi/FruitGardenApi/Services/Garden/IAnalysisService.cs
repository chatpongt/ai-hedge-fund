using FruitGardenApi.Models.Garden;

namespace FruitGardenApi.Services.Garden;

public interface IAnalysisService
{
    Task<AnalysisRun> StartAnalysisAsync(List<Guid>? plantIds = null);
    Task<AnalysisRun?> GetAnalysisRunAsync(Guid runId);
}
