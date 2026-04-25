namespace FruitGardenApi.Models.Garden;

public class Plant
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid ZoneId { get; set; }
    public string Name { get; set; } = "";
    public string Species { get; set; } = "";
    public string Variety { get; set; } = "";
    public DateOnly PlantedDate { get; set; }
    public string GrowthStage { get; set; } = "juvenile"; // seedling, juvenile, mature, bearing, dormant
    public string HealthStatus { get; set; } = "healthy"; // healthy, stressed, diseased, critical
    public float PositionX { get; set; }
    public float PositionY { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public GardenZone? Zone { get; set; }
    public ICollection<SoilReading> SoilReadings { get; set; } = [];
    public ICollection<GardenObservation> Observations { get; set; } = [];
    public ICollection<GardenTask> Tasks { get; set; } = [];
}
