namespace FruitGardenApi.Models.Equipment;

public class RepairRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid EquipmentId { get; set; }
    public DateOnly ReportedDate { get; set; }
    public DateOnly? RepairedDate { get; set; }
    public string IssueDescription { get; set; } = "";
    public decimal RepairCost { get; set; }
    public string RepairedBy { get; set; } = "";
    public string Status { get; set; } = "pending"; // pending, in_repair, completed
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Equipment? Equipment { get; set; }
}
