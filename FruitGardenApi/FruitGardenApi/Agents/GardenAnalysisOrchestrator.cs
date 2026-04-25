using FruitGardenApi.Models.Garden;
using FruitGardenApi.Repositories;
using Microsoft.SemanticKernel;

namespace FruitGardenApi.Agents;

public class GardenAnalysisOrchestrator(
    IGardenRepository repo,
    WateringPlugin watering,
    PestDetectionPlugin pest,
    HarvestPredictorPlugin harvest,
    DiseaseMonitorPlugin disease)
{
    public async Task<GardenActionPlan> RunAnalysisAsync(List<Guid>? plantIds = null)
    {
        var plants = await repo.GetPlantsAsync();
        if (plantIds?.Count > 0)
            plants = plants.Where(p => plantIds.Contains(p.Id)).ToList();

        // Run all agents for all plants in parallel (mirrors LangGraph parallel execution)
        var analysisResults = await Task.WhenAll(plants.Select(async plant =>
        {
            var (wateringResult, pestResult, harvestResult, diseaseResult) = await (
                watering.AnalyzeWateringAsync(plant.Id),
                pest.DetectPestsAsync(plant.Id),
                harvest.PredictHarvestAsync(plant.Id),
                disease.MonitorDiseaseAsync(plant.Id)
            );

            return new PlantAnalysisResult
            {
                PlantId = plant.Id,
                PlantName = plant.Name,
                Watering = wateringResult,
                PestDetection = pestResult,
                HarvestPrediction = harvestResult,
                DiseaseMonitor = diseaseResult,
            };
        }));

        // Prioritize tasks based on signals
        var prioritizedTasks = PrioritizeTasks(analysisResults);

        return new GardenActionPlan
        {
            RunId = Guid.NewGuid(),
            AnalyzedAt = DateTime.UtcNow,
            PlantResults = [.. analysisResults],
            PrioritizedTasks = prioritizedTasks,
            Summary = GenerateSummary(analysisResults),
        };
    }

    private static List<GardenTask> PrioritizeTasks(PlantAnalysisResult[] results)
    {
        var tasks = new List<GardenTask>();
        var today = DateOnly.FromDateTime(DateTime.Today);

        foreach (var r in results)
        {
            if (r.Watering.Signal == "water_needed")
                tasks.Add(new GardenTask { PlantId = r.PlantId, TaskType = "water", Priority = "urgent", DueDate = today, Instructions = r.Watering.RecommendedAction ?? "", Status = "pending" });

            if (r.DiseaseMonitor.Signal == "treatment_needed")
                tasks.Add(new GardenTask { PlantId = r.PlantId, TaskType = "spray", Priority = "urgent", DueDate = today, Instructions = r.DiseaseMonitor.RecommendedAction ?? "", Status = "pending" });

            if (r.PestDetection.Signal == "pest_detected")
                tasks.Add(new GardenTask { PlantId = r.PlantId, TaskType = "spray", Priority = "high", DueDate = today, Instructions = r.PestDetection.RecommendedAction ?? "", Status = "pending" });

            if (r.HarvestPrediction.Signal == "harvest_ready")
                tasks.Add(new GardenTask { PlantId = r.PlantId, TaskType = "harvest", Priority = "high", DueDate = today, Instructions = r.HarvestPrediction.RecommendedAction ?? "", Status = "pending" });

            if (r.HarvestPrediction.Signal == "harvest_urgent")
                tasks.Add(new GardenTask { PlantId = r.PlantId, TaskType = "harvest", Priority = "urgent", DueDate = today, Instructions = r.HarvestPrediction.RecommendedAction ?? "", Status = "pending" });

            if (r.PestDetection.Signal == "high_risk" || r.DiseaseMonitor.Signal == "disease_risk")
                tasks.Add(new GardenTask { PlantId = r.PlantId, TaskType = "spray", Priority = "medium", DueDate = today.AddDays(2), Instructions = r.DiseaseMonitor.RecommendedAction ?? r.PestDetection.RecommendedAction ?? "", Status = "pending" });
        }

        // Sort: urgent first, then by task type importance
        var priorityOrder = new[] { "urgent", "high", "medium", "low" };
        return tasks.OrderBy(t => Array.IndexOf(priorityOrder, t.Priority)).ToList();
    }

    private static string GenerateSummary(PlantAnalysisResult[] results)
    {
        var needsWater = results.Count(r => r.Watering.Signal == "water_needed");
        var hasPest = results.Count(r => r.PestDetection.Signal is "pest_detected" or "high_risk");
        var readyHarvest = results.Count(r => r.HarvestPrediction.Signal is "harvest_ready" or "harvest_urgent");
        var diseased = results.Count(r => r.DiseaseMonitor.Signal is "treatment_needed" or "disease_risk");

        return $"วิเคราะห์ {results.Length} ต้น: ต้องรดน้ำ {needsWater} ต้น, เสี่ยงศัตรูพืช {hasPest} ต้น, พร้อมเก็บเกี่ยว {readyHarvest} ต้น, ต้องดูแลโรค {diseased} ต้น";
    }
}
