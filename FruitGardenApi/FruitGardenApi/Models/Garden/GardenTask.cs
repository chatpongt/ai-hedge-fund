namespace FruitGardenApi.Models.Garden;

public class GardenTask
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid? PlantId { get; set; }
    public string TaskType { get; set; } = ""; // water, fertilize, prune, spray, harvest
    public string Priority { get; set; } = "medium"; // urgent, high, medium, low
    public DateOnly DueDate { get; set; }
    public string Status { get; set; } = "pending"; // pending, in_progress, completed, skipped
    public string Instructions { get; set; } = "";
    public Guid? AssignedWorkerId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? CompletedAt { get; set; }

    public Plant? Plant { get; set; }
}
