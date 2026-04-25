namespace FruitGardenApi.Models.Finance;

public class BudgetPlan
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Period { get; set; } = ""; // e.g. "2025-Q1", "2025-01"
    public decimal TotalBudget { get; set; }
    public string CategoriesJson { get; set; } = "{}"; // JSON: { "fertilizer": 5000, "labor": 20000 }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
