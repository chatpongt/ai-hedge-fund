using FruitGardenApi.Data;
using FruitGardenApi.Models.HR;
using Microsoft.EntityFrameworkCore;

namespace FruitGardenApi.Repositories;

public class HRRepository(AppDbContext db) : IHRRepository
{
    public Task<List<Worker>> GetWorkersAsync() => db.Workers.ToListAsync();

    public Task<Worker?> GetWorkerByIdAsync(Guid id) =>
        db.Workers.Include(w => w.Assignments).FirstOrDefaultAsync(w => w.Id == id);

    public async Task<Worker> CreateWorkerAsync(Worker worker)
    {
        db.Workers.Add(worker);
        await db.SaveChangesAsync();
        return worker;
    }

    public async Task<Worker> UpdateWorkerAsync(Worker worker)
    {
        db.Workers.Update(worker);
        await db.SaveChangesAsync();
        return worker;
    }

    public async Task<WorkAssignment> CreateAssignmentAsync(WorkAssignment assignment)
    {
        db.WorkAssignments.Add(assignment);
        await db.SaveChangesAsync();
        return assignment;
    }

    public Task<List<WorkAssignment>> GetAssignmentsAsync(Guid? workerId = null, string? status = null)
    {
        var q = db.WorkAssignments.Include(a => a.Worker).AsQueryable();
        if (workerId.HasValue) q = q.Where(a => a.WorkerId == workerId.Value);
        if (status != null) q = q.Where(a => a.Status == status);
        return q.OrderByDescending(a => a.AssignedDate).ToListAsync();
    }

    public Task<WorkAssignment?> GetAssignmentByIdAsync(Guid id) =>
        db.WorkAssignments.Include(a => a.Worker).FirstOrDefaultAsync(a => a.Id == id);

    public async Task<WorkAssignment> UpdateAssignmentAsync(WorkAssignment assignment)
    {
        db.WorkAssignments.Update(assignment);
        await db.SaveChangesAsync();
        return assignment;
    }

    public async Task<AttendanceLog> CreateAttendanceAsync(AttendanceLog log)
    {
        db.AttendanceLogs.Add(log);
        await db.SaveChangesAsync();
        return log;
    }

    public Task<List<AttendanceLog>> GetAttendanceAsync(Guid? workerId = null, int? year = null, int? month = null)
    {
        var q = db.AttendanceLogs.Include(a => a.Worker).AsQueryable();
        if (workerId.HasValue) q = q.Where(a => a.WorkerId == workerId.Value);
        if (year.HasValue) q = q.Where(a => a.Date.Year == year.Value);
        if (month.HasValue) q = q.Where(a => a.Date.Month == month.Value);
        return q.OrderByDescending(a => a.Date).ToListAsync();
    }

    public async Task<PayrollRecord> CreatePayrollAsync(PayrollRecord record)
    {
        db.PayrollRecords.Add(record);
        await db.SaveChangesAsync();
        return record;
    }

    public Task<List<PayrollRecord>> GetPayrollAsync(Guid? workerId = null)
    {
        var q = db.PayrollRecords.Include(p => p.Worker).AsQueryable();
        if (workerId.HasValue) q = q.Where(p => p.WorkerId == workerId.Value);
        return q.OrderByDescending(p => p.PeriodStart).ToListAsync();
    }
}
