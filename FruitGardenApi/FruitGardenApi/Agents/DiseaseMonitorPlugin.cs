using System.ComponentModel;
using FruitGardenApi.Models.Garden;
using FruitGardenApi.Repositories;
using Microsoft.SemanticKernel;

namespace FruitGardenApi.Agents;

public class DiseaseMonitorPlugin(IGardenRepository repo)
{
    [KernelFunction("monitor_disease")]
    [Description("Monitors disease risk based on weather conditions, plant health status, and recent observations")]
    public async Task<GardenSignal> MonitorDiseaseAsync(Guid plantId)
    {
        var plant = await repo.GetPlantByIdAsync(plantId);
        var observations = await repo.GetObservationsAsync(plantId);
        var weather = await repo.GetWeatherLogsAsync(14);

        var recentDiseaseObs = observations
            .Where(o => o.ObsType == "disease" && o.ObservationDate >= DateOnly.FromDateTime(DateTime.Today.AddDays(-14)))
            .ToList();

        // Current health status score
        var healthScore = plant?.HealthStatus switch
        {
            "healthy"  => 0.1f,
            "stressed" => 0.4f,
            "diseased" => 0.8f,
            "critical" => 1.0f,
            _          => 0.2f
        };

        // Disease observation score
        var highDisease = recentDiseaseObs.Count(o => o.Severity == "high");
        var obsScore = Math.Min(1f, highDisease * 0.4f + recentDiseaseObs.Count * 0.15f);

        // Weather risk: high humidity + warm night → fungal diseases
        var avgHumidity = weather.Any() ? weather.Average(w => w.HumidityPct) : 65f;
        var avgNightTemp = weather.Any() ? weather.Average(w => w.TempLow) : 22f;
        var weatherRisk = (avgHumidity > 80 && avgNightTemp > 24) ? 0.8f : 0.3f;

        var riskScore = healthScore * 0.4f + obsScore * 0.4f + weatherRisk * 0.2f;

        string signal, action;
        if (plant?.HealthStatus is "diseased" or "critical" || highDisease > 0 || riskScore > 0.6f)
        {
            signal = "treatment_needed";
            action = "พ่นยาป้องกันโรค ตัดส่วนที่ติดโรคออก แจ้งผู้เชี่ยวชาญ";
        }
        else if (riskScore > 0.35f)
        {
            signal = "disease_risk";
            action = "เพิ่มความถี่การตรวจสอบ พิจารณาพ่นยาป้องกัน";
        }
        else
        {
            signal = "healthy";
            action = "สุขภาพดี ดูแลตามปกติ";
        }

        return new GardenSignal
        {
            Signal = signal,
            Confidence = (float)Math.Round(Math.Max(riskScore, healthScore) * 100f),
            Reasoning = $"สถานะสุขภาพ: {plant?.HealthStatus ?? "ไม่ทราบ"}, การสังเกตโรค 14 วัน: {recentDiseaseObs.Count} ครั้ง, ความชื้นเฉลี่ย: {avgHumidity:F1}%",
            RecommendedAction = action,
        };
    }
}
