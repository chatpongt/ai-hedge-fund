using FruitGardenApi.Models.HR;

namespace FruitGardenApi.Repositories;

public interface IHRRepository
{
    Task<List<Worker>> GetWorkersAsync();
    Task<Worker?> GetWorkerByIdAsync(Guid id);
    Task<Worker> CreateWorkerAsync(Worker worker);
    Task<Worker> UpdateWorkerAsync(Worker worker);
    Task<WorkAssignment> CreateAssignmentAsync(WorkAssignment assignment);
    Task<List<WorkAssignment>> GetAssignmentsAsync(Guid? workerId = null, string? status = null);
    Task<WorkAssignment?> GetAssignmentByIdAsync(Guid id);
    Task<WorkAssignment> UpdateAssignmentAsync(WorkAssignment assignment);
    Task<AttendanceLog> CreateAttendanceAsync(AttendanceLog log);
    Task<List<AttendanceLog>> GetAttendanceAsync(Guid? workerId = null, int? year = null, int? month = null);
    Task<PayrollRecord> CreatePayrollAsync(PayrollRecord record);
    Task<List<PayrollRecord>> GetPayrollAsync(Guid? workerId = null);
}
