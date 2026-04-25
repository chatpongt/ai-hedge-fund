namespace FruitGardenApi.Models.HR;

public class AttendanceLog
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid WorkerId { get; set; }
    public DateOnly Date { get; set; }
    public string? ClockIn { get; set; }   // "08:00"
    public string? ClockOut { get; set; }  // "17:00"
    public float HoursWorked { get; set; }
    public string? AbsenceReason { get; set; } // sick, leave, holiday
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Worker? Worker { get; set; }
}
