namespace FruitGardenApi.Models.HR;

public class WorkAssignment
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid TaskId { get; set; }
    public Guid WorkerId { get; set; }
    public DateOnly AssignedDate { get; set; }
    public DateOnly DueDate { get; set; }
    public string Status { get; set; } = "assigned"; // assigned, in_progress, completed
    public float? ActualHours { get; set; }
    public string? CompletionNotes { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? CompletedAt { get; set; }

    public Worker? Worker { get; set; }
}
