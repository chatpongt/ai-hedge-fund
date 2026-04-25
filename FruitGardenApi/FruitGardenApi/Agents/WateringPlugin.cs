using System.ComponentModel;
using FruitGardenApi.Models.Garden;
using FruitGardenApi.Repositories;
using Microsoft.SemanticKernel;

namespace FruitGardenApi.Agents;

public class WateringPlugin(IGardenRepository repo)
{
    [KernelFunction("analyze_watering")]
    [Description("Analyzes soil moisture, recent rainfall, and watering history to determine if a plant needs water")]
    public async Task<GardenSignal> AnalyzeWateringAsync(Guid plantId)
    {
        var soil = await repo.GetLatestSoilReadingAsync(plantId);
        var weather = await repo.GetWeatherLogsAsync(7);

        var moisturePct = soil?.MoisturePct ?? 50f;
        var recentRainMm = weather.Sum(w => w.RainfallMm);
        var willRainSoon = weather.TakeLast(2).Any(w => w.WillRain);

        // Score: 0 = very dry (needs water), 1 = very wet (over watered)
        var moistureScore = Math.Clamp(moisturePct / 100f, 0f, 1f);
        var rainScore = Math.Clamp(recentRainMm / 30f, 0f, 1f);
        var forecastScore = willRainSoon ? 0.7f : 0.3f;

        var weighted = moistureScore * 0.5f + rainScore * 0.3f + forecastScore * 0.2f;

        string signal, action;
        if (weighted < 0.35f)
        {
            signal = "water_needed";
            action = "รดน้ำทันที 15-20 ลิตรต่อต้น";
        }
        else if (weighted > 0.75f)
        {
            signal = "over_watered";
            action = "หยุดรดน้ำ 2-3 วัน ตรวจสอบการระบายน้ำ";
        }
        else
        {
            signal = "adequate";
            action = "ไม่ต้องรดน้ำในวันนี้";
        }

        return new GardenSignal
        {
            Signal = signal,
            Confidence = (float)Math.Round(Math.Abs(weighted - 0.5f) * 200f),
            Reasoning = $"ความชื้นดิน: {moisturePct:F1}%, ฝนช่วง 7 วัน: {recentRainMm:F1} mm, คาดการณ์ฝน: {(willRainSoon ? "ใช่" : "ไม่")}",
            RecommendedAction = action,
        };
    }
}
