using FruitGardenApi.Models.HR;

namespace FruitGardenApi.Services.HR;

public record PayrollSummary(Guid WorkerId, string WorkerName, int DaysWorked, decimal TotalAmount);

public interface IHRService
{
    Task<List<Worker>> GetWorkersAsync();
    Task<Worker?> GetWorkerByIdAsync(Guid id);
    Task<Worker> CreateWorkerAsync(Worker worker);
    Task<Worker> UpdateWorkerAsync(Worker worker);
    Task<WorkAssignment> AssignTaskAsync(WorkAssignment assignment);
    Task<List<WorkAssignment>> GetAssignmentsAsync(Guid? workerId = null, string? status = null);
    Task<WorkAssignment> CompleteAssignmentAsync(Guid assignmentId, float actualHours, string? notes = null);
    Task<AttendanceLog> LogAttendanceAsync(AttendanceLog log);
    Task<List<AttendanceLog>> GetAttendanceAsync(Guid? workerId = null, int? year = null, int? month = null);
    Task<List<PayrollSummary>> CalculatePayrollAsync(DateOnly periodStart, DateOnly periodEnd);
    Task<PayrollRecord> RecordPayrollAsync(PayrollRecord record);
}
