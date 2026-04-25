namespace FruitGardenApi.Models.Garden;

public class SoilReading
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid PlantId { get; set; }
    public DateOnly ReadingDate { get; set; }
    public float Ph { get; set; }
    public float MoisturePct { get; set; }
    public float NitrogenPpm { get; set; }
    public float PhosphorusPpm { get; set; }
    public float PotassiumPpm { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Plant? Plant { get; set; }
}
