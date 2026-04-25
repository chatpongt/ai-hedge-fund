using System.ComponentModel;
using FruitGardenApi.Models.Garden;
using FruitGardenApi.Repositories;
using Microsoft.SemanticKernel;

namespace FruitGardenApi.Agents;

public class HarvestPredictorPlugin(IGardenRepository repo)
{
    private static readonly Dictionary<string, int> TypicalDaysToHarvest = new()
    {
        ["Mangifera indica"] = 120,
        ["Durio zibethinus"] = 100,
        ["Dimocarpus longan"] = 135,
        ["Litchi chinensis"] = 100,
        ["Citrus maxima"] = 180,
        ["Citrus aurantiifolia"] = 90,
        ["Carica papaya"] = 75,
        ["Musa acuminata"] = 90,
    };

    [KernelFunction("predict_harvest")]
    [Description("Predicts harvest readiness based on growth stage, days since planting, and observations")]
    public async Task<GardenSignal> PredictHarvestAsync(Guid plantId)
    {
        var plant = await repo.GetPlantByIdAsync(plantId);
        if (plant == null)
            return new GardenSignal { Signal = "not_ready", Confidence = 0, Reasoning = "ไม่พบข้อมูลต้นไม้" };

        var observations = await repo.GetObservationsAsync(plantId);
        var harvestObs = observations.Where(o => o.ObsType == "harvest" &&
            o.ObservationDate >= DateOnly.FromDateTime(DateTime.Today.AddDays(-30))).ToList();

        if (plant.GrowthStage is "seedling" or "juvenile")
        {
            return new GardenSignal
            {
                Signal = "not_ready",
                Confidence = 95f,
                Reasoning = $"ต้นไม้อยู่ในระยะ {plant.GrowthStage} ยังไม่ถึงวัยออกผล",
                RecommendedAction = "ดูแลการเจริญเติบโตต่อไป"
            };
        }

        var daysSincePlanted = (DateOnly.FromDateTime(DateTime.Today).DayNumber - plant.PlantedDate.DayNumber);
        var typicalDays = TypicalDaysToHarvest.GetValueOrDefault(plant.Species, 120);
        var readinessScore = Math.Min(1f, (float)daysSincePlanted / (typicalDays * 365f / 12f));

        var hasHarvestObs = harvestObs.Any(o => o.Notes.Contains("สุก") || o.Notes.Contains("พร้อม"));

        string signal, action;
        float confidence;

        if (hasHarvestObs || (plant.GrowthStage == "bearing" && readinessScore > 0.9f))
        {
            signal = "harvest_ready";
            action = "เก็บเกี่ยวได้ทันที ตรวจสอบความสุกก่อนเก็บ";
            confidence = 85f;
        }
        else if (plant.GrowthStage == "bearing" && readinessScore > 0.7f)
        {
            signal = "harvest_urgent";
            action = "เตรียมอุปกรณ์เก็บเกี่ยว คาดว่าพร้อมใน 1-2 สัปดาห์";
            confidence = 70f;
        }
        else
        {
            signal = "not_ready";
            action = "ติดตามการเจริญเติบโตต่อไป";
            confidence = 80f;
        }

        return new GardenSignal
        {
            Signal = signal,
            Confidence = confidence,
            Reasoning = $"ระยะ: {plant.GrowthStage}, อายุ: {daysSincePlanted / 365} ปี {(daysSincePlanted % 365) / 30} เดือน, การสังเกตการเก็บเกี่ยว: {harvestObs.Count} ครั้ง",
            RecommendedAction = action,
        };
    }
}
