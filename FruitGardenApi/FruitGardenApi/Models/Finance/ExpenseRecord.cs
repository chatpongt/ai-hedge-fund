namespace FruitGardenApi.Models.Finance;

public class ExpenseRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid? PlantId { get; set; }
    public DateOnly Date { get; set; }
    public decimal Amount { get; set; }
    public string Category { get; set; } = "other"; // fertilizer, pesticide, labor, water, equipment, other
    public string Description { get; set; } = "";
    public string? Vendor { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
