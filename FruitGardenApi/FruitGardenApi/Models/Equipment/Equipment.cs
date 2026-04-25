namespace FruitGardenApi.Models.Equipment;

public class Equipment
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = "";
    public string EquipmentType { get; set; } = ""; // tractor, sprayer, irrigation_pump, hand_tool, vehicle
    public string Brand { get; set; } = "";
    public string Model { get; set; } = "";
    public DateOnly PurchaseDate { get; set; }
    public decimal PurchaseCost { get; set; }
    public string Status { get; set; } = "operational"; // operational, maintenance, repair, retired
    public float TotalHoursUsed { get; set; }
    public float NextMaintenanceHours { get; set; }
    public DateOnly? NextMaintenanceDate { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<UsageLog> UsageLogs { get; set; } = [];
    public ICollection<MaintenanceRecord> MaintenanceRecords { get; set; } = [];
    public ICollection<RepairRecord> RepairRecords { get; set; } = [];
}
