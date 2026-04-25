namespace FruitGardenApi.Models.Equipment;

public class MaintenanceRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EquipmentId { get; set; }
    public DateOnly MaintenanceDate { get; set; }
    public string MaintenanceType { get; set; } = ""; // oil_change, filter, belt, inspection, calibration
    public decimal Cost { get; set; }
    public string DoneBy { get; set; } = "";
    public string Notes { get; set; } = "";
    public DateOnly? NextDueDate { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Equipment? Equipment { get; set; }
}
