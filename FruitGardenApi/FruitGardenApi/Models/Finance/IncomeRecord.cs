namespace FruitGardenApi.Models.Finance;

public class IncomeRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid? PlantId { get; set; }
    public DateOnly Date { get; set; }
    public decimal Amount { get; set; }
    public string Source { get; set; } = "harvest_sale"; // harvest_sale, subsidy, other
    public float? QuantityKg { get; set; }
    public decimal? PricePerKg { get; set; }
    public string Notes { get; set; } = "";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
