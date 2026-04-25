namespace FruitGardenApi.Models.HR;

public class PayrollRecord
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid WorkerId { get; set; }
    public DateOnly PeriodStart { get; set; }
    public DateOnly PeriodEnd { get; set; }
    public int DaysWorked { get; set; }
    public decimal TotalAmount { get; set; }
    public DateOnly? PaidDate { get; set; }
    public string Status { get; set; } = "pending"; // pending, paid
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Worker? Worker { get; set; }
}
