using FruitGardenApi.Models.HR;
using FruitGardenApi.Repositories;

namespace FruitGardenApi.Services.HR;

public class HRService(IHRRepository repo) : IHRService
{
    public Task<List<Worker>> GetWorkersAsync() => repo.GetWorkersAsync();
    public Task<Worker?> GetWorkerByIdAsync(Guid id) => repo.GetWorkerByIdAsync(id);
    public Task<Worker> CreateWorkerAsync(Worker worker) => repo.CreateWorkerAsync(worker);
    public Task<Worker> UpdateWorkerAsync(Worker worker) => repo.UpdateWorkerAsync(worker);
    public Task<WorkAssignment> AssignTaskAsync(WorkAssignment assignment) => repo.CreateAssignmentAsync(assignment);
    public Task<List<WorkAssignment>> GetAssignmentsAsync(Guid? workerId = null, string? status = null) => repo.GetAssignmentsAsync(workerId, status);

    public async Task<WorkAssignment> CompleteAssignmentAsync(Guid assignmentId, float actualHours, string? notes = null)
    {
        var a = await repo.GetAssignmentByIdAsync(assignmentId) ?? throw new KeyNotFoundException();
        a.Status = "completed";
        a.ActualHours = actualHours;
        a.CompletionNotes = notes;
        a.CompletedAt = DateTime.UtcNow;
        return await repo.UpdateAssignmentAsync(a);
    }

    public Task<AttendanceLog> LogAttendanceAsync(AttendanceLog log) => repo.CreateAttendanceAsync(log);
    public Task<List<AttendanceLog>> GetAttendanceAsync(Guid? workerId = null, int? year = null, int? month = null) =>
        repo.GetAttendanceAsync(workerId, year, month);

    public async Task<List<PayrollSummary>> CalculatePayrollAsync(DateOnly periodStart, DateOnly periodEnd)
    {
        var workers = await repo.GetWorkersAsync();
        var attendance = await repo.GetAttendanceAsync(year: periodStart.Year, month: periodStart.Month);

        return workers.Select(w =>
        {
            var workerAttendance = attendance.Where(a => a.WorkerId == w.Id && a.HoursWorked > 0).ToList();
            var days = workerAttendance.Count;
            return new PayrollSummary(w.Id, w.Name, days, days * w.DailyWage);
        }).ToList();
    }

    public Task<PayrollRecord> RecordPayrollAsync(PayrollRecord record) => repo.CreatePayrollAsync(record);
}
