using System.ComponentModel;
using FruitGardenApi.Models.Garden;
using FruitGardenApi.Repositories;
using Microsoft.SemanticKernel;

namespace FruitGardenApi.Agents;

public class PestDetectionPlugin(IGardenRepository repo)
{
    [KernelFunction("detect_pests")]
    [Description("Analyzes recent observations and weather conditions to assess pest risk for a plant")]
    public async Task<GardenSignal> DetectPestsAsync(Guid plantId)
    {
        var observations = await repo.GetObservationsAsync(plantId);
        var weather = await repo.GetWeatherLogsAsync(14);

        var recentObs = observations.Where(o => o.ObservationDate >= DateOnly.FromDateTime(DateTime.Today.AddDays(-14))).ToList();
        var pestObs = recentObs.Where(o => o.ObsType == "pest").ToList();

        // Pest observation score
        var highSeverityPests = pestObs.Count(o => o.Severity == "high");
        var medSeverityPests = pestObs.Count(o => o.Severity == "medium");
        var obsScore = Math.Min(1f, (highSeverityPests * 0.4f + medSeverityPests * 0.2f + pestObs.Count * 0.1f));

        // Weather risk (high humidity + warm = pest-friendly)
        var avgHumidity = weather.Any() ? weather.Average(w => w.HumidityPct) : 65f;
        var avgTemp = weather.Any() ? weather.Average(w => w.TempHigh) : 32f;
        var weatherScore = (avgHumidity > 75 && avgTemp > 30) ? 0.7f : 0.3f;

        var riskScore = obsScore * 0.6f + weatherScore * 0.4f;

        string signal, action;
        if (highSeverityPests > 0 || riskScore > 0.6f)
        {
            signal = "pest_detected";
            action = "พ่นยาฆ่าแมลงทันที ตรวจสอบต้นข้างเคียง";
        }
        else if (riskScore > 0.35f)
        {
            signal = "high_risk";
            action = "เฝ้าระวังอย่างใกล้ชิด พิจารณาพ่นยาป้องกัน";
        }
        else
        {
            signal = "low_risk";
            action = "ตรวจสอบตามปกติ";
        }

        return new GardenSignal
        {
            Signal = signal,
            Confidence = (float)Math.Round(riskScore * 100f),
            Reasoning = $"การสังเกตศัตรูพืช 14 วัน: {pestObs.Count} ครั้ง (สูง: {highSeverityPests}), ความชื้นเฉลี่ย: {avgHumidity:F1}%",
            RecommendedAction = action,
        };
    }
}
