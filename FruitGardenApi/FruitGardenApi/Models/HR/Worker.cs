namespace FruitGardenApi.Models.HR;

public class Worker
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = "";
    public string Role { get; set; } = "general_worker"; // general_worker, specialist, supervisor, permanent, seasonal
    public decimal DailyWage { get; set; }
    public DateOnly StartDate { get; set; }
    public string Status { get; set; } = "active"; // active, on_leave, inactive
    public string Contact { get; set; } = "";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<WorkAssignment> Assignments { get; set; } = [];
    public ICollection<AttendanceLog> AttendanceLogs { get; set; } = [];
}
