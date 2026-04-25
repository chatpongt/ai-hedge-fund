using FruitGardenApi.Models.HR;
using FruitGardenApi.Services.HR;
using Microsoft.AspNetCore.Mvc;

namespace FruitGardenApi.Controllers;

[ApiController]
[Route("api/hr")]
public class HRController(IHRService svc) : ControllerBase
{
    [HttpGet("workers")]
    public async Task<IActionResult> GetWorkers() => Ok(await svc.GetWorkersAsync());

    [HttpPost("workers")]
    public async Task<IActionResult> CreateWorker([FromBody] Worker worker) =>
        CreatedAtAction(nameof(GetWorkerById), new { id = worker.Id }, await svc.CreateWorkerAsync(worker));

    [HttpGet("workers/{id}")]
    public async Task<IActionResult> GetWorkerById(Guid id)
    {
        var worker = await svc.GetWorkerByIdAsync(id);
        return worker is null ? NotFound() : Ok(worker);
    }

    [HttpPut("workers/{id}")]
    public async Task<IActionResult> UpdateWorker(Guid id, [FromBody] Worker worker)
    {
        if (id != worker.Id) return BadRequest();
        return Ok(await svc.UpdateWorkerAsync(worker));
    }

    [HttpPost("assignments")]
    public async Task<IActionResult> AssignTask([FromBody] WorkAssignment assignment) =>
        CreatedAtAction(nameof(GetAssignments), await svc.AssignTaskAsync(assignment));

    [HttpGet("assignments")]
    public async Task<IActionResult> GetAssignments([FromQuery] Guid? workerId = null, [FromQuery] string? status = null) =>
        Ok(await svc.GetAssignmentsAsync(workerId, status));

    [HttpPut("assignments/{id}/complete")]
    public async Task<IActionResult> CompleteAssignment(Guid id, [FromQuery] float actualHours = 8, [FromQuery] string? notes = null) =>
        Ok(await svc.CompleteAssignmentAsync(id, actualHours, notes));

    [HttpPost("attendance")]
    public async Task<IActionResult> LogAttendance([FromBody] AttendanceLog log) =>
        CreatedAtAction(nameof(GetAttendance), await svc.LogAttendanceAsync(log));

    [HttpGet("attendance")]
    public async Task<IActionResult> GetAttendance([FromQuery] Guid? workerId = null, [FromQuery] int? year = null, [FromQuery] int? month = null) =>
        Ok(await svc.GetAttendanceAsync(workerId, year, month));

    [HttpGet("payroll")]
    public async Task<IActionResult> GetPayroll([FromQuery] DateOnly periodStart, [FromQuery] DateOnly periodEnd) =>
        Ok(await svc.CalculatePayrollAsync(periodStart, periodEnd));

    [HttpPost("payroll/record")]
    public async Task<IActionResult> RecordPayroll([FromBody] PayrollRecord record) =>
        CreatedAtAction(nameof(GetPayroll), await svc.RecordPayrollAsync(record));
}
