namespace FruitGardenApi.Models.Garden;

public class GardenZone
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public float AreaSqm { get; set; }
    public string SoilType { get; set; } = "loam"; // loam, clay, sandy
    public string IrrigationType { get; set; } = "manual"; // drip, sprinkler, manual
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<Plant> Plants { get; set; } = [];
}
