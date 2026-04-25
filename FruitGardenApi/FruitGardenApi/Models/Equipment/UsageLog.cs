namespace FruitGardenApi.Models.Equipment;

public class UsageLog
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EquipmentId { get; set; }
    public Guid? WorkerId { get; set; }
    public DateOnly UsageDate { get; set; }
    public float HoursUsed { get; set; }
    public Guid? ZoneId { get; set; }
    public string TaskDescription { get; set; } = "";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Equipment? Equipment { get; set; }
}
