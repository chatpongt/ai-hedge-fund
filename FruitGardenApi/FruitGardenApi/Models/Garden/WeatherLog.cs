namespace FruitGardenApi.Models.Garden;

public class WeatherLog
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public DateOnly LogDate { get; set; }
    public float TempHigh { get; set; }
    public float TempLow { get; set; }
    public float RainfallMm { get; set; }
    public float HumidityPct { get; set; }
    public bool WillRain { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
