namespace FruitGardenApi.Models.Garden;

public class GardenObservation
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid PlantId { get; set; }
    public DateOnly ObservationDate { get; set; }
    public string Observer { get; set; } = "";
    public string ObsType { get; set; } = "general"; // pest, disease, growth, harvest, general
    public string Severity { get; set; } = "low"; // low, medium, high
    public string Notes { get; set; } = "";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Plant? Plant { get; set; }
}
